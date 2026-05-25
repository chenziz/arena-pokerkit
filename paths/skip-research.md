# Path: skip-research — "I already have a style + strategy, jump to Stage 3"

> Loaded when the user replies `skip to research` (or `skip research`
> / `i have a strategy` / `jump to stage 3`) to the SKILL.md greeting.
> Assumes Stage 1 (Style) and Stage 2 (Strategy.md) are conceptually
> done — either the user has a working bot in the repo already, or
> they have a clear strategy they want to skip the formalisation of.
>
> Jumps to **Stage 3 (Auto Research)** and then Stage 4 (Curriculum).

---

## Pacing

```
Setup (verify state, narrate)
Stage 3      Auto Research — pull GTO + texture + HUD
             → Arena S5 → score with 4-stage anchor → ASK
Stage 4      Curriculum — iterate to plateau
```

We treat Stages 1 + 2 as "user supplied" — no style ASK, no
STRATEGY.md writer. We DO verify state before jumping.

---

## Setup verification (ACT, narrated)

If cwd is not `arena-pokerkit/`, clone + `uv sync` per `paths/quick.md`
Phase 1. Then check the user's state:

```bash
ls examples/agent.py STRATEGY.md  2>&1
```

Three branches:

### Branch A — both exist

```
Detected:
  ✓ examples/agent.py  (your bot)
  ✓ STRATEGY.md        (your strategy)

Treating Stages 1 + 2 as done. Stage 3 next.
```

### Branch B — agent.py exists, no STRATEGY.md

```
Detected:
  ✓ examples/agent.py  (your bot)
  ✗ STRATEGY.md        (missing)

Stage 3 (Auto Research) doesn't strictly need STRATEGY.md, but
decide() patches in Stage 4 will reference it. Two options:

  • `go`         — proceed to Stage 3, skip Strategy.md
  • `add it`     — drop back to Stage 2 first (writes STRATEGY.md, ~5 min)
```

### Branch C — fresh repo

```
This looks like a fresh repo (no examples/agent.py customisations,
no STRATEGY.md). `skip to research` assumes you have a working bot
already.

Want to drop into the regular `quick` path instead? It walks through
Stages 1-4 in order, ~1 hr total.

  • `quick`       — start the full 4-stage walk
  • `force skip`  — pretend Stages 1 + 2 are done, proceed to Stage 3
```

If user `force skip`s, default to `assets/decide_ranged.py` as a
stand-in baseline so Stage 3's research has something to wire into.

---

## Stage 3 — Auto Research (ACT)

Identical to `paths/quick.md` Stage 3. Pull GTO preflop chart, board
texture buckets, opponent HUD endpoint. Write to `research/*.json`.
Patch `examples/agent.py` to consult them.

Show the user the actual data files:

```
🤖 Stage 3: Auto Research

  ✓ research/preflop.json (4.2 KB)
  ✓ research/board_textures.json (1.1 KB)
  ✓ /texas/agent-stats endpoint registered (pulled per match)

  decide() patched to consult research before pure-style decisions.
```

Run local validation. ASK Arena S5:

```
Stage 3 wired. Run Arena S5 to measure? ~15 min.

  • `go`        — run Arena Stage 3
  • `show me`   — list what's in research/ first
  • `stop`      — lock in current bot
```

On `go`, `./pokerkit run`. On terminal state:
- Unlock stage milestone `research_wired` (and `style_picked` +
  `strategy_written` retroactively if they aren't already in the
  milestones file).
- Surface score with the 4-stage anchor table, mark Stage 3 with
  "← you ran this".
- If `first_arena_score` is unmarked, include the 4-line CI explainer
  (this is functionally the user's first Arena run on the skill).
- ASK approval for Stage 4.

---

## Stage 4 — Curriculum (identical to quick/guided)

Same iteration loop as `paths/quick.md` Stage 4. Run S5 → analyze →
patch → re-run → plateau check.

```
🤖 Stage 4: Curriculum Learning

  Loop:
    1. Run S5 (500 hands)
    2. Read failure_report.txt
    3. Propose 1 patch to decide()
    4. Re-run S5
    5. Repeat until plateau (last 2 deltas < +2 bb/100)
```

Three options at every iteration boundary:

```
  • `go`        — one more iteration
  • `show me`   — read failure_report.txt + the proposed patch
  • `stop`      — lock in current score
```

After iteration 1, unlock stage milestone `curriculum_running`. After
later iterations, pop `plateau_broken` and `positive_vs_panel` markers
as they trigger. Apply plateau / band-climb / overdue-climb rules from
SKILL.md Step 6.

---

## What skip-research **does not** do

- Re-ASK style (assumed done)
- Re-write STRATEGY.md (assumed done, or user chose to skip it)
- Skip the visible-artifact rule — Stage 3 still produces `research/`
  files the user can read; Stage 4 still produces `failure_report.txt`
  and decide() diffs
- Skip the 4-stage anchor table in score reports — still applies
- Run Arena previews (`--max-hands 50`) — only the full S5
