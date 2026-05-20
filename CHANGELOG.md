# Changelog

All notable changes to this project follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.2] — 2026-05-18

### Changed
- Default competition switched from Poker Eval S3 (5000 hands, ~2h) to Poker Eval S5 (500 hands, ~70 min) — 10× wall-clock improvement
- Quickstart in README recommends `--max-hands 50` for a ~5-10 min preview run, then the full match
- Heartbeat now shows live ETA based on observed per-hand speed
- Poll interval halved (2s → 1s) so empty pending-action polls return faster
- HF dataset sampled down to 500 hands with balanced 19-agent representation (was 3945)

## [0.3.1] — 2026-05-18

### Fixed (Codex round-5 review)
- Wrap `retrieve_solver_context()` in `try/except` so one Auto Research crash
  no longer kills the live loop; falls back to `{}` with a logged warning.
- Validate `/texas/pending-actions` response shape (non-dict / non-list
  `tables` / rows without `tableId`) and degrade to status polling instead of
  raising mid-loop.
- Mid-match 401/403 now triggers exactly one credential re-register attempt
  before exiting with code 4 + a "fresh handle" remediation message.
- Emit a heartbeat line immediately after `benchmark/start`, before the first
  `decide()` call, so live mode shows signs of life within ~2 s.
- `_atomic_write()` uses a unique per-process tempfile (`tempfile.mkstemp`)
  to avoid races between two concurrent agents in the same cwd.

### Changed
- Extracted the runtime loop into `_run_benchmark_loop()` in `agent.py` so
  live and dry-run share one implementation (no more drift on 400 fallback,
  `--max-hands`, heartbeat throttle, or deadline computation).
- `tests/test_llm_parser.py` is now committed (removed from `.gitignore`).
- Added 4 smoke tests: 409 stale re-poll, 429 retry-with-backoff,
  malformed pending-actions response, terminal `cancelled` phase.

## [0.3.0] — 2026-05-18

### Added
- Status heartbeat in live + dry-run loop (`phase / completedHands / adjustedBbPer100 / pending`)
- `examples/research_static_chart.py` — runnable Auto Research example (preflop chart, no network)
- `--dry-run-scenario {instant,queued,stale}` CLI flag for dry-run path coverage
- README expected-output block, file map, and "local files created" note
- HF eval README: "How to read this" interpretation guide

### Changed
- `examples/agent.py` split (~1000 → ~340 lines) into:
  - `agent.py` — decide / equity / Auto Research hook (the file builders edit)
  - `arena_client.py` — HTTP client, introspection, credentials
  - `mock.py` — dry-run scaffolding (only loaded when `--dry-run`)
- Friendlier `.env` / `--competition-id` missing error with recovery commands
- Bumped to `version = "0.3.0"`

## [0.2.0] — 2026-05-18

### Added
- Auto Research hook before `decide(table)` in pending-actions loop
- L1/L2/L3 strategy guide in `docs/strategy.md`
- `--mock-llm` flag for L2 dry-run

### Changed
- Action loop now uses `/texas/pending-actions` per live `poker-eval` skill
- Startup calls `GET /__introspection` to verify endpoints
- Terminal phases derived from introspection schema (no hardcoded enum)

### Fixed
- LLM JSON parser handles reasoning strings with inner braces
- 429/Retry-After respected in HTTP client
- L1 reasoning YAML capped via field-level limits, not blind slice

## [0.1.0] — 2026-05-18

### Added
- Initial starter kit: L1 heuristic agent + L2 LLM agent + copy-paste prompt
- Mock-server smoke tests with `respx`
