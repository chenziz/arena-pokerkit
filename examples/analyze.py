"""Failure analysis report for the Heuristic Learning loop.

Fetches your agent's recent submissions from Arena, identifies losing
patterns by position and hand, and prints a formatted report you can
paste directly into Claude Code / Codex to guide decide() improvements.

Usage:
    pokerkit analyze                      # most recent competition
    pokerkit analyze --match <compId>     # specific competition
    pokerkit analyze --top 10             # show top N worst hands (default 10)
    pokerkit analyze --out report.txt     # save to file (default: stdout)

Heuristic Learning workflow:
    1. pokerkit run --max-hands 50         (get baseline bb/100)
    2. cp examples/STRATEGY.md.template STRATEGY.md   (describe your strategy)
    3. pokerkit analyze --out failure_report.txt       (find losing patterns)
    4. paste STRATEGY.md + failure_report.txt + HL prompt into Claude Code
    5. pokerkit test                        (no regressions)
    6. pokerkit run --max-hands 50          (compare bb/100 delta)
    7. repeat from step 3
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from arena_client import ArenaClient, ArenaError, DEFAULT_BASE, CREDS_PATH

# 6-max seat → approximate position label (heuristic, not authoritative)
_SEAT_POS = {1: "BTN", 2: "SB", 3: "BB", 4: "UTG", 5: "MP", 6: "CO"}


def _load_creds() -> tuple[Optional[str], Optional[str]]:
    """Load (api_key, agent_id) from .arena-credentials if present, else env."""
    if CREDS_PATH.exists():
        try:
            c = json.loads(CREDS_PATH.read_text())
            return c.get("apiKey"), c.get("agentId") or c.get("id")
        except Exception:
            pass
    return os.environ.get("ARENA_API_KEY"), os.environ.get("ARENA_AGENT_ID")


def _fetch_submissions(client: ArenaClient, agent_id: Optional[str],
                       competition_id: Optional[str], limit: int) -> list[dict]:
    """Fetch per-hand submission data from /agent/submissions."""
    parts = [f"limit={limit}"]
    if agent_id:
        parts.append(f"agentId={agent_id}")
    if competition_id:
        parts.append(f"competitionId={competition_id}")
    qs = "?" + "&".join(parts)
    try:
        body = client.get(f"/agent/submissions{qs}")
    except ArenaError as e:
        print(f"[analyze] submissions fetch failed: {e}", file=sys.stderr)
        return []
    if isinstance(body, dict) and isinstance(body.get("data"), list):
        return body["data"]
    if isinstance(body, list):
        return body
    return []


def _resolve_latest_competition(submissions: list[dict]) -> Optional[str]:
    """Return the most-recent competitionId seen in submissions."""
    for sub in submissions:
        chal = sub.get("challenge") or {}
        cid = chal.get("competitionId") or chal.get("id")
        if cid:
            return cid
    return None


def analyze(submissions: list[dict], top_n: int = 10) -> str:
    """Produce a plain-text failure report from a list of submission dicts."""
    if not submissions:
        return (
            "No submissions found. Run `pokerkit run --max-hands 50` first,\n"
            "then re-run `pokerkit analyze`.\n"
        )

    total = len(submissions)
    wins = losses = 0
    by_seat: dict[int, dict] = {}
    all_hands: list[dict] = []

    for sub in submissions:
        data = sub.get("data") or {}
        payout = data.get("payoutChips") or 0
        committed = data.get("totalCommittedChips") or 0
        delta = payout - committed
        seat = data.get("seatNumber") or 0
        hole = list(data.get("holeCards") or [])
        reasoning = (data.get("reasoning") or "").strip()
        score = sub.get("score")

        if delta >= 0:
            wins += 1
        else:
            losses += 1

        if seat:
            rec = by_seat.setdefault(seat, {
                "seat": seat, "total": 0, "delta_sum": 0,
            })
            rec["total"] += 1
            rec["delta_sum"] += delta

        all_hands.append({
            "delta": delta,
            "seat": seat,
            "hole": hole,
            "reasoning": reasoning,
            "payout": payout,
            "committed": committed,
            "score": score,
        })

    # Sort worst hands (most negative delta first)
    all_hands.sort(key=lambda x: x["delta"])

    lines: list[str] = []
    sep = "=" * 62

    lines += [
        sep,
        "ARENA POKERKIT — FAILURE ANALYSIS REPORT",
        "(paste this into Claude Code alongside STRATEGY.md)",
        sep,
        f"Total submissions : {total}",
        f"Win rate          : {wins}/{total} ({100 * wins // total if total else 0}%)",
        f"Loss rate         : {losses}/{total}",
        "",
    ]

    # Position breakdown (worst first)
    lines.append("POSITION BREAKDOWN  (worst → best avg chip delta):")
    seat_rows = sorted(
        by_seat.values(),
        key=lambda r: r["delta_sum"] / max(r["total"], 1),
    )
    for r in seat_rows:
        pos = _SEAT_POS.get(r["seat"], f"seat{r['seat']}")
        avg = r["delta_sum"] / max(r["total"], 1)
        bar = "▼" if avg < 0 else "▲"
        lines.append(
            f"  {bar} Seat {r['seat']} ({pos:3})  {avg:+.0f} chips avg"
            f"  ({r['total']} hands)"
        )
    lines.append("")

    # Worst N hands
    n = min(top_n, len(all_hands))
    lines.append(f"WORST {n} DECISIONS (by chip delta):")
    for i, h in enumerate(all_hands[:n], 1):
        pos = _SEAT_POS.get(h["seat"], f"s{h['seat']}")
        hole_str = " ".join(h["hole"]) if h["hole"] else "??"
        lines.append(
            f"  #{i:02d}  {hole_str:7s}  {pos:3}  "
            f"delta={h['delta']:+d}"
            f"  (payout={h['payout']} committed={h['committed']})"
        )
        if h["reasoning"]:
            lines.append(f"       reasoning: {h['reasoning'][:80]}")
    lines.append("")

    # Top N winning hands (for contrast)
    best = sorted(all_hands, key=lambda x: x["delta"], reverse=True)[:min(3, len(all_hands))]
    lines.append("BEST 3 DECISIONS (for contrast):")
    for i, h in enumerate(best, 1):
        pos = _SEAT_POS.get(h["seat"], f"s{h['seat']}")
        hole_str = " ".join(h["hole"]) if h["hole"] else "??"
        lines.append(
            f"  #{i}  {hole_str:7s}  {pos:3}  delta={h['delta']:+d}"
        )
    lines.append("")

    lines += [
        sep,
        "NEXT STEP — paste to Claude Code:",
        '  "Read STRATEGY.md and this report. Which patterns do you see',
        "   in the losing hands? Improve decide() in examples/agent.py.",
        '   Zero LLM calls at runtime. Bake ranges and rules into code."',
        sep,
    ]

    return "\n".join(lines) + "\n"


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a failure analysis report for the Heuristic Learning loop.\n"
            "Fetches Arena submissions, ranks positions and hands by chip delta,\n"
            "and outputs a paste-ready report for Claude Code / Codex."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--match", default=None,
        help="competitionId to analyse (default: most recent)",
    )
    parser.add_argument(
        "--top", type=int, default=10,
        help="Number of worst hands to show (default 10)",
    )
    parser.add_argument(
        "--limit", type=int, default=200,
        help="Max submissions to fetch (default 200)",
    )
    parser.add_argument(
        "--out", default=None,
        help="Write report to file instead of stdout",
    )
    args = parser.parse_args(argv)

    load_dotenv()
    api_key, agent_id = _load_creds()
    if not api_key:
        print(
            "ERROR: no API key found.\n"
            "Run `pokerkit run --max-hands 1` first to register,\n"
            "or set ARENA_API_KEY in .env.",
            file=sys.stderr,
        )
        return 2

    base = os.environ.get("ARENA_API_BASE", DEFAULT_BASE)
    client = ArenaClient(base, api_key=api_key)
    try:
        subs = _fetch_submissions(client, agent_id, args.match, args.limit)
        report = analyze(subs, top_n=args.top)
        if args.out:
            Path(args.out).write_text(report)
            print(f"wrote → {args.out}")
        else:
            print(report, end="")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
