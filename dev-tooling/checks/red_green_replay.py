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
prospective Red moment. Cycle 179 wires SHA-256 computation:
when exactly one test file is staged, the red-mode-candidate
event carries a `test_file_checksum` field formatted as
`sha256:<64-char-hex>` (matching the v034 D2
`TDD-Red-Test-File-Checksum:` trailer format); when multiple
test files are staged, the hook rejects with a structured
`red-green-replay-multi-test-file` error and skips the
checksum (Red mode is per-file per the v034 D2 trailer
schema). Cycle 180 invokes pytest on the staged test file
in Red-mode-candidate flow: `[sys.executable, "-m", "pytest",
<abs-path>, "--tb=no", "-q"]`. A non-zero pytest returncode
confirms the Red moment and emits a structured
`red-green-replay-red-pytest-result` info event carrying
`pytest_returncode=<int>`. A zero pytest returncode means
the staged test passes — not a valid Red moment — and the
hook rejects with a structured
`red-green-replay-test-passed-at-red` error pointing the
developer at the constraint that Red mode requires the
staged test to fail. Cycle 181 wires Red trailer authoring:
once Red moment is confirmed, the hook computes
`TDD-Red-Output-Checksum` (SHA-256 of pytest output) and
`TDD-Red-Captured-At` (UTC ISO 8601 now), then invokes
`git interpret-trailers --in-place --trailer ... <msg_path>`
adding the full v034 D2 trailer set
(`TDD-Red-Test`, `TDD-Red-Failure-Reason`,
`TDD-Red-Test-File-Checksum`, `TDD-Red-Output-Checksum`,
`TDD-Red-Captured-At`) and **returns 0**, allowing the
commit to proceed. This is the first non-exempt path that
exits 0; the prior "always reject for non-exempt" contract
relaxes to "exit 0 iff Red moment fully verified". Future
cycles wire Green-mode detection from HEAD~0 trailer
inspection, Green-mode pytest invocation, Green trailer
authoring with `TDD-Green-Parent-Reflog:` reflog-
verification, and anti-cheat reflog inspection.

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

import datetime
import hashlib
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


def _head_has_red_trailers() -> bool:
    """Return True iff HEAD~0's commit message carries `TDD-Red-*` trailers.

    Used by the v034 D3 Green-mode dispatch: a feat:/fix: amend that
    stages impl files and whose parent (HEAD~0) carries the Red
    trailers from a prior Red commit is a Green-mode candidate. The
    `git log -1 --format=%B` invocation prints HEAD's full commit
    message; if no HEAD exists (fresh repo, not-a-git-repo), git
    exits non-zero with empty stdout and the substring check returns
    False.
    """
    result = subprocess.run(  # noqa: S603, S607
        ["git", "log", "-1", "--format=%B"],
        capture_output=True,
        text=True,
        check=False,
    )
    return "TDD-Red-Test-File-Checksum:" in result.stdout


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
        if len(tests_paths) > 1:
            log.error(
                "multi-test-file: Red mode is per-file (one test file per commit)",
                check_id="red-green-replay-multi-test-file",
                tests_paths=tests_paths,
                hint=(
                    "The v034 D2 trailer schema's "
                    "`TDD-Red-Test-File-Checksum:` is a singular field; "
                    "stage exactly one test file per Red commit."
                ),
            )
            return 1
        test_file_path = Path.cwd() / tests_paths[0]
        test_file_bytes = test_file_path.read_bytes()
        test_file_checksum = f"sha256:{hashlib.sha256(test_file_bytes).hexdigest()}"
        log.info(
            "red-mode-candidate: tests-only staged tree",
            check_id="red-green-replay-red-mode-candidate",
            tests_paths=tests_paths,
            test_file_checksum=test_file_checksum,
        )
        pytest_result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "pytest", str(test_file_path), "--tb=no", "-q"],
            capture_output=True,
            text=True,
            check=False,
        )
        if pytest_result.returncode == 0:
            log.error(
                "test-passed-at-red-moment: not a valid Red moment",
                check_id="red-green-replay-test-passed-at-red",
                tests_paths=tests_paths,
                test_file_checksum=test_file_checksum,
                pytest_returncode=pytest_result.returncode,
                hint=(
                    "Red mode requires the staged test to fail; "
                    "if the test already passes, this is not a Red moment "
                    "(the subsequent Green amend has nothing to verify)."
                ),
            )
            return 1
        log.info(
            "red-pytest-result: test failed at Red moment as required",
            check_id="red-green-replay-red-pytest-result",
            tests_paths=tests_paths,
            test_file_checksum=test_file_checksum,
            pytest_returncode=pytest_result.returncode,
        )
        pytest_output = pytest_result.stdout + pytest_result.stderr
        output_checksum = (
            f"sha256:{hashlib.sha256(pytest_output.encode('utf-8')).hexdigest()}"
        )
        captured_at = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ",
        )
        failure_reason = " ".join(pytest_output.split())[:200]
        trailer_args: list[str] = []
        for key, value in (
            ("TDD-Red-Test", tests_paths[0]),
            ("TDD-Red-Failure-Reason", failure_reason),
            ("TDD-Red-Test-File-Checksum", test_file_checksum),
            ("TDD-Red-Output-Checksum", output_checksum),
            ("TDD-Red-Captured-At", captured_at),
        ):
            trailer_args.extend(["--trailer", f"{key}: {value}"])
        subprocess.run(  # noqa: S603, S607
            ["git", "interpret-trailers", "--in-place", *trailer_args, str(msg_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        return 0
    if impl_paths and _head_has_red_trailers():
        log.info(
            "green-mode-candidate: HEAD~0 carries Red trailers + impl staged",
            check_id="red-green-replay-green-mode-candidate",
            impl_paths=impl_paths,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
