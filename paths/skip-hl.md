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
Why HL Loop (WHY framing — even on skip path)
First Arena baseline (if not already on record)
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

  • `go`             — iterate on the current decide()  ← default if you press enter
  • `back to stage 3` — wire research first, then iterate
  • `back to stage 2` — write STRATEGY.md first, then iterate
```

### Branch C — fresh repo

```
This looks like a fresh repo. `skip to HL loop` assumes you have a
working bot.

  • `quick`       — start the full 4-stage walk (~1 hr)  ← default if you press enter
  • `force skip`  — pretend Stages 1-3 are done, iterate on the default decide()
```

If user `force skip`s, default `examples/agent.py` to a copy of
`assets/decide_textured.py` so the curriculum has the strongest free
baseline to iterate from.

---

## Why HL Loop? (mention before dumping tools — even on skip path)

```
🎯 Why Stage 4 (HL loop)?

You're skipping Stages 1-3 because you already have a working bot.
Good — but worth understanding what we're doing before iterating.

The HL loop's job is to fix specific leaks in your bot. Every Arena
run leaves a trail — e.g. "losing 70 bb on AJ in MP" or "BB folding
too often vs BTN c-bet". The HL loop reads `failure_report.txt`,
identifies ONE leak per round, patches `decide()`, re-runs, repeats
until no patches improve the score.

This is how you go from "good strategy" to "good strategy that beats
THIS opponent panel". Expected lift: +5-15 bb/100 over 4-6 iterations,
typically pushing you from -3 into positive territory.

The loop only works against a real Arena trail. That's why we start
with one baseline match before we can patch anything.
```

## First Arena baseline (ACT — required before iteration loop)

Stage 4 measures DELTAS. We need a starting score before patching.

Check `.arena-poker-state['iterations']`:
- If it has at least 1 entry, use the most recent as the baseline.
- If empty, offer the **standard 2-option Arena picker** to establish
  baseline:

```
Need a baseline score before iterating. Pick one:

  • 500-hand quick test   — fast feedback (~15 min). Recommended for
    HL loop iteration (you'll re-run after each patch).

  • 5000-hand anytime-ready test  — definitive ranking (~2 hr). Only
    if you want a tight CI on the baseline before patching.

Most users pick `500` here — the HL loop runs many short matches.

Pick: `500` / `5000`.  (or `go` / enter → defaults to `500`)
```

On the user's pick, run `./pokerkit run` with the right competition
id — see SKILL.md "Rules for you" for the mapping.

On terminal state:
- Unlock `first_arena_score` (if not already).
- Unlock stage milestones `style_picked` + `strategy_written` +
  `research_wired` retroactively if state matches Branch A.
- Surface score with the **4-stage anchor table** + 4-line CI
  explainer (functionally first Arena run on the skill).
- Mark whichever stage row matches the user's actual setup
  (Branch A → Stage 3 row; Branch B → Stage 1 row; Branch C → Stage 1
  row with the textured baseline).

**3-question feedback at this Stage transition (first Arena baseline):**

```
✓ What just happened: baseline Arena run → {bb_per_100} ± {CI} bb/100
  ({hands} hands vs reference panel).
✓ Why this matters: this is the anchor every HL iteration measures
  against. We need a number BEFORE we can patch — there's nothing to
  improve on otherwise.
✓ What's next: HL loop — read failure_report.txt, propose ONE patch,
  re-run. Repeat until plateau. ~10 min per round.
```

Then enter the Stage 4 loop.

---

## Stage 4 — Curriculum Learning (loop until plateau)

Identical to `paths/quick.md` Stage 4. For each iteration:

1. `./pokerkit run` (500-hand quick test).
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
6. Re-run the 500-hand quick test. Surface score with **4-stage
   anchor table** + 1-line trajectory `{prev} → {curr} bb/100
   ({+/-}{delta})`.

After iteration 1, unlock stage milestone `curriculum_running`. After
later iterations, pop `beat_baseline` / `positive_vs_panel` /
`plateau_broken` markers as they trigger.

Three options at every iteration boundary, never more:

```
  • `go`        — one more iteration  ← default if you press enter
  • `show me`   — read failure_report.txt + the proposed patch
  • `stop`      — lock in current score
```

**3-question feedback after each iteration:**

```
✓ What just happened: round {n} patched {pattern} → {prev} → {curr}
  bb/100 ({delta:+}).
✓ Why this matters: {real lift if >+2; noise within ±20 CI if
  |delta|<5; regression if negative}.
✓ What's next: read failure_report.txt, propose next patch, re-run.
  ~10 min. Or `stop` to lock in.
```

Apply plateau / band-climb / overdue-climb rules from SKILL.md
Step 6. When plateau hits (last 2 deltas < +2 bb/100), offer the
standard 2-option Arena picker (`500` / `5000` — default `500` on
enter) — most users have been on 500 the whole loop and want a
5000-hand run to lock in their definitive number.

---

## Stage 4 close — the final tier (mention once at the end)

When the user finishes Stage 4, mention this once:

```
🌅 Beyond Stage 4 — solver / trained-weights territory.

The Stage 4 HL loop ceiling is roughly -3 to +5 bb/100. To go higher,
the industry approach is to **train your own neural net** or use a
**post-flop solver** for canonical spots. Examples (open-source):

  • Pluribus (CMU/Facebook, 2019) — first AI to beat human pros at
    6-max NLHE. MCCFR self-play.
  • DeepMind open_spiel — DeepCFR / NFSP / CFR+ implementations.
  • rlcard — RL training framework with NFSP baselines.
  • TexasSolver — open-source GTO post-flop solver.
  • Slumbot — public NLHE HU bot, semi-open methods.
  • PokerBench (Lin et al, Penn State 2025) — academic 6-max benchmark.

We don't take you there in this kit — that's a ~1 week + GPU project.
But the top of the Poker Arena leaderboard will be people doing
exactly this.
```

---

## What skip-hl **does not** do

- Re-ASK style or strategy (assumed done)
- Re-pull research (assumed wired or user chose to skip)
- Skip the visible-artifact rule — every iteration still produces
  `failure_report.txt` and a visible decide() diff
- Skip the 4-stage anchor table in score reports — still applies
- Skip the WHY framing — even on skip path, we tell the user WHY
  iterate before dumping tools
- Auto-graduate to the 5000-hand test — requires user opt-in after
  plateau
- Silently escalate to Level 5 (LLM-in-loop) or Level 6 (trained
  weights) — both require explicit opt-in past Stage 4
