"""Outside-in test for `dev-tooling/checks/check_tools.py`.

Per `python-skill-script-style-requirements.md` line 2098 / Plan
line 1753 (Phase-4-exit must-pass list):

    Verify every pinned tool is installed at the pinned version
    — both mise-pinned binaries (`uv`, `just`, `lefthook`) and
    uv-managed Python deps from `pyproject.toml`
    `[dependency-groups.dev]` per v024.

The check is restored from pre-redo to satisfy Phase-4-exit
must-pass; it lives outside the v032 D1 11-cycle redo scope per
Plan lines 1675-1712. Paired test pins one canonical violation
pattern: a `.mise.toml` pinning a non-existent binary.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK_TOOLS = _REPO_ROOT / "dev-tooling" / "checks" / "check_tools.py"


def test_check_tools_rejects_missing_pinned_binary(*, tmp_path: Path) -> None:
    """A `.mise.toml` pinning a non-existent binary is rejected.

    Fixture: `.mise.toml` pins `nonexistent-binary-xyz = "1.2.3"`.
    The check must read the pin, attempt to invoke the binary,
    fail to find it on PATH, and exit non-zero with a diagnostic.
    """
    (tmp_path / ".mise.toml").write_text(
        '[tools]\nnonexistent-binary-xyz = "1.2.3"\n',
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_CHECK_TOOLS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"check_tools should reject missing pinned binary; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "nonexistent-binary-xyz" in combined, (
        f"check_tools diagnostic does not surface missing binary name; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_check_tools_accepts_empty_mise_and_pyproject(*, tmp_path: Path) -> None:
    """Empty `.mise.toml` + empty pyproject dev-deps is accepted.

    Fixture: `.mise.toml` with empty `[tools]` table; no
    `pyproject.toml`. The check has nothing to verify and exits 0.
    """
    (tmp_path / ".mise.toml").write_text(
        "[tools]\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_CHECK_TOOLS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"check_tools should accept empty mise + no pyproject; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
