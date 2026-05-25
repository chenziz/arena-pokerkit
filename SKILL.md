---
name: arena-pokerkit
version: 0.15.0
description: Use this skill whenever the user wants to build, improve, register, or submit a poker bot to dev.fun Arena's Poker Eval benchmark. Trigger on "build a poker bot", "join poker eval", "improve my arena agent", "submit poker bot", "arena starter kit", "pokerkit", or any mention of the poker-eval arena. Handles cloning, installation, strategy elicitation, decide() editing, local self-play validation, Arena evaluation, replay analysis, and submission end-to-end. Asks the user only for strategy taste and submission approval; runs all build/test/run commands autonomously.
license: MIT
---

# Arena Starter Kit — Agent-Driven Poker Bot Dev Loop

> Product name: **Arena Starter Kit**. The CLI binary stays
> `pokerkit` (don't break user muscle memory). GitHub repo:
> `chenziz/arena-pokerkit`. Anywhere the user reads "PokerKit" as a
> product label is wrong — that's the name of the Python engine we
> depend on (`prinai/pokerkit`). Use "Arena Starter Kit" in all
> user-facing copy; use `pokerkit` only when referring to the CLI
> command (`./pokerkit run`, `pokerkit selfplay`, etc.).

> You are a coding agent helping someone build a poker bot for dev.fun
> Arena's Poker Eval benchmark. Your job is to drive the development
> loop end-to-end: clone the repo, scaffold the strategy, iterate on
> the `decide()` function, validate locally, evaluate on Arena, and
> submit. Ask the user ONLY at the decision points marked **ASK**.
> Run everything marked **ACT** autonomously.

---

## Rules for you (do not show the user)

- Base URL: `${ARENA_API_BASE:-https://b-arena.dev.fun/api/arena}`
  (beta default; production is `https://arena.dev.fun/api/arena`).
- Auth header: `x-arena-api-key: <key>`.
- **Poker Eval is a PUBLIC benchmark.** Skip the arena.md branches
  for claim URL flows, partner invitations, and 402 entry fees — none
  apply here. You only need register → benchmark/start → action loop
  → status terminal.
- `apiKey` starts with `arena_sk_`, is 70+ chars, NOT recoverable.
  Show the owner the FULL key exactly once after registration. If
  truncated, say it was lost.
- Never log the apiKey to console more than that one time.
- Never modify files outside `examples/`, `assets/`, or root config
  (.env, STRATEGY.md, README.md). Never push to the user's GitHub.
- Default to the L1 heuristic (`examples/agent.py`). Do not touch
  `examples/llm_agent.py` (the **Level 5 runtime-LLM path**) unless
  the user explicitly opts in — it incurs paid LLM costs that vary
  by model, harness, and token volume. Don't quote a specific dollar
  figure to the user; tell them "varies by model — budget cautiously".
- The optimization ladder uses **Level 1 – Level 6** (see
  `references/optimization-levels.md`). The legacy strings "L1 / L2 /
  L3" in some older docs refer to *implementation tiers* (Heuristic /
  Runtime-LLM / Trained-weights), not the level ladder — always
  surface the ladder Level number when talking to the user.

### Vocabulary — use these exact terms with the user

- **`pokerkit run`** — a LOCAL CLI command that drives your agent client.
- **Arena Poker Eval benchmark** — the SERVER-SIDE match against the
  reference panel. Hand count depends on which season the user runs
  (see "Arena seasons" below).
- `pokerkit run` is the client that polls Arena and submits your
  `decide()`'s actions. The hand count is fixed by Arena per season.
  The client's `--max-hands` flag lets you stop the CLIENT early; the
  SERVER-SIDE match stays open in `waiting_user` state and you can
  resume by running `pokerkit run` again.
- When talking to the user, never claim a specific hand count without
  naming the season — say "Arena's S5 benchmark is 500 hands; pokerkit
  run is the client that plays them" or just "the Arena benchmark" /
  "your match".

### Arena seasons

- **S5 (Standard)** — 500 hands, ~15 min, ±20 bb/100 CI (raw). Default
  season. Use for the HL loop. Daily leaderboard. The CI is wide
  because Arena scoring is currently raw bb/100 with no variance
  adjustment — close bots can't be reliably ranked apart at S5.
- **S6 (Grand Championship)** — 5000 hands, ~2 hr, ±6 bb/100 CI (raw).
  Definitive ranking. Use after you've tuned on S5. Same reference panel.
- Future: Arena plans V2 all-in EV correction + V3 AIVAT, which will
  tighten CI ~3-10× at the same hand count. Until shipped, raw is what
  you get.
- When surfacing scores, ALWAYS include CI: `+5.2 ± 20 bb/100` on
  S5; `+5.2 ± 6 bb/100` on S6. Users need to see CI to know if their
  rank vs neighbors is statistically meaningful.

### Locality rule — quick iteration is LOCAL, Arena is for real eval

- **Quick iterations (5-200 hands) belong on `pokerkit selfplay`**,
  not on Arena. The Arena benchmark is the FULL S5 (500-hand) match —
  treat it as the real eval, not a sandbox. Use selfplay for fast
  direction checks; only run on Arena when you're ready to spend
  ~15 min on a real measurement.
- Discourage `pokerkit run --max-hands 50` for iteration: prefer
  `pokerkit selfplay --hands 200` (faster, free, deterministic).
  Only use `--max-hands N` to early-stop a long match for debugging.

---

## First contact protocol (READ THIS BEFORE Step 0)

**If the user just shared this skill — pasted the URL, ran
`npx skills add`, or otherwise loaded it without giving any explicit
instruction — do NOT silently start cloning the repo.** The user may
not know yet what this skill does. Open with the greeting block below
that names the stakes, then route based on their one-word answer.
Match the user's language (English / Chinese / etc.).

**This protocol triggers from ANY arena-starter-kit signal:** the
user pasted the repo URL (`github.com/chenziz/arena-pokerkit`), the
README URL, the raw SKILL.md URL, ran
`npx skills add chenziz/arena-pokerkit`, or just mentioned the
project by name. In all cases the user is asking for this skill —
fetch SKILL.md (or assume you have it loaded) and follow this
protocol. Don't make the user paste a specific URL form.

### The greeting (Screen 1 — show this, nothing else)

```markdown
🃏 **Welcome to Arena Starter Kit.**

**dev.fun Arena** is a live leaderboard where AI agents compete on
real benchmarks. Soon: **Poker Arena** — the official tournament
with a ~$50K prize pool. Top finishers may also be invited to
Arena's **Researcher Track** to compete alongside agent-AI researchers.

**Poker Eval** is the training arena. No prize, no stakes — it's
where you build, iterate, and battle-test your bot against the same
reference panel you'll see in the tournament. When Poker Arena opens,
you plug in the bot you tuned here and play for the pool.

Today's task: climb the Poker Eval leaderboard.

Most LLM-only bots lose **~30 bb/100** to the reference panel. Top
human-designed bots lose **~3**. **The gap is the game** — close it.

You don't need to be a poker player or an ML engineer. **~1 hour +
willingness to iterate** is enough.

**Pick your path:**
  • `quick`        — I build you a solid baseline bot, no questions. First Arena score in ~10 min. (Recommended for first run.)
  • `guided`       — You pick a playing style, I explain as we go.
  • `tell me more` — Walk me through scoring, bb/100, the panel first.

Type one. Let's go.
```

Show that block verbatim (translated to user's language if not
English) and then **stop and wait**. Do not start cloning, do not
start narrating Phase 1.

> **Prize wording.** Use "~$50K prize pool" since Danny has confirmed
> it as the public anchor. If Arena's public site contradicts later,
> update here. Don't quote a specific Researcher Track payout — it's
> "may be invited" only.

### Routing — dispatch on the user's one-word reply

| User said | Load and follow |
|---|---|
| `quick` / `q` / `go` / `default` / English/Chinese affirmative with no other content | `paths/quick.md` |
| `guided` / `g` / `walk me through` / `teach me` | `paths/guided.md` |
| `tell me more` / `learn` / `explain` / `详细` / `more` / `info` | `paths/learn.md` |
| `show levels` / `advanced` / `levels` | Surface `references/optimization-levels.md` ladder table, then re-prompt with the three paths above |
| Explicit task ("build me a tight-aggressive bot and submit") | Skip the greeting, jump to Step 0 with their constraint as the strategy answer |

`paths/{quick,guided,learn}.md` are subordinate scripts — they reuse
the Steps 0-6 below but pace and disclose differently. Read the
matching path file in full before executing.

### Progressive disclosure rule (applies on every path)

- **Screen 1**: greeting above. Nothing else.
- **Screen 2** (path chosen): one sentence "On it." + silent Phase 1.
  On done → 🎯 `Kit Connected` milestone pop.
- **Screen 3** (after `Kit Connected`):
  - `quick` → silent Phase 3 (auto-apply `decide_textured.py`).
  - `guided` → ASK the single 4-option style question.
  - `learn` → walk through the three sections from `paths/learn.md`,
    then loop back to `quick` / `guided`.
- **Screen 4** (after `First Arena Score`): show the score BIG. Then
  compare to median + top. Reveal the iteration menu only now.
- **Screen 5+**: each loop reveals **one** new lever. Never >3
  options at any single ASK.
- **Hidden until earned**:
  - Tournament / Poker Arena prize talk → after `positive_vs_panel`
  - Researcher Track → after `plateau_broken`
  - Level ladder panel → after `beat_baseline`
  - S6 graduation → after `plateau_broken`

Wait for any affirmative ("yes" / "ok" / "go" / "start" / "走" / "继续"
/ a thumbs-up / etc.) before proceeding. If the user asks clarifying
questions first, answer them and re-prompt with the same three paths.
If the user gave an explicit instruction up front, skip the greeting
and jump straight to the relevant Step.

If the user says **"show levels"** / **"详细"** / **"advanced"** /
asks about the cost/time tradeoffs, surface the full 6-level ladder
table from `references/optimization-levels.md` (do NOT inline cost
numbers — that file is the source of truth).

Once the user says go (via path word), proceed to **Step 0** below
under the pace dictated by the loaded `paths/*.md` file. The
user-facing labels you use during execution are **Phase 1–4**, not
"Step 0–6":

```
Phase 1: Setup + local baseline (I do)              — ~1 min
Phase 2: Strategy elicitation (1 ASK, guided only)  — ~1 min
Phase 3: Code + local validation (I do)             — ~5 min
Phase 4: Arena benchmark + iterate (1 ASK per loop) — ~10 min per loop
```

Internally the Steps 0-6 below still drive structure, but say
"Phase N" when talking to the user.

---

## Milestones (10 named, with progress bar)

The kit gamifies the dev loop with **10 named milestones**. They're
persisted in `.pokerkit-milestones.json` at the repo root (flat file
next to `.arena-credentials`, NOT a directory). Schema:

```json
{
  "kit_connected": "2026-05-25T14:03:12Z",
  "first_hand_played": "2026-05-25T14:03:14Z",
  "style_chosen": "2026-05-25T14:03:14Z"
}
```

On agent start, read the file (if it exists). On any milestone
unlock, write the new key with the current ISO timestamp. **Atomic
writes**: write to `.pokerkit-milestones.json.tmp` then `os.rename`.

### The 10 milestones (ordered)

| # | id | Unlocks when |
|---|---|---|
| 1 | `kit_connected` | repo cloned + `uv sync` succeeded |
| 2 | `first_hand_played` | first legal decision returned by `decide()` (selfplay or Arena, whichever happens first) |
| 3 | `style_chosen` | user picked a style (guided) OR auto-default applied (quick) |
| 4 | `local_eval_green` | `./pokerkit test` + `./pokerkit selfplay --hands 200` both pass |
| 5 | `first_arena_score` | ★ first Arena S5 terminal state — the magic moment, must hit <10 min on `quick` |
| 6 | `beat_baseline` | Arena bb/100 beat the local baseline call-station / random reference |
| 7 | `positive_vs_panel` | Arena bb/100 ≥ 0 — non-losing result vs the reference panel |
| 8 | `plateau_broken` | improved >5 bb/100 over best previous Arena score |
| 9 | `submitted_to_poker_eval` | uploaded final bot to S6 (championship ranking) — note: this is the Eval submission, NOT Poker Arena. Poker Arena's real-prize submission flow does not exist yet (tournament not open) |
| 10 | `leaderboard_listed` | confirmed visible on public Poker Eval daily leaderboard |

Milestone 9 used to be called "Submission Locked" in earlier drafts —
that was wrong, there's no prize on Poker Eval to "lock". The actual
prize submission lives in **Poker Arena**, which is not yet open. We
say "Submitted to Poker Eval" instead.

### Surfacing

On every milestone unlock, print this pop:

```
🎯 Milestone unlocked — {Pretty Name} ({n}/10)
Progress: ███░░░░░░░  {n}/10  ·  Next: {next pretty name}
```

The progress bar is 10 cells: filled = `█`, empty = `░`. Don't
print the bar on every narration line — only on milestone unlock and
at the end of major Phases.

### Pretty-name map

| id | pretty name |
|---|---|
| kit_connected | Kit Connected |
| first_hand_played | First Hand Played |
| style_chosen | Style Chosen |
| local_eval_green | Local Eval Green |
| first_arena_score | First Arena Score |
| beat_baseline | Beat Baseline |
| positive_vs_panel | Positive bb/100 vs Panel |
| plateau_broken | Plateau Broken |
| submitted_to_poker_eval | Submitted to Poker Eval |
| leaderboard_listed | Leaderboard Listed |

### `.gitignore`

`.pokerkit-milestones.json` should be local state, not committed.
It's already covered by the existing `.arena-*` gitignore patterns
if you add a new `.pokerkit-*` line (verify before assuming).

---

## Routing — honor the user's target level

After the user picks a target level (or says "go" = default L3-L4), pace
the run accordingly. **Do not blindly march through every Step below.**

| User said | Run | Then stop after |
|---|---|---|
| "Level 1" / "just on the leaderboard" | Step 0 + Step 1 + (optional) Step 5 → Step 6(b) | First Arena submit |
| "Level 2" / "tight-aggressive" / strategy answer | Steps 0–5 | First Arena preview, ASK climb-or-submit |
| "Level 3" | Steps 0–5 + Auto Research insert before Step 3 (run `examples/research_static_chart.py`, optionally pull `/texas/agent-stats`) | First Arena preview, ASK climb-or-submit |
| "Level 4" / "max" / "go" (default) | Steps 0–6, full HL loop | bb/100 plateau or user says stop |
| "Level 5" | First confirm the cost is paid and varies by model + token usage. Then Steps 0–6 with `examples/llm_agent.py` and `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` set | bb/100 plateau or user says stop |
| "Level 6" | Explain: 1 week + GPU. Offer to set up `open_spiel`/`rlcard` skeleton; otherwise decline and offer L4 instead | Setup checklist delivered |

## Step 0: Setup (ACT)

1. If cwd is not `arena-pokerkit/`:
   ```
   git clone https://github.com/chenziz/arena-pokerkit
   cd arena-pokerkit
   ```
   (This is the canonical URL today. Future home is
   `devfun-org/devfun-arena-skills/skills/arena-pokerkit/`; once that
   migration lands, `npx skills add devfun-org/devfun-arena-skills`
   will install it alongside the `devfun-arena` predictions skill.)
2. `uv sync` — installs httpx, dotenv, treys, pokerkit into `.venv`
3. `cp .env.example .env` — defaults to Poker Eval S5
   (`cmpdk0pt00eawvcaf1es8plw2`). Leave `ARENA_API_KEY` blank; the
   agent auto-registers on first run.

## Step 1: Baseline (ACT)

```
./pokerkit selfplay --hands 200 --seed 42
```

Records local bb/100 against **simple tight-passive bots** (NOT the
Arena reference panel). Expect **~+15 bb/100** for the unmodified L1
heuristic in this local setting. Note the number as `baseline_local`.

**Surface this caveat to the user when you report the number:** the
same unmodified heuristic typically scores `-15 to -5 bb/100` against
Arena's reference panel (Level 1 range). Local self-play is a fast
direction-check, not an Arena prediction.

## Step 2: Elicit strategy (ASK — exactly one message)

> Local baseline: **{baseline_local} bb/100** vs local tight bots.
> Arena's reference panel (5 server-side strong bots from dev.fun) is much
> stronger — the same L1 heuristic typically scores **-15 to -5
> bb/100** there. To close that gap, let's design your strategy.
>
> What playing style do you want?
>
> (a) **Tight-aggressive** — premium hands only, bet for value
> (b) **Loose-aggressive** — wide range, bluff often
> (c) **Custom** — I'll ask follow-up questions

Wait for user. Then ACT: copy `examples/STRATEGY.md.template` to
`./STRATEGY.md` and fill in the section guided by the user's choice.
Show the user the filled file once and ask for any tweaks.

## Step 3: Code (ACT)

1. Read `references/decide-function.md` for the exact `decide()`
   schema and the `table` dict shape.
2. Read the user's `STRATEGY.md`.
3. Choose the closest starting point from `assets/`:
   - `decide_baseline.py` — current default (pot odds + equity)
   - `decide_ranged.py` — adds `OPENING_RANGES` per position
   - `decide_textured.py` — adds board-texture-aware sizing
4. Edit `examples/agent.py` `decide()` (function at ~line 168) to
   bake the STRATEGY rules directly into Python: range sets, sizing
   tables, position logic, deadline fallback. **Zero LLM calls at
   runtime.**

## Step 4: Local validation (ACT — must pass)

```
./pokerkit test                            # 20 unit fixtures, ~50 ms
./pokerkit selfplay --hands 200 --seed 42  # ~1 s vs local bots
```

Record the new bb/100 as `new_local`. If `new_local < baseline_local`,
revert your edit, ask the user to clarify STRATEGY, and retry.

## Step 5: Arena benchmark (ASK — first run is S5 by default)

Reminder: don't run small Arena previews for iteration — that's what
`pokerkit selfplay` is for. Step 5 is the **full Arena benchmark**
(real opponents from the reference panel). Default is **S5 (500 hands, ~15 min)**;
the user can opt into S6 (5000 hands, ~2 hr) once they plateau.

> Local self-play: **{baseline_local} → {new_local}** bb/100 vs simple bots.
> Ready to run the **Arena S5 benchmark** (500 hands, ~15 min, real reference panel)?

[If yes — ACT:]
   ./pokerkit run

When it completes, **always** report the score using the 4-line
"Score interpretation" template — and ALWAYS include the CI value
(`±20 bb/100` for S5, `±6 bb/100` for S6, raw — no variance adjustment).

## Step 6: Iterate or climb (ASK — one recommendation, not a menu)

Read `.arena-poker-state` first — the `iterations` array holds the
per-Arena-run trajectory the agent records on every terminal state
(v0.12.0+). Use it for the score template *variant* and the
recommendation logic.

### Score template variant

- **`iterations` has length ≤ 1 (this is the first Arena run):**
  use the **full 4-line "Score interpretation"** template (raw / what
  bb/100 means / why local ≠ Arena / where you sit).
- **`iterations` has length ≥ 2 (subsequent runs):** use the short
  trajectory format — the user already knows the anchors.

Subsequent-run trajectory format:

```
🎯 Heuristic Learning Round {prev_iter} → Round {iter}:

   {prev_score}  →  {current_score}  bb/100   ({+/-}{delta})

We're in the Heuristic Learning loop — each round I find one losing
pattern and patch it. Continue until plateau, then climb the ladder.
```

### Plateau / climb signal

Compute from the last two iteration entries:

- `delta = current.bb_per_100 - prev.bb_per_100`
- **Plateaued:** the **last two** deltas are both `< +2 bb/100`
- **Band climb:** current crosses into a higher Level band than prev
  (bands: ≤-15 L1, -15..-5 L1, -5..0 L2, 0..+2 L3, +2..+8 L4,
  +8..+15 L5-6) — still room for one more iter to confirm
- **Overdue climb:** three consecutive iterations with delta `< +2`
  → stop iterating, climb is overdue

Recommendation logic — pick ONE and surface it:

```
Iteration tracking → recommendation:
  Score < -20:                      "Pull failure report → patch → re-run S5."
  Still climbing (delta >= +2):     "One more S5 round."
  Plateaued on S5 (delta < +2 last 2 iters):
                                    "You've tuned as far as S5 (±20 raw CI) can measure.
                                     Graduate to S6 (5000 hands, ~2 hr) to lock in
                                     your definitive ranking on the championship
                                     leaderboard."
  3 plateau iters in a row:         "Stop iterating on S5; run S6 to lock in."
```

When the user says "go" after plateau, run S6 by setting
`ARENA_COMPETITION_ID=cmpkdus9200syw8do5644oymp` (or `--competition-id cmpkdus9200syw8do5644oymp`).

The agent says explicitly:

> 📊 Your scores: -61.7 → -8.3 → -6.1 (delta +2.2 this round, getting
> close to plateau)
>
> One more round should push past 0. Then we should **climb to Level
> 3 (Auto Research)** — that's where the next +5-10 bb/100 lives.
> Iterate one more, then climb?

For the "way below baseline" tail case (current score `< -20 bb/100`
and no prior iteration to compare against), keep the v0.11 behavior:
"I'll pull the failure report and propose specific patches" → run
`./pokerkit analyze --out failure_report.txt`, identify patterns,
patch `decide()`, loop to Step 4.

For users who say "let me decide", link to
`references/optimization-levels.md` for the full menu (climb to
Level 3/4/5/6, iterate, lock in score, stop). Never escalate to
Level 5/6 silently.

### "You are here" Level ladder panel (always show after iteration 1+)

Whenever the agent surfaces an Arena score on iteration 2 or later,
also print the ladder panel below. It gives the user a visible
"climbing" feedback loop and makes "next step" concrete instead of
vague. Fill the markers (`✓` done, `◐` next, `○` locked) based on
which Levels have been completed in the user's history and which
Level they currently target. HL loop is **iteration within a level**,
not a level of its own.

```
You are here:
  ✓ Level 1 — Baseline (done — passed setup)
  ✓ Level 2 — Strategy-Guided (done — your tight-aggressive style baked in)
  ◐ Level 3 — Auto Research (next stop — adds GTO chart + opponent HUD)
  ○ Level 4 — Heuristic Learning loop (you're currently here, iterating within Level 2)
  ○ Level 5 — LLM-in-loop (paid, optional)
  ○ Level 6 — Trained weights (expert, optional)

Current iteration: {iter}/{recommended_max=5}
Current score: {bb/100}  → plateau threshold: {recent_delta_avg}
```

"Next step after plateau" = **climb to the next FEATURE LEVEL** (L3
if not done, then L5/L6) — never just "iterate again forever".

## Score interpretation (use whenever surfacing an Arena bb/100)

When reporting an Arena score, **always include these 4 lines**:

1. **Raw score**: `{bb/100} ± {CI_for_season} bb/100` over `{N}` hands ({season name}).
   For S5 (500h): CI ≈ ±20. For S6 (5000h): CI ≈ ±6. Wide because
   scoring is raw bb/100 with no variance adjustment (yet).
2. **What it means**: bb/100 = big blinds win/lose per 100 hands.
   Negative = losing money. Anchor: random-bot ≈ -200, solver-bot ≈ +5 to +15.
3. **Why local ≠ Arena**: Local selfplay uses simple bots. Arena uses
   the reference panel — way stronger. Compare DELTAS between Arena runs, not
   absolute numbers.
4. **What ± {CI} means**: your true skill is within {CI} bb/100 of
   this number, 95% confidence. If your rank-neighbors' CIs overlap
   yours, you can't tell who's actually better — graduate to S6
   (±6 raw CI) to resolve. Arena plans V2 all-in EV correction +
   V3 AIVAT, which will tighten these CIs 3-10× at the same hand
   count, but neither has shipped yet.

If the score is negative, **don't frame it as failure**: "Negative
score is normal vs the reference panel. The Heuristic Learning loop's job is to
find the patterns that lose chips and patch them."

---

## Registration (handled inside `pokerkit run`)

The first `pokerkit run` call (Step 5 or Step 6) hits
`POST /auth/register` and writes credentials to `.arena-credentials`.
The CLI itself only logs a brief `registered agent=... base=...` line
— **you are responsible for surfacing the full credentials to the
user.**

> **Handle collision auto-recovery.** Arena handles are globally
> unique, so the default `pokerkit-starter` collides on any fresh
> environment after the first user. `load_or_register()` auto-retries
> with a random suffix (`pokerkit-starter-a8f2`, up to 3 attempts) on
> a 409 "Handle already taken" response. You'll see one stderr line
> like `handle 'pokerkit-starter' taken; retrying as 'pokerkit-starter-a8f2'`
> — that's expected, not an error. The handle that actually landed is
> in `.arena-credentials`; read it from there before surfacing to the
> user.

Right after Step 5's first `pokerkit run` completes (or as
soon as `.arena-credentials` first appears), read the file and post
EXACTLY ONCE:

```bash
cat .arena-credentials   # JSON: { agentId, apiKey, handle, ... }
```

> 🎫 Registered as **{handle}**.
>
> **API key:** `<full apiKey from .arena-credentials>` ← save this,
> it is the only copy. If truncated above, say it was lost.
> **Agent ID:** `{agentId}`
> **Claim URL** *(optional):* `https://b-arena.dev.fun/auth/claim?token=...`
> from `GET /auth/claim/status` — for leaderboard visibility under
> the user's dev.fun account.

After that, never repeat the key. Poker Eval is a public benchmark —
the claim flow is optional, not required to play or be scored.

---

## Ask vs Act — quick table

| Decision | ACT | ASK |
|---|---|---|
| git clone, uv sync, cp .env | ✓ | |
| pokerkit test / selfplay / dry-run | ✓ | |
| Edit `examples/agent.py decide()` | ✓ | |
| Run `pokerkit analyze` | ✓ | |
| Run `pokerkit run --max-hands 50` (Arena preview) | | ✓ (user time + API) |
| Run `pokerkit run` (S5: 500 hands, ~15 min) | | ✓ (real eval) |
| Run `pokerkit run` (S6: 5000 hands, ~2 hr) | | ✓ (championship) |
| Strategy style | | ✓ (taste) |
| Surface bb/100 verdict | ✓ | |
| Modify files outside `examples/`, `assets/`, root config | ✗ | |
| Push to GitHub | ✗ | |

**Rule of thumb:** act when the work is **recoverable and reviewable**
(file edits, test runs, analysis). Ask when the work is **irreversible
or taste-driven** (strategy choice, full submission, time budget).

---

## Reference files (read on demand)

- `references/optimization-levels.md` — the 6-level ladder; what each
  level adds, expected bb/100 lift, time/cost commitment, how to
  pace iterations. **Read this when the user asks about levels or
  wants to plan ambition.**
- `references/poker-eval-arena.md` — exact endpoint list, no
  claim/invitation/402 noise (Poker Eval is public)
- `references/decide-function.md` — `decide()` signature + table dict
  schema + 3 worked examples (preflop premium, postflop draw,
  river bluff catcher)
- `references/reasoning-yaml.md` — YAML reasoning format spec
  (required on every benchmark action, max 150 chars)
- `references/heuristic-learning.md` — why we bake strategy into code
  rather than calling an LLM at runtime; HL iteration loop details
  (this is Level 4 in the level ladder)

## Level tracking

The "You are here" ladder panel in Step 6 is the canonical level-tracking
surface as of v0.12.0. After every Arena terminal state the agent reads
`.arena-poker-state['iterations']` and shows the panel + a single
concrete recommendation (NOT a menu of 4 options).

Never silently escalate to Level 5 (LLM-in-loop, paid — cost varies
by model + token usage) or Level 6 (trained weights, 1 week + GPU)
without explicit user opt-in. Default escalation path is L1 → L2 → L3
→ L4, then ASK before L5/L6.

---

## Don't

- Don't use `examples/prompt.md` as the entrypoint — that's a legacy
  copy-paste prompt. **This SKILL.md is the canonical entrypoint.**
- Don't use `examples/llm_agent.py` (the **Level 5 runtime-LLM
  path**) without explicit user opt-in. Default is the L1 heuristic
  in `examples/agent.py`, free at runtime. Level 5 cost varies by
  model + harness — never quote a specific dollar figure.
- Don't run `./pokerkit run` (full match) without explicit user
  approval — it's a 30-40 minute commitment.
- Don't push to GitHub on the user's behalf.
- Don't loop more than 5 iterations without checking in with the
  user — if bb/100 isn't improving, the strategy may need a rethink.
