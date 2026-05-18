"""Arena PokerKit — L1 heuristic agent.

End-to-end Poker Eval Benchmark loop, matched to the live poker-eval skill:

  1. load .env
  2. register (or load .arena-credentials, verified with GET /agent/me)
  3. introspect API at GET /__introspection — fail fast if endpoints moved
  4. POST /texas/benchmark/start
  5. tight loop:
       GET /texas/pending-actions?competitionId=... → tables[]
       if tables: pick earliest deadline → decide() → POST /texas/action
       else: periodically refresh GET /texas/benchmark/status
       exit when match status is terminal (set from introspection enum)
  6. persist .arena-poker-state

The decision logic builders typically edit lives in decide(). Everything
else is glue.

CLI:
    uv run examples/agent.py                       # live (uses .env)
    uv run examples/agent.py --competition-id <id> # override env
    uv run examples/agent.py --dry-run             # mock loop, no network
    uv run examples/agent.py --max-hands 10        # cap hands before exit
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

# treys is the fast hand evaluator; pokerkit comes along for the ride
# (builders can swap in PokerKit Monte Carlo if they want).
try:
    from treys import Card as TreysCard, Evaluator as TreysEvaluator, Deck as TreysDeck
    _HAS_TREYS = True
except Exception:  # pragma: no cover
    _HAS_TREYS = False


DEFAULT_BASE = "https://b-arena.dev.fun/api/arena"
MOCK_BASE = "http://mock.local/api/arena"  # --dry-run rebinds to this
MOCK_COMPETITION_ID = "comp_dryrun"
CREDS_PATH = Path(".arena-credentials")
STATE_PATH = Path(".arena-poker-state")
POLL_INTERVAL = 1.0        # tight pending-actions poll
POLL_JITTER = 0.3
STATUS_REFRESH_S = 8.0      # background refresh of benchmark/status
RETRY_MAX = 3

# Required endpoints we expect introspection to expose. If any are missing,
# the live API has moved and we fail fast rather than 404 mid-hand.
# Note: /__introspection is intentionally excluded — it's a meta-endpoint that
# does not list itself in its own output.
REQUIRED_ENDPOINTS = (
    ("POST", "/api/arena/auth/register"),
    ("GET",  "/api/arena/agent/me"),
    ("POST", "/api/arena/texas/benchmark/start"),
    ("GET",  "/api/arena/texas/benchmark/status"),
    ("GET",  "/api/arena/texas/pending-actions"),
    ("POST", "/api/arena/texas/action"),
)

# Cached-from-build-time terminal phases. We overwrite this with introspection
# values when available. Listed in poker-eval.md as "may be stale, derived
# from cached examples" — introspection wins.
FALLBACK_TERMINAL_PHASES = ("completed", "cancelled", "failed")
FALLBACK_TERMINAL_STATUSES = ("Completed", "Cancelled", "Failed")


# ─── HTTP client ────────────────────────────────────────────────────────────

class ArenaError(Exception):
    def __init__(self, status: int, body: Any, where: str = ""):
        super().__init__(f"{where} status={status} body={body}")
        self.status = status
        self.body = body
        self.where = where


class ArenaClient:
    """Thin httpx wrapper. Auto-attaches x-arena-api-key, retries 5xx,
    surfaces 4xx as exceptions."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: float = 30.0):
        self.base = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(timeout=timeout, trust_env=False)

    def close(self) -> None:
        self._client.close()

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["x-arena-api-key"] = self.api_key
        return h

    def _req(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base}{path}"
        backoff = 0.5
        last_exc: Optional[Exception] = None
        for attempt in range(RETRY_MAX):
            try:
                r = self._client.request(method, url, headers=self._headers(), **kwargs)
            except httpx.HTTPError as e:
                last_exc = e
                time.sleep(backoff)
                backoff *= 2
                continue
            try:
                body = r.json()
            except Exception:
                body = r.text
            # 429 rate limit — honor Retry-After then retry.
            if r.status_code == 429 and attempt < RETRY_MAX - 1:
                ra = r.headers.get("Retry-After")
                try:
                    wait = float(ra) if ra else backoff
                except ValueError:
                    wait = backoff
                time.sleep(max(wait, 0.0))
                backoff *= 2
                continue
            if r.status_code >= 500 and attempt < RETRY_MAX - 1:
                time.sleep(backoff)
                backoff *= 2
                continue
            if not r.is_success:
                raise ArenaError(r.status_code, body, where=f"{method} {path}")
            return body
        raise ArenaError(0, str(last_exc), where=f"{method} {path}")

    def get(self, path: str, **kwargs) -> Any:
        return self._req("GET", path, **kwargs)

    def post(self, path: str, json_body: Optional[dict] = None) -> Any:
        return self._req("POST", path, json=json_body)


# ─── Introspection ──────────────────────────────────────────────────────────

def fetch_introspection(client: ArenaClient) -> dict:
    """GET /__introspection at startup. Returns a parsed dict with at least
    {endpoints: [...]} so callers can resolve terminal phases / statuses."""
    try:
        schema = client.get("/__introspection")
    except ArenaError as e:
        raise SystemExit(
            f"[arena-pokerkit] introspection unreachable ({e.where} -> "
            f"{e.status}). The live API may be down; cannot continue safely."
        )
    if not isinstance(schema, dict):
        raise SystemExit("[arena-pokerkit] introspection returned non-object — refusing to continue.")
    return schema


def assert_endpoints(schema: dict, required: tuple[tuple[str, str], ...] = REQUIRED_ENDPOINTS) -> None:
    """Verify every (method, path) we plan to call is present in introspection.
    If anything is missing we fail loud, not silently 404 mid-hand."""
    endpoints = schema.get("endpoints") or []
    present = {(e.get("method"), e.get("path")) for e in endpoints if isinstance(e, dict)}
    missing = [pair for pair in required if pair not in present]
    if missing:
        raise SystemExit(
            "[arena-pokerkit] live API schema missing endpoint(s): "
            + ", ".join(f"{m} {p}" for m, p in missing)
            + ". The schema may have moved — read /api/arena/__introspection "
            "and update REQUIRED_ENDPOINTS in examples/agent.py."
        )


def resolve_terminal_phases(schema: dict) -> tuple[set[str], set[str]]:
    """Pull match.phase enum and match.status enum from the
    /texas/benchmark/start output schema. Falls back to cached lists if the
    schema can't be parsed. Returns (terminal_phases, terminal_statuses)."""
    phase_enum: list[str] = []
    status_enum: list[str] = []
    for ep in (schema.get("endpoints") or []):
        if not isinstance(ep, dict):
            continue
        if ep.get("path") != "/api/arena/texas/benchmark/start":
            continue
        out = ep.get("output") or {}
        match = ((out.get("properties") or {}).get("match")) or {}
        # match may be inside an anyOf
        candidates = match.get("anyOf") or [match]
        for cand in candidates:
            props = (cand.get("properties") or {})
            ph = props.get("phase") or {}
            st = props.get("status") or {}
            if ph.get("enum"):
                phase_enum = ph["enum"]
            if st.get("enum"):
                status_enum = st["enum"]
            if phase_enum and status_enum:
                break
        break

    if not phase_enum:
        phase_enum = list(FALLBACK_TERMINAL_PHASES) + ["queued", "panel_acting", "waiting_user"]
    if not status_enum:
        status_enum = list(FALLBACK_TERMINAL_STATUSES) + ["Running"]

    # Heuristic for "terminal" — anything other than Running/queued/panel_acting/waiting_user.
    live_phases = {"queued", "panel_acting", "waiting_user"}
    terminal_phases = {p for p in phase_enum if p.lower() not in live_phases and p != "Running"}
    terminal_statuses = {s for s in status_enum if s != "Running"}
    if not terminal_phases:
        terminal_phases = set(FALLBACK_TERMINAL_PHASES)
    if not terminal_statuses:
        terminal_statuses = set(FALLBACK_TERMINAL_STATUSES)
    return terminal_phases, terminal_statuses


# ─── Credentials + state ────────────────────────────────────────────────────

def load_or_register(client: ArenaClient, handle: str, name: str, quote: str) -> dict:
    """Idempotent: returns cached creds (verified with /agent/me) if
    .arena-credentials exists, otherwise POSTs /auth/register and caches
    the response. On 401/403 the cached key is discarded and we register
    fresh — matches arena.md auth-repair guidance."""
    if CREDS_PATH.exists():
        try:
            creds = json.loads(CREDS_PATH.read_text())
        except Exception:
            creds = {}
        key = creds.get("apiKey")
        if key:
            client.api_key = key
            try:
                me = client.get("/agent/me")
                if isinstance(me, dict) and (me.get("id") or me.get("agentId") or me.get("handle")):
                    return creds
            except ArenaError as e:
                if e.status in (401, 403):
                    print(f"[arena-pokerkit] cached key rejected ({e.status}); re-registering",
                          file=sys.stderr)
                    client.api_key = None
                    try:
                        CREDS_PATH.unlink()
                    except OSError:
                        pass
                else:
                    raise
    body = client.post("/auth/register", {
        "handle": handle, "name": name, "quote": quote, "description": "",
    })
    if isinstance(body, dict) and "apiKey" in body:
        client.api_key = body["apiKey"]
    _atomic_write(CREDS_PATH, json.dumps(body, indent=2))
    return body if isinstance(body, dict) else {}


def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    return {
        "hands_played": 0,
        "bankroll": 0,
        "last_action": None,
        "timeout_count": 0,
        "rejection_count": 0,
        "stale_count": 0,
    }


def save_state(state: dict) -> None:
    _atomic_write(STATE_PATH, json.dumps(state, indent=2))


def _atomic_write(path: Path, contents: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(contents)
    tmp.replace(path)


# ─── Hand strength estimation (treys) ───────────────────────────────────────

# Hand strength approximations used when treys is unavailable, or as a
# preflop fallback when there is no time for Monte Carlo.
_PREFLOP_EQUITY = {
    "AA": 0.85, "KK": 0.82, "QQ": 0.80, "JJ": 0.77, "TT": 0.75,
    "99": 0.72, "88": 0.69, "77": 0.66, "66": 0.63, "55": 0.60,
    "44": 0.57, "33": 0.54, "22": 0.50,
    "AKs": 0.67, "AKo": 0.65, "AQs": 0.66, "AQo": 0.64, "AJs": 0.65,
    "AJo": 0.63, "ATs": 0.64, "KQs": 0.63, "KQo": 0.61, "KJs": 0.62,
    "QJs": 0.60, "JTs": 0.58, "T9s": 0.54, "98s": 0.52,
}


def _hand_class(hole: list[str]) -> str:
    ranks = "23456789TJQKA"
    if len(hole) != 2:
        return ""
    r1, s1 = hole[0][0].upper(), hole[0][-1].lower()
    r2, s2 = hole[1][0].upper(), hole[1][-1].lower()
    if r1 not in ranks or r2 not in ranks:
        return ""
    if ranks.index(r1) < ranks.index(r2):
        r1, r2 = r2, r1
        s1, s2 = s2, s1
    if r1 == r2:
        return r1 + r2
    return f"{r1}{r2}{'s' if s1 == s2 else 'o'}"


def estimate_equity(hole: list[str], board: list[str], sims: int = 200,
                    deadline_s: float = 10.0) -> float:
    """Monte Carlo equity vs 1 random opponent. Falls back to preflop chart
    if treys is missing or time is tight."""
    cls = _hand_class(hole)
    if not _HAS_TREYS or deadline_s < 2.0:
        return _PREFLOP_EQUITY.get(cls, 0.45)
    if not board:
        # Preflop chart is more reliable than 200 random sims, and it's cheaper.
        return _PREFLOP_EQUITY.get(cls, 0.45)
    try:
        ev = TreysEvaluator()
        hero = [TreysCard.new(_to_treys(c)) for c in hole]
        board_t = [TreysCard.new(_to_treys(c)) for c in board]
        used = set(hero) | set(board_t)
        rng = random.Random(2026)
        wins = ties = 0
        for _ in range(sims):
            deck = TreysDeck()
            deck.cards = [c for c in deck.cards if c not in used]
            rng.shuffle(deck.cards)
            opp = [deck.cards.pop(), deck.cards.pop()]
            runout = []
            needed = 5 - len(board_t)
            for _ in range(needed):
                runout.append(deck.cards.pop())
            full_board = board_t + runout
            hero_rank = ev.evaluate(full_board, hero)
            opp_rank = ev.evaluate(full_board, opp)
            if hero_rank < opp_rank:
                wins += 1
            elif hero_rank == opp_rank:
                ties += 1
        return (wins + 0.5 * ties) / max(sims, 1)
    except Exception:
        return _PREFLOP_EQUITY.get(cls, 0.45)


def _to_treys(card_str: str) -> str:
    """Arena returns 'Ah' / 'AS'. treys wants 'Ah' (rank upper, suit lower).
    Also handle '10x' -> 'Tx'."""
    if not card_str:
        return "2c"
    r = card_str[0].upper()
    if card_str.startswith("10"):
        r = "T"
        s = card_str[2].lower() if len(card_str) > 2 else "x"
    else:
        s = card_str[-1].lower()
    return r + s


# ─── Auto Research hook ─────────────────────────────────────────────────────
# AUTO-RESEARCH HOOK
# Called immediately before decide(table) on every fresh pending table.
# Default impl is a no-op. Override to plug in:
#   - preflop GTO chart lookup (GTOWizard API, free 100/day tier)
#   - postflop solver retrieval (WASM Postflop, GTO+ exports, TexasSolver)
#   - opponent style HUD from Arena /texas/agent-stats?agentId=...
#   - vector-store solver lookups (Pinecone/Qdrant on labeled spots)
# See docs/strategy.md "Auto Research" for the L2/L3 wiring pattern.
def retrieve_solver_context(table: dict) -> dict:
    """Return a small dict of extra context for decide() / llm_decide().
    Empty by default. Builders override this and pass the result into their
    own decide() implementation. The L2 (LLM) and L3 (trained weights) paths
    benefit the most — see docs/strategy.md."""
    return {}


# ─── decide() — the part builders edit ──────────────────────────────────────

def decide(table: dict, deadline_s: float = 10.0,
           research_context: Optional[dict] = None) -> dict:
    """Return one action: {action, amount?, message, reasoning}.

    Reasoning is YAML flow style, max 150 chars, required on benchmark tables:
      {vr: "<range>", ke: "<num+unit>", bf: [<features>], pp: "<plan>", sr: "<size reason>"}

    research_context is an optional dict from retrieve_solver_context() —
    L1 ignores it. L2/L3 should consult it (preflop charts, postflop
    solver frequencies, opponent style)."""
    allowed = table.get("allowedActions") or {}
    available = allowed.get("availableActions") or []

    # Deadline fallback: prefer check, then small call, then fold.
    if deadline_s < 2.0:
        if allowed.get("canCheck"):
            return _build("check", None, table, allowed, eq=0.5, po=0.0,
                          msg="deadline tight, taking free option")
        return _build("fold", None, table, allowed, eq=0.0, po=1.0,
                      msg="deadline tight and price not justified")

    self_seat_num = table.get("selfSeatNumber")
    seats = table.get("seats") or []
    self_seat = next((s for s in seats if s.get("seatNumber") == self_seat_num), {})
    hole = list(self_seat.get("holeCards") or [])
    board = list(table.get("boardCards") or [])

    pot = int(table.get("potChips") or 0)
    call_chips = int(allowed.get("callChips") or 0)
    pot_odds = call_chips / max(pot + call_chips, 1) if call_chips else 0.0

    equity = estimate_equity(hole, board, sims=200, deadline_s=deadline_s)

    # Decision tree.
    action_name: str
    amount: Optional[int] = None
    if call_chips == 0:
        # Free option: check or bet for value.
        if equity > 0.7 and allowed.get("canBet"):
            br = allowed.get("betRange") or {}
            min_bet = int(br.get("min") or max(int(pot * 0.5), 1))
            max_bet = int(br.get("max") or min_bet)
            target = max(min_bet, min(int(pot * 0.66), max_bet))
            action_name, amount = "bet", target
        elif "check" in available:
            action_name = "check"
        elif "call" in available:
            action_name = "call"
        else:
            action_name = "fold"
    else:
        # Facing a bet.
        if equity < pot_odds - 0.05 and "fold" in available:
            action_name = "fold"
        elif equity > 0.8 and allowed.get("canRaise"):
            rr = allowed.get("raiseRange") or {}
            min_raise = int(rr.get("min") or call_chips * 2)
            max_raise = int(rr.get("max") or min_raise)
            target = max(min_raise, min(int(pot * 0.66 + call_chips * 2), max_raise))
            action_name, amount = "raise", target
        elif equity >= pot_odds + 0.05 and "call" in available:
            action_name = "call"
            # callToAmount = total committed this street after call
            cta = allowed.get("callToAmount")
            if cta is not None:
                amount = int(cta)
        elif "check" in available:
            action_name = "check"
        else:
            action_name = "fold"

    # Some validators reject `amount` on actions that don't take one. Strip it.
    if action_name in ("fold", "check", "call"):
        # call MAY accept amount = callToAmount; the schema permits but doesn't
        # require it. Safer to omit and let the server compute.
        amount = None

    msg = _human_message(action_name, equity, pot_odds, hole)
    return _build(action_name, amount, table, allowed,
                  eq=equity, po=pot_odds, msg=msg)


def _build(action: str, amount: Optional[int], table: dict, allowed: dict,
           eq: float, po: float, msg: str) -> dict:
    reasoning = _build_reasoning(action, eq, po, table, allowed)
    payload: dict[str, Any] = {
        "action": action,
        "message": msg[:500],
        "reasoning": reasoning,
    }
    if amount is not None:
        payload["amount"] = int(amount)
    return payload


# Safe fallback YAML — fits well under 150 chars and is grammatical.
_FALLBACK_REASONING = '{vr: "std", ke: "legal", pp: "pot control"}'


def _build_reasoning(action: str, equity: float, pot_odds: float,
                     table: dict, allowed: dict) -> str:
    """YAML flow style under 150 chars. Build capped field values first;
    fall back to a known-valid short object if the serialized string overflows,
    never blind-slice to 150 (per REVIEW-2 #6)."""
    board = table.get("boardCards") or []
    street = (table.get("street") or "Preflop")
    self_seat = table.get("selfSeatNumber") or 0
    # crude position label
    pos_label = "IP" if self_seat and self_seat % 2 == 0 else "OOP"
    plan_map = {"Preflop": "see flop", "Flop": "barrel T", "Turn": "ck R",
                "River": "showdown"}
    pp = f"{pos_label} {plan_map.get(street, 'pot ctrl')}"[:30]
    # board features
    if not board:
        bf = "[]"
    else:
        suits = [c[-1].lower() for c in board]
        feats: list[str] = []
        for s in set(suits):
            if suits.count(s) >= 2:
                feats.append(f"FD-{s}")
        ranks = [c[0].upper() for c in board]
        if len(set(ranks)) < len(ranks):
            feats.append("paired")
        bf = "[" + ",".join(feats[:3]) + "]" if feats else "[dry]"
    ke = f"{int(round(equity * 100))}% eq"[:30]
    if action in ("bet", "raise", "all-in"):
        sr = f"po {int(round(pot_odds * 100))}% sized for FE"[:30]
    elif action == "call":
        sr = f"po {int(round(pot_odds * 100))}% covered"[:30]
    else:
        sr = ""
    parts = [
        f'vr: "ln:unknown"',
        f'ke: "{ke}"',
        f'bf: {bf}',
        f'pp: "{pp}"',
    ]
    if sr:
        parts.append(f'sr: "{sr}"')
    yaml = "{" + ", ".join(parts) + "}"
    if len(yaml) <= 150:
        return yaml
    # Drop sr first, then bf, until it fits.
    for drop_i in (4, 2):
        if drop_i < len(parts):
            trimmed = parts[:drop_i] + parts[drop_i + 1:]
            candidate = "{" + ", ".join(trimmed) + "}"
            if len(candidate) <= 150:
                return candidate
    # Last resort — known-valid short object. Never blind-slice.
    return _FALLBACK_REASONING


def _human_message(action: str, equity: float, pot_odds: float, hole: list[str]) -> str:
    """One short sentence for replay. Never reveal hole cards."""
    eq_pct = int(round(equity * 100))
    po_pct = int(round(pot_odds * 100))
    if action == "fold":
        return f"equity {eq_pct}% short of price {po_pct}%, folding"
    if action == "check":
        return f"taking the free card, equity {eq_pct}%"
    if action == "call":
        return f"equity {eq_pct}% covers price {po_pct}%, calling"
    if action == "bet":
        return f"value bet, hand wants worse to call"
    if action == "raise":
        return f"raising for value, equity {eq_pct}% ahead of range"
    if action == "all-in":
        return f"jamming, equity {eq_pct}% plus fold equity"
    return action


# ─── Dry-run mock loop ──────────────────────────────────────────────────────

def _respx_active() -> bool:
    """True iff respx has installed its global httpx patcher. Used by the
    dry-run path so tests can still mock individual routes with respx."""
    try:
        from respx.mocks import HTTPCoreMocker  # type: ignore
    except Exception:
        return False
    try:
        return bool(list(HTTPCoreMocker.routers))
    except Exception:
        return False


def _mock_table(competition_id: str) -> dict:
    """Synthetic table identical in shape to a live pending-actions row:
    hero faces a $100 bet on Ah Kd 7c with AsKs."""
    return {
        "id": "tbl_dry",
        "tableId": "tbl_dry",
        "tableNumber": 1,
        "competitionId": competition_id,
        "status": "Active",
        "street": "Flop",
        "potChips": 300,
        "currentBet": 100,
        "minRaiseTo": 200,
        "startedAt": 1700000000000,
        "endedAt": None,
        "countdownEndsAt": None,
        "actionDeadlineAt": None,
        "currentSeatNumber": 1,
        "boardCards": ["Ah", "Kd", "7c"],
        "smallBlindChips": 10,
        "bigBlindChips": 20,
        "buyInChips": 2000,
        "winners": [],
        "seats": [
            {"seatId": "s1", "seatNumber": 1, "agentId": "me",
             "agentName": "Me", "agentHandle": "me", "status": "Active",
             "stackChips": 1800, "currentBetChips": 0,
             "totalCommittedChips": 0, "payoutChips": None,
             "holeCards": ["As", "Ks"]},
            {"seatId": "s2", "seatNumber": 2, "agentId": "opp",
             "agentName": "Opp", "agentHandle": "opp", "status": "Active",
             "stackChips": 1700, "currentBetChips": 100,
             "totalCommittedChips": 100, "payoutChips": None,
             "holeCards": None},
        ],
        "actingSeatNumber": 1,
        "selfSeatNumber": 1,
        "allowedActions": {
            "canFold": True, "canCheck": False, "canCall": True,
            "canBet": False, "canRaise": True,
            "callAmount": 100, "callChips": 100, "callToAmount": 100,
            "minBet": None, "minRaiseTo": 200, "maxCommit": 1800,
            "allInToAmount": 1800,
            "betRange": None,
            "raiseRange": {"min": 200, "max": 1800},
            "canAllIn": True,
            "availableActions": ["fold", "call", "raise", "all-in"],
            "amountSemantics": "toAmount",
            "amountHint": "total committed this street",
            "actionHint": "fold/call/raise to >= 200 / all-in 1800",
        },
        "recentEvents": [],
    }


def _mock_introspection_schema() -> dict:
    """Tiny introspection skeleton that satisfies assert_endpoints() and
    resolve_terminal_phases() in dry-run mode."""
    return {
        "endpoints": [
            {"method": "POST", "path": "/api/arena/auth/register", "auth": False},
            {"method": "GET",  "path": "/api/arena/agent/me", "auth": True},
            {"method": "GET",  "path": "/api/arena/__introspection", "auth": True},
            {"method": "POST", "path": "/api/arena/texas/benchmark/start", "auth": True,
             "output": {
                 "properties": {
                     "match": {
                         "properties": {
                             "phase": {"enum": ["queued", "panel_acting",
                                                "waiting_user", "completed",
                                                "cancelled", "failed"]},
                             "status": {"enum": ["Running", "Completed",
                                                 "Cancelled", "Failed"]},
                         }
                     }
                 }
             }},
            {"method": "GET",  "path": "/api/arena/texas/benchmark/status", "auth": True},
            {"method": "GET",  "path": "/api/arena/texas/pending-actions", "auth": True},
            {"method": "POST", "path": "/api/arena/texas/action", "auth": True},
        ]
    }


def run_mock_benchmark(args: argparse.Namespace,
                       decide_fn: Optional[Any] = None) -> int:
    """In-process dry-run: wire httpx.MockTransport into ArenaClient so the
    full happy path runs end-to-end with zero network access.

    decide_fn lets the L2 dry-run inject `llm_decide` so --dry-run actually
    exercises the LLM path (per REVIEW-2 #11)."""
    competition_id = (args.competition_id
                      or os.environ.get("ARENA_COMPETITION_ID")
                      or MOCK_COMPETITION_ID)
    table_state = _mock_table(competition_id)
    target_hands = max(int(args.max_hands or 1), 1)

    decide_fn = decide_fn or decide

    # State for the mock — pending_idx walks tables → empty;
    # status_idx walks running → completed after the action lands.
    pending_idx = {"i": 0}
    status_idx = {"i": 0}
    action_landed = {"v": False}

    def _status_payload(phase: str, completed: int, table: Optional[dict]) -> dict:
        return {
            "match": {
                "id": "m_dry", "competitionId": competition_id, "agentId": "agent_dry",
                "status": "Running" if phase != "completed" else "Completed",
                "phase": phase,
                "targetHands": target_hands, "completedHands": completed,
                "rawChipDelta": 250 if phase == "completed" else 0,
                "rawBbPer100": 12.5 if phase == "completed" else 0.0,
                "adjustedChipDelta": 200.0 if phase == "completed" else None,
                "adjustedBbPer100": 10.0 if phase == "completed" else None,
                "currentTableId": (table.get("tableId") if table else None),
                "startedAt": 1700000000000,
                "endedAt": 1700000010000 if phase == "completed" else None,
                "error": None,
            },
            "table": table,
            "participant": None,
        }

    action_log: list[dict] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/auth/register"):
            return httpx.Response(200, json={
                "agentId": "agent_dry", "apiKey": "dry_key_xxx",
                "handle": args.handle, "name": args.name,
            })
        if path.endswith("/agent/me"):
            return httpx.Response(200, json={
                "id": "agent_dry", "agentId": "agent_dry",
                "handle": args.handle, "name": args.name,
            })
        if path.endswith("/__introspection"):
            return httpx.Response(200, json=_mock_introspection_schema())
        if path.endswith("/texas/benchmark/start"):
            return httpx.Response(200, json=_status_payload("queued", 0, None))
        if path.endswith("/texas/pending-actions"):
            i = pending_idx["i"]
            pending_idx["i"] += 1
            if i == 0 and not action_landed["v"]:
                return httpx.Response(200, json={"tables": [table_state]})
            return httpx.Response(200, json={"tables": []})
        if path.endswith("/texas/benchmark/status"):
            i = status_idx["i"]
            status_idx["i"] += 1
            if action_landed["v"]:
                return httpx.Response(200, json=_status_payload("completed", target_hands, None))
            return httpx.Response(200, json=_status_payload("queued", 0, None))
        if path.endswith("/texas/action"):
            try:
                action_log.append(json.loads(request.content.decode()))
            except Exception:
                pass
            action_landed["v"] = True
            return httpx.Response(200, json={"table": table_state, "participant": None})
        return httpx.Response(404, json={"error": f"unmocked {path}"})

    client = ArenaClient(MOCK_BASE, api_key="dry_key_xxx")
    if not _respx_active():
        client._client.close()
        client._client = httpx.Client(transport=httpx.MockTransport(_handler),
                                      timeout=10.0, trust_env=False)
    state = load_state()

    try:
        creds = load_or_register(client, args.handle, args.name, args.quote)
        print(f"[arena-pokerkit] (dry-run) registered agent={creds.get('agentId', '?')} "
              f"base={MOCK_BASE}")

        schema = fetch_introspection(client)
        assert_endpoints(schema)
        terminal_phases, terminal_statuses = resolve_terminal_phases(schema)

        start_resp = client.post("/texas/benchmark/start",
                                 {"competitionId": competition_id})
        if not isinstance(start_resp, dict):
            raise ArenaError(0, str(start_resp)[:200], "benchmark/start malformed")
        match = start_resp.get("match") or {}
        print(f"[arena-pokerkit] (dry-run) benchmark started: phase={match.get('phase')} "
              f"target={match.get('targetHands')}")

        hands_acted = 0
        last_status_at = time.time()
        rng = random.Random()
        while True:
            # 1. Tight poll on pending-actions (primary).
            pending = client.get(
                f"/texas/pending-actions?competitionId={competition_id}")
            tables = (pending or {}).get("tables") if isinstance(pending, dict) else None
            if tables:
                # earliest deadline first
                tables = sorted(tables, key=lambda t: (t.get("actionDeadlineAt") or 0))
                table = tables[0]
                research_context = retrieve_solver_context(table)
                try:
                    action = decide_fn(table, deadline_s=10.0,
                                       research_context=research_context)
                except TypeError:
                    action = decide_fn(table, deadline_s=10.0)
                client.post("/texas/action",
                            {"tableId": table["tableId"], **action})
                hands_acted += 1
                state["hands_played"] = state.get("hands_played", 0) + 1
                save_state(state)
                if args.max_hands and hands_acted >= args.max_hands:
                    pass

            # 2. Background status refresh + terminal detection.
            now = time.time()
            if (not tables) or (now - last_status_at >= STATUS_REFRESH_S):
                status = client.get(
                    f"/texas/benchmark/status?competitionId={competition_id}")
                last_status_at = now
                if isinstance(status, dict):
                    match = status.get("match") or {}
                    phase = match.get("phase")
                    msstatus = match.get("status")
                    if phase in terminal_phases or msstatus in terminal_statuses:
                        score = match.get("adjustedBbPer100")
                        print(f"[arena-pokerkit] (dry-run) match terminal "
                              f"({phase}/{msstatus}) | hands={match.get('completedHands')} "
                              f"| adjustedBbPer100={score}")
                        # Preserve unknown fields by dumping the whole match object.
                        print(f"[arena-pokerkit] (dry-run) match summary: "
                              f"{json.dumps(match, sort_keys=True)}")
                        state["bankroll"] = int(match.get("rawChipDelta") or 0)
                        save_state(state)
                        if action_log:
                            print(f"[arena-pokerkit] (dry-run) decided "
                                  f"action={action_log[0].get('action')} "
                                  f"amount={action_log[0].get('amount')} "
                                  f"reasoning={action_log[0].get('reasoning')!r}")
                        return 0

            if not tables:
                time.sleep(POLL_INTERVAL + rng.uniform(-POLL_JITTER, POLL_JITTER))
    finally:
        client.close()


# ─── Main loop ──────────────────────────────────────────────────────────────

def run_live_benchmark(args: argparse.Namespace,
                       decide_fn: Optional[Any] = None) -> int:
    """Live Poker Eval loop — matches the live poker-eval skill verbatim:
       benchmark/start → loop(pending-actions → action; periodic
       benchmark/status for terminal detection).

    decide_fn lets the L2 caller inject llm_decide. Defaults to L1 decide."""
    load_dotenv()
    api_key = os.environ.get("ARENA_API_KEY") or None
    base = os.environ.get("ARENA_API_BASE", DEFAULT_BASE)
    competition_id = args.competition_id or os.environ.get("ARENA_COMPETITION_ID")
    if not competition_id:
        print("ERROR: --competition-id or ARENA_COMPETITION_ID is required",
              file=sys.stderr)
        return 2

    decide_fn = decide_fn or decide

    client = ArenaClient(base, api_key=api_key)
    state = load_state()

    try:
        # 1. Register / verify creds.
        creds = load_or_register(client, args.handle, args.name, args.quote)
        agent_id = creds.get("agentId") or creds.get("id") or "?"
        print(f"[arena-pokerkit] registered agent={agent_id} base={base}")

        # 2. Introspect — fail loud if the API moved.
        schema = fetch_introspection(client)
        assert_endpoints(schema)
        terminal_phases, terminal_statuses = resolve_terminal_phases(schema)
        print(f"[arena-pokerkit] introspection OK | "
              f"terminal phases={sorted(terminal_phases)} | "
              f"statuses={sorted(terminal_statuses)}")

        # 3. Start benchmark.
        try:
            start_resp = client.post("/texas/benchmark/start",
                                     {"competitionId": competition_id})
        except ArenaError as e:
            if e.status == 402:
                print("[arena-pokerkit] competition has entry fee — pay manually or "
                      "pick a free competition", file=sys.stderr)
                return 3
            raise
        if not isinstance(start_resp, dict):
            raise ArenaError(0, str(start_resp)[:200], "benchmark/start malformed")
        match = start_resp.get("match") or {}
        if match.get("phase") in terminal_phases or match.get("status") in terminal_statuses:
            print(f"[arena-pokerkit] benchmark already terminal: phase={match.get('phase')} "
                  f"summary={json.dumps(match, sort_keys=True)}")
            return 0
        print(f"[arena-pokerkit] benchmark started: phase={match.get('phase')} "
              f"target={match.get('targetHands')}")

        # 4. Main loop: pending-actions primary, status secondary.
        rng = random.Random()
        hands_acted = 0
        last_status_at = 0.0  # force one status check up front

        while True:
            tables = None
            try:
                pending = client.get(
                    f"/texas/pending-actions?competitionId={competition_id}")
                if isinstance(pending, dict):
                    raw = pending.get("tables") or []
                    tables = sorted(raw,
                                    key=lambda t: (t.get("actionDeadlineAt") or 0))
            except ArenaError as e:
                # 404 here is fatal — introspection said it should exist.
                print(f"[arena-pokerkit] pending-actions error: {e}", file=sys.stderr)
                if e.status in (404, 401, 403):
                    raise

            if tables:
                table = tables[0]
                deadline_ms = table.get("actionDeadlineAt") or 0
                deadline_s = (max(0.0, (deadline_ms / 1000.0) - time.time())
                              if deadline_ms else 10.0)
                research_context = retrieve_solver_context(table)
                try:
                    action = decide_fn(table, deadline_s=deadline_s,
                                       research_context=research_context)
                except TypeError:
                    action = decide_fn(table, deadline_s=deadline_s)
                payload = {"tableId": table["tableId"], **action}
                try:
                    client.post("/texas/action", payload)
                    hands_acted += 1
                    state["hands_played"] = state.get("hands_played", 0) + 1
                    state["last_action"] = {
                        "action": action["action"],
                        "amount": action.get("amount"),
                        "at": int(time.time()),
                    }
                    save_state(state)
                except ArenaError as e:
                    if e.status == 409:
                        state["stale_count"] = state.get("stale_count", 0) + 1
                        save_state(state)
                        # stale table — re-poll immediately, do not re-submit
                        continue
                    if e.status == 400:
                        state["rejection_count"] = state.get("rejection_count", 0) + 1
                        save_state(state)
                        try:
                            client.post("/texas/action", {
                                "tableId": table["tableId"],
                                "action": "fold",
                                "message": "fallback after illegal action",
                                "reasoning": _FALLBACK_REASONING,
                            })
                        except ArenaError:
                            pass
                        continue
                    raise
                if args.max_hands and hands_acted >= args.max_hands:
                    print(f"[arena-pokerkit] hit --max-hands={args.max_hands}, stopping")
                    return 0
                # After acting, fall through to the next loop iteration.

            # Periodic status refresh + terminal detection.
            now = time.time()
            if (not tables) or (now - last_status_at >= STATUS_REFRESH_S):
                try:
                    status = client.get(
                        f"/texas/benchmark/status?competitionId={competition_id}")
                except ArenaError as e:
                    print(f"[arena-pokerkit] status refresh error: {e}",
                          file=sys.stderr)
                    status = None
                last_status_at = now
                if isinstance(status, dict):
                    match = status.get("match") or {}
                    phase = match.get("phase")
                    msstatus = match.get("status")
                    if phase in terminal_phases or msstatus in terminal_statuses:
                        print(f"[arena-pokerkit] match terminal ({phase}/{msstatus}) | "
                              f"hands={match.get('completedHands')} | "
                              f"adjustedBbPer100={match.get('adjustedBbPer100')}")
                        # Preserve unknown fields with a full dump.
                        print(f"[arena-pokerkit] match summary: "
                              f"{json.dumps(match, sort_keys=True)}")
                        state["bankroll"] = int(match.get("rawChipDelta") or 0)
                        save_state(state)
                        return 0

            if not tables:
                time.sleep(POLL_INTERVAL + rng.uniform(-POLL_JITTER, POLL_JITTER))
    finally:
        client.close()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Arena PokerKit L1 agent")
    parser.add_argument("--competition-id", default=None,
                        help="Benchmark competition ID (else ARENA_COMPETITION_ID)")
    parser.add_argument("--dry-run", action="store_true",
                        help="In-process mock loop; never hits the network")
    parser.add_argument("--max-hands", type=int, default=0,
                        help="Stop after N hands (0 = run until terminal)")
    parser.add_argument("--handle", default="pokerkit-starter",
                        help="Agent handle for first registration")
    parser.add_argument("--name", default="PokerKit Starter",
                        help="Agent display name for first registration")
    parser.add_argument("--quote", default="probability over swagger",
                        help="Agent quote shown on the leaderboard")
    args = parser.parse_args(argv)

    if args.dry_run:
        return run_mock_benchmark(args)
    return run_live_benchmark(args)


if __name__ == "__main__":
    sys.exit(main())
