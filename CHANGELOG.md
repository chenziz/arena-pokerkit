# Changelog

All notable changes to this project follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.7.0] — 2026-05-24 — "Local Self-Play Release"

### Added
- `pokerkit selfplay` — local headless self-play with **zero network
  calls**. Plays your `decide()` against simple in-process opponents
  (tight-passive / loose-passive / random / always-call / mixed) and
  prints bb/100 in ~1 second per 200 hands. Closes the "middle"
  iteration gap between unit tests (50 ms, no opponent) and Arena
  benchmark (3-5 min, real DeepCFR panel). Supports HU through 6-max,
  configurable stacks / blinds, RNG seed, and `--agent path/to/decide.py`
  for non-default agents.
- `examples/selfplay.py` — implementation; uses the bundled `pokerkit`
  library for the engine, with an adapter that builds the same `table`
  dict shape that `decide()` consumes from Arena's `/pending-actions`.
- Baseline reference verdict printed at end of every Arena run. After
  the terminal "match complete" line, agent now prints whether your
  score is `🏆 above heuristic baseline`, `✓ within heuristic baseline`,
  `↺ below baseline — iterate`, or `⚠ well below baseline — check
  bugs`, anchored to the typical L1 range of -15 to -5 bb/100 vs the
  DeepCFR panel.

### Fixed
- Stale mock credentials are now auto-detected and cleared on live
  runs. After a `pokerkit run --dry-run`, the `.arena-credentials`
  file contained `agentId=agent_dry` and an unusable mock key; the
  next live `pokerkit run` would 401 mid-match with a confusing
  error. `load_or_register` now refuses creds matching
  `agentId == "agent_dry"` or `apiKey.startswith("dry_"|"mock_")`
  and re-registers fresh.

## [0.6.0] — 2026-05-24 — "Two Paths Release"

### Changed
- **README repositioned around two explicit paths.** Local PokerKit
  (`pokerkit test`, `pokerkit run --dry-run`) is for fast iteration
  while editing `decide()`. Arena Evaluation (`pokerkit run` or Claude
  Code reading `/skills/arena.md`) is for real benchmarking against
  the DeepCFR reference panel. Previous framing ("two ways to build")
  conflated runtime evaluation with offline HF dataset analysis.
- README now clarifies that `pokerkit run` is a **Python shortcut** for
  the Arena path that skips the official onboarding skill's full
  flow (multi-competition picking, claim URL surfacing, partner
  invitations, heartbeats). Users who want those features should paste
  the prompt from https://b-arena.dev.fun/poker-eval into Claude Code,
  let it read `/skills/arena.md`, and follow the official flow. Both
  paths share `.arena-credentials`, so onboarding via Claude Code and
  iterating via `pokerkit` is a supported workflow.
- Two-paths decision matrix added to README (purpose / speed / network
  / opponent / when-to-use / commands per path).

## [0.5.1] — 2026-05-24

### Fixed
- `pokerkit analyze` now calls the correct Texas Hold'em endpoints
  (`/texas/recent-tables` + `/agent/{agentId}/replays`) instead of the
  prediction-style `/agent/submissions` (which returns 400 for Texas
  competitions). Validated end-to-end against a live Poker Eval S5
  match. Report now joins hole cards / position / board / winners from
  `recent-tables` with precise `chipDelta` per hand from `replays`.
- `/replays` limit clamped to 50 (server cap).

## [0.5.0] — 2026-05-23 — "Heuristic Learning Release"

### Added
- `pokerkit analyze` — failure analysis report for the Heuristic Learning
  loop; fetches `/agent/submissions`, ranks positions and hands by chip
  delta, outputs a paste-ready report for Claude Code / Codex
- `examples/analyze.py` — implementation of the `analyze` verb
- `examples/STRATEGY.md.template` — fillable poker strategy template;
  read by the coding agent alongside `failure_report.txt` to guide
  `decide()` improvements (zero LLM calls at runtime)
- Heuristic Learning loop section in `docs/strategy.md` — explains the
  paradigm (LLM writes code, not plays hands), 6-step loop diagram,
  and what research data to bake into `decide()`
- "Heuristic Learning mode" prompt in `examples/prompt.md` — copy-paste
  prompt for coding agents improving `decide()` offline
- "Improve your agent" section in README with HL loop quick-start

## [0.4.0] — 2026-05-22 — "Replay Release"

### Added
- `pokerkit replay <match-id>` — self-contained HTML viewer for past matches (single file, no server). Backed by live `/agent/{agentId}/replays` + `/agent/submissions`. Graceful fallback when the replays endpoint is absent.
- `pytest-pokerkit` scenario fixtures (`examples/testing.py`) — 20 canonical hands (preflop premium / preflop trash / cbet / draws / value bets / bluff catchers / multi-way / shoves) plus `tests/test_user_decide_example.py` showing how to unit-test your `decide()` in 50ms.
- `examples/skeletons/{always_fold,always_call,random_action}.py` — drop-in `decide()` agents to sanity-check your submission pipeline before plugging in your model.
- `pokerkit` branded CLI (`pokerkit run | replay | test | version`) via repo-root shell wrapper + `[project.scripts]` entry-point. `pokerkit run --agent path/to/decide.py` loads any external `decide()` symbol via `importlib.util`.
- `examples/colab/quickstart.ipynb` + Colab badge — browser-only onboarding (install / register / dry-run / 20-hand live preview).
- README terminal demo (`docs/demo.gif`).

### Changed
- `--max-hands N` now counts settled hands (server-side `match.completedHands`), not action submissions. The previous behavior stopped after ~N/3.5 hands because each hand averages ~3-4 action submissions; users setting `--max-hands 30` saw the run end after ~8 hands. We keep `hands_acted` for telemetry only and require at least one `/texas/benchmark/status` refresh before honoring the cap.
- README + docs time estimates corrected: full S5 match ~30-40 min (was misstated as ~70 min based on the S3 rate; verified at ~4-5 s/settled hand on S5), preview ~3-5 min (was 5-10 min).
- Starting heartbeat shows `0/?` for unknown target until first status refresh (was misleading `0/N` based on `--max-hands`).
- Version bumped to 0.4.0.

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
