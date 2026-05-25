# First-run permissions — canonical heads-up

> **SOURCE OF TRUTH.** This file is the canonical permission heads-up
> the agent surfaces to the user BEFORE running the first command in
> a freshly-cloned repo. SKILL.md, paths/quick.md, paths/guided.md,
> and README.md quote from this file. If you're updating the wording,
> **edit it here only** — then propagate the new text to the other
> four places.

---

## Full heads-up (used in SKILL.md Step 0 verbatim)

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
       - Gemini CLI: trust this directory before running. Gemini
         refuses to run in an untrusted folder with the message
         "Gemini CLI is not running in a trusted directory". Pick one:
           * Set env:    export GEMINI_CLI_TRUST_WORKSPACE=true
           * Pass flag:  gemini --skip-trust ...
           * Interactive mode: gemini (no --prompt) → "Trust folder"
             — it asks once and remembers in
             ~/.gemini/trustedFolders.json
           * Ship config: cp .gemini/settings.json.example
             .gemini/settings.json (pre-trusts the workspace)
       - Cursor / Aider / Windsurf / Continue: approve when prompted
         on first run. Each tool has its own per-workspace dialog.

If your sandbox gives you options like "approve once / add permission
rule / hand off" — pick **approve** (one-time is fine; "add rule" is
also fine and more permanent). Don't pick "hand off" — that defeats
the whole point of me driving for you.
```

---

## Network usage (paste this when the user asks "what does it call?")

```
Network usage — the honest breakdown:

  - One-time: `uv sync` downloads Python packages from PyPI.
    ~30 seconds, ~50MB. Standard `pip`-style install. Happens during
    Phase 1 (Setup) only.

  - Per Arena run (Phase 4 / Stage 3+ only, you explicitly approve):
    API calls to b-arena.dev.fun for the benchmark match.

  - Everything else (selfplay, tests, code edits, replay):
    pure local Python. No network.
```

---

## Read-only sandbox fallback (Codex strict-mode safe)

Some sandboxes (notably Codex CLI in strict read-only mode) can't
write a `.env` file. The kit works without one — just export the env
vars directly:

```bash
# Setup (writeable sandbox — default):
cp .env.example .env

# Setup (read-only sandbox — Codex strict mode):
# Use environment variables directly, skip .env file:
export ARENA_API_BASE=https://b-arena.dev.fun/api/arena
export ARENA_COMPETITION_ID=cmpdk0pt00eawvcaf1es8plw2
```

If the agent detects `cp` is blocked (or the `.env` write fails with
EROFS / EACCES), fall back to the `export` form silently and tell the
user once: *"Your sandbox is read-only; I'm using env vars instead of
a .env file. Same effect."*

---

## Wrapper-less command form

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

---

## Short 5-line version (for paths/quick.md and paths/guided.md)

```
💡 First-run permission heads-up — your sandbox may prompt on the
first few commands. That's expected. The kit only runs local Python;
the one-time exception is `uv sync` (PyPI install, ~30s) and Arena
evaluation (you approve before I start). Pre-grant for Claude Code:
copy .claude/settings.json.example to .claude/settings.json. For
Codex: copy .codex/config.toml.example to ~/.codex/config.toml OR
approve the workspace once when prompted. For Gemini CLI: copy
.gemini/settings.json.example to .gemini/settings.json (or export
GEMINI_CLI_TRUST_WORKSPACE=true) — Gemini refuses to run in an
untrusted directory. Full text: references/permissions.md.
```

---

## 3-line teaser (for README.md)

```
First-run sandbox prompts are expected — the kit only runs local
Python plus `uv sync` (PyPI) and Arena API (you approve). Pre-grant
options: see references/permissions.md.
```
