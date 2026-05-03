"""Outside-in test for `dev-tooling/checks/no_lloc_soft_warnings.py` — release-gate for 201-250 LLOC soft-band files.

Per `SPECIFICATION/constraints.md` §"File LLOC ceiling" (post-v008):
the release-gate rejects any first-party `.py` file in the 201-250
LLOC soft band. Files at or below 200 LLOC pass; files above 250
LLOC are NOT this check's concern (the per-commit `file_lloc.py`
hard-fails them).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NO_LLOC_SOFT_WARNINGS = _REPO_ROOT / "dev-tooling" / "checks" / "no_lloc_soft_warnings.py"


def _run_check(*, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_NO_LLOC_SOFT_WARNINGS)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def _write_py_with_lloc(*, tmp_path: Path, rel_path: str, n_statements: int) -> None:
    full = tmp_path / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    body_lines = "\n".join(f"x_{i} = {i}" for i in range(n_statements))
    full.write_text(
        "from __future__ import annotations\n\n__all__: list[str] = []\n\n" + body_lines + "\n",
        encoding="utf-8",
    )


def test_no_lloc_soft_warnings_rejects_file_in_soft_band(*, tmp_path: Path) -> None:
    """A `.py` file with 201-250 LLOC fails the release-gate (exit 1)."""
    _write_py_with_lloc(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/medium.py",
        n_statements=220,
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "soft band" in combined
    assert ".claude-plugin/scripts/livespec/medium.py" in combined


def test_no_lloc_soft_warnings_accepts_file_at_or_below_soft_ceiling(*, tmp_path: Path) -> None:
    """A `.py` file with ≤ 200 LLOC passes the release-gate (exit 0)."""
    _write_py_with_lloc(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/small.py",
        n_statements=50,
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_no_lloc_soft_warnings_ignores_file_above_hard_ceiling(*, tmp_path: Path) -> None:
    """A `.py` file with > 250 LLOC is NOT this check's concern (per-commit file_lloc.py handles it)."""
    _write_py_with_lloc(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/big.py",
        n_statements=300,
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_no_lloc_soft_warnings_emits_each_offender(*, tmp_path: Path) -> None:
    """Multiple soft-band files produce one diagnostic each; check still exits non-zero."""
    _write_py_with_lloc(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/medium_a.py",
        n_statements=210,
    )
    _write_py_with_lloc(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/medium_b.py",
        n_statements=240,
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "medium_a.py" in combined
    assert "medium_b.py" in combined


def test_no_lloc_soft_warnings_excludes_blank_lines_and_comments_and_docstrings(
    *, tmp_path: Path
) -> None:
    """LLOC counting matches file_lloc.py: blank/comment/docstring lines don't count."""
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "padded.py"
    blanks = "\n" * 250
    comments = "\n".join(f"# comment {i}" for i in range(250))
    docstring_lines = "\n".join(f"docstring line {i}" for i in range(250))
    source.write_text(
        f'"""\n{docstring_lines}\n"""\n'
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        f"{blanks}\n"
        f"{comments}\n"
        "\n"
        "x = 0\ny = 1\nz = 2\n",
        encoding="utf-8",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_no_lloc_soft_warnings_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes (exit 0)."""
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_no_lloc_soft_warnings_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "no_lloc_soft_warnings_for_import_test",
        str(_NO_LLOC_SOFT_WARNINGS),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)
