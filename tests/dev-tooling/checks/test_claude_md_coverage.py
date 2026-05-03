"""Outside-in test for `dev-tooling/checks/claude_md_coverage.py` — every directory has CLAUDE.md.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-claude-md-coverage` row), every
directory under `.claude-plugin/scripts/` (excluding the
`_vendor/` subtree), `<repo-root>/tests/` (excluding the
`fixtures/` subtree at any depth), and `<repo-root>/dev-
tooling/` MUST contain a `CLAUDE.md` file.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CLAUDE_MD_COVERAGE = _REPO_ROOT / "dev-tooling" / "checks" / "claude_md_coverage.py"


def test_claude_md_coverage_rejects_directory_missing_claude_md(*, tmp_path: Path) -> None:
    """A directory under scripts/ without CLAUDE.md fails the check.

    Fixture: `.claude-plugin/scripts/livespec/foo/` exists
    with a `.py` file inside but no `CLAUDE.md`. The check
    must walk the in-scope trees, detect the missing file,
    exit non-zero, and surface the offending directory path.
    """
    foo_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "foo"
    foo_dir.mkdir(parents=True)
    (foo_dir / "bar.py").write_text(
        "from __future__ import annotations\n__all__: list[str] = []\n",
        encoding="utf-8",
    )
    # Need to add CLAUDE.md to ancestor dirs so the check
    # surfaces only the leaf.
    for ancestor in (
        tmp_path / ".claude-plugin" / "scripts",
        tmp_path / ".claude-plugin" / "scripts" / "livespec",
    ):
        (ancestor / "CLAUDE.md").write_text("# stub\n", encoding="utf-8")

    result = subprocess.run(
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
    expected_path = ".claude-plugin/scripts/livespec/foo"
    assert expected_path in combined, (
        f"claude_md_coverage diagnostic does not surface offending dir `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_claude_md_coverage_accepts_fully_covered_tree(*, tmp_path: Path) -> None:
    """A tree where every in-scope directory has CLAUDE.md passes (exit 0)."""
    for d in (
        tmp_path / ".claude-plugin" / "scripts",
        tmp_path / ".claude-plugin" / "scripts" / "livespec",
        tmp_path / "tests",
        tmp_path / "dev-tooling",
    ):
        d.mkdir(parents=True)
        (d / "CLAUDE.md").write_text("# stub\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_CLAUDE_MD_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"claude_md_coverage should accept fully-covered tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_claude_md_coverage_exempts_vendor_subtree(*, tmp_path: Path) -> None:
    """Directories under `_vendor/` are exempt from the CLAUDE.md requirement.

    Pass-case: `.claude-plugin/scripts/_vendor/` and any
    descendant directory has no CLAUDE.md and the check
    still exits 0.
    """
    for d in (
        tmp_path / ".claude-plugin" / "scripts",
        tmp_path / ".claude-plugin" / "scripts" / "livespec",
    ):
        d.mkdir(parents=True)
        (d / "CLAUDE.md").write_text("# stub\n", encoding="utf-8")
    vendor_lib = tmp_path / ".claude-plugin" / "scripts" / "_vendor" / "returns"
    vendor_lib.mkdir(parents=True)
    (vendor_lib / "io.py").write_text("# vendored\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_CLAUDE_MD_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"claude_md_coverage should exempt _vendor/ with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_claude_md_coverage_exempts_fixtures_subtree(*, tmp_path: Path) -> None:
    """Directories under any `fixtures/` subtree are exempt.

    Pass-case: `tests/fixtures/some_dir/` has no CLAUDE.md;
    the check exits 0.
    """
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "CLAUDE.md").write_text("# stub\n", encoding="utf-8")
    fixture_dir = tests_dir / "fixtures" / "deep" / "nested"
    fixture_dir.mkdir(parents=True)

    result = subprocess.run(
        [sys.executable, str(_CLAUDE_MD_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"claude_md_coverage should exempt fixtures/ with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_claude_md_coverage_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes the check (exit 0)."""
    result = subprocess.run(
        [sys.executable, str(_CLAUDE_MD_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"claude_md_coverage should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_claude_md_coverage_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "claude_md_coverage_for_import_test", str(_CLAUDE_MD_COVERAGE),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
