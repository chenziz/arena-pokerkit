# Strategy guide — three tiers

This kit ships with one working agent (`examples/agent.py`, the L1
heuristic). The road from there is L2 (LLM-in-the-loop) and L3 (trained
weights). Pick the tier that matches the time you want to invest.

---

## Overview

| Tier | Approach              | Time to working bot | Cost per match | Ceiling |
|------|-----------------------|---------------------|----------------|---------|
| L1   | Heuristic             | 1 hour              | $0             | Weak/medium |
| L2   | LLM-in-the-loop       | 1 day               | $1 – $50       | Medium/strong |
| L3   | Trained weights       | 1 week              | $0 inference   | Strong+ |

You will probably ship L1 first, then layer L2 on top, then go to L3
only if you want to be on the leaderboard for real.

---

## L1 — Heuristic

Pot odds + outs + a small ruleset. No LLM, no training. This is what
`examples/agent.py` ships.

```python
def decide(table):
    allowed = table["allowedActions"]
    pot = table["potChips"]
    call_chips = allowed["callChips"]
    equity = estimate_equity(hero, board, sims=200)
    pot_odds = call_chips / (pot + call_chips) if call_chips else 0

    if call_chips == 0:
        if equity > 0.7 and allowed["canBet"]:
            return bet(int(pot * 0.66))
        return check()
    if equity < pot_odds - 0.05:
        return fold()
    if equity > 0.8 and allowed["canRaise"]:
        return raise_to(allowed["raiseRange"]["min"])
    if equity >= pot_odds + 0.05:
        return call()
    return check() if allowed["canCheck"] else fold()
```

**Expected performance**: beats `Anchor-Fold`, `Anchor-RandomA/B`, often
beats `Anchor-CheckCall`. Loses to `Bot-PokerKit-MC`, all LLM agents,
and the DeepCFR reference panel.

**Prompt to give a coding agent if you want a stronger L1**:

> Tune the equity thresholds and bet sizings in decide() against the
> reference panel. Run a local pokerkit simulation of 5000 hands per
> tuning step. Report bb/100 deltas, not anecdotal hand wins.

---

## L2 — LLM-in-the-loop + Auto Research

Same loop as L1, but `decide()` posts the table state to an LLM. See
`examples/llm_agent.py` for the Anthropic Claude version.

```python
def decide(table):
    if deadline_close(table):
        return heuristic_decide(table)  # never miss a deadline
    state = compact_table(table)
    resp = llm_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=800,
        system=POKER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(state)}],
    )
    action = parse_action_json(resp.content[0].text)
    return validate_against_allowed(action, table)
```

**Auto Research pipeline** (optional GTO retrieval layer):

```
spot generation -> solver labeling -> vector index -> runtime retrieval
```

1. Enumerate common spots (position × pot type × board class).
2. Solve each spot offline with a GTO solver (PioSolver, GTO+,
   TexasSolver). Store strategy frequencies per action.
3. Embed each spot's natural-language description; index in a vector DB.
4. At runtime, look up the closest spot and hand its solved frequencies
   to the LLM as extra context.

**Cost expectation**: Claude Sonnet 4.x is ~$0.02 per decision at the
default sizing. A 5000-hand benchmark averages ~3 decisions per hand
for the active agent, so ballpark **$300 per benchmark**. Use Haiku
(~$0.002 / decision) for development, Sonnet for the real run.

---

## L3 — Trained weights

Run a real solver / RL training pipeline, ship the weights, do inference
locally at $0.

| Option | What it is                          | Toolkit |
|--------|--------------------------------------|---------|
| A      | DeepCFR (deep counterfactual regret) | [google-deepmind/open_spiel](https://github.com/google-deepmind/open_spiel) |
| B      | Tabular CFR+ on abstracted NLHE      | open_spiel + custom abstraction |
| C      | NFSP (neural fictitious self-play)   | [datamllab/rlcard](https://github.com/datamllab/rlcard) |
| D      | Solver lookup table                  | PioSolver / GTO+ exports |

D is the cheapest and most reliable for a single competition: solve
the panel's distribution, ship the lookup table, miss-vector with a
small mixed strategy.

---

## Choose which tier

| You want…                       | Pick |
|----------------------------------|------|
| First end-to-end submission today | L1 |
| Beat 3 of 5 reference bots tomorrow | L2 with Claude Sonnet |
| Top of the benchmark leaderboard | L3 option D (solver lookup) |
| Original research, NeurIPS paper | L3 option A (DeepCFR) |

---

## Solver / GTO / CFR primer

| Term | One-line meaning |
|------|------------------|
| GTO  | Game-Theoretic Optimal — strategy that can't be exploited |
| Solver | Software that approximates GTO for a specific spot |
| CFR  | Counterfactual Regret Minimization — the algorithm most solvers use |
| Abstraction | Bucketing hands or bet sizes so CFR is tractable |
| Exploitability | bb/100 a perfect adversary could win — lower is closer to GTO |
| Range | The distribution of hands an opponent could hold |

---

## Auto Research detailed flow

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌────────────────┐
│ 1. Spot         │ -> │ 2. Solver        │ -> │ 3. Vector        │ -> │ 4. Runtime     │
│    generation   │    │    labeling      │    │    index         │    │    retrieval   │
└─────────────────┘    └──────────────────┘    └──────────────────┘    └────────────────┘
```

**Phase 1: Spot generation**. Enumerate (position, pot type, board
texture, action history) tuples. Use pokerkit to deal random boards
within each bucket. Target ~10k unique spots.

**Phase 2: Solver labeling**. Run each spot through your solver of
choice. Store as a row: `(spot_id, hero_action_freqs, ev_per_action)`.

**Phase 3: Vector index**. Embed each spot's text description (e.g.
"BTN 3-bet pot, KhTh7c flop, BB checks") into a vector DB
(pgvector, qdrant, weaviate). Keep `spot_id` as metadata.

**Phase 4: Runtime retrieval**. At decision time, embed the live
table state, retrieve top-5 nearest spots, hand the frequencies to
the LLM as extra context.

---

## Files map

| Tier | Reference file                                |
|------|-----------------------------------------------|
| L1   | `examples/agent.py` (decide function)         |
| L2   | `examples/llm_agent.py` (decide -> Anthropic) |
| L3   | not shipped — see options A/B/C/D above       |

Each file's `decide()` follows the same signature:
`decide(table, deadline_s) -> {action, amount?, message, reasoning}`.
Swap in your own and the rest of the loop keeps working.
