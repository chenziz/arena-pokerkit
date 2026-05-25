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
Why Auto Research (WHY framing — even on skip path)
Stage 3      Auto Research — pull GTO + texture + HUD
             → Arena (500 or 5000) → score with 4-stage anchor → ASK
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

## Why Auto Research? (mention before dumping tools — even on skip path)

```
🎯 Why Stage 3 (Auto Research)?

You're skipping Stages 1 + 2 because you already have a bot. Good —
but Stage 3 is where the next +12-20 bb/100 lives, so it's worth
understanding what we're adding before we dump tools into your bot.

Your existing decide() makes decisions based on whatever logic you
wrote. Stage 3 adds DATA your bot looks up instead of guessing:

  • GTO charts — the optimal preflop ranges, not your guess at them
  • Opponent HUD (live /texas/agent-stats) — lets your bot exploit
    THIS panel's specific patterns instead of playing every villain
    the same
  • Board-texture buckets — correctly sized bets on dry vs wet vs
    paired boards, not one-size-fits-all sizing

Without these, your strategy is opinions on paper. With them, your
bot looks up the right answer before deciding. Expected lift: +12 to
+20 bb/100 against the reference panel.
```

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

Run local validation (`./pokerkit test` + `./pokerkit selfplay`) in
**parallel / background** — surface results as one-liners (don't
block on them). Then offer the **standard 2-option Arena picker**
(identical wording across all paths):

```
🎯 Ready for Arena?

You can pick either:

  • 500-hand quick test   — fast feedback (~15 min). Run after each
    HL iteration to verify patches. CI is ~±20 bb/100 so close bots
    can tie; use this for direction-checking.

  • 5000-hand anytime-ready test  — definitive ranking (~2 hr).
    Sample is large enough to give ~±6 bb/100 CI. Use this when
    you're confident, want a real leaderboard score.

Most users do 500-hand a few times during HL loop, then one 5000-hand
when they've plateaued and want the locked-in number.

Pick: `500` / `5000`.   (or `go` / enter → defaults to `500`; `show me` to list research/ first)
```

On the user's pick, run `./pokerkit run` with the right competition
id — see SKILL.md "Rules for you" for the mapping.

On terminal state:
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

### Why iterate? (mention before starting the loop)

```
🎯 Why Stage 4 (HL loop)?

Stage 3 gave your bot DATA. But every Arena run leaks specific patterns
— e.g. "losing 70 bb on AJ in MP" or "BB folding too often vs BTN
c-bet". The HL loop reads `failure_report.txt`, identifies ONE leak per
round, patches `decide()`, and re-runs. Repeat until no patches improve
the score.

This is how you go from "good strategy" to "good strategy that beats
THIS opponent panel". Expected lift: +5-15 bb/100 over 4-6 iterations.
```

Same iteration loop as `paths/quick.md` Stage 4. Run 500-hand quick
test → analyze → patch → re-run → plateau check.

```
🤖 Stage 4: Curriculum Learning

  Loop:
    1. Run the 500-hand quick test
    2. Read failure_report.txt
    3. Propose 1 patch to decide()
    4. Re-run the 500-hand quick test
    5. Repeat until plateau (last 2 deltas < +2 bb/100)
```

Three options at every iteration boundary:

```
  • `go`        — one more iteration  ← default if you press enter
  • `show me`   — read failure_report.txt + the proposed patch
  • `stop`      — lock in current score
```

**3-question feedback after each iteration:**

```
✓ What just happened: round {n} patched {pattern} → {prev} → {curr}
  bb/100 ({delta:+}).
✓ Why this matters: {real lift / noise / regression — see 4-stage
  anchor + ±CI band}.
✓ What's next: read failure_report.txt, propose next patch, re-run.
  Or `stop` to lock in.
```

After iteration 1, unlock stage milestone `curriculum_running`. After
later iterations, pop `plateau_broken` and `positive_vs_panel` markers
as they trigger. Apply plateau / band-climb / overdue-climb rules from
SKILL.md Step 6. When plateau hits, offer the standard 2-option Arena
picker (`500` / `5000`).

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

## What skip-research **does not** do

- Re-ASK style (assumed done)
- Re-write STRATEGY.md (assumed done, or user chose to skip it)
- Skip the visible-artifact rule — Stage 3 still produces `research/`
  files the user can read; Stage 4 still produces `failure_report.txt`
  and decide() diffs
- Skip the 4-stage anchor table in score reports — still applies
- Skip the WHY framing — even on skip path, we tell the user WHY
  Auto Research and WHY iterate before dumping tools
- Run Arena previews (`--max-hands 50`) — only the full match
