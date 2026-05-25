# Path: guided — "Walk me through it, I want to participate"

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
             → Arena S5 → score + 4-stage anchor → ASK
Stage 2      Strategy.md — ASK (edit inline?)
             → Arena S5 → score → ASK
Stage 3      Auto Research — ASK (which sources?)
             → Arena S5 → score → ASK
Stage 4      Curriculum — same as quick, iterate to plateau
```

Same stage milestones and within-stage markers as `quick.md`. The
difference is **what you say between unlocks**, not the milestones
themselves.

---

## Phase 1 — Setup (ACT, narrated)

Run the same setup commands as `paths/quick.md`. While they run, drop
**one sentence each** about what's happening:

- `git clone` — *"Pulling the kit. Thin Python wrapper around
  Arena's API plus 3 reference `decide()` implementations."*
- `uv sync` — *"Installing httpx + treys + pokerkit (the engine, not
  the kit) into a venv."*
- `./pokerkit selfplay --hands 200` — *"200 hands vs tight-passive
  local bots. NOT the Arena panel — just a fast sanity check that
  your bot plays legal poker."*

Print:

```
Repo ready. Baseline against local bots: {baseline_local} bb/100.
(That's vs simple local opponents — Arena's reference panel is way stronger.)
```

---

## Stage 1 — Style (ASK)

```
🤖 Stage 1: Style

  Pick a starting style. Each maps to a reference decide() in assets/:

    (a) tight-aggressive  — premium hands only, value-bet, low variance
                            (← default if you say `go`)
    (b) loose-aggressive  — wide range, frequent c-bets, 3-bets light
    (c) balanced          — board-texture aware, mixed ranges

  Type a letter, or `go` for (a).
```

Map:

| User said | File copied to `examples/agent.py` | Style label |
|---|---|---|
| `a` / `tight` / `go` | `assets/decide_baseline.py` | tight-aggressive |
| `b` / `aggro` / `loose` | `assets/decide_ranged.py` (tweak openings wider) | loose-aggressive |
| `c` / `balanced` / `mixed` | `assets/decide_textured.py` | balanced |

Save the picked style to `.pokerkit-milestones.json` (key
`style_label`). Unlock stage milestone `style_picked` and pop:

```
🎯 Stage 1 unlocked — Style Picked (1/4 stages)
Progress: █░░░  Stage 1 / 4  ·  Next: Strategy Written
```

Then run local validation (`pokerkit test` + `pokerkit selfplay`) and
ASK Arena S5:

```
Stage 1 wired in. Time for the real eval. 500 hands vs Arena's
reference panel (5 server-side bots, way stronger than local
self-play). ~15 min.

  • `go`       — run Arena Stage 1
  • `inspect`  — show me examples/agent.py first
```

On `go`, `./pokerkit run`. On terminal state, surface the score with
the **4-stage anchor table** marking Stage 1 with "← you ran this".
Include the 4-line CI explainer (this is the first Arena run).

Then ASK approval for Stage 2.

---

## Stage 2 — Strategy.md (ASK — let user edit inline)

```
🤖 Stage 2: Strategy.md

  I'm going to write STRATEGY.md — a real strategy file with ranges,
  sizing, and adaptation rules. decide() will read it before every
  action.

  Before I write it, do you want to:

  • `go`       — I write it based on your tight-aggressive style
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

  • `go`         — wire it into decide() and run Arena Stage 2
  • `edit X`     — change line/section X (you tell me what)
  • `explain Y`  — what does section Y mean
```

Loop on `edit` / `explain` until user says `go`.

On `go`:
1. Patch `examples/agent.py` to read STRATEGY.md before each action.
2. Run local validation.
3. Run `./pokerkit run`.
4. Unlock stage milestone `strategy_written` and pop.
5. Surface score with 4-stage anchor table (Stage 2 row marked).
6. If `beat_baseline` triggers, pop that marker.
7. ASK approval for Stage 3.

---

## Stage 3 — Auto Research (ASK — which sources?)

```
🤖 Stage 3: Auto Research

  I can pull these data sources and bake them into decide():

    (1) GTO preflop chart (6-max ranges)         → research/preflop.json
    (2) Board texture buckets (dry/wet/paired)   → research/board_textures.json
    (3) Opponent HUD via /texas/agent-stats      → pulled per match

  • `all`       — pull all three (recommended)
  • `1`, `1,2`  — pick specific sources
  • `skip`      — keep current bot, run Arena Stage 3 anyway
```

On user's pick: pull the chosen sources, write the JSON files, patch
`examples/agent.py` to consult them. Show the user the actual file
list:

```
✓ research/preflop.json (4.2 KB)
✓ research/board_textures.json (1.1 KB)
✓ agent.py patched to consult both before pure-style decisions.
```

Run local validation. Run `./pokerkit run`. On terminal state:
- Unlock stage milestone `research_wired` and pop.
- Surface score with 4-stage anchor table (Stage 3 row marked).
- If `positive_vs_panel` triggers, pop that marker.
- ASK approval for Stage 4.

---

## Stage 4 — Curriculum (same as quick, iterate to plateau)

This stage is identical between `quick` and `guided` paths — the
loop is the loop. Follow the Stage 4 section of `paths/quick.md`:

1. Run S5.
2. Generate `failure_report.txt` via `./pokerkit analyze`.
3. Read the report, propose ONE patch, show the diff.
4. `./pokerkit test`, re-run S5.
5. Surface score with 4-stage anchor table + 1-line trajectory.
6. Apply plateau / band-climb / overdue-climb rules from SKILL.md
   Step 6 to decide whether to keep iterating or graduate to S6.

After iteration 1, unlock stage milestone `curriculum_running`. After
later iterations, pop `plateau_broken` if triggered.

Three options at every iteration boundary, never more:

```
  • `go`       — one more iteration
  • `show me`  — read failure_report.txt + the proposed patch
  • `stop`     — lock in current score
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
- After `plateau_broken`: reveal **S6 graduation** option.
- After `submitted_to_poker_eval` (if you go there): reveal **Poker
  Arena tournament** as the prize destination they're building toward.

This staged reveal is the "progressive disclosure" pattern — keep it
strict. Never dump multiple unlocks at once.
