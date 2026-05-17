# AGENTS.md — Working in this repo

Brief for Claude Code, Codex, Cursor, and any other coding agent that
opens this repository.

## Purpose

This repo is a starter kit for builders who want to ship a poker agent
to **dev.fun Arena PVE Benchmark mode**. The kit registers, opens a
benchmark match against a fixed reference panel of 5 DeepCFR bots,
polls for turns, and submits legal actions until the match ends.

## Critical facts (do not deviate)

- **Mode is PVE Benchmark, not PVP lobby.** Use
  `POST /texas/benchmark/start` + `GET /texas/benchmark/status`, never
  `POST /texas/join`.
- **`reasoning` field is required on benchmark actions.** YAML flow
  style, max 150 characters. Format:
  `{vr: "<range>", ke: "<num+unit>", bf: [<features>], pp: "<plan>", sr: "<size reason>"}`
- **Phases are `queued -> panel_acting -> waiting_user -> completed`.**
  The agent only submits when `match.phase == "waiting_user"` and a
  `table` object is present.
- **`amount` semantics = total chips committed on this street after
  acting**, not the increment.
- **Never hardcode API field names.** `GET /__introspection` is the
  live source of truth. For this kit we copy field names from the
  TypeBox schemas as of build time, but production agents should
  re-fetch introspection at session start.
- **Auth header**: `x-arena-api-key: <apiKey>`. Never log it.
- **Poll interval ~2s with jitter.** Tables auto-fold on timeout.

## File map

- `examples/agent.py` — L1 heuristic agent. The decision logic
  builders edit lives in `decide()`. Everything above and below
  `decide()` is glue (HTTP client, registration, polling, state).
- `examples/llm_agent.py` — L2 starter. Same loop, but `decide()`
  delegates to Anthropic Claude. Falls back to the L1 heuristic on
  parse failure or timeout.
- `examples/prompt.md` — copy-paste prompt for any coding agent that
  can read markdown and call HTTP.
- `docs/play.md` — verbose onboarding doc, end-to-end credentials and
  game flow.
- `docs/strategy.md` — three-tier strategy guide (L1 / L2 / L3).
- `pyproject.toml` — uv-managed. Required deps: httpx, python-dotenv,
  treys, pokerkit. Optional: `[llm]` -> anthropic, `[dev]` -> pytest,
  respx.

## Testing

The repo ships a small `pytest` suite in `tests/` (gitignored from the
public starter but used in CI). For local verification, mock the
endpoints with `respx`:

- `POST /auth/register`
- `POST /texas/benchmark/start`
- `GET  /texas/benchmark/status`  ← returns `table` directly in benchmark mode
- `POST /texas/action`
- `GET  /__introspection`

There is no `/texas/pending-actions` call in the benchmark loop. The
status endpoint embeds the live table when it is your turn.

Run `examples/agent.py --dry-run` to use the built-in in-process mock
loop without network access. `--dry-run` wires an `httpx.MockTransport`
into the client so the full happy path (register → benchmark/start →
status × N → action) runs end-to-end with zero outbound traffic.

## When editing `decide()`

You only need to look at `examples/agent.py`. Everything outside
`decide()` is glue and rarely changes. Inputs you get:

- `table["allowedActions"]["availableActions"]` — legal action list
- `table["allowedActions"]["callChips"]` — chips needed to call
- `table["allowedActions"]["raiseRange"]` — `{min, max}` or `null`
- `table["allowedActions"]["betRange"]` — `{min, max}` or `null`
- `table["potChips"]`, `table["boardCards"]`, `table["seats"]`
- `table["selfSeatNumber"]` (use to find your seat in `seats`)
- `table.get("secondsUntilDeadline", 10)` — synthesized client-side

Return: `{"action": str, "amount": int?, "message": str, "reasoning": str}`.
`reasoning` must be YAML flow style under 150 chars.

## Style

Keep diffs small. This repo is a sandbox, not a framework. If you
need to add a new helper, put it inside `examples/agent.py` first. We
only break things out into a package if at least two files would
import it.
