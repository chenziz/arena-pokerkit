# Path: learn — "explain Arena scoring + how the bot works first"

> Loaded when the user replies `learn` (or `tell me more` / `explain`
> / `详细` / `more`) to the SKILL.md first-contact greeting. The goal
> is **not** a comprehensive tutorial — that's decision paralysis.
> The goal: answer the three questions the user actually has BEFORE
> committing to any code work, then route to `quick` or `guided`.
>
> Each section ≤ 120 words. Always end with "ready to build one?"

---

## Section 1 — What dev.fun Arena is, what Poker Arena is, what Poker Eval is

```
**dev.fun Arena** is a public leaderboard where AI agents compete on
real benchmarks. Different game types live as separate competitions.

**Poker Arena** is the upcoming **tournament** — significant prize
pool, top finishers may be invited to a Researcher Track. Not open
yet; date TBA.

**Poker Eval** is the **training arena**: same engine, same opponent
reference panel, same scoring, no prize, no stakes. It's where you
build, iterate, and tune your bot **before** Poker Arena opens. The
leaderboard is daily and public — climbing it is your proof your
bot's ready.

You build here. You compete there (later).
```

---

## Section 2 — The 4-stage progression (this is what `quick` / `guided` do)

```
You don't build a poker bot in one shot. You build it through **4
progressive stages**, each producing an artifact you own and a
visible score lift:

  Stage 1  Style          → ~-25 bb/100  (label saved, decide() reads it)
  Stage 2  Strategy.md    → ~-15 bb/100  (real ranges + sizing in a file YOU own)
  Stage 3  Auto Research  → ~-5  bb/100  (GTO + HUD data baked into decide())
  Stage 4  Curriculum     → ~+3  bb/100  (iterate: run → analyze → patch → repeat)

Anchors:
  random bot           ~-200
  Stage 1 (style)      ~-25
  Stage 2 (strategy)   ~-15
  Stage 3 (research)   ~-5
  Stage 4 (curriculum) ~+3
  Top human-designed   ~+10

Every Arena score we report is anchored against this table. No
mystery scores. Each stage has a visible artifact in your repo.
```

---

## Section 3 — bb/100, scoring CI, and the reference panel

```
**bb/100** = big blinds won (or lost) per 100 hands. A bot's score
against a fixed opponent set is reported in this unit. Most first-time
bots score around -25 to -15 — that's expected and matches the Stage 1
or Stage 2 anchor.

**S5 CI**: 500 hands, ±20 bb/100 raw. Wide. Two close bots can't be
ranked apart at S5 — that's why S6 exists (5000 hands, ±6 bb/100 CI).

**The reference panel**: 5 strong bots Arena maintains. Currently
DeepCFR-style trained agents — not LLMs, trained on millions of
self-play hands. The exact lineup may rotate over time; tuning vs the
current panel transfers because strong fundamentals win against all of
them.

You climb the 4 stages against the same panel. Each stage closes
~10 bb/100 of the gap.
```

---

## After all three sections — offer the real choices

```
That's the setup. Ready to actually build one?

  • `quick`              — I drive all 4 stages, ~1 hr, you approve at boundaries
  • `guided`             — Same 4 stages, you participate actively (pick style,
                          edit Strategy.md, choose research)
  • `skip to research`   — You already have a style + strategy, jump to Stage 3
  • `skip to HL loop`    — You already have a working bot, jump to Stage 4

Type one.
```

If the user keeps asking questions, answer them but always offer the
paths after each answer. Don't let `learn` become a forever-FAQ loop —
the addictive moment is **seeing their first score with a real
artifact in their repo**, not reading more docs.

---

## Topics to expand on if asked (not unprompted)

| User asks | Quick answer | Deeper file |
|---|---|---|
| "what's S5 vs S6?" | S5 = 500 hands, ~15 min, daily. S6 = 5000 hands, ~2 hr, definitive. Same panel. | `references/poker-eval-arena.md` |
| "what's an Auto Research source?" | GTO preflop chart, board-texture buckets, opponent HUD via `/texas/agent-stats`. All offline lookups; zero LLM calls at runtime. | `references/optimization-levels.md` Level 3 |
| "what's Curriculum / HL loop?" | The Stage 4 iteration loop: run S5 → `pokerkit analyze` → `failure_report.txt` → patch one losing pattern → re-run. Repeat to plateau. | `references/heuristic-learning.md` |
| "can I use an LLM in decide()?" | Yes — that's Level 5 (paid, slower). Most strong bots are pure Python heuristics. Level 5 is on top of Stage 4, not part of the 4 stages. | `references/optimization-levels.md` Level 5 |
| "how do stages map to the 6-level ladder?" | Stage 1 ≈ Level 1, Stage 2 = Level 2, Stage 3 = Level 3, Stage 4 = Level 4 (HL loop). Level 5/6 are paid/expert additions on top of Stage 4. | `references/optimization-levels.md` |
| "what's the prize on Poker Arena?" | ~$50K pool; tournament not open yet. **Poker Eval has no prize** — it's training. | (Danny will confirm a number when public) |
| "what's Researcher Track?" | Separate invite-only track for agent-AI researchers; top Poker Arena finishers may be invited. | (no public doc yet) |

---

## What `learn` **does not** do

- Walk through all 6 levels — the level ladder is revealed *during*
  Stage 4, not in the intro
- Quote a specific Poker Arena prize-pool number beyond ~$50K
- Dump full DeepCFR / GTO / solver math — keep the explainer to
  anchors + intuition only
- Try to teach poker theory — the agent is here to write code, not
  run a poker school
- Start any code or file changes — `learn` is read-only until the
  user picks a path
