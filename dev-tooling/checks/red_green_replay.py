"""red_green_replay — v034 D2-D3 replay-based TDD enforcement.

Per `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
§"Testing approach — Activation §v034 D2-D3 Red→Green replay
contract" and Plan §"Per-commit Red→Green replay discipline
(v034 D2-D3)", this hook is invoked as a `commit-msg` git
hook with the path to `.git/COMMIT_EDITMSG` as argv[1]. It
reads the commit subject; for `feat:` or `fix:` types it
runs the v034 D3 Red-or-Green-mode logic (test-file SHA-256
checksum, pytest invocation, trailer authoring); for other
Conventional Commit types (chore, docs, build, ci, style,
test, refactor, perf, revert) it exits 0 immediately.

Cycles 173-176 implement minimum-viable type discrimination
with the full v034 D3 exempt set ({chore, docs, build, ci,
style, test, refactor, perf, revert} — nine config/meta
types). Non-exempt subjects (feat:, fix:, and any unknown
type) exit 1. Cycle 177 adds the first staged-tree
inspection: when a non-exempt subject is presented and the
staged tree is empty (`git diff --cached --name-only`
returns no paths, including the not-a-git-repo failure
mode), the hook emits a structured diagnostic to stderr
identifying the empty-staging rejection reason (neither Red
nor Green mode is reachable without staged changes). Cycle
178 adds test/impl classification of the staged paths via
`_classify_staged`; when a feat:/fix: commit stages files
under `tests/` only (no entries under `livespec/`, `bin/`,
or `dev-tooling/`), the hook emits a structured
`red-mode-candidate` event identifying the commit as a
prospective Red moment. Future cycles wire SHA-256 checksum
computation, pytest invocation per mode, Green-mode
detection from HEAD~0 trailer inspection, trailer authoring
via `git interpret-trailers --in-place`, and anti-cheat
reflog inspection.

This file is authored under the v033 discipline still in
force (the replay hook itself is not yet gating; the v033
`red_output_in_commit.py` is still active). The v034 D5
replay-hook activation commit replaces the v033 hook with
this one and authors the initial
`phase-5-deferred-violations.toml`.

Output discipline: per spec lines 1738-1762, `print` (T20)
and `sys.stderr.write` (`check-no-write-direct`) are banned
in dev-tooling/**. Diagnostics flow through structlog (JSON
to stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import
time.
"""

from __future__ import annotations

import subprocess  # noqa: S404
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_EXEMPT_TYPE_PREFIXES = (
    "chore:",
    "docs:",
    "build:",
    "ci:",
    "style:",
    "test:",
    "refactor:",
    "perf:",
    "revert:",
)
_TESTS_PREFIX = "tests/"
_IMPL_PREFIXES = ("livespec/", "bin/", "dev-tooling/")


def _classify_staged(*, paths: list[str]) -> tuple[list[str], list[str]]:
    """Bucket staged paths into (tests, impl) — other paths are dropped.

    A path is a tests-bucket member iff it starts with `tests/`; an
    impl-bucket member iff it starts with `livespec/`, `bin/`, or
    `dev-tooling/`. Any other path (config, docs, top-level scripts,
    etc.) participates in neither bucket and so cannot trigger
    Red-mode or Green-mode dispatch.
    """
    tests_paths = [p for p in paths if p.startswith(_TESTS_PREFIX)]
    impl_paths = [p for p in paths if p.startswith(_IMPL_PREFIXES)]
    return tests_paths, impl_paths


def main() -> int:
    msg_path = Path(sys.argv[1])
    subject = msg_path.read_text(encoding="utf-8").split("\n", 1)[0]
    if subject.startswith(_EXEMPT_TYPE_PREFIXES):
        return 0
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("red_green_replay")
    staged_result = subprocess.run(  # noqa: S603, S607
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    staged_paths = [line for line in staged_result.stdout.splitlines() if line]
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
        log.info(
            "red-mode-candidate: tests-only staged tree",
            check_id="red-green-replay-red-mode-candidate",
            tests_paths=tests_paths,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
