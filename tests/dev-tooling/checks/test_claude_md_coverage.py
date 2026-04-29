"""Outside-in test for `dev-tooling/checks/claude_md_coverage.py`.

Per `python-skill-script-style-requirements.md` §"Agent-oriented
documentation: CLAUDE.md coverage" (lines 2142-2176) and the
canonical-target table line 2094:

    Every directory under `scripts/` (excluding `_vendor/`),
    `tests/` (excluding `fixtures/` subtrees at any depth), and
    `dev-tooling/` contains a `CLAUDE.md`.

Cycle 51 pins the canonical violation: a directory under
`.claude-plugin/scripts/` (excluding `_vendor/`) with no
`CLAUDE.md` is rejected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CLAUDE_MD_COVERAGE = _REPO_ROOT / "dev-tooling" / "checks" / "claude_md_coverage.py"


def test_claude_md_coverage_rejects_scripts_dir_missing_claude_md(*, tmp_path: Path) -> None:
    """A `scripts/` subdirectory without CLAUDE.md is rejected.

    Fixture: `.claude-plugin/scripts/livespec/orphan_dir/` exists
    (with one Python file) but has NO `CLAUDE.md`. The check
    must walk the scripts tree, observe the missing file, exit
    non-zero, and surface the offending directory.
    """
    orphan_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "orphan_dir"
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "code.py").write_text(
        'from __future__ import annotations\n\n__all__: list[str] = []\n',
        encoding="utf-8",
    )
    # Note: NO CLAUDE.md inside orphan_dir/. That's the violation.
    # Also create CLAUDE.md in parent dirs so the check fails ONLY
    # because of orphan_dir, not the parents.
    for parent_rel in (
        Path(".claude-plugin") / "scripts",
        Path(".claude-plugin") / "scripts" / "livespec",
    ):
        (tmp_path / parent_rel / "CLAUDE.md").write_text("# placeholder\n", encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_CLAUDE_MD_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"claude_md_coverage should reject directory without CLAUDE.md; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/orphan_dir"
    assert expected_path in combined, (
        f"claude_md_coverage diagnostic does not surface offending directory "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_claude_md_coverage_accepts_directory_with_claude_md(*, tmp_path: Path) -> None:
    """A `scripts/` subdirectory containing CLAUDE.md is accepted.

    Fixture: `.claude-plugin/scripts/livespec/` plus one
    subdirectory, all carrying CLAUDE.md. The check walks and
    exits 0.
    """
    livespec_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    livespec_dir.mkdir(parents=True)
    sub_dir = livespec_dir / "sub"
    sub_dir.mkdir()
    for d in (livespec_dir.parent, livespec_dir, sub_dir):
        (d / "CLAUDE.md").write_text("# placeholder\n", encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_CLAUDE_MD_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"claude_md_coverage should accept directory tree with CLAUDE.md everywhere; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
