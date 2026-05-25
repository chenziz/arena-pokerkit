"""Unit tests for `_normalize_action_name` (v0.18.2).

The Arena wire format uses hyphenated `"all-in"`. Various user-written
decide() implementations have emitted variants — `AllIn`, `all_in`,
` all-in `, `allin`. Both `examples/agent.py` (heuristic path) and
`examples/llm_agent.py` (Level 5 runtime-LLM path) must normalise all
four to `"all-in"` before the membership check / wire submission.

Without this, a stray capitalisation or underscore silently 400s the
server mid-hand.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "examples"))

from agent import _normalize_action_name  # noqa: E402


@pytest.mark.parametrize(
    "raw",
    [
        "AllIn",
        "all_in",
        " all-in ",
        "allin",
        "ALL-IN",
        "All-In",
        "all-in",
    ],
)
def test_normalize_all_in_variants(raw: str) -> None:
    """Every reasonable variant of all-in canonicalises to `'all-in'`."""
    assert _normalize_action_name(raw) == "all-in"


def test_normalize_dict_form_preserves_other_fields() -> None:
    """Dict-form input rewrites only the `action` key, leaves the rest alone."""
    out = _normalize_action_name(
        {"action": "AllIn", "amount": 500, "message": "ship"}
    )
    assert out["action"] == "all-in"
    assert out["amount"] == 500
    assert out["message"] == "ship"


def test_normalize_dict_form_noop_when_already_canonical() -> None:
    """No-op fast path: canonical action returns the same dict object."""
    canonical = {"action": "all-in", "amount": 500}
    out = _normalize_action_name(canonical)
    # Either the same object or an equal dict — both are correct contracts.
    assert out["action"] == "all-in"
    assert out["amount"] == 500


def test_normalize_handles_other_actions() -> None:
    """Fold/check/call/bet/raise survive normalisation untouched (case + ws)."""
    assert _normalize_action_name("fold") == "fold"
    assert _normalize_action_name("FOLD") == "fold"
    assert _normalize_action_name(" check ") == "check"
    assert _normalize_action_name("Raise") == "raise"


def test_normalize_non_string_passthrough() -> None:
    """Non-string input is returned unchanged rather than crashing."""
    assert _normalize_action_name(None) is None
    assert _normalize_action_name(42) == 42


def test_validate_against_allowed_accepts_normalised_all_in() -> None:
    """The Level 5 LLM path's `_validate_against_allowed` must NOT treat
    `AllIn` / `all_in` / ` all-in ` / `allin` as illegal when the server's
    availableActions contains `all-in`."""
    from llm_agent import _validate_against_allowed  # noqa: E402

    table = {
        "allowedActions": {
            "availableActions": ["fold", "call", "all-in"],
            "allInToAmount": 500,
        }
    }
    for variant in ("AllIn", "all_in", " all-in ", "allin"):
        out = _validate_against_allowed(
            {"action": variant, "amount": 500}, table
        )
        assert out["action"] == "all-in", f"variant {variant!r} → {out!r}"
