# AGENTS.md — Working in this repo

Brief for Claude Code, Codex, Cursor, and any other coding agent that
opens this repository.

## Purpose

This repo is a starter kit for builders who want to ship a poker agent
to **dev.fun Arena Poker Eval Benchmark mode**. The kit registers,
opens a benchmark match against a fixed reference panel of DeepCFR bots,
polls `/texas/pending-actions` for turns, and submits legal actions
until the match ends.

## Critical facts (do not deviate)

- **Mode is Poker Eval Benchmark, not PVP lobby.** Use
  `POST /texas/benchmark/start` to enter, and
  `GET /texas/pending-actions` as the primary action poll — never
  `POST /texas/join` (that's the lobby route).
- **Loop matches the live poker-eval skill verbatim**:
  ```
  benchmark/start → loop:
      GET /texas/pending-actions   (tight, returns tables[] when YOUR turn)
      POST /texas/action            (submit decision with required reasoning)
      GET /texas/benchmark/status   (periodic refresh + terminal detection)
  ```
- **Introspect at startup.** Call `GET /__introspection` after auth and
  verify every endpoint we plan to use is present (`REQUIRED_ENDPOINTS`
  in `examples/agent.py`). Read terminal phase/status enums from the
  schema — do NOT hardcode `{"completed","cancelled","failed"}`.
- **`reasoning` field is required on benchmark actions.** YAML flow
  style, max 150 characters. Format:
  `{vr: "<range>", ke: "<num+unit>", bf: [<features>], pp: "<plan>", sr: "<size reason>"}`
  Build capped field values first; if the serialized object exceeds
  150 chars, fall back to a known-valid short object — never blind-slice.
- **`amount` semantics = total chips committed on this street after
  acting**, not the increment.
- **Auth header**: `x-arena-api-key: <apiKey>`. Never log it. After
  loading cached credentials, verify with `GET /agent/me`; on 401/403
  discard and re-register.
- **Pending-actions poll**: ~1s with jitter. Tables auto-fold on
  timeout, so sort by earliest `actionDeadlineAt` and act on the
  freshest pending table.

## File map

- `examples/agent.py` — L1 heuristic agent. The decision logic
  builders edit lives in `decide()`. Everything above and below
  `decide()` is glue (HTTP client, registration, introspection,
  polling, state).
- `examples/llm_agent.py` — L2 starter. Same loop, but `decide()`
  delegates to Anthropic Claude. Falls back to the L1 heuristic on
  parse failure or timeout. `--dry-run --mock-llm` exercises
  `llm_decide()` end-to-end without network or Anthropic credits.
- `examples/prompt.md` — copy-paste prompt for any coding agent that
  can read markdown and call HTTP.
- `docs/play.md` — verbose onboarding doc, end-to-end credentials and
  game flow.
- `docs/strategy.md` — three-tier strategy guide (L1 / L2 / L3) plus
  the **Auto Research** hook.
- `pyproject.toml` — uv-managed. Required deps: httpx, python-dotenv,
  treys, pokerkit. Optional: `[llm]` -> anthropic, `[dev]` -> pytest,
  respx.

## Auto Research hook

`examples/agent.py` exposes `retrieve_solver_context(table) -> dict`,
called immediately before `decide(table)` on every fresh pending table.
Default is a no-op. Override it to plug in preflop GTO charts,
postflop solver retrieval, or opponent style HUD pulled from
`/texas/agent-stats`. See `docs/strategy.md` for the L2/L3 patterns.

## Testing

Run `uv run pytest tests/` after changes. The committed suite
(`tests/test_smoke.py`) mocks the live endpoints with `respx` and
covers:

- `POST /auth/register` (one-shot; cached on rerun)
- `GET  /agent/me` (cached-cred verification path)
- `GET  /__introspection` (required-endpoint assertion)
- `POST /texas/benchmark/start`
- `GET  /texas/pending-actions` (primary action poll)
- `POST /texas/action` (asserts legal action + valid `reasoning` YAML)
- `GET  /texas/benchmark/status` (terminal phase detection)

For a no-deps smoke, `examples/agent.py --dry-run` wires an
`httpx.MockTransport` into the client so the full happy path runs
end-to-end with zero outbound traffic.

## When editing `decide()`

You only need to look at `examples/agent.py`. Everything outside
`decide()` is glue and rarely changes. Inputs you get:

- `table["allowedActions"]["availableActions"]` — legal action list
- `table["allowedActions"]["callChips"]` — chips needed to call
- `table["allowedActions"]["raiseRange"]` — `{min, max}` or `null`
- `table["allowedActions"]["betRange"]` — `{min, max}` or `null`
- `table["potChips"]`, `table["boardCards"]`, `table["seats"]`
- `table["selfSeatNumber"]` (use to find your seat in `seats`)
- `table["actionDeadlineAt"]` — epoch ms; the runner converts to seconds
- `research_context` — dict from `retrieve_solver_context()` (default `{}`)

Return: `{"action": str, "amount": int?, "message": str, "reasoning": str}`.
`reasoning` must be YAML flow style under 150 chars.

## Style

Keep diffs small. This repo is a sandbox, not a framework. If you
need to add a new helper, put it inside `examples/agent.py` first. We
only break things out into a package if at least two files would
import it.
