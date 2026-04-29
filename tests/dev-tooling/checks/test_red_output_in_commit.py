"""Outside-in test for `dev-tooling/checks/red_output_in_commit.py`.

Per Plan lines 1708-1712 (v032 D4):

    walks `git log --grep` against the v032-redo commit range
    and rejects any feature/bugfix commit lacking a `## Red
    output` fenced block in its body; activates as a hard
    `just check` gate at Phase 5 exit, **informational
    pre-Phase-5-exit**.

Phase 4 = pre-Phase-5-exit, so the check operates in
**informational mode**: it logs warnings for non-conforming
commits but always exits 0. The Phase 5 exit-criterion flips
this to hard-fail mode.

Cycle 56 pins the canonical violation pattern AND the
informational-mode exit-code semantics. The fixture creates a
disposable git repo with one redo-format commit lacking
`## Red output`; the test asserts that the warning surfaces
in stderr but exit code is 0 (Phase 4 informational mode).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_RED_OUTPUT_IN_COMMIT = _REPO_ROOT / "dev-tooling" / "checks" / "red_output_in_commit.py"


def _git(*, cwd: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    # S603/S607: argv is a fixed list (literal git binary + repo-controlled
    # args); bare `git` is the canonical invocation per system PATH;
    # no untrusted shell input.
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
        env={"HOME": str(cwd), "GIT_CONFIG_GLOBAL": "/dev/null", "PATH": "/usr/bin:/bin"},
    )


def test_red_output_in_commit_warns_but_passes_in_phase4_informational_mode(
    *,
    tmp_path: Path,
) -> None:
    """A redo commit without `## Red output` warns but exits 0 (Phase 4).

    Fixture: a fresh git repo with one redo-format commit
    (`phase-5: cycle 1 — foo`) whose body has NO `## Red
    output` block. The check, run from this repo's cwd, must
    log a warning naming the offending sha but exit 0 because
    Phase 4 is informational mode.
    """
    _git(cwd=tmp_path, args=["init", "-q"])
    _git(cwd=tmp_path, args=["config", "user.email", "test@example.com"])
    _git(cwd=tmp_path, args=["config", "user.name", "Test"])
    (tmp_path / "file.txt").write_text("content\n", encoding="utf-8")
    _git(cwd=tmp_path, args=["add", "file.txt"])
    _git(
        cwd=tmp_path,
        args=[
            "commit",
            "-m",
            "phase-5: cycle 1 — foo",
            "-m",
            "no red block in this body.",
        ],
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_OUTPUT_IN_COMMIT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"red_output_in_commit Phase-4 informational mode must exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "Red output" in combined or "red_output" in combined, (
        f"red_output_in_commit must surface a warning about missing `## Red output`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_red_output_in_commit_silent_when_block_present(*, tmp_path: Path) -> None:
    """A redo commit WITH a `## Red output` block produces no warning.

    Fixture: a fresh git repo with one redo-format commit whose
    body carries a `## Red output` heading. The check must walk
    the log, find the block, and emit no diagnostic for that
    commit. Exit 0 (Phase 4 informational mode and conformant
    commit both produce 0).
    """
    _git(cwd=tmp_path, args=["init", "-q"])
    _git(cwd=tmp_path, args=["config", "user.email", "test@example.com"])
    _git(cwd=tmp_path, args=["config", "user.name", "Test"])
    (tmp_path / "file.txt").write_text("content\n", encoding="utf-8")
    _git(cwd=tmp_path, args=["add", "file.txt"])
    _git(
        cwd=tmp_path,
        args=[
            "commit",
            "-m",
            "phase-5: cycle 1 — foo",
            "-m",
            "Body prose.\n\n## Red output\n\n```\npytest red text\n```\n",
        ],
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_OUTPUT_IN_COMMIT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"red_output_in_commit must exit 0 for conformant commit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "missing `## Red output`" not in combined, (
        f"red_output_in_commit must not emit missing-block warning for conformant commit; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
