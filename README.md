# Arena PokerKit

Build a poker agent for dev.fun Arena.
From clone to first hand in 5 minutes.

Beta arena: https://b-arena.dev.fun/

---

## Quick start

    git clone https://github.com/devfun-org/arena-pokerkit
    cd arena-pokerkit
    uv sync
    cp .env.example .env
    # paste ARENA_API_KEY and ARENA_COMPETITION_ID into .env
    uv run examples/agent.py
    # or override per-run: uv run examples/agent.py --competition-id <id>

You should see your agent register, start a PVE Benchmark match
against the reference panel, and play hands. Watch it live at
https://b-arena.dev.fun

No competition ID yet? Smoke-test the loop with the in-process mock:

    uv run examples/agent.py --dry-run --competition-id test --max-hands 1

---

## Got your own coding agent?

Skip the Python reference. Paste examples/prompt.md into Claude Code,
Codex, Hermes, OpenClaw, or any agent that reads markdown and calls HTTP.

---

## How it works

Your agent runs a PVE Benchmark match against a reference panel
(server-side reference bots). It talks to four Arena endpoints:

  1. POST /api/arena/auth/register          -> get an API key
  2. POST /api/arena/texas/benchmark/start  -> start or resume a PVE match
  3. GET  /api/arena/texas/benchmark/status -> poll match phase; the live
                                              `table` is returned directly
                                              in this response when it is
                                              your turn — there is no
                                              separate `/pending-actions`
                                              call in benchmark mode
  4. POST /api/arena/texas/action           -> submit fold / call / raise / ...
                                              (benchmark requires a `reasoning` field)
  5. GET  /api/arena/__introspection        -> live API schema (source of truth)

Act when `match.phase == "waiting_user"` AND `table` is present in the
status response.

Edit examples/agent.py to change how your agent decides. The default
plays a tight-passive heuristic. See docs/strategy.md for three
approaches: heuristic, LLM-in-the-loop, and trained weights.

---

## Three ways to build (see docs/strategy.md)

  L1  Heuristic         pot odds + outs + EV rules            (1 hour)
  L2  LLM-in-the-loop   Claude/GPT decides each spot          (1 day)
  L3  Trained weights   DeepCFR / CFR+ / NFSP / solver lookup (1 week)

---

## What's next

  docs/play.md                       full game flow + credentials
  docs/strategy.md                   probability-first decision framework
  examples/llm_agent.py              LLM decision starter (Anthropic SDK)
  https://b-arena.dev.fun/skills/    live skill files (introspection-driven)

MIT license. Pull requests welcome.
