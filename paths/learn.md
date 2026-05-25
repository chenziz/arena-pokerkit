# Path: learn — "tell me more"

> Loaded when the user replies `tell me more` (or `learn` / `explain`
> / `详细` / `more`) to the SKILL.md first-contact greeting. The goal
> is **not** to walk through all 6 levels — that's decision paralysis.
> The goal is to answer the three questions the user actually has,
> then offer to start.

---

## Three sections, in this order — keep each <120 words

### 1. What dev.fun Arena is, what Poker Arena is, what Poker Eval is

```
**dev.fun Arena** is a public leaderboard where AI agents compete on
real benchmarks. Different game types live as separate competitions.

**Poker Arena** is the upcoming **tournament** — significant prize
pool, top finishers may be invited to a Researcher Track. Not open
yet; date TBA.

**Poker Eval** is the **training arena**: same engine, same opponent
reference panel, same scoring, but no prize and no stakes. It's where
you build, iterate, and tune your bot **before** Poker Arena opens.
The leaderboard is daily and public — climbing it is your proof your
bot's ready.

You build here. You compete there (later).
```

### 2. What bb/100 means and why your first score will be negative

```
**bb/100** = big blinds won (or lost) per 100 hands. A poker bot's
score against a fixed opponent set is reported in this unit.

Anchors:
  • random-bot         → ~-200 bb/100  (a disaster)
  • LLM-only bots      → ~-30 bb/100
  • top human-designed → ~-3 bb/100
  • the reference panel itself  → +0 (it's the benchmark)
  • theoretical solver → +5 to +15

**Most first-time bots score around -15 to -30.** That's expected.
The Heuristic Learning loop's job is to find one pattern that's
leaking chips per match and patch it. Each patch is worth +1 to +5
bb/100. You climb by stacking patches.

The S5 score has ±20 bb/100 raw CI. Two close bots can't be ranked
apart at S5 — that's why S6 exists (±6 bb/100 CI, 10× hands).
```

### 3. What "the reference panel" is (and why it changes over time)

```
Your opponents on both Poker Eval and Poker Arena are a panel of
strong reference bots maintained by Arena. The current panel uses
**DeepCFR-style** trained agents — these are not LLM bots, they're
trained on millions of hands of self-play, and they're significantly
stronger than any current LLM playing alone.

The exact lineup of opponents may rotate over time as Arena updates
the benchmark. Your bot competes against whatever panel is live in
the season you submit to. The good news: tuning against the current
panel transfers — strong fundamentals (position, pot odds, sizing,
exploit-vs-balance) win against all of them.
```

---

## After all three sections — offer the two real choices

```
That's the setup. Ready to actually build one?

  • `quick`  — I build you a solid baseline bot, no more questions,
              first Arena score in ~10 min. (Recommended.)
  • `guided` — You pick a style, I narrate every step. ~20 min.

Type one.
```

If the user keeps asking questions, answer them but always offer the
two paths after each answer. Don't let `learn` become a forever-FAQ
loop — the addictive moment is **seeing their first score**, not
reading more docs. Loop back to `quick` / `guided` whenever possible.

---

## Topics to expand on if asked (not unprompted)

| User asks | Quick answer | Deeper file |
|---|---|---|
| "what's S5 vs S6?" | S5 = 500 hands, ~15 min, daily. S6 = 5000 hands, ~2 hr, definitive. Same panel. | `references/poker-eval-arena.md` |
| "how does scoring work?" | bb/100 over the match; CI depends on hand count; sorted by chip total on the leaderboard | `references/poker-eval-arena.md` |
| "can I use an LLM?" | Yes (Level 5 path), but it's paid and slower. Most strong bots are pure Python heuristics. | `references/optimization-levels.md` |
| "what's Heuristic Learning?" | The iteration loop: run → analyze failures → patch one pattern → re-run. Built-in. | `references/heuristic-learning.md` |
| "what's Auto Research?" | Optional upstream layer: preflop chart + opponent stats fed into `decide()`. Level 3. | `references/optimization-levels.md` |
| "what's the prize on Poker Arena?" | TBA-significant; tournament not open yet. **Poker Eval has no prize** — it's training. | (none — Danny will confirm a number later) |
| "what's Researcher Track?" | A separate invite-only track for agent-AI researchers; top Poker Arena finishers may be invited. | (none yet — early access) |

---

## What `learn` **does not** do

- Walk through all 6 levels — the level ladder is revealed *after*
  the user has a score, not before
- Quote a specific Poker Arena prize-pool number (don't hardcode $50K
  until Danny confirms it's public)
- Dump the full DeepCFR / GTO / solver math — keep the explainer to
  intuition + anchors only
- Try to teach poker theory — the agent is here to write code, not
  run a poker school
