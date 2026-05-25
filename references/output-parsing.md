# Output parsing — `pokerkit selfplay` and `pokerkit run`

Quick reference for parsing the human-readable output of the kit's
CLI commands into structured values the agent needs (`baseline_local`,
`new_local`, Arena bb/100, win/loss counts, etc).

---

## `pokerkit selfplay` — final summary block

The CLI prints a fixed-format summary block at the end of every
selfplay run. The block is delimited by horizontal rules (`────────…`)
and the agent should grep within those bounds.

### Exact format (from `examples/selfplay.py:452-466`)

```
────────────────────────────────────────────────────────
  hands       : 200
  opponent    : tight x1
  wins/losses : 137/51  (push: 12)
  net chips   : +28
  bb/100      : +14.0
  elapsed     : 0.3s  (612 hands/s)
────────────────────────────────────────────────────────

  Reminder: this is vs SIMPLE local bots, NOT DeepCFR.
  Confirm improvements with `pokerkit run --max-hands 50` on Arena.
```

Note the **leading two-space indent** and the **colon + single-space
separator**. The `bb/100` value has a leading sign (`+` or `-`) and
one decimal place (`%+.1f` format).

### Regex to extract `baseline_local` / `new_local`

```python
import re
m = re.search(r"^\s*bb/100\s*:\s*([+-]?\d+(?:\.\d+)?)", output, re.M)
baseline_local = float(m.group(1)) if m else None
```

Or, in shell:

```bash
./pokerkit selfplay --hands 200 --seed 42 \
  | grep -E '^\s*bb/100\s*:' \
  | awk -F: '{ gsub(/^ +| +$/, "", $2); print $2 }'
# → +14.0
```

### Other fields the agent may need

| Field | Regex |
|---|---|
| `hands` | `^\s*hands\s*:\s*(\d+)` |
| `wins` / `losses` / `pushes` | `^\s*wins/losses\s*:\s*(\d+)/(\d+)\s*\(push:\s*(\d+)\)` |
| `net_chips` | `^\s*net chips\s*:\s*([+-]?\d+)` |
| `bb/100` | `^\s*bb/100\s*:\s*([+-]?\d+(?:\.\d+)?)` |
| `elapsed_s` | `^\s*elapsed\s*:\s*([\d.]+)s` |

If the regex doesn't match (e.g. the run errored before reaching the
summary), surface the run as failed and ask the user — never invent a
number.

---

## `pokerkit run` (Arena) — terminal state

Arena scores aren't parsed from stdout — they come from
`.arena-poker-state['iterations'][-1]['bb_per_100']` (a JSON file
written atomically by `arena_client.py`). Read that file at the end
of every Arena run.

```python
import json
state = json.load(open(".arena-poker-state"))
last = state["iterations"][-1]
arena_score = last["bb_per_100"]
arena_ci    = last.get("ci_bb_per_100")
arena_hands = last["hands"]
```

The `iterations` array is append-only (one entry per Arena terminal
state). Use the last two entries for the trajectory format in
SKILL.md Step 6.

---

## `pokerkit test` — pytest output

Standard pytest. Look for the final line `N passed in T.Ts` or
`M failed, N passed`. Treat any non-zero exit code as failure and
surface the failing test names to the user.

```bash
./pokerkit test 2>&1 | tail -3
# → ... 34 passed in 0.50s
```

---

## `pokerkit analyze --out failure_report.txt`

Writes a human-readable failure summary to the given path. Read the
file directly — don't parse stdout. Format described in
`references/heuristic-learning.md`.
