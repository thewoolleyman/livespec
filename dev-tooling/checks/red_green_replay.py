"""red_green_replay — v034 D2-D3 replay-based TDD enforcement.

Per PROPOSAL.md §"Testing approach — Activation §v034 D2-D3
Red→Green replay contract" and Plan §"Per-commit Red→Green
replay discipline (v034 D2-D3)", this hook is invoked as a
`commit-msg` git hook with the path to `.git/COMMIT_EDITMSG`
as argv[1]. It reads the commit subject; for `feat:`/`fix:`
types it dispatches to the Red-mode or Green-mode handler in
`_red_green_replay_modes` (test-file SHA-256 checksum, pytest
invocation, trailer authoring); for the nine exempt
Conventional Commit types (chore, docs, build, ci, style,
test, refactor, perf, revert) it exits 0 immediately.

Cycle-by-cycle authoring history (cycles 173-183) is preserved
in git log; not load-bearing for current behavior. Cycle 4c
(2026-05-02) extracted the Red-mode and Green-mode handlers
into the sibling `_red_green_replay_modes.py` so this file
stays under the 200 LLOC ceiling.

Output discipline: per spec lines 1738-1762, `print` (T20)
and `sys.stderr.write` (`check-no-write-direct`) are banned
in dev-tooling/**. Diagnostics flow through structlog (JSON
to stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import
time.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))
# Make the script's own directory importable when this module is
# loaded via `importlib.util.spec_from_file_location` (test path)
# in addition to the natural `python3 dev-tooling/checks/red_green_replay.py`
# subprocess invocation (which adds the dir automatically).
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

# Importing from sibling `_*` module for the heavy mode handlers
# (cycle 4c LLOC reduction). The leading underscore in the module
# name marks it as a private helper rather than a check entry
# point.
from _red_green_replay_modes import (  # noqa: E402  — sibling private import
    _handle_green_mode,
    _handle_red_mode,
    _head_has_red_trailers,
)

__all__: list[str] = []


_EXEMPT_TYPE_RE = re.compile(
    r"^(chore|docs|build|ci|style|test|refactor|perf|revert)"
    r"(\([^)]+\))?!?:",
)
_TESTS_PREFIX = "tests/"
# Impl-tree prefixes (cycle 2.8 fix). The repo's actual layout
# is `.claude-plugin/scripts/livespec/...` and
# `.claude-plugin/scripts/bin/...`, NOT bare `livespec/` /
# `bin/`. Cycle 2.8 added the production prefixes alongside
# the legacy bare prefixes (kept for paired-test fixture
# compatibility — tmp_path tests synthesize paths like
# `livespec/foo.py`). Production has no top-level `livespec/`
# or `bin/` dirs, so the legacy prefixes contribute zero
# false positives in real repos.
_IMPL_PREFIXES = (
    ".claude-plugin/scripts/livespec/",
    ".claude-plugin/scripts/bin/",
    "livespec/",
    "bin/",
    "dev-tooling/",
)


def _classify_staged(*, paths: list[str]) -> tuple[list[str], list[str]]:
    """Bucket staged paths into (tests, impl) — other paths are dropped.

    A path is a tests-bucket member iff it starts with `tests/`;
    an impl-bucket member iff it starts with one of `_IMPL_PREFIXES`.
    Any other path (config, docs, top-level scripts, etc.)
    participates in neither bucket and so cannot trigger
    Red-mode or Green-mode dispatch.
    """
    tests_paths = [p for p in paths if p.startswith(_TESTS_PREFIX)]
    impl_paths = [p for p in paths if p.startswith(_IMPL_PREFIXES)]
    return tests_paths, impl_paths


def _configure_logger() -> structlog.stdlib.BoundLogger:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    return structlog.get_logger("red_green_replay")


def _staged_files_list() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in result.stdout.splitlines() if line]


def main() -> int:
    msg_path = Path(sys.argv[1])
    subject = msg_path.read_text(encoding="utf-8").split("\n", 1)[0]
    if _EXEMPT_TYPE_RE.match(subject):
        return 0
    log = _configure_logger()
    staged_paths = _staged_files_list()
    if not staged_paths:
        log.error(
            "no staged files; cannot enter Red or Green mode",
            check_id="red-green-replay-empty-staged",
            hint=(
                "Red mode requires staged tests + no impl; "
                "Green mode requires staged impl + HEAD~0 Red trailers."
            ),
        )
        return 1
    tests_paths, impl_paths = _classify_staged(paths=staged_paths)
    if tests_paths and not impl_paths:
        return _handle_red_mode(msg_path=msg_path, log=log, tests_paths=tests_paths)
    if impl_paths and _head_has_red_trailers():
        return _handle_green_mode(msg_path=msg_path, log=log, impl_paths=impl_paths)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
