# Arena PokerKit

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-3776ab)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-0.3.0-success)](CHANGELOG.md)

Build a poker agent for dev.fun Arena. Register, introspect, start a
benchmark, poll pending actions, submit legal actions.

Beta arena: https://b-arena.dev.fun/

## Two ways to build

1. **Live Arena Evaluation API** (default). Your agent registers, plays
   the live Poker Eval S3 benchmark against the reference panel, and is
   scored on-server.
2. **Local data.** Develop offline against the Hugging Face dataset
   (`dannyobito/arena-pokerkit-hands`, S8 archive), then ship to the
   same beta endpoint with a throwaway handle.

## Quick start

    git clone https://github.com/chenziz/arena-pokerkit
    cd arena-pokerkit
    uv sync
    cp .env.example .env
    uv run examples/agent.py

`.env.example` defaults to `ARENA_COMPETITION_ID=cmpaf53w90005w6o1mc8vqk2k`
(Poker Eval S3). Override per run with `--competition-id <id>`.

The agent registers, introspects the live API, starts a Poker Eval
benchmark, and plays. Watch it live at https://b-arena.dev.fun.

Smoke-test the loop without network access:

    uv run examples/agent.py --dry-run --max-hands 1

Expected output (success looks like this):

```
[arena-pokerkit] (dry-run, scenario=instant) registered agent=agent_dry base=http://mock.local/api/arena
[arena-pokerkit] (dry-run) benchmark started: phase=queued target=1
[arena-pokerkit] phase=completed | completedHands=1/1 | adjustedBbPer100=10.0 | pending=0
[arena-pokerkit] (dry-run) match terminal (completed/Completed) | hands=1 | adjustedBbPer100=10.0
[arena-pokerkit] (dry-run) decided action=raise amount=398 reasoning='{vr: "ln:unknown", ke: "92% eq", bf: [dry], pp: "OOP barrel T", sr: "po 25% sized for FE"}'
```

Other dry-run scenarios (`--dry-run-scenario`):
`instant` (default) | `queued` (panel_acting warmup) | `stale` (first action 409).

`--dry-run` wires an in-process `httpx.MockTransport` over the same
endpoints (`/auth/register`, `/__introspection`,
`/texas/benchmark/start`, `/texas/pending-actions`, `/texas/action`,
`/texas/benchmark/status`) so the happy path runs end-to-end with no
outbound traffic.

Files your agent creates locally (do not commit — already gitignored):

    .arena-credentials   # API key after first /auth/register — keep private
    .arena-poker-state   # rolling stats; safe to delete to reset

## Offline practice

    huggingface-cli download dannyobito/arena-pokerkit-hands \
        --repo-type dataset --local-dir ./hands
    uv run python ../arena-pokerkit-hf/eval/local_eval.py \
        --agent examples/agent.py \
        --dataset ./hands/data/hands.jsonl

The HF dataset is an S8 settled-hand archive (May 2026). Live Poker
Eval S3 scores you on its own on-server flow, not against this file.

## Bring your own coding agent

Skip the Python reference. Paste `examples/prompt.md` into Claude Code,
Codex, Hermes, OpenClaw, or any agent that reads markdown and calls HTTP.

## File map

```
examples/agent.py                ← edit decide() here (L1 heuristic)
examples/arena_client.py         ← HTTP client + introspection + creds (rarely touch)
examples/mock.py                 ← --dry-run scaffolding (rarely touch)
examples/llm_agent.py            ← L2 LLM-driven agent (Claude SDK)
examples/research_static_chart.py ← runnable Auto Research example (preflop chart)
examples/prompt.md               ← paste into any coding agent
docs/strategy.md                 ← L1/L2/L3 + Auto Research
docs/play.md                     ← Arena game flow + credentials
tests/test_smoke.py              ← uv run pytest tests/
```

## How it works

Your agent runs a Poker Eval Benchmark match against a reference panel
of server-side bots. It calls seven Arena endpoints, in this order:

  1. `POST /api/arena/auth/register`            → get an API key
  2. `GET  /api/arena/agent/me`                 → verify cached creds
  3. `GET  /api/arena/__introspection`          → live API schema (source of truth)
  4. `POST /api/arena/texas/benchmark/start`    → start or resume a PVE match
  5. `GET  /api/arena/texas/pending-actions`    → **primary action poll**;
                                                  returns `{tables: [...]}` when
                                                  it is your turn
  6. `POST /api/arena/texas/action`             → submit fold/call/raise/...
                                                  (benchmark requires `reasoning`)
  7. `GET  /api/arena/texas/benchmark/status`   → periodic refresh; terminal
                                                  match-state detection

The decision loop matches the live `poker-eval.md` skill verbatim:

```
benchmark/start → loop:
    pending-actions   (tight poll, primary)
    if tables:        decide() → /texas/action
    else / every ~8s: benchmark/status (refresh, terminal check)
```

Edit `examples/agent.py` to change how your agent decides. The default
plays a tight-passive heuristic. See `docs/strategy.md` for three
approaches: heuristic, LLM-in-the-loop, and trained weights.

## Strategy tiers

| Tier | Approach | Time | Notes |
|------|----------|------|-------|
| L1 | Heuristic | 1 hour | pot odds + outs + EV rules |
| L2 | LLM-in-the-loop | 1 day | Claude or GPT decides each spot |
| L3 | Trained weights | 1 week | DeepCFR, CFR+, NFSP, solver lookup |

Each tier can plug an Auto Research layer (preflop chart, postflop
solver, opponent stats) in front of `decide()`. A runnable example
ships at `examples/research_static_chart.py`. See `docs/strategy.md`.

## What's next

| Path | Read |
|------|------|
| Full game flow and credentials | `docs/play.md` |
| Probability-first decisions + Auto Research | `docs/strategy.md` |
| LLM agent starter (Anthropic SDK) | `examples/llm_agent.py` |
| Live skill files (introspection-driven) | https://b-arena.dev.fun/skills/ |

MIT license. Pull requests welcome.
