"""Branded CLI entrypoint for arena-pokerkit.

Verbs:
    pokerkit run     [--max-hands N] [--competition-id ID] [--dry-run]
                     [--dry-run-scenario S] [--agent path/to/decide.py]
    pokerkit replay  [--match ID | --latest | --list]
    pokerkit test                  # runs `pytest tests/`
    pokerkit version               # prints version + git commit

The `run` verb dispatches to `agent.main()` so behavior is identical
to `uv run examples/agent.py`. `replay` dispatches to `replay.main()`.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional


VERSION = "0.4.0"


def _ensure_path() -> None:
    """Make examples/ importable whether invoked as `python -m examples.cli`
    or via the installed `pokerkit` entry-point."""
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))


def _git_commit() -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(Path(__file__).resolve().parent.parent),
            stderr=subprocess.DEVNULL, timeout=2)
        return out.decode().strip() or None
    except Exception:
        return None


def _print_help() -> None:
    print("""usage: pokerkit <command> [options]

commands:
  run         play a benchmark (alias of `uv run examples/agent.py`)
  replay      render a self-contained HTML viewer for past matches
  test        run the pytest smoke suite
  version     print version + git commit

examples:
  pokerkit run --max-hands 50              # 50-hand preview (~3-5 min on S5)
  pokerkit run --dry-run --max-hands 1     # offline smoke
  pokerkit run --agent examples/skeletons/random_action.py
  pokerkit replay --latest                 # writes replay.html
  pokerkit replay --list                   # last 10 competitions
""")


def main(argv: Optional[list[str]] = None) -> int:
    _ensure_path()
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv or argv[0] in ("-h", "--help", "help"):
        _print_help()
        return 0
    cmd, rest = argv[0], argv[1:]

    if cmd == "version":
        commit = _git_commit()
        suffix = f" ({commit})" if commit else ""
        print(f"arena-pokerkit {VERSION}{suffix}")
        return 0

    if cmd == "run":
        import agent  # noqa: WPS433
        return agent.main(rest)

    if cmd == "replay":
        import replay  # noqa: WPS433
        return replay.main(rest)

    if cmd == "test":
        repo_root = Path(__file__).resolve().parent.parent
        return subprocess.call([sys.executable, "-m", "pytest",
                                str(repo_root / "tests"), "-q"])

    print(f"unknown command: {cmd}", file=sys.stderr)
    _print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
