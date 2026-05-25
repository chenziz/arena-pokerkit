# Path: guided — "Walk me through it, I want to participate"

> **First-turn handshake required.** Before any tool call in this
> path, surface the scope handshake from `SKILL.md` ("👋 Before I
> start — quick scope check…") and wait for affirmative. The
> handshake is a ONE-TIME gate on first contact; do not repeat it on
> subsequent turns within the same session.

> **Permission heads-up source:** the canonical full text lives in
> `references/permissions.md`. The short block in Phase 1 below is a
> 5-line synced copy. If you edit, mirror to SKILL.md, quick.md, and
> README.md. **DO NOT EDIT inline copies in isolation — sync from
> references/permissions.md.**

> Loaded when the user replies `guided` to the SKILL.md first-contact
> greeting. Same 4-stage progression as `quick.md`, but **the user
> participates actively at each stage**:
>
> - Stage 1: user picks the style from a 3-option menu
> - Stage 2: user can edit STRATEGY.md inline before commit
> - Stage 3: user chooses which research sources to pull
> - Stage 4: same as quick — agent iterates, user approves each round
>
> ~1.5 hr wall clock instead of ~1 hr on quick.

---

## Pacing

```
Setup        (Phase 1, narrated)
Stage 1      Style — ASK (3 options)
             → Arena (500 or 5000) → score + 4-stage anchor → ASK
Stage 2      Strategy.md — ASK (edit inline?)
             → Arena → score → ASK
Stage 3      Auto Research — ASK (which sources?)
             → Arena → score → ASK
Stage 4      Curriculum — same as quick, iterate to plateau
```

Same stage milestones and within-stage markers as `quick.md`. The
difference is **what you say between unlocks**, not the milestones
themselves.

---

## Phase 1 — Setup (ACT, narrated — permission heads-up FIRST)

**Step 1 — surface the permission heads-up FIRST, before any command.**
The guided path is more conversational than quick, but the heads-up
ordering rule is the same: a sandbox prompt that arrives unannounced
confuses the user. Paste this (translate inline if non-English):

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

**Step 2 — narrated setup.** Run the same setup commands as
`paths/quick.md`. **Run `./pokerkit test` and `./pokerkit selfplay`
in parallel / background** — narrate while they run, surface result
as `🎯 Tests passed: 34/34` and `🎯 Selfplay baseline: +X.X bb/100`
when each completes. Never block the user reading narration.

While the commands run, drop **one sentence each** about what's happening:

- `git clone` — *"Pulling the kit. Thin Python wrapper around
  Arena's API plus 3 reference `decide()` implementations."*
- `uv sync` — *"Installing httpx + treys + pokerkit (the engine, not
  the kit) into a venv."*
- `./pokerkit selfplay --hands 200` — *"200 hands vs tight-passive
  local bots. NOT the Arena panel — just a fast sanity check that
  your bot plays legal poker."*

If `cp .env.example .env` fails (read-only sandbox / Codex strict
mode), skip the `.env` file and `export ARENA_API_BASE=https://b-arena.dev.fun/api/arena`
+ `export ARENA_COMPETITION_ID=cmpdk0pt00eawvcaf1es8plw2` instead.
Tell the user once: *"Your sandbox is read-only; using env vars
instead of .env. Same effect."* Full text:
`references/permissions.md`.

Print:

```
Repo ready. Baseline against local bots: {baseline_local} bb/100.
(That's vs simple local opponents — Arena's reference panel is way stronger.)
```

**3-question feedback at this Stage transition:**

```
✓ What just happened: cloned + installed + background tests
  {M}/{M} pass + local baseline {N} bb/100.
✓ Why this matters: env works, `decide()` is legal. Local bots are
  way weaker than Arena's panel — local numbers do NOT predict Arena.
✓ What's next: Stage 1 (Style) — I walk you through 4 quick decision
  spots (Q1-Q4) with EV feedback so you LEARN your style instead of
  just picking one. ~3 min.
```

---

## Stage 1 — Style (ASK)

> **Profiling first.** Before picking (a)/(b)/(c), walk the user through
> **4 quick decision spots (Q1-Q4)**. Each has a "real" EV (pre-computed
> via Monte Carlo over realistic opponent ranges) so the user *learns*
> from their answer — not just vibes. After each pick, show the EV
> feedback block. Then summarize their profile into one of the 3 styles.

### Q1 — Preflop open: QJo from MP, folds around

```
🃏 Q1 / 4

  100bb effective. 6-max. Folds to you in MP with QJo (queen-jack offsuit).
  Action's on you.

    (1) raise  (open 2.5bb)
    (2) call   (limp 1bb)
    (3) fold

  Type 1, 2, or 3.
```

**After user picks (show this block):**

```
✓ Your choice: **{user_pick}**

Other options' EV (Monte Carlo, 2000 iters vs modern 6-max ranges):

| Option   | EV         | Reason                                                                |
|---       |---         |---                                                                    |
| `raise`  | +0.66 BB ★ | Captures fold equity vs SB+BB (~55% combined fold), plays strong-range pot when called |
| `call`   | -0.25 BB   | Limping invites multiway, gives up initiative — modern 6-max nobody limps MP |
| `fold`   |  0.00 BB   | Safe but leaves money on the table — QJo is a clear open from MP     |
```

**Why the ★ play is best:** QJo from MP has enough equity vs likely
defending ranges (~46.9% raw equity when called) AND wins the blinds
outright a majority of the time. Raising is the only +EV line.

If user picked raise → "← good pick, you have an aggressive baseline."
If user picked fold/call → "the +0.66 play is raise; your pick is
{conservative/passive} — we'll note that and adjust."

---

### Q2 — Defending the BB: 76s vs BTN 10bb open

```
🃏 Q2 / 4

  100bb. BTN raises to 10bb (a huge sizing — not standard 2.5x).
  Folds to you in BB with 76s (seven-six suited).

    (1) 3-bet to 30bb
    (2) call (invest 9 more)
    (3) fold

  Type 1, 2, or 3.
```

**After user picks:**

```
✓ Your choice: **{user_pick}**

Other options' EV (Monte Carlo vs BTN 10bb-open range):

| Option   | EV         | Reason                                                                |
|---       |---         |---                                                                    |
| `3-bet`  | -7.65 BB   | BTN's 10bb open range is uncapped; 76s has 36% equity in a 3bp, can't profitably bloat |
| `call`   | -2.90 BB   | Pot odds need ~44%, you have 39%. Implied odds help but BB is OOP postflop |
| `fold`   |  0.00 BB ★ | A 10bb open is HUGE — fold equity is gone, postflop is OOP w/ a marginal hand |
```

**Why the ★ play is best:** Against a *standard* 2.5x BTN open, 76s is
a defend (call or mix 3-bet). Against a **10bb sizing**, the math
flips — fold equity collapses and pot odds get worse. The lesson:
**sizing > hand strength**. Adjust to villain's bet size, not your
range chart.

If user picked fold → "← good read, you adjust to sizing."
If user picked call/3-bet → "your instinct is to defend BB suited
connectors — usually right, but the 10bb sizing changes the math.
We'll note 'plays defensively vs standard sizing'."

---

### Q3 — Postflop c-bet: AK on K♦7♠2♥ (dry), OOP after preflop raise

```
🃏 Q3 / 4

  100bb. You raised MP, BB called. Flop: K♦ 7♠ 2♥ (rainbow, dry).
  Pot 7bb. You have A♥K♣ — top pair top kicker.

    (1) c-bet 33% pot (~2.3bb)
    (2) check

  Type 1 or 2.
```

**After user picks:**

```
✓ Your choice: **{user_pick}**

Other options' EV (Monte Carlo, hero 88.3% equity vs caller range):

| Option   | EV          | Reason                                                                |
|---       |---          |---                                                                    |
| `c-bet`  | +7.54 BB ★  | Range advantage on K-high dry board; ~55% of BB's range folds, value from worse Kx |
| `check`  | +1.68 BB    | Slowplay is fine (no draws to protect), but you give up fold equity AND lose value from worse |
```

**Why the ★ play is best:** Dry K-high boards = preflop raiser's
playground. You have range advantage AND nut advantage. C-betting
small (33%) prints money — folds the dominated portion of BB's range
and gets called by Kx that you crush. Checking on a dry board with
TPTK leaves ~6bb on the table.

If user picked c-bet → "← good, you have a postflop pulse."
If user picked check → "the +7.54 play is c-bet; check loses ~6bb of
value. We'll note 'leans passive postflop' and pick a style that
nudges you toward more aggression."

---

### Q4 — River bluff-catcher: JJ on T♠7♠4♦A♦9♠, facing 70%-pot river bet

```
🃏 Q4 / 4

  100bb. Pot 20bb on the river. Board: T♠ 7♠ 4♦ A♦ 9♠
  (3 spades on board, A on turn).  You have J♥J♦ (no spade).
  Villain bets 14bb (70% pot).

    (1) call
    (2) fold

  Type 1 or 2.
```

**After user picks:**

```
✓ Your choice: **{user_pick}**

Other options' EV (vs realistic vs GTO opponent):

| Option   | EV (vs real)  | EV (vs GTO)  | Reason                                                                |
|---       |---            |---           |---                                                                    |
| `call`   | -2.00 BB      | +5.68 BB     | JJ is a pure bluff-catcher: 100% vs bluffs, 0% vs value. Result depends on villain's bluff freq |
| `fold`   |  0.00 BB ★    |  0.00 BB     | Real opponents under-bluff river big bets (~25% vs GTO ~41%). Fold against unknown villain |
```

**Why the ★ play depends on villain:**
- **Unknown / human villain** → fold. Most players under-bluff scary
  river boards (3-flush + ace). At 25% bluff freq, call is -2.0 BB.
- **Solver / GTO villain** → call. At GTO bluff freq (~41%), call is
  +5.7 BB. JJ is exactly the kind of medium-strength hand GTO is
  trying to make indifferent.

The lesson: **river bluff-catching is about villain frequencies, not
hand strength.** JJ here is the same equity hand whether villain
bluffs 25% or 50% — what changes is the *required* equity vs the
*observed* bluff rate.

If user picked fold → "← good, defaults to fold vs unknowns."
If user picked call → "your instinct is to call light — works vs GTO
solvers but loses to typical underbluffing humans. We'll note 'calls
station tendencies'."

---

### Style label from Q1-Q4

After all 4 answers, map the user's pattern to a style. The user
gets the **4-option style question** (TAG / LAG / Balanced / Custom)
next; the pattern just pre-selects the recommended option.

| Pattern                                        | Style label       |
|---                                             |---                |
| Mostly aggressive (Q1 raise, Q3 c-bet, Q2 3b/call) | loose-aggressive  |
| Mostly fold/check (Q1 raise, Q3 check, Q2 fold, Q4 fold) | tight-aggressive  |
| Mixed by spot (adjusts to sizing in Q2, board in Q3) | balanced          |
| Outlier / asks for control                     | custom (deeper interview) |

Show the user:

```
📊 Your profile from Q1-Q4:

  Q1 QJo MP        → you picked {choice}  ({★ if optimal})
  Q2 76s vs 10bb   → you picked {choice}  ({★ if optimal})
  Q3 AK on K72     → you picked {choice}  ({★ if optimal})
  Q4 JJ vs river   → you picked {choice}  ({★ if optimal})

  Style: {label} — {1-line description}

  This maps to {assets/decide_X.py}. Want to use it?
```

Then continue to the original Style menu (a/b/c), with the recommended
style pre-selected based on the profile. User can override.

---

```
🤖 Stage 1: Style — 4-option style question

  Pick a starting style. Each maps to a reference decide() in assets/:

    (a) tight-aggressive  — pick this and I'll wire it in immediately
                            (← default if you say `go`; low variance)
    (b) loose-aggressive  — pick this and I'll wire it in immediately
                            (wide range, frequent c-bets, 3-bets light)
    (c) balanced          — mix of TAG and LAG, value-heavy but willing
                            to bluff in clear spots. Wired in immediately
                            (board-texture aware, mixed ranges).
    (d) custom            — I'll ask 4-6 follow-up questions about ranges,
                            sizing, and aggression before writing
                            STRATEGY.md. Pick this if you have a specific
                            playstyle in mind (~1-2 minutes of deeper
                            interview, not an instant generation).

  Type a letter, or `go` / enter for (a) tight-aggressive default.
```

Map:

| User said | File copied to `examples/agent.py` | Style label |
|---|---|---|
| `a` / `tight` / `go` | `assets/decide_baseline.py` | tight-aggressive |
| `b` / `aggro` / `loose` | `assets/decide_ranged.py` (tweak openings wider) | loose-aggressive |
| `c` / `balanced` / `mixed` | `assets/decide_textured.py` | balanced |
| `d` / `custom` | Ask 4-6 follow-up Qs → fill template → pick closest `assets/decide_*.py` as base | custom |

Save the picked style to `.pokerkit-milestones.json` (key
`style_label`). Unlock stage milestone `style_picked` and pop:

```
🎯 Stage 1 unlocked — Style Picked (1/4 stages)
Progress: █░░░  Stage 1 / 4  ·  Next: Strategy Written
```

Then run local validation (`pokerkit test` + `pokerkit selfplay`) and
offer the **standard 2-option Arena picker** (identical wording across
all paths):

```
Stage 1 wired in. Time for the real eval — Arena's reference panel,
way stronger than local self-play.

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

Pick: `500` / `5000`.   (or `go` / enter → defaults to `500`; `inspect` to see examples/agent.py first)
```

On the user's pick, run `./pokerkit run` with the right competition
id — see SKILL.md "Rules for you" for the mapping.

On terminal state, surface the score with the **4-stage anchor
table** marking Stage 1 with "← you ran this". Include the 4-line CI
explainer (this is the first Arena run).

**3-question feedback at this Stage transition:**

```
✓ What just happened: Stage 1 ({style_label}, picked from your Q1-Q4
  profile) on Arena → {bb_per_100} ± {CI} bb/100 vs the panel.
✓ Why this matters: this is your honest baseline. Any future stage's
  lift is measured against this number — not against local selfplay.
✓ What's next: Stage 2 — STRATEGY.md spec with ranges + sizing +
  adaptation. You can edit it inline before I wire it in. ~5 min to
  write + ~5 min to edit + ~15 min Arena.
```

Then ASK approval for Stage 2 (default = `go` on enter).

---

## Stage 2 — Strategy.md (ASK — let user edit inline)

```
🤖 Stage 2: Strategy.md

  I'm going to write STRATEGY.md — a real strategy spec with ranges,
  sizing, and adaptation rules. STRATEGY.md is the SOURCE; I'll
  translate it into `examples/agent.py decide()` Python. The runtime
  bot reads only the generated code, not the markdown — but you only
  edit the markdown, and I'll re-translate whenever you change it.

  Before I write it, do you want to:

  • `go`       — I write it based on your tight-aggressive style  ← default if you press enter
  • `outline`  — show me the section headers first, I'll pick
  • `template` — just copy the blank template, I'll fill it in myself
```

On `go`: copy `examples/STRATEGY.md.template` to repo root and fill
it in based on the Stage 1 style. Show the user the full file (or a
generous snippet ≥ 15 lines) and ASK:

```
📄 STRATEGY.md written. This file is YOURS — read, edit, ask me
about any line.

{full_strategy_md_or_first_30_lines}

  • `go`         — wire it into decide() and validate locally  ← default if you press enter
  • `edit X`     — change line/section X (you tell me what)
  • `explain Y`  — what does section Y mean
```

Loop on `edit` / `explain` until user says `go`.

On `go`:
1. **Translate STRATEGY.md into `examples/agent.py decide()` Python.**
   The markdown is the spec; the Python is the build artifact. The
   runtime bot reads only the generated code. Re-translate whenever
   the user edits STRATEGY.md or after an HL iteration.
2. Run local validation — and **surface the results to the user**.
   Both modes, both visible:

```bash
./pokerkit test                          # 20 unit scenarios (21 pytest tests)
./pokerkit selfplay --hands 200 --seed 42  # 200-hand match vs simple bot
```

Capture the actual output from each command. Then print a unified
results block (use real numbers from the run; examples illustrative):

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
failures and stop the flow — do not offer Stage 3 until tests pass.

### Honest reflection — local ≠ Arena

Immediately after the results block, print this reflection. It is
**mandatory** — do not skip to Stage 3 (or Arena) without showing it:

```
✓ Your bot plays the strategy you wrote and edited. Local results are
  positive — but the local opponent is a simple tight-passive bot.

  Arena's reference panel is much stronger (DeepCFR-style trained
  agents). The same Strategy MD against the panel would likely score
  around -25 to -15 bb/100 — that's the typical Stage 2 anchor.

  Before going to Arena, let's give your bot more knowledge — that's
  what Stage 3 (Auto Research) and Stage 4 (Curriculum) add.
```

3. Unlock stage milestone `strategy_written` and pop.
   (Stage 2's milestone fires on the local validation passing, not on
   an Arena run — Arena is now gated behind Stage 3.)

### Anticipation tease — Stage 3, NOT Arena

Then ASK (note: **no Arena option here as default**):

```
🔓 Stage 3 — Auto Research unlocked.

   Your STRATEGY.md is "opinions on paper". Stage 3 adds DATA:
     • Preflop GTO ranges (e.g. Upswing 6-max chart)
     • Board texture buckets (dry/wet/paired sizing tables)
     • Opponent HUD (their VPIP / aggression — pulled live)

   I bake these into decide() so your bot looks up data before
   making decisions, not just relies on your strategy preamble.
   Expected lift: +12 to +20 bb/100 over current. Should bring Arena
   score to -10 to -3.

  • `go`           — start Stage 3 (Auto Research)  ← default if you press enter
  • `show me`      — open STRATEGY.md and walk through it again first
  • `edit more`    — tweak STRATEGY.md again before Stage 3
  • `arena anyway` — measure Stage 2 on Arena now (will likely score
                     -25 to -15 bb/100; Stage 3 + 4 are where the climb is)
```

If the user picks `arena anyway`, warn once more before running:

```
You can run Arena now, but Stage 2 bots typically score -25 to -15
bb/100 against the reference panel. Stage 3 + Stage 4 are where the
real climb happens. Sure you want to spend ~15 min on a Stage 2
measurement?

  • `yes`     — run Arena anyway
  • `no`      — proceed to Stage 3 instead
```

Only on explicit `yes` do you run `./pokerkit run` from Stage 2. On
terminal state, surface score with 4-stage anchor table (Stage 2 row
marked) and re-offer Stage 3.

---

## Stage 3 — Auto Research (ASK — which sources?)

### Why Auto Research? (mention before picking sources)

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
+20 bb/100 over Stage 2.
```

```
🤖 Stage 3: Auto Research

  I can pull these data sources and bake them into decide():

    (1) GTO preflop chart (6-max ranges)         → research/preflop.json
    (2) Board texture buckets (dry/wet/paired)   → research/board_textures.json
    (3) Opponent HUD via /texas/agent-stats      → pulled per match

  • `all`       — pull all three (recommended)  ← default if you press enter / `go`
  • `1`, `1,2`  — pick specific sources
  • `skip`      — keep current bot, run Arena anyway
```

On user's pick: pull the chosen sources, write the JSON files, patch
`examples/agent.py` to consult them. Show the user the actual file
list:

```
✓ research/preflop.json (4.2 KB)
✓ research/board_textures.json (1.1 KB)
✓ agent.py patched to consult both before pure-style decisions.
```

Run local validation. Then offer the **standard 2-option Arena
picker** (`500` / `5000`). On terminal state:
- Unlock stage milestone `research_wired` and pop.
- Surface score with 4-stage anchor table (Stage 3 row marked).
- If `positive_vs_panel` triggers, pop that marker.
- ASK approval for Stage 4.

---

## Stage 4 — Curriculum (same as quick, iterate to plateau)

### Why iterate? (mention before starting the loop)

```
🎯 Why Stage 4 (HL loop)?

Stage 3 gave your bot DATA. But every Arena run leaks specific patterns
— e.g. "losing 70 bb on AJ in MP" or "BB folding too often vs BTN
c-bet". The HL loop reads `failure_report.txt`, identifies ONE leak per
round, patches `decide()`, and re-runs. Repeat until no patches improve
the score.

This is how you go from "good strategy" to "good strategy that beats
THIS opponent panel". Expected lift: +5-15 bb/100 over 4-6 iterations,
typically pushing you from -3 into positive territory.
```

This stage is otherwise identical between `quick` and `guided` paths —
the loop is the loop. Follow the Stage 4 section of `paths/quick.md`:

1. Run the 500-hand quick test.
2. Generate `failure_report.txt` via `./pokerkit analyze`.
3. Read the report, propose ONE patch, show the diff.
4. `./pokerkit test`, re-run the 500-hand quick test.
5. Surface score with 4-stage anchor table + 1-line trajectory.
6. Apply plateau / band-climb / overdue-climb rules from SKILL.md
   Step 6 to decide whether to keep iterating or graduate to the
   5000-hand anytime-ready test.

After iteration 1, unlock stage milestone `curriculum_running`. After
later iterations, pop `plateau_broken` if triggered.

Three options at every iteration boundary, never more:

```
  • `go`       — one more iteration  ← default if you press enter
  • `show me`  — read failure_report.txt + the proposed patch
  • `stop`     — lock in current score
```

**3-question feedback after each iteration:**

```
✓ What just happened: round {n} patched {pattern} → {prev} → {curr}
  bb/100 ({delta:+}).
✓ Why this matters: {real lift if >+2; noise within ±20 CI if
  |delta|<5; regression if negative — will revert if next round
  confirms}.
✓ What's next: read failure_report.txt for next leak, propose patch,
  re-run 500-hand. ~10 min. Or `stop` to lock in.
```

When plateau hits, offer the standard 2-option Arena picker (`500` /
`5000` — default `500` on enter) — most users have been on 500 the
whole loop and want a 5000-hand run to lock in their definitive number.

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

## Progressive reveal (when to surface what)

- After Stage 1 score: reveal the **4-stage anchor table** (Stage 1
  row marked).
- After Stage 2 score: same table, Stage 2 row marked, plus a 1-line
  trajectory.
- After Stage 3 score: same table, Stage 3 row marked, trajectory.
- After Stage 4 starts: reveal the **6-level optimization ladder**
  (`references/optimization-levels.md`) — Stage 4 IS Level 4 (HL
  loop), but the user is welcome to climb to Level 5/6 after plateau.
- After `plateau_broken`: reveal **5000-hand anytime-ready test**
  graduation option.
- After Stage 4 close: surface the **final-tier ladder** (Pluribus,
  open_spiel, etc.) as the road past this kit.

This staged reveal is the "progressive disclosure" pattern — keep it
strict. Never dump multiple unlocks at once.
