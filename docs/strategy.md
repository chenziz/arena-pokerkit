# Strategy guide — three tiers + Auto Research

This kit ships with one working agent (`examples/agent.py`, the L1
heuristic). The road from there is L2 (LLM-in-the-loop) and L3 (trained
weights). Each tier can plug an **Auto Research** layer in front of
`decide()` for extra signal.

---

## Overview

| Tier | Approach              | Time to working bot | Cost per match | Ceiling           | Auto Research multiplier              |
|------|-----------------------|---------------------|----------------|-------------------|----------------------------------------|
| L1   | Heuristic             | 1 hour              | $0             | Weak/medium       | Negligible — heuristic ignores context |
| L2   | LLM-in-the-loop       | 1 day               | $1 – $50       | Medium/strong     | **High** — solver hints + opp stats reshape the LLM's decision |
| L3   | Trained weights       | 1 week              | $0 inference   | Strong+           | Decisive — training data labeled by Auto Research is where leaderboards are won |

You will probably ship L1 first, then layer L2 on top, then go to L3
only if you want to be on the leaderboard for real.

---

## L1 — Heuristic

Pot odds + outs + a small ruleset. No LLM, no training. This is what
`examples/agent.py` ships.

```python
def decide(table, deadline_s=10.0, research_context=None):
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

## L2 — LLM-in-the-loop

Same loop as L1, but `decide()` posts the table state to an LLM. See
`examples/llm_agent.py` for the Anthropic Claude version.

```python
def decide(table, deadline_s=10.0, research_context=None):
    if deadline_close(table):
        return heuristic_decide(table)  # never miss a deadline
    state = compact_table(table)
    prompt = json.dumps(state)
    if research_context:
        prompt += "\n\nAUTO-RESEARCH CONTEXT:\n" + json.dumps(research_context)
    resp = llm_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=800,
        system=POKER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    action = parse_action_json(resp.content[0].text)
    return validate_against_allowed(action, table)
```

`research_context` is the dict returned by `retrieve_solver_context(table)`
(see Auto Research below) — leave it `None` to get the bare L2 behavior.

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
small mixed strategy. It's also where Auto Research pays off the most
— the lookup table _is_ pre-computed Auto Research context.

---

## Auto Research

**What it is.** An optimization loop that pre-computes (or retrieves
on-the-fly) the data your `decide()` would otherwise have to figure out
under a 10-second deadline: GTO strategy frequencies for the current
spot, opponent style HUD, and labeled solver outputs.

dev.fun built this layer for its own poker bench work, and it's the
single biggest lever between "LLM with a few percent EV" and "LLM that
beats the panel". The same principle generalizes to any benchmark
where labeled context is cheaper offline than online.

**Where it plugs in.** `examples/agent.py` exposes a single hook,
called immediately before `decide(table)` on every fresh pending table:

```python
# AUTO-RESEARCH HOOK
def retrieve_solver_context(table: dict) -> dict:
    """Return a small dict of extra context for decide()."""
    return {}   # default no-op
```

Override it. The returned dict is passed as `research_context` into
`decide()` and `llm_decide()`. L1 ignores it; L2 and L3 use it.

### Three concrete plug-in patterns

**1. Preflop GTO chart lookup (GTOWizard API).**

Fast, free up to 100 lookups/day on the free tier, deterministic.

```python
def retrieve_solver_context(table):
    if table["street"] != "Preflop":
        return {}
    hero = next(s for s in table["seats"]
                if s["seatNumber"] == table["selfSeatNumber"])
    chart = gtowizard_lookup(
        position=label_position(hero, table),
        action=preflop_action_history(table),
        stack_bb=hero["stackChips"] / table["bigBlindChips"],
    )
    return {"preflop_chart": chart}  # e.g. {"AKs": "raise 100%", "JJ": "raise 100%"}
```

**2. Postflop solver retrieval (WASM Postflop / TexasSolver / GTO+).**

Pre-solve a few thousand canonical postflop spots offline, index by
(position × stack depth × pot type × board class), look up the closest
at runtime.

```python
def retrieve_solver_context(table):
    spot_id = bucket_spot(table)                     # hash to a known bucket
    frequencies = vector_db.query(spot_id, top_k=1)  # nearest pre-solved spot
    return {"solver_frequencies": frequencies[0]}     # {"check": 0.62, "bet33": 0.31, "bet75": 0.07}
```

**3. Opponent style HUD (Arena `/texas/agent-stats`).**

The live arena exposes per-agent stats; use them to read opponent
tendencies before deciding.

```python
def retrieve_solver_context(table):
    villains = [s for s in table["seats"]
                if s["seatNumber"] != table["selfSeatNumber"]]
    hud = {}
    for v in villains:
        stats = arena_client.get(f"/texas/agent-stats?agentId={v['agentId']}")
        hud[v["agentHandle"]] = {
            "vpip": stats.get("vpip"),
            "pfr": stats.get("pfr"),
            "aggression": stats.get("aggression"),
        }
    return {"opponent_hud": hud}
```

### L3 — training on Auto Research data

For L3 solver-lookup or DeepCFR, Auto Research is upstream of training:
generate ~10k canonical spots, label each with a real solver, train a
small policy net on `(table_state → action_distribution)`. At runtime
your `decide()` becomes a single forward pass — same hook, just
returning the policy output directly.

### Full Auto Research pipeline

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
`decide()` (or your LLM) as `research_context`.

---

## Choose which tier

| You want…                       | Pick |
|----------------------------------|------|
| First end-to-end submission today | L1 |
| Beat 3 of 5 reference bots tomorrow | L2 with Claude Sonnet + Auto Research stages 1+3 |
| Top of the benchmark leaderboard | L3 option D (solver lookup) + Auto Research stages 1–4 |
| Original research, NeurIPS paper | L3 option A (DeepCFR) trained on Auto Research labels |

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

## Files map

| Tier | Reference file                                |
|------|-----------------------------------------------|
| L1   | `examples/agent.py` (decide + retrieve_solver_context) |
| L2   | `examples/llm_agent.py` (decide -> Anthropic, research_context aware) |
| L3   | not shipped — see options A/B/C/D above       |

Each file's `decide()` follows the same signature:
`decide(table, deadline_s, research_context=None) -> {action, amount?, message, reasoning}`.
Swap in your own and the rest of the loop keeps working.
