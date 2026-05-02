"""Outside-in test for `dev-tooling/checks/per_file_coverage.py` — v033 D2 per-file 100% gate.

Per the v033 D2 revision file at `brainstorming/approach-2-nlspec-
based/history/v033/proposed_changes/critique-fix-v032-revision.md`,
every covered `.py` file MUST hit 100% line and 100% branch
coverage independently — not just total. This script supersedes
the totalize-only `[tool.coverage.report].fail_under = 100`
threshold by reading the `.coverage` data file (post-combine, as
produced by `pytest --cov --cov-branch`) and failing the first
time any single covered file drops below 100% on either axis.

This module holds the OUTERMOST behavioral test for that gate.
Cycle 1 pins the missing-line-coverage rejection: a synthetic
`subject.py` with five executable statements has only two
recorded as covered in the synthetic `.coverage` data file; the
check must exit non-zero and surface the offending source file
plus enough information to locate the gap. Subsequent cycles
will pin missing-branch-coverage rejection, the no-data case,
and the all-files-100% accept case.

The fixture builds a synthetic project root at `tmp_path` with
exactly one source file plus a hand-authored `.coverage` data
file produced via `coverage.CoverageData.add_lines` (writing
parallel-mode-disabled, single-file form so `Coverage.load()`
finds it directly without needing a `combine()` step). The check
is invoked as a subprocess with `cwd=tmp_path` per the standard
dev-tooling/checks invocation contract.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from coverage import CoverageData

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_PER_FILE_COVERAGE = _REPO_ROOT / "dev-tooling" / "checks" / "per_file_coverage.py"


def test_per_file_coverage_rejects_file_below_100_line_coverage(*, tmp_path: Path) -> None:
    """A measured file with line coverage below 100% makes the check exit non-zero.

    The fixture writes a synthetic `subject.py` with five
    executable statements (the canonical livespec module preamble
    of `from __future__ import annotations` + `__all__` + three
    trivial assignment statements). A hand-authored `.coverage`
    data file records only two of those statements as covered
    (lines 1 and 3 — the import and the `__all__` declaration);
    the three assignment statements (lines 5, 6, 7) are missing.
    The check, invoked with `cwd=tmp_path`, must walk the
    `.coverage` data, detect `subject.py` at <100% line coverage,
    exit non-zero, and surface the offending file path so the
    developer can locate the gap.
    """
    src_file = tmp_path / "subject.py"
    src_file.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "x = 1\n"
        "y = 2\n"
        "z = 3\n",
        encoding="utf-8",
    )

    # Build the synthetic .coverage data file directly via the
    # CoverageData API. suffix=False writes a single
    # `.coverage` (no parallel-mode .coverage.<host>.<pid>.<random>
    # files) so per_file_coverage.py's Coverage.load() finds it
    # immediately without needing a combine() step. add_lines
    # records the set of executed line numbers per file.
    data = CoverageData(basename=str(tmp_path / ".coverage"), suffix=False)
    data.add_lines({str(src_file): [1, 3]})
    data.write()

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PER_FILE_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"per_file_coverage should reject subject.py at <100% line coverage with non-zero exit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_token = "subject.py"
    assert expected_token in combined, (
        f"per_file_coverage diagnostic does not surface offending file `{expected_token}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_per_file_coverage_rejects_when_no_coverage_data_file_exists(*, tmp_path: Path) -> None:
    """No `.coverage` file in cwd makes the check exit non-zero with a clear diagnostic.

    Per `per_file_coverage.py` lines 70-72: the helper inspects
    `cwd / ".coverage"` and, if missing, logs a "no coverage data
    found" error and returns 1. Drives that early-exit branch:
    fixture is a fresh tmp_path with no `.coverage` file. The
    check must exit non-zero and surface the missing path so the
    developer knows pytest --cov was skipped.
    """
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PER_FILE_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"per_file_coverage should reject missing .coverage file with non-zero exit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "no coverage data found" in combined, (
        f"per_file_coverage diagnostic does not surface 'no coverage data found' message; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_per_file_coverage_accepts_when_all_files_at_100_percent(*, tmp_path: Path) -> None:
    """A `.coverage` data file where every measured file is at 100% passes the check.

    Per `per_file_coverage.py` lines 86-98: when the per-file
    walk finds no offenders, the helper returns 0. Fixture: a
    synthetic `subject.py` with exactly two executable statements
    (the import line + the __all__ declaration); the `.coverage`
    data file records both as covered. The check exits 0.

    Drives the success-path return on line 98 (`return 0`) and the
    no-offenders branch (86->83 in coverage's report: when the
    loop body's `if line_pct < 100.0` arm is NOT taken, control
    returns to the loop header, and on loop exit the empty
    offenders list short-circuits the if-offenders block,
    returning 0).
    """
    src_file = tmp_path / "subject.py"
    src_file.write_text(
        "from __future__ import annotations\n__all__: list[str] = []\n",
        encoding="utf-8",
    )
    data = CoverageData(basename=str(tmp_path / ".coverage"), suffix=False)
    # Both executable statements covered: the future-import (line 1)
    # and the __all__ declaration (line 2). Coverage's `add_lines`
    # records executed lines per file.
    data.add_lines({str(src_file): [1, 2]})
    data.write()

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PER_FILE_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"per_file_coverage should accept all-100% data with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_per_file_coverage_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main().

    Closes branch 48->51 (`if str(_VENDOR_DIR) not in sys.path`
    already-present branch — pytest's pythonpath has pre-populated
    sys.path) and branch 101->exit (`if __name__ == "__main__":`
    else-arm — module imported, not run as a script).
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "per_file_coverage_for_import_test", str(_PER_FILE_COVERAGE),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"


def test_full_coverage_pct_constant_pins_v033_d2_threshold() -> None:
    """The `_FULL_COVERAGE_PCT` constant pins the v033 D2 100.0% threshold.

    Per v033 D2: every covered file MUST be at 100% line coverage.
    The threshold is policy-set with no carveout. This test pins
    the policy in code so a future loosening of the threshold
    requires explicit test failure + intentional bump.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "per_file_coverage_for_constant_test", str(_PER_FILE_COVERAGE),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._FULL_COVERAGE_PCT == 100.0  # noqa: SLF001
