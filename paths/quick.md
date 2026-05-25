# Path: quick — "I drive all 4 stages, you approve at boundaries"

> **First-turn handshake required.** Before any tool call in this
> path, surface the scope handshake from `SKILL.md` ("👋 Before I
> start — quick scope check…") and wait for affirmative. The
> handshake is a ONE-TIME gate on first contact; do not repeat it on
> subsequent turns within the same session.

> **Pre-action confirm required before each Arena run.** Use the
> "About to register and play {500|5000} hands…" template from
> `SKILL.md`. Per-action, not session-wide.

> **Permission heads-up source:** the canonical full text lives in
> `references/permissions.md`. The short block in Phase 1 below is a
> 5-line synced copy. If you edit, mirror to SKILL.md, guided.md, and
> README.md. **DO NOT EDIT inline copies in isolation — sync from
> references/permissions.md.**

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
Stage 1      Style                    → style label saved, decide() Python updated
             → Arena (500-hand quick test) → score with 4-stage anchor → ASK
Stage 2      Strategy.md              → STRATEGY.md (spec) used to write decide() Python
             → Arena → score → ASK
Stage 3      Auto Research            → research/*.json pulled, decide() consults
             → Arena → score → ASK
Stage 4      Curriculum (HL loop)     → failure_report.txt + decide() patches
             → iterate to plateau
```

Three or fewer options on any ASK. Never dump the level ladder up front.

---

## Phase 1 — Setup (ACT, silent except permission heads-up + final summary)

**Step 1 — surface the permission heads-up FIRST, before any command.**
Even on quick path, this is non-negotiable: a sandbox prompt that
arrives unannounced confuses the user. Paste this block (translate
inline if non-English) and wait one beat before running anything:

```
💡 Heads-up — your sandbox may prompt on the first few commands.
That's normal. The kit only runs local Python on your machine. Two
network steps you should know about:
  1. `uv sync` (Phase 1, one-time) — downloads Python deps from PyPI
     (~30 sec, ~50MB). Standard package install.
  2. Arena evaluation (Stage 3+, you approve each time) — calls
     b-arena.dev.fun for the benchmark.
Everything else is pure local Python. One-time approve is enough.

Pre-grant if you'd rather skip prompts:
  • Claude Code: cp .claude/settings.json.example .claude/settings.json
  • Codex CLI:   cp .codex/config.toml.example ~/.codex/config.toml
                 (or approve workspace once when Codex asks)
  • Gemini CLI:  cp .gemini/settings.json.example .gemini/settings.json
                 (or `export GEMINI_CLI_TRUST_WORKSPACE=true`,
                  or `gemini --skip-trust ...` — Gemini refuses
                  untrusted directories)
Full version: references/permissions.md.
```

**Step 2 — silent setup.** After the heads-up is on screen, run, in order:

```bash
# if not already inside the repo:
git clone https://github.com/chenziz/arena-pokerkit
cd arena-pokerkit

uv sync
cp .env.example .env             # if read-only sandbox, skip this and
                                  # export ARENA_API_BASE + ARENA_COMPETITION_ID
                                  # directly (see references/permissions.md)
```

**Parallel tests** — kick off `./pokerkit test` and
`./pokerkit selfplay --hands 200 --seed 42` in the **background** while
you continue narrating. Do NOT block on them. Surface their results as
they complete:

```
🎯 Tests passed: 34/34   (background)
🎯 Selfplay baseline: +14.2 bb/100 vs tight-passive   (background)
```

If a test fails, surface the failure out-of-band and stop the flow until
it passes. Otherwise, narration continues immediately.

When the selfplay result arrives, print one line:

```
Repo ready. Baseline against local bots: {baseline_local} bb/100.
(That's vs simple local opponents — Arena's reference panel is way stronger.)
```

**3-question feedback at this Stage transition:**

```
✓ What just happened: cloned repo, installed deps, baseline +{N} bb/100
  vs local bots (background tests passed {M}/{M}).
✓ Why this matters: proves your environment works and `decide()` returns
  legal actions. Does NOT tell you Arena performance — local bots are
  much weaker than the reference panel.
✓ What's next: Stage 1 (Style) — I pick tight-aggressive default and
  copy it into examples/agent.py. ~30 sec, no Arena yet.
```

Local baseline number from `selfplay` goes into the iteration history
as `baseline_local`. Do not invent an Arena number here. Parse the
selfplay output for the `  bb/100      : +XX.X` line in the final
summary block (regex `^\s*bb/100\s*:\s*([+-]?\d+(?:\.\d+)?)`). Full
output-parsing reference: `references/output-parsing.md`.

---

## Stage 1 — Style (ACT, narrate clearly)

```
🤖 Stage 1: Style

  Picking "tight-aggressive" — a balanced, low-variance default.
  Saved to .pokerkit-milestones.json. decide() Python updated to match.

  Running it:
    ./pokerkit selfplay --hands 200 --seed 42
    → +14 bb/100 vs local tight-passive. Direction OK.
```

Apply by copying the closest reference impl:

```bash
cp assets/decide_baseline.py examples/agent.py
```

Then ASK approval to run Arena (this is the user's first real eval).
Use the **standard 2-option picker** (identical wording across all
paths):

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

Pick: `500` / `5000`.  (or just `go` / enter → defaults to `500`)
```

On the user's pick, run `./pokerkit run` with the right competition
id — see SKILL.md "Rules for you" for the mapping.

On terminal state:

1. Read `.arena-credentials` and surface the registration block ONCE
   per the SKILL.md "Registration" section (full apiKey, agentId,
   claim URL).
2. Unlock the within-stage marker `first_arena_score`.
3. Unlock the stage milestone `style_picked` and print the stage pop.
4. Surface the score using the **4-stage anchor table** from SKILL.md
   "Score interpretation" — mark Stage 1 with "← you ran this".
5. **3-question feedback at this Stage transition:**

```
✓ What just happened: Stage 1 (TAG style) on Arena → {bb_per_100} ± {CI}
  bb/100 over {hands} hands vs the reference panel.
✓ Why this matters: this is your honest baseline against the panel —
  any future improvement is measured against this number, not local
  selfplay.
✓ What's next: Stage 2 (Strategy.md) writes a real strategy spec
  (ranges + sizing + adaptation), then re-runs Arena. Expected lift:
  ~10 bb/100. ~5 min to write + ~15 min Arena.
```

6. ASK:

```
Ready for Stage 2?

  • `go`        — write Strategy.md and run Stage 2  ← default if you just press enter
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
3. **Translate STRATEGY.md into `examples/agent.py decide()` Python** —
   the markdown is the SPEC, the Python is the BUILD ARTIFACT. Use
   `assets/decide_ranged.py` as the implementation reference. The
   runtime bot reads only the generated Python; the agent re-runs this
   translation whenever STRATEGY.md changes or a Heuristic Learning
   iteration completes.

Then show the user a snippet of the actual file:

```
🤖 Stage 2: Strategy.md

  📄 STRATEGY.md written to repo root. This file is YOURS — read it,
  edit it, ask me about any line. The bot itself reads only the
  generated `examples/agent.py decide()` code — but you only ever
  edit the markdown, and I'll re-translate when you do.

  Snippet:

    UTG range:  AA-TT, AKs, AKo, AQs  (4% of hands)
    BTN range:  AA-22, AXs, KQs-K9s, suited gappers  (35%)
    Sizing:     2.5x open, 33% c-bet dry boards, 66% c-bet wet boards
    Adapt:      vs >40% VPIP villain, widen value range one tier
    ...

  STRATEGY.md is the spec. I translated it into decide() Python — the
  runtime bot reads the code, not the markdown. Edit STRATEGY.md and
  ask me to re-translate any time.
```

Run local validation — and **surface the results to the user**.
Both modes, both visible. **Kick these off in parallel / background**
so the user keeps reading narration instead of waiting:

```bash
./pokerkit test                          # 20 unit scenarios (21 pytest tests)
./pokerkit selfplay --hands 200 --seed 42  # 200-hand match vs simple bot
```

Capture the actual output from each command. Then print a unified
results block in this shape (use real numbers from the run; the
examples here are illustrative):

```
🧪 Local test — fixed scenarios:
   PASS  AKs UTG → bot raises ✓
   PASS  72o BB vs MP open → bot folds ✓
   PASS  AA on dry flop → bot bets ✓
   ...
   21 / 21 passed (your bot makes the "obvious right play" in all
   canonical spots)

🎯 Local self-play — 200 hands vs tight-passive bot:
   Win rate:  68% (137 / 200 hands won net)
   bb/100:    +14.8 bb/100  ← positive locally
   speed:     0.6 sec total
```

If `pokerkit test` exits non-zero or any scenario fails, surface the
failures and stop the flow — do not offer the next stage until tests
pass.

### Honest reflection — local ≠ Arena

Immediately after the results block, print this reflection. It is
**mandatory** — do not skip to Stage 3 without showing it:

```
✓ Your bot plays the strategy you wrote. Local results are positive —
  but the local opponent is a simple tight-passive bot.

  Arena's reference panel is much stronger (DeepCFR-style trained
  agents). The same Strategy MD against the panel would likely score
  around -25 to -15 bb/100 — that's the typical Stage 2 anchor.

  Before going to Arena, let's give your bot more knowledge — that's
  what Stage 3 (Auto Research) and Stage 4 (Curriculum) add.
```

Unlock stage milestone `strategy_written` and print stage pop here.
(Stage 2's milestone fires on the local validation passing, not on
an Arena run — Arena is now gated behind Stage 3.)

### Anticipation tease — Stage 3, NOT Arena

**3-question feedback at this Stage transition:**

```
✓ What just happened: STRATEGY.md written, decide() re-translated from
  it, local tests {M}/{M} pass, local selfplay +{N} bb/100.
✓ Why this matters: your bot now plays a coherent strategy. But local
  bots are weak — Arena's reference panel would still score this
  around -25 to -15 bb/100. Stage 3 closes that gap with real data.
✓ What's next: Stage 3 (Auto Research) — pull GTO charts + board
  textures + opponent HUD, bake into decide(). ~5 min, no Arena yet.
```

Then ASK (note: **no Arena option here**):

```
🔓 Stage 3 — Auto Research

   Your STRATEGY.md is "opinions on paper". Stage 3 adds DATA:
     • Preflop GTO ranges (e.g. Upswing 6-max chart)
     • Board texture buckets (dry/wet/paired sizing tables)
     • Opponent HUD (their VPIP / aggression — pulled live)

   I bake these into decide() so your bot looks up data before
   making decisions, not just relies on your strategy preamble.

  • `go`         — start Stage 3 (Auto Research)  ← default if you press enter
  • `show me`    — open STRATEGY.md and walk through it first
  • `tweak it`   — tell me what to change in STRATEGY.md before Stage 3
```

If the user insists on running Arena before Stage 3 (e.g. "run arena
anyway", "skip to arena"), you may run `./pokerkit run` — but only
after warning once:

```
You can run Arena now, but Stage 2 bots typically score -25 to -15
bb/100 against the reference panel. Stage 3 + Stage 4 are where the
real climb happens. Sure you want to spend ~15 min on a Stage 2
measurement?

  • `yes`     — run Arena anyway
  • `no`      — proceed to Stage 3 instead
```

Only on explicit `yes` after that warning do you run Arena from
Stage 2.

---

## Stage 3 — Auto Research (ACT)

### Why Auto Research? (mention before pulling data)

```
🎯 Why Stage 3 (Auto Research)?

Your STRATEGY.md is "opinions on paper". The numbers in it (ranges,
sizings) came from your style preference, not from data. Stage 3
gives your bot real DATA to look up:

  • GTO charts — the optimal preflop ranges, not your guess at them
  • Opponent HUD (live /texas/agent-stats) — lets your bot exploit
    THIS panel's specific patterns instead of playing every villain
    the same
  • Board-texture buckets — correctly sized bets on dry vs wet vs
    paired boards, not one-size-fits-all sizing

Without these, your strategy is opinions on paper. With them, your
bot looks up the right answer before deciding. Expected lift: +12 to
+20 bb/100 over Stage 2, typically bringing Arena from -25..-15 to
-10..-3.
```

Then ACT:

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

Run local validation. Then offer the **standard 2-option Arena
picker** (same wording as Stage 1 ASK):

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

Pick: `500` / `5000`.  (or just `go` / enter → defaults to `500`)
```

On the user's pick, run `./pokerkit run` with the right competition
id — see SKILL.md "Rules for you" for the mapping.

On terminal state:
- Unlock stage milestone `research_wired` and print stage pop.
- Surface score with 4-stage anchor table, mark Stage 3 row with
  "← you ran this".
- If `positive_vs_panel` triggers, also pop that marker.
- **3-question feedback at this Stage transition:**

```
✓ What just happened: Stage 3 with GTO + textures + HUD baked in →
  {bb_per_100} ± {CI} bb/100 ({delta} vs Stage {prev}).
✓ Why this matters: your bot now consults data, not just style. This
  is the typical "good amateur" plateau — most strategies max out
  here unless they adapt to specific panel patterns.
✓ What's next: Stage 4 (Curriculum / HL loop) — read failure_report,
  patch one leak per round, re-run. Typical lift: +5-15 bb/100 over
  4-6 iterations. ~10 min per loop.
```

- ASK approval to proceed to Stage 4 (default = `go` on enter).

---

## Stage 4 — Curriculum Learning (ACT, iterative)

### Why iterate? (mention before starting the loop)

```
🎯 Why Stage 4 (HL loop)?

Stage 3 gave your bot DATA (GTO charts, board buckets, opponent HUD).
But every Arena run leaks specific patterns — e.g. "losing 70 bb on
AJ in MP" or "BB folding too often vs BTN c-bet". The HL loop reads
`failure_report.txt`, identifies ONE leak per round, patches `decide()`,
and re-runs. Repeat until no patches improve the score.

This is how you go from "good strategy" to "good strategy that beats
THIS opponent panel". Expected lift: +5-15 bb/100 over 4-6 iterations,
typically pushing you from -3 into positive territory.
```

```
🤖 Stage 4: Curriculum Learning

  Now the loop begins:
    1. Run the 500-hand quick test on the existing bot
    2. I read failure_report.txt
    3. I propose 1 patch to decide()
    4. Re-run the 500-hand quick test
    5. Repeat until score plateaus (last 2 deltas < +2 bb/100)
```

For each iteration:

1. `./pokerkit run` (500-hand quick test).
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
6. Re-run the 500-hand quick test. Surface score with 4-stage anchor
   table + 1-line trajectory `{prev} → {curr} bb/100 ({+/-}{delta})`.

After iteration 1, unlock stage milestone `curriculum_running` and
pop the stage panel.

After each subsequent iteration:
- If `plateau_broken` marker triggers (>5 bb/100 over best previous),
  pop it.
- Apply the plateau / band-climb / overdue-climb rules from SKILL.md
  Step 6 to decide whether to keep iterating or graduate to the
  5000-hand anytime-ready test.

Three options at every iteration boundary, never more:

```
  • `go`        — one more iteration  ← default if you press enter
  • `show me`   — read failure_report.txt myself
  • `stop`      — lock in current score
```

**3-question feedback after each iteration:**

```
✓ What just happened: round {n} patched {pattern} → {prev} → {curr}
  bb/100 ({delta:+}).
✓ Why this matters: {delta_explanation — "real lift" if >+2,
  "noise within CI ±20" if |delta|<5 on 500-hand, "regression — will
  revert if next round confirms" if negative}.
✓ What's next: read failure_report.txt for next leak, propose patch,
  re-run 500-hand. ~10 min. Or `stop` to lock in this score.
```

When plateau hits, offer the 2-option Arena picker again (`500` /
`5000` — default `500` on enter) — most users have been on 500 the
whole loop and want a 5000-hand run to lock in their definitive number.

---

## Stage 4 close — the final tier (mention once at the end)

When the user finishes Stage 4 (plateau hit OR they say `stop`),
mention this once:

```
🌅 Beyond Stage 4 — solver / trained-weights territory.

The Stage 4 HL loop ceiling is roughly -3 to +5 bb/100. To go higher,
the industry approach is to **train your own neural net** or use a
**post-flop solver** for canonical spots. Examples (open-source):

  • Pluribus (CMU/Facebook, 2019) — first AI to beat human pros at
    6-max NLHE. MCCFR self-play.
  • DeepMind open_spiel — DeepCFR / NFSP / CFR+ implementations.
  • rlcard — RL training framework with NFSP baselines.
  • TexasSolver — open-source GTO post-flop solver. Bake lookup tables
    into your decide().
  • Slumbot — public NLHE HU bot, semi-open methods.
  • PokerBench (Lin et al, Penn State 2025) — academic 6-max benchmark.

We don't take you there in this kit — that's a ~1 week + GPU project.
But the top of the Poker Arena leaderboard will be people doing
exactly this. If you want to seriously compete, your roadmap is:
this kit → train weights (or import solver tables) on top.
```

---

## What the quick path **does not** do

- Ask about strategy style (`guided` does that)
- Explain bb/100 / scoring / variance up front (`learn` does that)
- Skip the visible-artifact rule — even on quick path, the user sees
  STRATEGY.md content, research/ contents, and decide() diffs
- Claim a score without running a real Arena match (no fake numbers)
- Run Arena previews (`--max-hands 50`) — only the full 500-hand or
  5000-hand match
- Auto-graduate to the 5000-hand test — that requires user opt-in
  after plateau
