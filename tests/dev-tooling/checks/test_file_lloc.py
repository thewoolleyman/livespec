"""Outside-in test for `dev-tooling/checks/file_lloc.py` — Phase 4 file-LLOC enforcement.

Per `python-skill-script-style-requirements.md` §"Complexity
thresholds" (lines 1689-1711) and Plan Phase 4 line 1677, the
`file_lloc.py` check enforces "file ≤ 200 logical lines" across
the repo. A "logical line" follows Python's canonical
`tokenize.NEWLINE` definition: every NEWLINE token terminates one
logical line; blank lines and comment-only physical lines emit
`NL` not `NEWLINE` and are NOT counted. This is the unambiguous
language-level definition that the spec's "logical lines" phrase
points at; ruff's PLR0915 uses an AST-level statement count for
the in-function ceiling, but the file-level ceiling defers to the
line-level tokenizer view because docstring expression statements
+ multi-physical-line statements both behave the same way under
that lens (one statement = one logical line, period).

This module holds the OUTERMOST behavioral test for that ceiling.
Each cycle advances one specific failure mode: cycle 31 pins the
violation case (a file with 201 logical lines is rejected with
exit non-zero and its path surfaced in the diagnostic).
Subsequent cycles pin the pass case + the boundary at exactly 200
LLOC.

The check is invoked as a subprocess with the repo root at
`cwd=tmp_path`, matching the contract documented in
`dev-tooling/checks/CLAUDE.md` ("invokable as `python3
dev-tooling/checks/<name>.py`; no CLI flags; reads the repo at
cwd"). Subprocess invocation also exercises the script's
`__main__` plumbing end-to-end exactly as the `justfile` invokes
it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_FILE_LLOC = _REPO_ROOT / "dev-tooling" / "checks" / "file_lloc.py"


def test_file_lloc_rejects_python_file_with_201_logical_lines(*, tmp_path: Path) -> None:
    """A Python file with 201 logical lines makes the check exit non-zero and name the path.

    The fixture builds a synthetic project root mirroring the
    real layout: `.claude-plugin/scripts/livespec/oversized.py`
    is a Python file whose body is 201 trivial assignment
    statements (each `x = 0\\n` — one logical line per physical
    line). The check, invoked with `cwd=tmp_path`, must walk the
    in-scope trees (`.claude-plugin/scripts/livespec/**`,
    `.claude-plugin/scripts/bin/**`, `<repo-root>/dev-tooling/**`
    per `python-skill-script-style-requirements.md`), detect the
    file as exceeding the 200-LLOC ceiling, exit non-zero, and
    surface the offending path
    (`.claude-plugin/scripts/livespec/oversized.py`) in its
    diagnostic output so the developer can locate the file.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    oversized = package_dir / "oversized.py"
    body_lines = ["x = 0\n"] * 201
    oversized.write_text("".join(body_lines), encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_FILE_LLOC)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"file_lloc should reject 201-LLOC file with non-zero exit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/oversized.py"
    assert expected_path in combined, (
        f"file_lloc diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_file_lloc_accepts_python_file_with_200_logical_lines(*, tmp_path: Path) -> None:
    """A Python file with exactly 200 logical lines passes the check (boundary).

    The fixture builds a synthetic project root mirroring the
    real layout: `.claude-plugin/scripts/livespec/in_spec.py`
    contains exactly 200 trivial assignment statements (each
    `x = 0\\n` — one logical line per physical line). 200 is the
    inclusive ceiling per `python-skill-script-style-
    requirements.md` line 1696 ("File ≤ 200 logical lines"); the
    check must accept files at the boundary, exit 0, and emit
    nothing on stdout (structlog goes to stderr; stderr being
    empty here would over-specify and risk fragility against
    future structlog output, so this assertion targets exit code
    only — the no-emit guarantee is implied by exit 0).
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    in_spec = package_dir / "in_spec.py"
    body_lines = ["x = 0\n"] * 200
    in_spec.write_text("".join(body_lines), encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_FILE_LLOC)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"file_lloc should accept 200-LLOC file with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_file_lloc_rejects_oversized_file_under_tests_tree(*, tmp_path: Path) -> None:
    """A 201-LLOC file under `tests/` is also rejected — tests share the style scope.

    Per `python-skill-script-style-requirements.md` line 67-69
    ("Tests under `<repo-root>/tests/` MUST comply unless a test
    explicitly exercises a non-conforming input ..."), the
    `tests/` tree is in-scope for the same style rules as the
    shipped code. `file_lloc.py` MUST therefore walk `tests/`
    in addition to the three shipped trees and surface offenders
    located there.

    Fixture: a 201-LLOC file at `tests/livespec/test_oversized.py`
    (mirroring the package one-to-one per Plan line 1460-1462).
    The check must exit non-zero and surface the offending path
    so the developer can locate the file. Without this case, a
    test file silently exceeding 200 logical lines would slip
    through `just check-complexity`.
    """
    tests_dir = tmp_path / "tests" / "livespec"
    tests_dir.mkdir(parents=True)
    oversized = tests_dir / "test_oversized.py"
    body_lines = ["x = 0\n"] * 201
    oversized.write_text("".join(body_lines), encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_FILE_LLOC)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"file_lloc should reject 201-LLOC file under tests/ with non-zero exit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = "tests/livespec/test_oversized.py"
    assert expected_path in combined, (
        f"file_lloc diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
