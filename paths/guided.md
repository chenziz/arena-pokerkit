# Path: guided — "Walk me through it"

> Loaded when the user replies `guided` to the SKILL.md first-contact
> greeting. The goal: same end state as `quick` (a real Arena S5
> score), but you pause for **one** style choice and you explain each
> decision as you go. ~20 min wall clock instead of ~10.

---

## Pacing

```
Screen 1: greeting (already shown by SKILL.md)
Screen 2: "On it. I'll explain as we go." → narrated Phase 1 → 🎯 Kit Connected
Screen 3: single style question (4 options, default highlighted) → 🎯 Style Chosen
Screen 4: narrated Phase 3 → 🎯 Local Eval Green
Screen 5: ASK approval to run Arena S5
Screen 6: pop the score BIG → reveal one new lever
```

Same milestone unlocks as `quick.md`, same progress bar format. The
difference is **what you say between unlocks**, not the milestones
themselves.

---

## Phase 1 — Setup (ACT, narrated)

Run the same commands as `paths/quick.md`. While they run, drop **one
sentence each** about what's happening:

- `git clone` — *"Pulling the kit. It's a thin Python wrapper around
  Arena's API plus 3 reference `decide()` implementations."*
- `uv sync` — *"Installing httpx + treys + pokerkit (the engine, not
  the kit) into a venv."*
- `./pokerkit selfplay` — *"200 hands vs tight-passive local bots.
  This is NOT the Arena panel — it's a fast sanity check that your
  bot can play legal poker."*

On success, unlock `kit_connected` with the progress bar (same format
as quick path).

---

## Phase 2 — Strategy choice (ASK — exactly one message)

This is the one ASK that defines `guided`. Keep it tight:

```
Your bot needs a style. Four canned starting points — each maps to
a reference `decide()` in assets/:

  (a) `tight`     — premium hands only, value-bet, low variance
                    (← default if you say `go`)
  (b) `aggro`     — wide range, frequent c-bets, 3-bets light
  (c) `mixed`     — balanced ranges, board-texture aware
  (d) `LLM`       — punt to an LLM for each decision (paid, Level 5)

Type one letter. Or `go` for (a).
```

Map:

| User said | File copied to `examples/agent.py` | Milestone note |
|---|---|---|
| `a` / `tight` / `go` | `assets/decide_baseline.py` | "tight-passive baked in" |
| `b` / `aggro` | `assets/decide_ranged.py` + tweak openings wider | "loose-aggressive baked in" |
| `c` / `mixed` | `assets/decide_textured.py` | "board-texture-aware baked in" |
| `d` / `LLM` | Branch to `examples/llm_agent.py` after a cost warning | "Level 5 LLM path" |

If `d`, surface the cost warning verbatim from SKILL.md ("cost varies
by model + token usage") and require explicit second confirmation
before proceeding. Don't quote a dollar figure.

Unlock `style_chosen` with the user's actual pick written into the
milestone note (not "auto-default"). Optionally also write a
`STRATEGY.md` at repo root summarizing the choice — useful for the
iteration loop later.

---

## Phase 3 — Local validation (ACT, narrated)

Same commands as quick path. While they run:

- `./pokerkit test` — *"20 unit scenarios covering preflop, flop
  decisions, all-ins, and edge cases. ~50 ms."*
- `./pokerkit selfplay --hands 200` — *"Comparing your new bot to
  local tight-passive baseline. Want this number > baseline before
  spending 15 min on Arena."*

If the new local number is lower than baseline, **don't silently
override** — surface it: *"Hmm, your `{style}` lost {delta} bb/100 vs
local baseline. Want to retry with a different style, or push on to
Arena anyway? (Local bots are weak — Arena might still go fine.)"*

On success, unlock `local_eval_green`.

---

## Phase 4 — Arena S5 (ASK)

Same prompt as quick path, but with one extra sentence of context:

```
Time for the real eval. 500 hands vs Arena's reference panel (5
server-side bots that are way stronger than local self-play). ~15 min,
runs in the background — I'll narrate every ~100 hands.

`go` to start, or `inspect` to read examples/agent.py first.
```

On `go`, `./pokerkit run` and narrate as in `quick.md`.

---

## Screen 6 — score reveal + one new lever

Use the full 4-line "Score interpretation" template (first-run
variant). Then introduce **one** new lever, not three:

```
Your score: {bb_per_100} ± 20 bb/100  (S5, 500 hands)

One pattern in your hands is leaking the most chips. I can find it
and patch it:

  ./pokerkit analyze --out failure_report.txt

Want me to run it and show you the top leak?
```

The other two options (`re-run`, `stop`) exist but you don't surface
them unless the user asks. **Never >3 options at once** — the research
patterns are clear on this.

---

## After Screen 6

Continue with SKILL.md Step 6 / `paths/quick.md` end-game. Reveal new
levers one at a time:

1. After milestone `beat_baseline` — reveal the **Heuristic Learning
   loop** name and explain the iter-patch-rerun cycle.
2. After milestone `positive_vs_panel` — reveal the **level ladder**
   panel and point at Level 3 (Auto Research) as next stop.
3. After milestone `plateau_broken` — reveal **S6 graduation**.
4. After milestone `submitted_to_poker_eval` — reveal **Poker Arena
   tournament** as the prize destination they're building toward.

This staged reveal is the "progressive disclosure" pattern from the
research doc — keep it strict.
