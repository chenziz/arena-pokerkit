"""Arena HTTP client + introspection + credential helpers.

This module is the "plumbing" you usually don't need to read or edit.
It wraps the Arena REST API with:

  - httpx client with 429/5xx retry + Retry-After honored
  - typed ArenaError for surfaced 4xx
  - introspection fetch + required-endpoint assertion (fail loud, not 404 mid-hand)
  - terminal phase/status resolution from the live schema
  - idempotent credential cache (re-verifies cached key via /agent/me)
  - small JSON state cache for cross-run continuity

Builders normally only touch `examples/agent.py` — this file is shared by
`agent.py`, `llm_agent.py`, and `mock.py`.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

import httpx


DEFAULT_BASE = "https://b-arena.dev.fun/api/arena"
MOCK_BASE = "http://mock.local/api/arena"  # --dry-run rebinds to this
CREDS_PATH = Path(".arena-credentials")
STATE_PATH = Path(".arena-poker-state")
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
            "and update REQUIRED_ENDPOINTS in examples/arena_client.py."
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
    """Write atomically using a unique per-process tempfile so two concurrent
    agents in the same cwd cannot clobber each other's `.tmp` file."""
    parent = path.parent if str(path.parent) else Path(".")
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(parent) if str(parent) else None,
    )
    try:
        with os.fdopen(fd, "w") as f:
            f.write(contents)
        os.replace(tmp_name, str(path))
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
