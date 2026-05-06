"""Outside-in test for `dev-tooling/checks/file_lloc.py` — per-file LLOC two-tier policy.

Per `SPECIFICATION/constraints.md` §"File LLOC ceiling" (post-v005):
files at 201-250 LLOC pass with a structured warning (SOFT ceiling);
files above 250 LLOC fail (HARD ceiling). LLOC excludes blank lines,
comment-only lines, and module/class/function docstrings.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_FILE_LLOC = _REPO_ROOT / "dev-tooling" / "checks" / "file_lloc.py"


def _run_check(*, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_FILE_LLOC)],
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


def test_file_lloc_rejects_file_exceeding_hard_ceiling(*, tmp_path: Path) -> None:
    """A `.py` file with > 250 LLOC fails (exit 1)."""
    _write_py_with_lloc(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/big.py",
        n_statements=300,
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert ".claude-plugin/scripts/livespec/big.py" in combined
    assert "hard ceiling" in combined


def test_file_lloc_warns_but_passes_in_soft_band(*, tmp_path: Path) -> None:
    """A `.py` file with 201-250 LLOC passes with exit 0 but emits a warning."""
    _write_py_with_lloc(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/medium.py",
        n_statements=220,
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    assert "soft ceiling" in combined
    assert ".claude-plugin/scripts/livespec/medium.py" in combined


def test_file_lloc_accepts_file_at_or_below_soft_ceiling(*, tmp_path: Path) -> None:
    """A `.py` file with ≤ 200 LLOC passes silently (no warning, exit 0)."""
    _write_py_with_lloc(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/small.py",
        n_statements=50,
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    assert "soft ceiling" not in combined
    assert "hard ceiling" not in combined


def test_file_lloc_accepts_file_at_exactly_hard_ceiling(*, tmp_path: Path) -> None:
    """A `.py` file with exactly 250 LLOC passes (warning emitted, exit 0).

    250 is in the soft band (201-250); only > 250 is the hard fail.
    Constructing exactly 250 LLOC: 3 setup lines (future-import,
    blank line, __all__) plus 247 assignment statements. blank lines
    don't count, future-import and __all__ count as 2 LLOC, +247 = 249.
    Use 248 statements to land at exactly 250 LLOC.
    """
    _write_py_with_lloc(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/edge.py",
        n_statements=248,
    )
    result = _run_check(cwd=tmp_path)
    # Exit 0 either way (in soft band or below); just verify no hard fail.
    assert result.returncode == 0


def test_file_lloc_excludes_blank_lines_and_comments_and_docstrings(*, tmp_path: Path) -> None:
    """Blank lines, comments, and docstrings do not count toward LLOC."""
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
        "x = 0\n"
        "y = 1\n"
        "z = 2\n",
        encoding="utf-8",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_file_lloc_emits_both_tiers_in_one_run(*, tmp_path: Path) -> None:
    """When both soft and hard offenders exist, hard wins (exit 1) + both diagnostics emit."""
    _write_py_with_lloc(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/medium.py",
        n_statements=220,
    )
    _write_py_with_lloc(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/big.py",
        n_statements=300,
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "soft ceiling" in combined
    assert "hard ceiling" in combined


def test_file_lloc_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes (exit 0)."""
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_file_lloc_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "file_lloc_for_import_test",
        str(_FILE_LLOC),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)
