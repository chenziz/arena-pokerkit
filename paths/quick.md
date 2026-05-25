# Path: quick — "I drive all 4 stages, you approve at boundaries"

> Loaded when the user replies `quick` to the SKILL.md first-contact
> greeting. The goal: walk the user through the **4-stage progression**
> (Style → Strategy.md → Auto Research → Curriculum) without asking
> design questions. At each stage boundary, **show the artifact**,
> **report the score with the 4-stage anchor table**, and **ASK
> "go / show me / stop"** before the next stage.
>
> No magic checkmarks. No fake scores. Every stage produces a real
> file the user can read and own.

---

## Pacing (high level)

```
Setup        (Phase 1, silent)        → repo cloned, uv synced, baseline noted
Stage 1      Style                    → style label saved, decide() reads it
             → Arena S5 → score with 4-stage anchor table → ASK
Stage 2      Strategy.md              → STRATEGY.md written, decide() reads it
             → Arena S5 → score → ASK
Stage 3      Auto Research            → research/*.json pulled, decide() consults
             → Arena S5 → score → ASK
Stage 4      Curriculum (HL loop)     → failure_report.txt + decide() patches
             → iterate to plateau
```

Three or fewer options on any ASK. Never dump the level ladder up front.

---

## Phase 1 — Setup (ACT, silent except final line)

Run, in order:

```bash
# if not already inside the repo:
git clone https://github.com/chenziz/arena-pokerkit
cd arena-pokerkit

uv sync
cp .env.example .env
./pokerkit selfplay --hands 200 --seed 42   # local baseline number
```

When complete, print one line:

```
Repo ready. Baseline against local bots: {baseline_local} bb/100.
(That's vs simple local opponents — Arena's reference panel is way stronger.)
```

Local baseline number from `selfplay` goes into the iteration history
as `baseline_local`. Do not invent an Arena number here.

---

## Stage 1 — Style (ACT, narrate clearly)

```
🤖 Stage 1: Style

  Picking "tight-aggressive" — a balanced, low-variance default.
  Saved to .pokerkit-milestones.json. decide() now reads this flag.

  Running it:
    ./pokerkit selfplay --hands 200 --seed 42
    → +14 bb/100 vs local tight-passive. Direction OK.
```

Apply by copying the closest reference impl:

```bash
cp assets/decide_baseline.py examples/agent.py
```

Then ASK approval to run Arena S5 (this is the user's first real eval):

```
Ready to measure Stage 1 on Arena? 500 hands vs the reference panel,
~15 min. Say `go` to start.
```

On `go`, run `./pokerkit run`. On terminal state:

1. Read `.arena-credentials` and surface the registration block ONCE
   per the SKILL.md "Registration" section (full apiKey, agentId,
   claim URL).
2. Unlock the within-stage marker `first_arena_score`.
3. Unlock the stage milestone `style_picked` and print the stage pop.
4. Surface the score using the **4-stage anchor table** from SKILL.md
   "Score interpretation" — mark Stage 1 with "← you ran this".
5. ASK:

```
That's your Stage 1 score. Next: Stage 2 (Strategy.md) — I write a
real strategy file with ranges, sizing, adaptation rules. decide()
will read it before every action. Expected lift: ~10 bb/100.

  • `go`        — write Strategy.md and run Stage 2
  • `show me`   — show the planned Strategy.md outline before writing
  • `stop`      — lock in Stage 1 result for today
```

---

## Stage 2 — Strategy.md (ACT)

On `go`:

1. Copy `examples/STRATEGY.md.template` to repo root as `STRATEGY.md`.
2. Fill it in based on the Stage 1 style (tight-aggressive by
   default). Real ranges per position, real sizing tables, real
   adaptation rules.
3. Patch `examples/agent.py` to read STRATEGY.md before each action
   (use `assets/decide_ranged.py` as the implementation reference).

Then show the user a snippet of the actual file:

```
🤖 Stage 2: Strategy.md

  📄 STRATEGY.md written to repo root. This file is YOURS — read it,
  edit it, ask me about any line.

  Snippet:

    UTG range:  AA-TT, AKs, AKo, AQs  (4% of hands)
    BTN range:  AA-22, AXs, KQs-K9s, suited gappers  (35%)
    Sizing:     2.5x open, 33% c-bet dry boards, 66% c-bet wet boards
    Adapt:      vs >40% VPIP villain, widen value range one tier
    ...

  decide() now reads STRATEGY.md before every action.
```

Run local validation:

```bash
./pokerkit test
./pokerkit selfplay --hands 200 --seed 42
```

Both must pass. Then ASK:

```
Strategy.md is wired in. Want to run Arena S5 to measure Stage 2?
(~15 min, real reference panel)

  • `go`        — run Arena Stage 2
  • `show me`   — open STRATEGY.md and walk through it first
  • `tweak it`  — tell me what to change before running
```

On `go`, `./pokerkit run`. On terminal state:
- Unlock stage milestone `strategy_written` and print stage pop.
- Surface score with 4-stage anchor table, mark Stage 2 row with
  "← you ran this".
- If `beat_baseline` triggers, also pop that marker.
- ASK approval to proceed to Stage 3.

---

## Stage 3 — Auto Research (ACT)

```
🤖 Stage 3: Auto Research

  Pulling data sources to make decide() smarter:
    ✓ GTO preflop chart (6-max ranges)         → research/preflop.json
    ✓ Board texture buckets (dry/wet/paired)   → research/board_textures.json
    ✓ Opponent stats endpoint registered       → pulled at match start

  decide() updated to consult these before pure-style decisions.
  Copying assets/decide_textured.py as the new examples/agent.py.
```

Concretely:

1. Run `examples/research_static_chart.py` if present (writes
   `research/preflop.json`).
2. Write board-texture buckets to `research/board_textures.json`.
3. Patch `examples/agent.py` to consult these JSONs at decision time
   (`assets/decide_textured.py` is the reference impl).
4. Optionally pull `/texas/agent-stats` once at match start in
   `examples/agent.py` (cache to in-process state).

Run local validation. Then ASK:

```
Research wired in. Want to run Arena S5 to measure Stage 3?

  • `go`        — run Arena Stage 3
  • `show me`   — list what's in research/ first
  • `stop`      — lock in Stage 2 result
```

On `go`, `./pokerkit run`. On terminal state:
- Unlock stage milestone `research_wired` and print stage pop.
- Surface score with 4-stage anchor table, mark Stage 3 row with
  "← you ran this".
- If `positive_vs_panel` triggers, also pop that marker.
- ASK approval to proceed to Stage 4.

---

## Stage 4 — Curriculum Learning (ACT, iterative)

```
🤖 Stage 4: Curriculum Learning

  Now the loop begins:
    1. Run S5 (500 hands on the existing bot)
    2. I read failure_report.txt
    3. I propose 1 patch to decide()
    4. Re-run S5
    5. Repeat until score plateaus (last 2 deltas < +2 bb/100)
```

For each iteration:

1. `./pokerkit run` (S5).
2. `./pokerkit analyze --out failure_report.txt`.
3. Read the report, identify ONE losing pattern, patch `decide()`.
4. Show the diff of the patch to the user:
   ```
   📄 Patch round {n}: tightening UTG range vs aggressive villains.
      examples/agent.py:
      -   if pos == "UTG" and hand_class >= 8:
      +   if pos == "UTG" and hand_class >= 9 and villain_vpip < 0.30:
   ```
5. `./pokerkit test` — must pass.
6. Re-run S5. Surface score with 4-stage anchor table + 1-line
   trajectory `{prev} → {curr} bb/100 ({+/-}{delta})`.

After iteration 1, unlock stage milestone `curriculum_running` and
pop the stage panel.

After each subsequent iteration:
- If `plateau_broken` marker triggers (>5 bb/100 over best previous),
  pop it.
- Apply the plateau / band-climb / overdue-climb rules from SKILL.md
  Step 6 to decide whether to keep iterating or graduate to S6.

Three options at every iteration boundary, never more:

```
  • `go`        — one more iteration
  • `show me`   — read failure_report.txt myself
  • `stop`      — lock in current score
```

---

## What the quick path **does not** do

- Ask about strategy style (`guided` does that)
- Explain bb/100 / scoring / variance up front (`learn` does that)
- Skip the visible-artifact rule — even on quick path, the user sees
  STRATEGY.md content, research/ contents, and decide() diffs
- Claim a score without running real Arena S5 (no fake numbers)
- Run Arena previews (`--max-hands 50`) — only the full S5
- Auto-graduate to S6 — that requires user opt-in after plateau
