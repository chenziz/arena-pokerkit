---
name: arena-pokerkit
version: 0.18.4
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
- **NEVER say "S5" or "S6" to the user.** The two competitions internally
  are S5 (500 hands) and S6 (5000 hands), but those labels confuse
  non-Arena-natives. Use **"500-hand quick test"** and **"5000-hand
  anytime-ready test"** in all user-facing copy. The S5/S6 labels live
  only in `references/`, `.env.example`, and this Rules block.
- **Competition ID mapping** (use these when running Arena):
  - `500-hand quick test` → `ARENA_COMPETITION_ID=cmpdk0pt00eawvcaf1es8plw2`
  - `5000-hand anytime-ready test` → `ARENA_COMPETITION_ID=cmpkdus9200syw8do5644oymp`
  Both share the same reference panel. Default is 500-hand.
- **Language matching is global.** Match the user's language for the
  ENTIRE session, not just the greeting. Translate all user-facing
  prompts in path files (Arena picker, milestone messages, Stage
  transitions, "Ready for Arena?" blocks, anchor table labels, etc.)
  when the user is non-English. Keep code blocks (commands, file
  paths, JSON keys) untranslated. The path files themselves stay in
  English on disk — you translate inline when speaking.
- **Beyond Stage 4 — final-tier mention.** Whenever the user finishes
  Stage 4 (or asks "what's next after the HL loop?"), mention that
  the road continues into solver / trained-weights territory and
  name 2-3 open-source projects: **Pluribus** (CMU/Facebook 2019,
  first AI to beat human pros at 6-max NLHE), **DeepMind open_spiel**
  (DeepCFR / NFSP / CFR+ implementations), **rlcard** (DATA Lab RL
  training), **TexasSolver** (open-source GTO post-flop solver),
  **Slumbot** (Eric Jackson, HU NLHE), **PokerBench** (Penn State
  2025 academic 6-max benchmark). This kit doesn't go there — that's
  ~1 week + GPU. But the leaderboard top is people doing exactly
  this. Don't gate it behind a milestone — just mention once at
  Stage 4 close.

### Vocabulary — use these exact terms with the user

- **`pokerkit run`** — a LOCAL CLI command that drives your agent client.
- **Arena Poker Eval benchmark** — the SERVER-SIDE match against the
  reference panel. Two competition sizes available (see below).
- `pokerkit run` is the client that polls Arena and submits your
  `decide()`'s actions. The hand count is fixed by Arena per
  competition. The client's `--max-hands` flag lets you stop the
  CLIENT early; the SERVER-SIDE match stays open in `waiting_user`
  state and you can resume by running `pokerkit run` again.
- When talking to the user, name the competition size — say "the
  500-hand quick test" or "the 5000-hand anytime-ready test", not
  "S5" / "S6".

### Two Arena competition sizes (user-facing labels)

- **500-hand quick test** — 500 hands, ~15 min, ±20 bb/100 CI (raw).
  Default for build/iterate. Run after each HL-loop iteration to see
  if your patch worked. CI is ~±20 bb/100 so close bots can tie —
  use this for direction-checking, not for locking in your rank.
  Maps to `competition_id = cmpdk0pt00eawvcaf1es8plw2` (internally S5).
- **5000-hand anytime-ready test** — 5000 hands, ~2 hr, ±6 bb/100 CI
  (raw). Run when you feel confident, want a tight CI on your real
  ranking. Big enough to eliminate variance. Same reference panel.
  Maps to `competition_id = cmpkdus9200syw8do5644oymp` (internally S6).
- Future: Arena plans V2 all-in EV correction + V3 AIVAT, which will
  tighten CI ~3-10× at the same hand count. Until shipped, raw is what
  you get.
- When surfacing scores, ALWAYS include CI: `+5.2 ± 20 bb/100` on the
  500-hand test; `+5.2 ± 6 bb/100` on the 5000-hand test. Users need
  to see CI to know if their rank vs neighbors is statistically
  meaningful.

### Locality rule — quick iteration is LOCAL, Arena is for real eval

- **Quick iterations (5-200 hands) belong on `pokerkit selfplay`**,
  not on Arena. The Arena benchmark is the FULL 500-hand quick test —
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
reference panel you'll see in the tournament.

**Building a poker bot has 4 stages.** Each stage produces an
artifact you own and a visible score lift:

| Stage | What you build | Artifact | bb/100 |
|---|---|---|---|
| **1. Style** | Minimum bot, pick a TAG/LAG/balanced style | style label saved | -30 ~ -20 |
| **2. Strategy.md** | Real ranges, sizing, adaptation rules | `STRATEGY.md` (yours to edit) | -25 ~ -10 |
| **3. Auto Research** | GTO charts + opponent HUD baked into decide() | `research/*.json` data files | -10 ~ -3 |
| **4. Curriculum** | Run → analyze failures → patch → repeat | `failure_report.txt` + decide() diffs | -3 ~ +5 |

Most users walk through 1 → 2 → 3 → 4 in ~1 hour. All free.

**Pick your path:**
  • `quick`              — I drive all 4 stages, you approve at boundaries (~1 hr)
  • `guided`             — Same 4 stages, you participate actively (pick style, edit Strategy.md, choose research)
  • `learn`              — Explain Arena scoring + how the bot works first
  • `skip to research`   — You already have a style + strategy, jump to Stage 3
  • `skip to HL loop`    — You already have a working bot, jump to Stage 4 (curriculum)

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
| `skip to research` / `skip research` / `i have a strategy` / `jump to stage 3` | `paths/skip-research.md` |
| `skip to HL loop` / `skip to curriculum` / `i have a bot` / `jump to stage 4` | `paths/skip-hl.md` |
| `show levels` / `advanced` / `levels` | Surface `references/optimization-levels.md` ladder table, then re-prompt with the paths above |
| Explicit task ("build me a tight-aggressive bot and submit") | Skip the greeting, jump to Step 0 with their constraint as the strategy answer |

**If the user replies with anything not matching the above keywords**
(e.g. "help", "start building", "what's the prize?", a question, or
just any free text):
- If it's a question: answer briefly, then re-show the 5 path choices.
- If it's an intent-y phrase: best-match (e.g. "help" / "show me" →
  `learn`; "I want to build" → `quick`; "I know what I'm doing" → ask
  if `skip to research` or `skip to HL loop`).
- If totally ambiguous: re-prompt with "Not sure what to do? Pick
  one: `quick` / `guided` / `learn` / `skip to research` /
  `skip to HL loop`."

`paths/{quick,guided,learn,skip-research,skip-hl}.md` are subordinate
scripts — they reuse the Steps 0-6 below but pace and disclose
differently. Read the matching path file in full before executing.

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
  - 5000-hand anytime-ready test → after `plateau_broken`

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

## Milestones (4 stage milestones + within-stage markers)

The kit gamifies the dev loop with **4 stage milestones** anchored to
the 4-stage progression (Style / Strategy / Research / Curriculum)
plus 4 within-stage progress markers (First Arena Score / Beat
Baseline / Positive vs Panel / Plateau Broken). All persisted in
`.pokerkit-milestones.json` at the repo root (flat file next to
`.arena-credentials`, NOT a directory). Schema:

```json
{
  "style_picked": "2026-05-25T14:03:12Z",
  "strategy_written": "2026-05-25T14:05:14Z",
  "first_arena_score": "2026-05-25T14:12:14Z"
}
```

On agent start, read the file (if it exists). On any milestone
unlock, write the new key with the current ISO timestamp. **Atomic
writes**: write to `.pokerkit-milestones.json.tmp` then `os.rename`.

### The 4 stage milestones (ordered)

| Stage | id | Pretty name | Unlocks when |
|---|---|---|---|
| Stage 1 | `style_picked` | Style Picked | A style (TAG/LAG/balanced/custom) is selected — guided ASKs, quick auto-defaults — and the style label is saved |
| Stage 2 | `strategy_written` | Strategy Written | `STRATEGY.md` exists in repo root as the SPEC (real ranges + sizing + adaptation rules); the agent has translated it into `decide()` Python — the runtime bot reads only the generated code, not the markdown |
| Stage 3 | `research_wired` | Research Wired | At least one research data source baked in (`research/preflop.json`, board-texture buckets, or `/texas/agent-stats` hook); `decide()` consults it before pure-style decisions |
| Stage 4 | `curriculum_running` | Curriculum Running | First HL loop iteration completed: `failure_report.txt` generated + at least one `decide()` patch applied + re-run logged in `.arena-poker-state['iterations']` |

### Within-stage progress markers (kept from prior versions)

| id | Pretty name | Unlocks when |
|---|---|---|
| `first_arena_score` | First Arena Score | ★ first Arena terminal state (500-hand quick test) — the magic moment; usually fires inside Stage 1 or Stage 2 |
| `beat_baseline` | Beat Baseline | Arena bb/100 beat the local baseline call-station / random reference |
| `positive_vs_panel` | Positive bb/100 vs Panel | Arena bb/100 ≥ 0 — non-losing result vs the reference panel |
| `plateau_broken` | Plateau Broken | improved >5 bb/100 over best previous Arena score (fires inside Stage 4) |

Stage milestones and within-stage markers are independent. A user on
the `quick` path will typically unlock: Style Picked → First Arena
Score → Strategy Written → Beat Baseline → Research Wired → Positive
vs Panel → Curriculum Running → Plateau Broken.

### Surfacing

On every **stage milestone** unlock, print this pop with a 4-cell
stage bar:

```
🎯 Stage {n} unlocked — {Pretty Name} ({n}/4 stages)
Progress: █░░░  Stage {n} / 4  ·  Next: {next stage pretty name}
```

On every **within-stage marker** unlock, print this pop with no stage
bar (markers fire opportunistically):

```
🎯 Milestone unlocked — {Pretty Name}
```

Don't print the bar on every narration line — only on stage milestone
unlock and at the end of major Phases.

### Pretty-name map

| id | pretty name | type |
|---|---|---|
| style_picked | Style Picked | stage 1 |
| strategy_written | Strategy Written | stage 2 |
| research_wired | Research Wired | stage 3 |
| curriculum_running | Curriculum Running | stage 4 |
| first_arena_score | First Arena Score | marker |
| beat_baseline | Beat Baseline | marker |
| positive_vs_panel | Positive bb/100 vs Panel | marker |
| plateau_broken | Plateau Broken | marker |

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

### Permission heads-up (read this BEFORE the first command)

The very first thing you do here is run `./pokerkit` (or `uv sync` /
`uv run`) against a freshly-cloned repo your sandbox has never seen.
**Most agents will pause for a Bash permission prompt at this point.**
This is expected — fresh agents sandbox unfamiliar repo paths by
default, and the `./` shell wrapper adds an extra layer of suspicion.

**Surface this to the user BEFORE running anything**, so they have
context when the prompt appears. Paste (or paraphrase in the user's
language) the block below verbatim.

> **Source of truth.** The canonical full text lives in
> `references/permissions.md`. This block is a synced copy — if you
> edit anything here, mirror the change there too (and to
> `paths/quick.md`, `paths/guided.md`, `README.md`). Other agents
> reading this skill should treat `references/permissions.md` as the
> editable source.

```
💡 Heads-up — your sandbox may ask permission for the first few
commands I run in this repo. That's normal because the kit is new to
your agent. Three things to know:

  1. Local-only Python. The kit installs and runs Python on your
     machine. There are exactly two network steps:
       - One-time: `uv sync` downloads Python packages from PyPI
         (~30 seconds, ~50MB). Standard package install.
       - Per Arena run (Stage 3+ only, you explicitly approve before
         I start): API calls to b-arena.dev.fun for the benchmark.
     Everything else (selfplay, tests, code edits) is pure local
     Python — no network.

  2. One-time grant is enough. Once you approve, all subsequent
     commands work without prompting.

  3. Pre-grant options (per agent):
       - Claude Code: copy .claude/settings.json.example to
         .claude/settings.json before we start. Allowlists the exact
         commands the kit needs (git clone, uv sync, ./pokerkit, etc).
       - Codex CLI: copy .codex/config.toml.example to
         ~/.codex/config.toml, OR just approve the workspace once
         when prompted — Codex auto-adds it to its trusted list.
       - Cursor / Aider / Windsurf / Continue: approve when prompted
         on first run. Each tool has its own per-workspace dialog.

If your sandbox gives you options like "approve once / add permission
rule / hand off" — pick **approve** (one-time is fine; "add rule" is
also fine and more permanent). Don't pick "hand off" — that defeats
the whole point of me driving for you.
```

If the user is non-English, translate inline (the rules for global
language matching apply here too).

#### Read-only sandbox fallback (Phase 1 `cp .env.example .env`)

Some sandboxes (notably Codex CLI strict read-only mode) can't write
`.env`. The kit works without one — just export env vars directly:

```bash
# Setup (writeable sandbox — default):
cp .env.example .env

# Setup (read-only sandbox — Codex strict mode):
export ARENA_API_BASE=https://b-arena.dev.fun/api/arena
export ARENA_COMPETITION_ID=cmpdk0pt00eawvcaf1es8plw2
```

If `cp` is blocked or `.env` write fails (EROFS / EACCES), fall back
to the `export` form silently and tell the user once: *"Your sandbox
is read-only; I'm using env vars instead of a .env file. Same effect."*

### Wrapper-less command form

Every `./pokerkit <verb>` in this kit has an equivalent
`uv run python examples/<script>.py` form. Some sandboxes auto-allow
`uv run` but block arbitrary `./` invocations — use the wrapper-less
form as a fallback if the shell wrapper keeps getting blocked. Both
forms produce identical output.

| Short form | Equivalent |
|---|---|
| `./pokerkit run` | `uv run python examples/agent.py` |
| `./pokerkit selfplay --hands 200` | `uv run python examples/selfplay.py --hands 200` |
| `./pokerkit test` | `uv run python -m pytest tests/ -q` |
| `./pokerkit analyze --out failure_report.txt` | `uv run python examples/analyze.py --out failure_report.txt` |
| `./pokerkit replay --latest` | `uv run python examples/replay.py --latest` |
| `./pokerkit version` | `uv run python examples/cli.py version` |

### Setup steps

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
3. `cp .env.example .env` — defaults to Poker Eval 500-hand quick
   test (`cmpdk0pt00eawvcaf1es8plw2`, internally S5). Leave
   `ARENA_API_KEY` blank; the agent auto-registers on first run.
   If `cp` is blocked or the FS is read-only (Codex strict mode),
   skip the `.env` write and `export ARENA_API_BASE=https://b-arena.dev.fun/api/arena`
   + `export ARENA_COMPETITION_ID=cmpdk0pt00eawvcaf1es8plw2` instead
   — same effect. See `references/permissions.md`.

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

## Step 5: Arena benchmark (ASK — first run is the 500-hand quick test by default)

Reminder: don't run small Arena previews for iteration — that's what
`pokerkit selfplay` is for. Step 5 is the **full Arena benchmark**
(real opponents from the reference panel). Default is the **500-hand
quick test** (~15 min); the user can opt into the **5000-hand
anytime-ready test** (~2 hr) when they want a tight CI.

Surface the 2-option picker (use this template, identical wording
across all paths):

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

Pick: `500` / `5000`.
```

[If `500` — ACT:]
   ./pokerkit run    # uses default ARENA_COMPETITION_ID=cmpdk0pt00eawvcaf1es8plw2

[If `5000` — ACT:]
   ARENA_COMPETITION_ID=cmpkdus9200syw8do5644oymp ./pokerkit run

When it completes, **always** report the score using the 4-line
"Score interpretation" template — and ALWAYS include the CI value
(`±20 bb/100` for the 500-hand test, `±6 bb/100` for the 5000-hand
test, raw — no variance adjustment).

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
  Score < -20:                      "Pull failure report → patch → re-run the 500-hand quick test."
  Still climbing (delta >= +2):     "One more 500-hand round."
  Plateaued (delta < +2 last 2 iters):
                                    "You've tuned as far as the 500-hand quick test
                                     (±20 raw CI) can measure. Graduate to the
                                     5000-hand anytime-ready test (~2 hr) to lock in
                                     your definitive ranking with a tight ±6 CI."
  3 plateau iters in a row:         "Stop iterating on the 500-hand test; run
                                     the 5000-hand test to lock in."
```

When the user says "go" after plateau, run the 5000-hand test by
setting `ARENA_COMPETITION_ID=cmpkdus9200syw8do5644oymp` (or
`--competition-id cmpkdus9200syw8do5644oymp`).

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

**Iron rule: every Arena score render MUST include the 4-stage anchor
table.** No isolated numbers. No bare bb/100 figure without the
anchor table around it. Always frame as "you are at Stage N, score Y,
next stage targets Z."

### The 4-stage anchor table (paste this every time)

```
📊 Your Stage {N} score: {bb_per_100} ± {CI} bb/100  ({season}, {hands} hands)

  random bot:         ~-200
  Stage 1 (style):    ~-25
  Stage 2 (strategy): ~-15
  Stage 3 (research): ~-5
  Stage 4 (curriculum): ~+3
  Top bots:           ~+10

You are at Stage {N} ({stage_name}). Score {bb_per_100}.
→ Next stage target: ~{next_anchor} bb/100.
```

Substitute `{N}`, `{stage_name}`, `{bb_per_100}`, `{CI}`, `{season}`,
`{hands}` from the user's actual run + their current stage in
`.pokerkit-milestones.json`. Mark "← you ran this" on the row for the
user's current stage so they see where they sit. The `{next_anchor}`
is the next-stage row from the table; if the user is at Stage 4,
point at Top Bots instead.

### Plus the 4-line CI explainer (first Arena run only)

On the FIRST Arena run, also include these 4 lines under the table:

1. **Raw score**: `{bb/100} ± {CI} bb/100` over `{N}` hands ({test name}).
   For the 500-hand quick test: CI ≈ ±20. For the 5000-hand
   anytime-ready test: CI ≈ ±6. Wide because scoring is raw bb/100
   with no variance adjustment (yet).
2. **What it means**: bb/100 = big blinds win/lose per 100 hands.
   Negative = losing money.
3. **Why local ≠ Arena**: Local selfplay uses simple bots. Arena uses
   the reference panel — way stronger. Compare DELTAS between Arena runs, not
   absolute numbers.
4. **What ± {CI} means**: your true skill is within {CI} bb/100 of
   this number, 95% confidence. If your rank-neighbors' CIs overlap
   yours, you can't tell who's actually better — graduate to the
   5000-hand anytime-ready test (±6 raw CI) to resolve. Arena plans
   V2 all-in EV correction + V3 AIVAT, which will tighten these CIs
   3-10× at the same hand count, but neither has shipped yet.

Subsequent Arena runs use the anchor table + a 1-line trajectory
(`{prev_score} → {current_score} bb/100 ({+/-}{delta})`), no CI
explainer repeated.

If the score is negative, **don't frame it as failure**: "Negative
score is normal vs the reference panel until you reach Stage 4. The
curriculum loop's job is to find the patterns that lose chips and
patch them."

---

## Beyond Stage 4 — solver / trained-weights territory

When the user closes out Stage 4 (or asks "what's the ceiling?"),
surface this once. Don't gate it behind a milestone — just mention it
as the final tier the leaderboard top is built from.

The Stage 4 HL loop ceiling is roughly **-3 to +5 bb/100** vs the
reference panel. To go higher, the industry approach is to **train
your own neural net** or use a **post-flop solver** for canonical
spots. Examples (all open-source):

- **Pluribus** (Facebook AI / CMU, 2019) — first AI to beat human pros
  at 6-max NLHE. Used MCCFR self-play + AIVAT scoring. Methods paper
  public, model not.
- **DeepMind open_spiel** — includes DeepCFR, NFSP, CFR+
  implementations. Trainable on 6-max NLHE with a GPU.
- **rlcard** (DATA Lab) — RL training framework for poker, includes
  6-max NLHE environments and NFSP baselines.
- **TexasSolver** — open-source GTO post-flop solver. Pre-compute
  optimal frequencies for canonical spots, bake the lookup table into
  your bot.
- **Slumbot** (Eric Jackson) — public NLHE HU bot, semi-open methods.
  HU-only but worth studying.
- **PokerBench** (Lin et al, Penn State 2025) — academic 6-max NLHE
  benchmark, useful for comparing your bot.

This kit doesn't take you there — that's a ~1-week + GPU project. But
the top of the Poker Arena leaderboard will be people doing exactly
this. If you want to seriously compete, your roadmap is: this kit →
train weights (or import solver tables) on top.

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
| Run `pokerkit run` (500-hand quick test, ~15 min) | | ✓ (real eval) |
| Run `pokerkit run` (5000-hand anytime-ready test, ~2 hr) | | ✓ (definitive) |
| Strategy style | | ✓ (taste) |
| Surface bb/100 verdict | ✓ | |
| Modify files outside `examples/`, `assets/`, root config | ✗ | |
| Push to GitHub | ✗ | |

**Rule of thumb:** act when the work is **recoverable and reviewable**
(file edits, test runs, analysis). Ask when the work is **irreversible
or taste-driven** (strategy choice, full submission, time budget).

---

## Reference files (read on demand)

- `references/permissions.md` — **canonical** first-run permission
  heads-up + Codex/Claude pre-grant options + read-only sandbox
  fallback + wrapper-less command table. Edit point for any
  permission wording change. SKILL.md / paths / README quote from
  this file.
- `references/output-parsing.md` — how to grep `pokerkit selfplay`
  output for `baseline_local` bb/100 (exact line format, regex).
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
