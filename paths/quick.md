# Path: quick — "I'm in, just do it"

> Loaded when the user replies `quick` to the SKILL.md first-contact
> greeting. The goal is one thing: **land a real Arena Poker Eval
> score on the leaderboard in ~10 min wall clock**, with zero strategy
> questions. The user gets a baseline bot you chose, then you reveal
> the iteration menu only after they see their score.

---

## Pacing

```
Screen 1: greeting (already shown by SKILL.md)
Screen 2: "On it. I'll narrate." → silent Phase 1 → 🎯 Kit Connected
Screen 3: silent Phase 3 (apply decide_textured) → 🎯 Local Eval Green
Screen 4: ASK approval to run Arena S5 (only ASK on quick path)
Screen 5: pop the score BIG → reveal iteration menu
```

Three or fewer options on any screen. Never dump the level ladder up front.

---

## Phase 1 — Setup (ACT, silent except milestone pop)

Run, in order:

```bash
# if not already inside the repo:
git clone https://github.com/chenziz/arena-pokerkit
cd arena-pokerkit

uv sync
cp .env.example .env
./pokerkit selfplay --hands 200 --seed 42   # local baseline number
```

On success, unlock milestone `kit_connected` (see milestone list in
`SKILL.md` → "Milestones"). Print the progress bar:

```
🎯 Milestone unlocked — Kit Connected (1/10)
Progress: █░░░░░░░░░  1/10  ·  Next: First Hand Played
```

Local baseline number from `selfplay` goes into the iteration history
as `baseline_local`. **Do not surface the raw number yet** — it's
meaningless without the Arena anchor. You'll show it alongside the
Arena score in Screen 5.

---

## Phase 2 — Auto-pick the bot (ACT, silent)

Quick path skips Step 2 (strategy elicitation). Default action:

```bash
cp assets/decide_textured.py examples/agent.py
```

Why `decide_textured.py`: it's the strongest of the three reference
implementations (board-texture-aware sizing on top of OPENING_RANGES).
It's the boring win — solid baseline, no questions asked.

Unlock `first_hand_played` and `style_chosen` (auto-default) together:

```
🎯 Milestone unlocked — First Hand Played (2/10)
🎯 Milestone unlocked — Style Chosen (3/10)  · auto-default: textured
Progress: ███░░░░░░░  3/10  ·  Next: Local Eval Green
```

---

## Phase 3 — Local validation (ACT, silent)

```bash
./pokerkit test                            # 20 unit fixtures, must pass
./pokerkit selfplay --hands 200 --seed 42  # ~1 s, capture new bb/100
```

Both must pass. If `selfplay` reports a number lower than
`baseline_local`, revert and re-run with `decide_ranged.py` as a
fallback. If both reference bots underperform local default, surface
that to the user and let them pick.

On success, unlock milestone `local_eval_green`:

```
🎯 Milestone unlocked — Local Eval Green (4/10)
Progress: ████░░░░░░  4/10  ·  Next: First Arena Score
```

---

## Phase 4 — Arena S5 (ASK — this is the only ASK on quick path)

```
Ready. Your bot is wired and locally clean.

Next: 500 hands vs Arena's reference panel — about 15 min, real
benchmark. Say `go` to start, or `wait` if you want to inspect the
bot first.
```

On `go`, run:

```bash
./pokerkit run
```

While it runs, narrate roughly every 100 hands: `hands=200/500 ·
adjustedBbPer100=-7.2 · pending=0`. No drama, no level talk yet.

When it terminates (status `completed`), read `.arena-credentials` and
surface the registration block **once** (full apiKey, agentId, claim
URL) per SKILL.md "Registration" section. Then unlock
`first_arena_score`:

```
🎯 Milestone unlocked — First Arena Score (5/10) ★
Progress: █████░░░░░  5/10  ·  Next: Beat Baseline
```

---

## Screen 5 — show the score BIG

Use the **full 4-line "Score interpretation"** template from SKILL.md
(first-run variant). Then drop the iteration menu — **3 options max**:

```
Your score:

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {bb_per_100} ± 20 bb/100   (S5, 500 hands)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Anchor: LLM-only bots lose ~30. Top human-designed bots lose ~3.
You're at {bb_per_100}. The gap is the game.

What now?
  • `analyze` — I pull the failure report and patch one losing pattern
  • `re-run` — same bot, fresh 500 hands (variance check)
  • `stop` — that's your line in the sand for today

Type one.
```

Do NOT introduce Levels, the ladder panel, or graduation to S6 yet.
Those unlock once the user has done at least one analyze→patch→re-run
cycle (milestone `beat_baseline` or `positive_vs_panel`).

---

## After Screen 5 — hand off to `paths/guided.md` or SKILL.md Step 6

If the user picks `analyze`, follow the SKILL.md Step 6 iteration loop
but keep narration in the same milestone-pop style. Each new milestone
pop counts as the user's primary feedback signal — not a long score
recap each round.

If they pick `stop`, write the final state and acknowledge: *"You're
on the board. Come back any time — `./pokerkit run` resumes from here."*

---

## What the quick path **does not** do

- Ask about strategy style (`guided` does that)
- Explain bb/100 / DeepCFR / variance up front (`learn` does that)
- Show the 6-level ladder (revealed lazily after first iteration)
- Run Arena previews (`--max-hands 50`) — only the full S5
- Auto-graduate to S6 — that requires user opt-in after plateau
