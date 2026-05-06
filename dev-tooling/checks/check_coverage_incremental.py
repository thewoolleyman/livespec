"""check_coverage_incremental — path-scoped per-file 100% gate.

A path-scoped fast-feedback variant of `check-coverage` for the
Red→Green authoring loop. Invocation contract:

    just check-coverage-incremental --paths <impl_path> [<impl_path>...]

For each `<impl_path>` (repo-root-relative): resolve its
mirror-paired test path, then run pytest on the combined test
set with full `--cov` (no path filter — path-scoped `--cov=<dir>`
filters break under subprocess instrumentation because coverage's
`source=` resolves the relative path against the subprocess's cwd
at measurement time). Apply the per-file 100% line+branch gate via
`coverage report --include=<impl_paths> --fail-under=100`.

Both subprocess invocations always run; the script returns the
maximum of their return codes. This is intentional — running
both surfaces both failures simultaneously, which is the
fast-feedback role of v039 D3, and avoids the otherwise-untestable
"pytest failed, did we run coverage?" branch profile that would
require synthetic failing-test fixtures to exercise.

Wall-clock target: under 10 seconds for a typical single-file
pair. NOT a replacement for `check-coverage` — the full-tree
run remains the load-bearing pre-commit gate. The fast-feedback
role is to surface coverage gaps proactively during authoring,
BEFORE the Green amend triggers a multi-minute aggregate retry
on a missed defensive branch.

CLI-flag exemption note: the dev-tooling/checks/ CLAUDE.md
guidance reads "no CLI flags; the script reads the repo at
cwd." This script REQUIRES a `--paths` flag to scope the
per-file gate; the precedent is `red_green_replay.py` which
takes `argv[1]` as the COMMIT_EDITMSG path. The exemption is
documented at the v039 D3 canonical-target-list row.

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import
time. Subprocess stdout/stderr (pytest's progress; coverage's
report) flows through to the developer's terminal unmodified
by NOT capturing it.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_SOURCE_TREES_TO_TESTS: dict[Path, Path] = {
    Path(".claude-plugin") / "scripts" / "livespec": Path("tests") / "livespec",
    Path(".claude-plugin") / "scripts" / "bin": Path("tests") / "bin",
    Path("dev-tooling") / "checks": Path("tests") / "dev-tooling" / "checks",
}
# Isolated coverage data file. The script spawns its own pytest as
# a subprocess; if we let pytest-cov default to `.coverage` the
# inner data file would clash with any outer pytest-cov session
# that ALSO writes to `.coverage` (e.g., the test that exercises
# this script's own happy path runs INSIDE pytest, which is
# already writing to `.coverage` for the outer session). The
# unique `_DATA_FILE` name keeps the inner data isolated; the
# `coverage report` step reads the same file via `--data-file`.
_DATA_FILE: str = ".coverage.check-coverage-incremental"
# pytest-cov's `.pth` startup hook activates inside ANY subprocess
# whose env has `COV_CORE_*` set — including the inner pytest the
# script spawns when invoked under an outer pytest-cov session
# (this script's own happy-path test). Activating the hook in the
# inner subprocess would attach the inner coverage measurement to
# the OUTER session's data file, defeating the `_DATA_FILE`
# isolation above. Strip those vars from the env handed to the
# inner pytest invocation so it starts a fresh measurement against
# `_DATA_FILE` only.
_COV_CORE_ENV_PREFIX: str = "COV_CORE_"


def _resolve_mirror_test_path(*, impl_path: Path) -> Path:
    """Map an impl path to its v033 D1 mirror-paired test path.

    Walks the three known impl trees in `_SOURCE_TREES_TO_TESTS`;
    on the first match, transforms `<rel_parent>/<name>.py` to
    `<tests_tree>/<rel_parent>/test_<name>.py`. Leading
    underscores in `<name>.py` are stripped before the `test_`
    prefix is added (matches `tests_mirror_pairing.py`'s
    `_expected_paired_test_path`). Raises `ValueError` if
    `impl_path` is not under any recognized impl tree —
    `check-coverage-incremental` only operates on the v033 D1
    mirror-paired trees.
    """
    for source_tree, tests_tree in _SOURCE_TREES_TO_TESTS.items():
        try:
            rel = impl_path.relative_to(source_tree)
        except ValueError:
            continue
        parent = rel.parent
        name = rel.name
        test_name = f"test_{name[1:]}" if name.startswith("_") else f"test_{name}"
        return tests_tree / parent / test_name
    msg = (
        f"impl path {impl_path} is not under any v033 D1 mirror-paired source tree "
        f"(.claude-plugin/scripts/livespec/, .claude-plugin/scripts/bin/, dev-tooling/checks/)"
    )
    raise ValueError(msg)


def _resolve_test_paths(
    *,
    impl_paths: list[Path],
    log: structlog.stdlib.BoundLogger,
) -> list[Path] | None:
    """Resolve impl paths to mirror-paired test paths, or None on resolution failure.

    For each impl_path: call `_resolve_mirror_test_path` and
    confirm the resulting test file exists on disk. On either
    failure (ValueError raised, or test file not present), log
    a structured diagnostic and return None. Otherwise return
    the list of resolved test paths in the same order as
    impl_paths. An empty input returns the empty list — a
    no-op behavior the loop-not-taken branch unit-test
    exercises directly (argparse's `nargs="+"` ensures `main`
    never invokes this with an empty list, so the unreachable
    branch is otherwise unmeasured).
    """
    test_paths: list[Path] = []
    for impl in impl_paths:
        try:
            test_path = _resolve_mirror_test_path(impl_path=impl)
        except ValueError as exc:
            log.exception(
                "could not resolve mirror-paired test for impl path",
                impl_path=str(impl),
                reason=str(exc),
            )
            return None
        if not test_path.is_file():
            log.error(
                "mirror-paired test does not exist",
                impl_path=str(impl),
                expected_test=str(test_path),
            )
            return None
        test_paths.append(test_path)
    return test_paths


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check-coverage-incremental",
        description=(
            "Path-scoped per-file 100% line+branch coverage gate (v039 D3). "
            "Resolves each --paths impl to its mirror-paired test, runs "
            "pytest with full --cov, then applies the per-file gate via "
            "coverage report --include=<impl> --fail-under=100."
        ),
    )
    _ = parser.add_argument(
        "--paths",
        nargs="+",
        required=True,
        type=Path,
        metavar="IMPL_PATH",
        help="impl path(s), repo-root-relative, to scope the per-file coverage gate to",
    )
    return parser


def _configure_logger() -> structlog.stdlib.BoundLogger:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    return structlog.get_logger("check_coverage_incremental")


def main() -> int:
    log = _configure_logger()
    args = _build_parser().parse_args()
    impl_paths: list[Path] = list(args.paths)
    test_paths = _resolve_test_paths(impl_paths=impl_paths, log=log)
    if test_paths is None:
        return 1

    inner_env = {k: v for k, v in os.environ.items() if not k.startswith(_COV_CORE_ENV_PREFIX)}
    inner_env["COVERAGE_FILE"] = _DATA_FILE

    # S603/S607: argv is a fixed list (literal binary names + repo-controlled
    # paths from --paths); no untrusted shell input.
    pytest_rc = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "--cov",
            "--cov-branch",
            "--cov-config=pyproject.toml",
            "--cov-report=",
            "--cov-fail-under=0",
            *(str(p) for p in test_paths),
        ],
        env=inner_env,
        check=False,
    ).returncode
    include = ",".join(str(p) for p in impl_paths)
    coverage_rc = subprocess.run(
        [
            "uv",
            "run",
            "coverage",
            "report",
            f"--data-file={_DATA_FILE}",
            f"--include={include}",
            "--fail-under=100",
        ],
        check=False,
    ).returncode
    return max(pytest_rc, coverage_rc)


if __name__ == "__main__":
    raise SystemExit(main())
