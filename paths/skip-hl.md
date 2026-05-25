# Path: skip-hl — "I have a working bot, jump to Stage 4 (curriculum)"

> Loaded when the user replies `skip to HL loop` (or `skip to
> curriculum` / `i have a bot` / `jump to stage 4`) to the SKILL.md
> greeting. Assumes Stages 1 + 2 + 3 are conceptually done — the user
> has a bot they're happy with and just wants to iterate.
>
> Jumps straight to **Stage 4 (Curriculum Learning)**.

---

## Pacing

```
Setup (verify state, narrate)
First Arena S5 baseline (if not already on record)
Stage 4   Curriculum — iterate to plateau
```

No style ASK, no Strategy.md writer, no Research wiring. We DO verify
state before jumping.

---

## Setup verification (ACT, narrated)

If cwd is not `arena-pokerkit/`, clone + `uv sync` per `paths/quick.md`
Phase 1. Then check state:

```bash
ls examples/agent.py STRATEGY.md research/  2>&1
```

Three branches:

### Branch A — everything exists

```
Detected:
  ✓ examples/agent.py  (your bot)
  ✓ STRATEGY.md        (your strategy)
  ✓ research/          (your data sources)

Treating Stages 1 + 2 + 3 as done. Stage 4 next.
```

### Branch B — agent.py only

```
Detected:
  ✓ examples/agent.py  (your bot)
  ✗ STRATEGY.md / research/  (missing)

Stage 4 (curriculum) iterates on whatever decide() ships now. Your
patches will be based on raw failure_report.txt patterns, not on
strategy/research lookups.

  • `go`             — iterate on the current decide()
  • `back to stage 3` — wire research first, then iterate
  • `back to stage 2` — write STRATEGY.md first, then iterate
```

### Branch C — fresh repo

```
This looks like a fresh repo. `skip to HL loop` assumes you have a
working bot.

  • `quick`       — start the full 4-stage walk (~1 hr)
  • `force skip`  — pretend Stages 1-3 are done, iterate on the default decide()
```

If user `force skip`s, default `examples/agent.py` to a copy of
`assets/decide_textured.py` so the curriculum has the strongest free
baseline to iterate from.

---

## First Arena baseline (ACT — required before iteration loop)

Stage 4 measures DELTAS. We need a starting score before patching.

Check `.arena-poker-state['iterations']`:
- If it has at least 1 entry, use the most recent as the baseline.
- If empty, run one fresh Arena S5 to establish baseline:

```
Need a baseline score before iterating. Running Arena S5 now.

  ./pokerkit run

~15 min. I'll narrate every ~100 hands.
```

On terminal state:
- Unlock `first_arena_score` (if not already).
- Unlock stage milestones `style_picked` + `strategy_written` +
  `research_wired` retroactively if state matches Branch A.
- Surface score with the **4-stage anchor table** + 4-line CI
  explainer (functionally first Arena run on the skill).
- Mark whichever stage row matches the user's actual setup
  (Branch A → Stage 3 row; Branch B → Stage 1 row; Branch C → Stage 1
  row with the textured baseline).

Then enter the Stage 4 loop.

---

## Stage 4 — Curriculum Learning (loop until plateau)

Identical to `paths/quick.md` Stage 4. For each iteration:

1. `./pokerkit run` (S5).
2. `./pokerkit analyze --out failure_report.txt`.
3. Read the report, identify ONE losing pattern, patch `decide()`.
4. Show the diff:
   ```
   📄 Patch round {n}: tightening UTG range vs aggressive villains.
      examples/agent.py:
      -   if pos == "UTG" and hand_class >= 8:
      +   if pos == "UTG" and hand_class >= 9 and villain_vpip < 0.30:
   ```
5. `./pokerkit test` — must pass.
6. Re-run S5. Surface score with **4-stage anchor table** + 1-line
   trajectory `{prev} → {curr} bb/100 ({+/-}{delta})`.

After iteration 1, unlock stage milestone `curriculum_running`. After
later iterations, pop `beat_baseline` / `positive_vs_panel` /
`plateau_broken` markers as they trigger.

Three options at every iteration boundary, never more:

```
  • `go`        — one more iteration
  • `show me`   — read failure_report.txt + the proposed patch
  • `stop`      — lock in current score
```

Apply plateau / band-climb / overdue-climb rules from SKILL.md
Step 6. When plateau hits on S5 (last 2 deltas < +2 bb/100),
recommend graduation to S6.

---

## What skip-hl **does not** do

- Re-ASK style or strategy (assumed done)
- Re-pull research (assumed wired or user chose to skip)
- Skip the visible-artifact rule — every iteration still produces
  `failure_report.txt` and a visible decide() diff
- Skip the 4-stage anchor table in score reports — still applies
- Auto-graduate to S6 — requires user opt-in after plateau
- Silently escalate to Level 5 (LLM-in-loop) or Level 6 (trained
  weights) — both require explicit opt-in past Stage 4
