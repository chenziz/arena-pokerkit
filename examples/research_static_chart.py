"""Runnable Auto Research example — tiny in-memory preflop chart.

A drop-in `retrieve_solver_context(table)` that returns the recommended
preflop action for the hero's hand class + position bucket. No network,
no API key — pure lookup table. Good enough to make decide()'s preflop
play meaningfully better than the default heuristic.

Wire it into agent.py by replacing the no-op stub:

    # in examples/agent.py, near the top of the file
    from research_static_chart import research_static_chart as retrieve_solver_context

Or call it explicitly from llm_agent.py — the result is serialized into
the LLM prompt as AUTO-RESEARCH CONTEXT.

Run standalone for a quick smoke check:

    uv run examples/research_static_chart.py
"""
from __future__ import annotations

from typing import Optional


# 6-max NLHE opening ranges, position × hand class → suggested action.
# This is a coarse caricature of a real preflop chart — good enough to
# show shape, NOT good enough to win a benchmark. Replace with a real
# GTOWizard / WASM Postflop / TexasSolver export when you ship.
_OPEN_CHART = {
    # UTG (tightest)
    "UTG": {
        "raise": {"AA", "KK", "QQ", "JJ", "TT", "99",
                  "AKs", "AKo", "AQs", "AJs", "KQs"},
        "call":  set(),
    },
    # Middle position
    "MP": {
        "raise": {"AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
                  "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs",
                  "KQs", "KJs", "QJs"},
        "call":  set(),
    },
    # Cutoff (wider)
    "CO": {
        "raise": {"AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55",
                  "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo",
                  "A9s", "A8s", "A7s", "A6s", "A5s",
                  "KQs", "KQo", "KJs", "KTs", "QJs", "QTs", "JTs", "T9s", "98s"},
        "call":  set(),
    },
    # Button (widest open)
    "BTN": {
        "raise": {"AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                  "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo",
                  "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                  "KQs", "KQo", "KJs", "KJo", "KTs", "K9s",
                  "QJs", "QTs", "Q9s", "JTs", "J9s", "T9s", "98s", "87s", "76s"},
        "call":  set(),
    },
    # Small blind (mixed, here simplified to a tight raise)
    "SB": {
        "raise": {"AA", "KK", "QQ", "JJ", "TT", "99", "88",
                  "AKs", "AKo", "AQs", "AQo", "AJs", "ATs", "KQs", "KJs", "QJs"},
        "call":  set(),
    },
    # Big blind (defends wide vs late opens; treat as call/check by default)
    "BB": {
        "raise": {"AA", "KK", "QQ", "JJ", "TT",
                  "AKs", "AKo", "AQs"},
        "call":  set(),  # BB calls happen automatically when checked to
    },
}

# 6-max seat → position label heuristic. Live Arena tables typically
# rotate the button so this is only correct for the canonical seating —
# real implementations should read seat.position once that field lands.
_SEAT_TO_POS_6MAX = {1: "BTN", 2: "SB", 3: "BB", 4: "UTG", 5: "MP", 6: "CO"}


def _hand_class(hole: list[str]) -> str:
    """Convert ['As', 'Ks'] -> 'AKs'. Returns '' if unparseable."""
    ranks = "23456789TJQKA"
    if not hole or len(hole) != 2:
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


def _position_label(table: dict) -> str:
    self_seat = table.get("selfSeatNumber") or 0
    return _SEAT_TO_POS_6MAX.get(self_seat, "MP")


def research_static_chart(table: dict) -> dict:
    """Return a small dict with preflop chart recommendation, hand class,
    and position bucket. Empty on postflop streets — postflop spots need
    a real solver, not a static chart.

    Shape:
      {
        "preflop_action": "raise" | "call" | "fold",
        "hand_class": "AKs",
        "position": "BTN",
        "source": "static-chart-v1",
      }
    """
    street = (table.get("street") or "Preflop").lower()
    if street != "preflop":
        return {}

    self_seat_num = table.get("selfSeatNumber")
    seats = table.get("seats") or []
    self_seat = next((s for s in seats if s.get("seatNumber") == self_seat_num), {})
    hole = list(self_seat.get("holeCards") or [])
    cls = _hand_class(hole)
    if not cls:
        return {}

    pos = _position_label(table)
    rules = _OPEN_CHART.get(pos) or {}
    if cls in rules.get("raise", set()):
        action = "raise"
    elif cls in rules.get("call", set()):
        action = "call"
    else:
        action = "fold"

    return {
        "preflop_action": action,
        "hand_class": cls,
        "position": pos,
        "source": "static-chart-v1",
    }


def _demo() -> int:
    """Quick smoke check: print recommendations for a few canonical spots."""
    spots = [
        {"label": "BTN AKs preflop",
         "table": {"street": "Preflop", "selfSeatNumber": 1,
                   "seats": [{"seatNumber": 1, "holeCards": ["As", "Ks"]}]}},
        {"label": "UTG 72o preflop",
         "table": {"street": "Preflop", "selfSeatNumber": 4,
                   "seats": [{"seatNumber": 4, "holeCards": ["7d", "2c"]}]}},
        {"label": "SB QQ preflop",
         "table": {"street": "Preflop", "selfSeatNumber": 2,
                   "seats": [{"seatNumber": 2, "holeCards": ["Qh", "Qd"]}]}},
        {"label": "BTN AKs FLOP (chart skips postflop)",
         "table": {"street": "Flop", "selfSeatNumber": 1,
                   "boardCards": ["Ah", "Kd", "7c"],
                   "seats": [{"seatNumber": 1, "holeCards": ["As", "Ks"]}]}},
        {"label": "CO 22 preflop",
         "table": {"street": "Preflop", "selfSeatNumber": 6,
                   "seats": [{"seatNumber": 6, "holeCards": ["2s", "2c"]}]}},
    ]
    for s in spots:
        print(f"{s['label']:48s} -> {research_static_chart(s['table'])}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_demo())
