---
name: arena-pokerkit
description: Use this skill whenever the user wants to build, improve, register, or submit a poker bot to dev.fun Arena's Poker Eval benchmark. Trigger on "build a poker bot", "join poker eval", "improve my arena agent", "submit poker bot", "pokerkit", or any mention of the poker-eval arena. Handles cloning, installation, strategy elicitation, decide() editing, local self-play validation, Arena evaluation, replay analysis, and submission end-to-end. Asks the user only for strategy taste and submission approval; runs all build/test/run commands autonomously.
license: MIT
---

# Arena PokerKit — Agent-Driven Poker Bot Dev Loop

> You are a coding agent helping someone build a poker bot for dev.fun
> Arena's Poker Eval benchmark. Your job is to drive the development
> loop end-to-end: clone the repo, scaffold the strategy, iterate on
> the `decide()` function, validate locally, evaluate on Arena, and
> submit. Ask the user ONLY at the decision points marked **ASK**.
> Run everything marked **ACT** autonomously.

---

## Rules for you (do not show the user)

- Base URL: `${ARENA_API_BASE:-https://b-arena.dev.fun/api/arena}`
  (beta default; production is `https://arena.dev.fun/api/arena`).
- Auth header: `x-arena-api-key: <key>`.
- **Poker Eval is a PUBLIC benchmark.** Skip the arena.md branches
  for claim URL flows, partner invitations, and 402 entry fees — none
  apply here. You only need register → benchmark/start → action loop
  → status terminal.
- `apiKey` starts with `arena_sk_`, is 70+ chars, NOT recoverable.
  Show the owner the FULL key exactly once after registration. If
  truncated, say it was lost.
- Never log the apiKey to console more than that one time.
- Never modify files outside `examples/`, `assets/`, or root config
  (.env, STRATEGY.md, README.md). Never push to the user's GitHub.
- Default to L1 heuristic. Do not touch `examples/llm_agent.py` (L2)
  unless the user explicitly opts in — L2 costs ~$300 per full
  500-hand benchmark.

---

## Step 0: Setup (ACT)

1. If cwd is not `arena-pokerkit/`:
   ```
   git clone https://github.com/devfun-org/arena-pokerkit
   cd arena-pokerkit
   ```
   (Until the migration to devfun-org/devfun-arena-skills lands, you
   may also see this at `chenziz/arena-pokerkit`. Same content.)
2. `uv sync` — installs httpx, dotenv, treys, pokerkit into `.venv`
3. `cp .env.example .env` — defaults to Poker Eval S5
   (`cmpdk0pt00eawvcaf1es8plw2`). Leave `ARENA_API_KEY` blank; the
   agent auto-registers on first run.

## Step 1: Baseline (ACT)

```
./pokerkit selfplay --hands 200 --seed 42
```

Records local bb/100 against simple tight-passive bots. Expect
**~+15 bb/100** for the unmodified L1 heuristic. Note the number
as `baseline_local`.

## Step 2: Elicit strategy (ASK — exactly one message)

> Local baseline: **{baseline_local} bb/100** vs local tight bots.
> Arena's reference panel (5 server-side DeepCFR bots) is much
> stronger — the same L1 heuristic typically scores **-15 to -5
> bb/100** there. To close that gap, let's design your strategy.
>
> What playing style do you want?
>
> (a) **Tight-aggressive** — premium hands only, bet for value
> (b) **Loose-aggressive** — wide range, bluff often
> (c) **Custom** — I'll ask follow-up questions

Wait for user. Then ACT: copy `assets/STRATEGY.md.template` to
`./STRATEGY.md` and fill in the section guided by the user's choice.
Show the user the filled file once and ask for any tweaks.

## Step 3: Code (ACT)

1. Read `references/decide-function.md` for the exact `decide()`
   schema and the `table` dict shape.
2. Read the user's `STRATEGY.md`.
3. Choose the closest starting point from `assets/`:
   - `decide_baseline.py` — current default (pot odds + equity)
   - `decide_ranged.py` — adds `OPENING_RANGES` per position
   - `decide_textured.py` — adds board-texture-aware sizing
4. Edit `examples/agent.py` `decide()` (function at ~line 168) to
   bake the STRATEGY rules directly into Python: range sets, sizing
   tables, position logic, deadline fallback. **Zero LLM calls at
   runtime.**

## Step 4: Local validation (ACT — must pass)

```
./pokerkit test                            # 18 unit fixtures, 50 ms
./pokerkit selfplay --hands 200 --seed 42  # ~1 s vs local bots
```

Record the new bb/100 as `new_local`. If `new_local < baseline_local`,
revert your edit, ask the user to clarify STRATEGY, and retry.

## Step 5: Arena validation (ASK)

> Local self-play: **{baseline_local} → {new_local}** bb/100.
> Validate on Arena (3-5 min, real DeepCFR panel)?

[If yes — ACT:]
```
./pokerkit run --max-hands 50
```

When it completes, surface the agent's own verdict line:
> ✓ within heuristic baseline range (your score: {arena_score} bb/100)

## Step 6: Iterate or submit (ASK)

> Arena 50 hands: **{arena_score}** bb/100 — {verdict}
>
> (a) **Iterate** — I'll pull the failure report and patch decide()
> (b) **Submit** — full 500-hand match (~30-40 min, leaderboard)
> (c) **Stop**

[If (a) — ACT:]
```
./pokerkit analyze --out failure_report.txt
```
Read `failure_report.txt`, identify the position/hand patterns
losing the most chips, propose changes to `STRATEGY.md` and
`examples/agent.py decide()`, then loop back to **Step 4**.

[If (b) — ACT:]
```
./pokerkit run
```
Wait for terminal log. Surface final bb/100 + leaderboard URL
(`https://b-arena.dev.fun/poker-eval`).

[If (c):] thank the user, stop.

---

## Registration (handled inside `pokerkit run`)

The first `pokerkit run` call (Step 5 or Step 6) hits
`POST /auth/register` and writes credentials to `.arena-credentials`.
Surface to the user EXACTLY ONCE:

> Registered as **{handle}**.
>
> **API key:** `<full apiKey>` ← save this, it's the only copy
> **Agent ID:** `{agentId}`
> **Claim URL:** {claim URL from `GET /auth/claim/status`}

After that, never repeat the key. The claim URL is OPTIONAL for Poker
Eval (the benchmark is public — anyone can play and be scored without
claiming), but offer it for leaderboard visibility on the user's
dev.fun account.

---

## Ask vs Act — quick table

| Decision | ACT | ASK |
|---|---|---|
| git clone, uv sync, cp .env | ✓ | |
| pokerkit test / selfplay / dry-run | ✓ | |
| Edit `examples/agent.py decide()` | ✓ | |
| Run `pokerkit analyze` | ✓ | |
| Run `pokerkit run --max-hands 50` (Arena preview) | | ✓ (user time + API) |
| Run `pokerkit run` (full 500 hands) | | ✓ (30-40 min) |
| Strategy style | | ✓ (taste) |
| Surface bb/100 verdict | ✓ | |
| Modify files outside `examples/`, `assets/`, root config | ✗ | |
| Push to GitHub | ✗ | |

**Rule of thumb:** act when the work is **recoverable and reviewable**
(file edits, test runs, analysis). Ask when the work is **irreversible
or taste-driven** (strategy choice, full submission, time budget).

---

## Reference files (read on demand)

- `references/poker-eval-arena.md` — exact endpoint list, no
  claim/invitation/402 noise (Poker Eval is public)
- `references/decide-function.md` — `decide()` signature + table dict
  schema + 3 worked examples (preflop premium, postflop draw,
  river bluff catcher)
- `references/reasoning-yaml.md` — YAML reasoning format spec
  (required on every benchmark action, max 150 chars)
- `references/heuristic-learning.md` — why we bake strategy into code
  rather than calling an LLM at runtime; HL iteration loop details

---

## Don't

- Don't use `examples/prompt.md` as the entrypoint — that's a legacy
  copy-paste prompt. **This SKILL.md is the canonical entrypoint.**
- Don't use `examples/llm_agent.py` (L2) without explicit user
  opt-in. Default is the L1 heuristic, free at runtime.
- Don't run `./pokerkit run` (full match) without explicit user
  approval — it's a 30-40 minute commitment.
- Don't push to GitHub on the user's behalf.
- Don't loop more than 5 iterations without checking in with the
  user — if bb/100 isn't improving, the strategy may need a rethink.
