"""Arena PokerKit — L2 LLM agent.

Same end-to-end loop as agent.py (pending-actions → decide → action,
periodic benchmark/status terminal check), but decide() delegates to
Anthropic Claude. Falls back to the L1 heuristic on any parse failure,
timeout, or missing API key.

Cost estimate: ~$0.02 per decision with Claude Sonnet 4.x at default
sizing. Run a small benchmark before pointing this at long matches.

CLI:
    uv run examples/llm_agent.py
    uv run examples/llm_agent.py --dry-run        # mock loop, no network
    uv run examples/llm_agent.py --dry-run --mock-llm   # mock loop, mocked LLM
    uv run examples/llm_agent.py --model haiku    # cheaper / faster
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Optional

# Reuse the L1 decision surface + shared plumbing.
from agent import (  # type: ignore
    _build_reasoning,
    decide as heuristic_decide,
    retrieve_solver_context,
    run_live_benchmark,
)


SYSTEM_PROMPT = """You are a probability-first No-Limit Texas Hold'em agent
playing dev.fun Arena PVE Benchmark.

You will receive a JSON table state. Pick exactly ONE legal action from
allowedActions.availableActions. Output ONE JSON object on the last line:

  {"action": "<name>", "amount": <int?>, "message": "<<=500 chars>",
   "reasoning": "<<=150 chars YAML flow>"}

Rules:
- action MUST be in availableActions.
- For bet/raise/all-in, amount is TOTAL chips committed on this street
  after acting, within allowedActions.{betRange,raiseRange}.{min,max}.
- For fold/check/call, omit amount.
- reasoning is YAML flow style, max 150 chars, format:
  {vr: "<range>", ke: "<num+unit>", bf: [<features>], pp: "<plan>",
   sr: "<size reason>"}
  vr=villain range (prefix ln: or typ:), ke=key estimate (e.g. "38% eq"),
  bf=board features (e.g. [FD-h, blk-Ahs]), pp=position+next-street plan,
  sr=sizing rationale (required for bet/raise/all-in).
- message is one short sentence about intent. Never reveal hole cards.
- Output ONLY the JSON object, nothing after it.
"""


# ─── Mock LLM (for --dry-run --mock-llm) ────────────────────────────────────

class _MockLLMResponse:
    def __init__(self, text: str) -> None:
        class _Block:
            def __init__(self, t: str) -> None:
                self.type = "text"
                self.text = t
        self.content = [_Block(text)]


class _MockAnthropic:
    """Drop-in stand-in for anthropic.Anthropic that always returns a
    parseable JSON action. Used by --mock-llm to exercise the parse +
    validate path without real network calls."""

    def __init__(self, *_, **__) -> None:
        self.messages = self

    def create(self, **kwargs) -> _MockLLMResponse:
        # Return a payload that exercises _parse_action_json + _validate_against_allowed.
        text = json.dumps({
            "action": "call",
            "message": "mock LLM says call for pot odds",
            "reasoning": '{vr: "std", ke: "55% eq", bf: [dry], pp: "IP call", sr: "po 25% covered"}',
        })
        return _MockLLMResponse(text)


_MOCK_LLM = False


def _maybe_mock_anthropic_module():
    """If --mock-llm is set, monkey-patch the anthropic SDK before llm_decide
    imports it. Returns a usable stand-in module."""
    if not _MOCK_LLM:
        return None
    class _Mod:
        Anthropic = _MockAnthropic
    return _Mod()


def llm_decide(table: dict, deadline_s: float = 10.0,
               model: str = "claude-sonnet-4-5",
               max_tokens: int = 800,
               research_context: Optional[dict] = None) -> dict:
    """Ask Claude for an action. Fall back to heuristic on any failure.

    research_context is the dict returned by retrieve_solver_context(table)
    — preflop chart, postflop solver frequencies, opponent stats. When
    non-empty, it's serialized into the user prompt as extra context."""
    mock_mod = _maybe_mock_anthropic_module()
    if mock_mod is not None:
        anthropic = mock_mod  # type: ignore
    else:
        try:
            import anthropic  # type: ignore
        except ImportError:
            return heuristic_decide(table, deadline_s=deadline_s,
                                    research_context=research_context)

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return heuristic_decide(table, deadline_s=deadline_s,
                                    research_context=research_context)

    if deadline_s < 3.0:
        # Not enough time for an LLM round-trip; use the local heuristic.
        return heuristic_decide(table, deadline_s=deadline_s,
                                research_context=research_context)

    if mock_mod is not None:
        client = anthropic.Anthropic()
    else:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = "TABLE STATE:\n" + json.dumps(_compact_table(table), separators=(",", ":"))
    if research_context:
        prompt += ("\n\nAUTO-RESEARCH CONTEXT:\n"
                   + json.dumps(research_context, separators=(",", ":")))
    prompt += "\n\nRespond with ONLY the JSON action object on the last line."

    try:
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            getattr(b, "text", "") for b in resp.content
            if getattr(b, "type", None) == "text"
        ).strip()
        action = _parse_action_json(text)
        if action is None:
            return heuristic_decide(table, deadline_s=deadline_s,
                                    research_context=research_context)
        action = _validate_against_allowed(action, table)
        # Validate reasoning shape — blind truncation can produce invalid
        # YAML flow and get rejected by the benchmark server.
        reasoning = action.get("reasoning", "") or ""
        if not (reasoning.startswith("{") and reasoning.endswith("}")
                and len(reasoning) <= 150
                and all(k in reasoning for k in ("vr:", "ke:", "pp:"))):
            action["reasoning"] = _build_reasoning(
                action.get("action", "fold"),
                0.0, 0.0, table, table.get("allowedActions") or {},
            )
        return action
    except Exception:
        return heuristic_decide(table, deadline_s=deadline_s,
                                research_context=research_context)


def _compact_table(table: dict) -> dict:
    """Drop noise so the prompt stays small."""
    allowed = table.get("allowedActions") or {}
    self_seat_num = table.get("selfSeatNumber")
    seats = table.get("seats") or []
    self_seat = next((s for s in seats if s.get("seatNumber") == self_seat_num), {})
    return {
        "street": table.get("street"),
        "potChips": table.get("potChips"),
        "boardCards": table.get("boardCards"),
        "hero": {
            "seatNumber": self_seat_num,
            "stackChips": self_seat.get("stackChips"),
            "holeCards": self_seat.get("holeCards"),
            "currentBet": self_seat.get("currentBetChips"),
        },
        "opponents": [
            {
                "seatNumber": s.get("seatNumber"),
                "stackChips": s.get("stackChips"),
                "currentBet": s.get("currentBetChips"),
                "status": s.get("status"),
            }
            for s in seats if s.get("seatNumber") != self_seat_num
        ],
        "allowedActions": {
            "availableActions": allowed.get("availableActions"),
            "callChips": allowed.get("callChips"),
            "callToAmount": allowed.get("callToAmount"),
            "betRange": allowed.get("betRange"),
            "raiseRange": allowed.get("raiseRange"),
            "minBet": allowed.get("minBet"),
            "minRaiseTo": allowed.get("minRaiseTo"),
        },
        "smallBlind": table.get("smallBlindChips"),
        "bigBlind": table.get("bigBlindChips"),
        "recentEvents": [
            {
                "type": e.get("type"),
                "summary": e.get("summary"),
            } for e in (table.get("recentEvents") or [])[-10:]
        ],
    }


def _strip_code_fences(text: str) -> str:
    """Strip ``` / ```json fences. Tolerate language tags and trailing fence."""
    s = text.strip()
    if not s.startswith("```"):
        return s
    nl = s.find("\n")
    if nl >= 0:
        s = s[nl + 1:]
    else:
        s = s.lstrip("`")
        if s.lower().startswith("json"):
            s = s[4:]
    if s.rstrip().endswith("```"):
        s = s.rstrip()[: -3]
    return s.strip()


def _extract_balanced_json(text: str) -> Optional[str]:
    """Find the first balanced {...} block, ignoring braces inside strings."""
    depth = 0
    start = -1
    in_str = False
    esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth == 0:
                continue
            depth -= 1
            if depth == 0 and start >= 0:
                return text[start:i + 1]
    return None


def _parse_action_json(text: str) -> Optional[dict]:
    """Parse the JSON action from LLM output. Tolerates fences and surrounding
    prose. Crucially does NOT split on inner braces (e.g. the YAML flow
    reasoning string contains `{...}`)."""
    s = _strip_code_fences(text)
    obj: Any = None
    try:
        obj = json.loads(s)
    except Exception:
        chunk = _extract_balanced_json(s)
        if chunk is None:
            return None
        try:
            obj = json.loads(chunk)
        except Exception:
            return None
    if not isinstance(obj, dict):
        return None
    if "action" not in obj or "message" not in obj or "reasoning" not in obj:
        return None
    obj["message"] = str(obj["message"])[:500]
    obj["reasoning"] = str(obj["reasoning"])
    return obj


def _validate_against_allowed(action: dict, table: dict) -> dict:
    """Coerce LLM action into something the server will accept."""
    allowed = table.get("allowedActions") or {}
    available = set(allowed.get("availableActions") or [])
    name = action.get("action")
    if name not in available:
        if "check" in available:
            action["action"] = "check"
            action.pop("amount", None)
        else:
            action["action"] = "fold"
            action.pop("amount", None)
        return action
    if name in ("fold", "check", "call"):
        action.pop("amount", None)
        return action
    amount = int(action.get("amount") or 0)
    if name == "bet":
        rng = allowed.get("betRange") or {}
    elif name == "raise":
        rng = allowed.get("raiseRange") or {}
    else:  # all-in
        rng = {"min": allowed.get("allInToAmount"), "max": allowed.get("allInToAmount")}
    lo = int((rng or {}).get("min") or amount or 0)
    hi = int((rng or {}).get("max") or amount or lo)
    if lo and hi:
        amount = max(lo, min(amount or lo, hi))
    action["amount"] = amount
    return action


def main(argv: Optional[list[str]] = None) -> int:
    global _MOCK_LLM
    parser = argparse.ArgumentParser(description="Arena PokerKit L2 LLM agent")
    parser.add_argument("--competition-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dry-run-scenario",
                        choices=("instant", "queued", "stale"),
                        default="instant")
    parser.add_argument("--mock-llm", action="store_true",
                        help="Use an in-memory mock LLM so --dry-run actually "
                             "exercises llm_decide() instead of falling back "
                             "to the heuristic.")
    parser.add_argument("--max-hands", type=int, default=0)
    parser.add_argument("--model", default="claude-sonnet-4-5")
    parser.add_argument("--handle", default="pokerkit-llm")
    parser.add_argument("--name", default="PokerKit LLM")
    parser.add_argument("--quote", default="thinking out loud")
    args = parser.parse_args(argv)

    _MOCK_LLM = bool(args.mock_llm)

    # Bind model into llm_decide via a small closure so the runner can
    # call decide_fn(table, deadline_s, research_context=...).
    def _decide(table: dict, deadline_s: float = 10.0,
                research_context: Optional[dict] = None) -> dict:
        return llm_decide(table, deadline_s=deadline_s, model=args.model,
                          research_context=research_context)

    if args.dry_run:
        from mock import run_mock_benchmark
        return run_mock_benchmark(args, decide_fn=_decide,
                                  retrieve_solver_context=retrieve_solver_context)
    return run_live_benchmark(args, decide_fn=_decide)


if __name__ == "__main__":
    sys.exit(main())
