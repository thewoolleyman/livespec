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
