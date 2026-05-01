"""Outside-in test for `dev-tooling/checks/file_lloc.py` — per-file LLOC ≤ 200 cap.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-complexity` row, which composes ruff
C901+PLR with file_lloc.py): every `.py` file under
`.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/
bin/**`, and `<repo-root>/dev-tooling/**` MUST have at most
200 logical lines of code (LLOC). LLOC excludes blank lines,
comment-only lines, and module/class/function docstrings —
it counts only executable statements.

Cycle 159 implements the per-file cap with a synthetic
fixture exceeding the threshold.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_FILE_LLOC = _REPO_ROOT / "dev-tooling" / "checks" / "file_lloc.py"


def test_file_lloc_rejects_file_exceeding_two_hundred_lines(*, tmp_path: Path) -> None:
    """A `.py` file with > 200 LLOC fails the check.

    Fixture: `.claude-plugin/scripts/livespec/big.py` contains
    `from __future__ import annotations`, the canonical
    `__all__` declaration, and 250 trivial assignment
    statements (`x_<n> = <n>`). The check must walk livespec/,
    count LLOC, detect the violation, exit non-zero, and
    surface the file path plus actual LLOC count.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "big.py"
    body_lines = "\n".join(f"x_{i} = {i}" for i in range(250))
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        f"{body_lines}\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_FILE_LLOC)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"file_lloc should reject 250-LLOC file; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/big.py"
    assert expected_path in combined, (
        f"file_lloc diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_file_lloc_accepts_small_file(*, tmp_path: Path) -> None:
    """A `.py` file with ≤ 200 LLOC passes the check (exit 0)."""
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "small.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_FILE_LLOC)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"file_lloc should accept small file with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_file_lloc_excludes_blank_lines_and_comments_and_docstrings(*, tmp_path: Path) -> None:
    """Blank lines, comments, and docstrings do not count toward LLOC.

    Fixture: a livespec module with 250 blank lines + 250
    comment lines + a long docstring + only 5 actual
    executable statements. LLOC ≤ 200, so the check must
    accept it.
    """
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

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_FILE_LLOC)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"file_lloc should accept padded file (LLOC ≤ 200) with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_file_lloc_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes the check (exit 0)."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_FILE_LLOC)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"file_lloc should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_file_lloc_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "file_lloc_for_import_test", str(_FILE_LLOC),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
