"""Outside-in test for `dev-tooling/checks/heading_coverage.py` — every spec-tree-root NLSpec heading has a coverage entry.

Per `SPECIFICATION/constraints.md` §"Heading taxonomy" (post-v004),
the registry maps `(spec_root, spec_file, heading)` triples and the
check walks ONLY the five template-declared NLSpec files at each
spec-tree root (`spec.md`, `contracts.md`, `constraints.md`,
`non-functional-requirements.md`, `scenarios.md`) — never
recursing into `proposed_changes/`,
`history/`, `templates/<name>/history/`, or any other subdirectory;
never including the skill-owned `README.md` at the tree root.

Failure modes covered: uncovered heading, orphan registry entry,
missing `reason` on a TODO entry. Skip rule covered: `Scenario:`
prefix.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_HEADING_COVERAGE = _REPO_ROOT / "dev-tooling" / "checks" / "heading_coverage.py"


def _run_check(*, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_HEADING_COVERAGE)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def _write_registry(*, tmp_path: Path, entries: list[dict[str, object]]) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "heading-coverage.json").write_text(
        json.dumps(entries) if entries else "[]",
        encoding="utf-8",
    )


def _write_spec_file(*, tmp_path: Path, rel_path: str, body: str) -> None:
    full = tmp_path / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(body, encoding="utf-8")


def test_heading_coverage_rejects_uncovered_heading(*, tmp_path: Path) -> None:
    """A spec heading without a matching registry entry fails."""
    _write_spec_file(
        tmp_path=tmp_path, rel_path="SPECIFICATION/spec.md", body="# Title\n\n## Foo\n\nbody\n"
    )
    _write_registry(tmp_path=tmp_path, entries=[])
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "spec heading missing coverage entry" in combined
    assert "Foo" in combined


def test_heading_coverage_accepts_covered_heading(*, tmp_path: Path) -> None:
    """A spec heading with a matching (spec_root, spec_file, heading) triple passes."""
    _write_spec_file(
        tmp_path=tmp_path, rel_path="SPECIFICATION/spec.md", body="# Title\n\n## Foo\n\nbody\n"
    )
    _write_registry(
        tmp_path=tmp_path,
        entries=[
            {
                "heading": "## Foo",
                "spec_root": "SPECIFICATION",
                "spec_file": "spec.md",
                "test": "tests/foo.py::test_foo",
            }
        ],
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_heading_coverage_rejects_orphan_registry_entry(*, tmp_path: Path) -> None:
    """A registry entry whose triple does not match any spec heading fails."""
    _write_spec_file(
        tmp_path=tmp_path, rel_path="SPECIFICATION/spec.md", body="# Title\n\n## Foo\n\nbody\n"
    )
    _write_registry(
        tmp_path=tmp_path,
        entries=[
            {
                "heading": "## Foo",
                "spec_root": "SPECIFICATION",
                "spec_file": "spec.md",
                "test": "tests/foo.py::test_foo",
            },
            {
                "heading": "## OldName",
                "spec_root": "SPECIFICATION",
                "spec_file": "spec.md",
                "test": "tests/old.py::test_old",
            },
        ],
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "registry entry orphaned" in combined
    assert "OldName" in combined


def test_heading_coverage_rejects_todo_without_reason(*, tmp_path: Path) -> None:
    """A `test: TODO` entry without a non-empty `reason` field fails."""
    _write_spec_file(
        tmp_path=tmp_path, rel_path="SPECIFICATION/spec.md", body="# Title\n\n## Foo\n\nbody\n"
    )
    _write_registry(
        tmp_path=tmp_path,
        entries=[
            {
                "heading": "## Foo",
                "spec_root": "SPECIFICATION",
                "spec_file": "spec.md",
                "test": "TODO",
            }
        ],
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "TODO registry entry missing reason" in combined


def test_heading_coverage_accepts_todo_with_reason(*, tmp_path: Path) -> None:
    """A `test: TODO` entry WITH a non-empty `reason` field passes."""
    _write_spec_file(
        tmp_path=tmp_path, rel_path="SPECIFICATION/spec.md", body="# Title\n\n## Foo\n\nbody\n"
    )
    _write_registry(
        tmp_path=tmp_path,
        entries=[
            {
                "heading": "## Foo",
                "spec_root": "SPECIFICATION",
                "spec_file": "spec.md",
                "test": "TODO",
                "reason": "test pending",
            }
        ],
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_heading_coverage_skips_scenario_prefix(*, tmp_path: Path) -> None:
    """Headings beginning with `Scenario:` are skipped — no entry needed."""
    body = "# Title\n\n## Foo\n\n## Scenario: happy path\n"
    _write_spec_file(tmp_path=tmp_path, rel_path="SPECIFICATION/spec.md", body=body)
    _write_registry(
        tmp_path=tmp_path,
        entries=[
            {
                "heading": "## Foo",
                "spec_root": "SPECIFICATION",
                "spec_file": "spec.md",
                "test": "tests/foo.py::test_foo",
            }
        ],
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_heading_coverage_does_not_recurse_into_proposed_changes(*, tmp_path: Path) -> None:
    """A `## Proposal:` heading under proposed_changes/ does NOT require a registry entry."""
    _write_spec_file(
        tmp_path=tmp_path, rel_path="SPECIFICATION/spec.md", body="# Title\n\n## Foo\n"
    )
    _write_spec_file(
        tmp_path=tmp_path,
        rel_path="SPECIFICATION/proposed_changes/whatever.md",
        body="## Proposal: should be ignored\n",
    )
    _write_registry(
        tmp_path=tmp_path,
        entries=[
            {
                "heading": "## Foo",
                "spec_root": "SPECIFICATION",
                "spec_file": "spec.md",
                "test": "tests/foo.py::test_foo",
            }
        ],
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_heading_coverage_does_not_recurse_into_history(*, tmp_path: Path) -> None:
    """Headings under `history/v*/` are NOT counted by the check."""
    _write_spec_file(
        tmp_path=tmp_path, rel_path="SPECIFICATION/spec.md", body="# Title\n\n## Foo\n"
    )
    _write_spec_file(
        tmp_path=tmp_path,
        rel_path="SPECIFICATION/history/v001/spec.md",
        body="# Title\n\n## Snapshot heading\n",
    )
    _write_registry(
        tmp_path=tmp_path,
        entries=[
            {
                "heading": "## Foo",
                "spec_root": "SPECIFICATION",
                "spec_file": "spec.md",
                "test": "tests/foo.py::test_foo",
            }
        ],
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_heading_coverage_does_not_count_readme(*, tmp_path: Path) -> None:
    """The skill-owned `README.md` at the tree root is not walked."""
    _write_spec_file(
        tmp_path=tmp_path, rel_path="SPECIFICATION/spec.md", body="# Title\n\n## Foo\n"
    )
    _write_spec_file(
        tmp_path=tmp_path,
        rel_path="SPECIFICATION/README.md",
        body="# Orientation\n\n## Some Section\n",
    )
    _write_registry(
        tmp_path=tmp_path,
        entries=[
            {
                "heading": "## Foo",
                "spec_root": "SPECIFICATION",
                "spec_file": "spec.md",
                "test": "tests/foo.py::test_foo",
            }
        ],
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_heading_coverage_skips_non_directory_under_templates(*, tmp_path: Path) -> None:
    """A non-directory entry under `templates/` is ignored (e.g., a stray file)."""
    _write_spec_file(
        tmp_path=tmp_path, rel_path="SPECIFICATION/spec.md", body="# Title\n\n## Foo\n"
    )
    # Stray file under templates/ — must be skipped, not treated as sub-spec root.
    _write_spec_file(
        tmp_path=tmp_path,
        rel_path="SPECIFICATION/templates/stray.txt",
        body="not a sub-spec directory\n",
    )
    _write_registry(
        tmp_path=tmp_path,
        entries=[
            {
                "heading": "## Foo",
                "spec_root": "SPECIFICATION",
                "spec_file": "spec.md",
                "test": "tests/foo.py::test_foo",
            }
        ],
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_heading_coverage_walks_sub_spec_trees(*, tmp_path: Path) -> None:
    """Sub-spec roots under `SPECIFICATION/templates/<name>/` are walked too."""
    _write_spec_file(
        tmp_path=tmp_path, rel_path="SPECIFICATION/spec.md", body="# Title\n\n## Main\n"
    )
    _write_spec_file(
        tmp_path=tmp_path,
        rel_path="SPECIFICATION/templates/livespec/spec.md",
        body="# Title\n\n## Sub-spec heading\n",
    )
    _write_registry(
        tmp_path=tmp_path,
        entries=[
            {
                "heading": "## Main",
                "spec_root": "SPECIFICATION",
                "spec_file": "spec.md",
                "test": "tests/main.py::test_main",
            },
            {
                "heading": "## Sub-spec heading",
                "spec_root": "SPECIFICATION/templates/livespec",
                "spec_file": "spec.md",
                "test": "tests/sub.py::test_sub",
            },
        ],
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_heading_coverage_disambiguates_same_heading_across_files(*, tmp_path: Path) -> None:
    """Two files with the same heading text need TWO registry entries (different spec_file)."""
    _write_spec_file(
        tmp_path=tmp_path, rel_path="SPECIFICATION/spec.md", body="# Title\n\n## Summary\n"
    )
    _write_spec_file(
        tmp_path=tmp_path, rel_path="SPECIFICATION/contracts.md", body="# Title\n\n## Summary\n"
    )
    _write_registry(
        tmp_path=tmp_path,
        entries=[
            {
                "heading": "## Summary",
                "spec_root": "SPECIFICATION",
                "spec_file": "spec.md",
                "test": "tests/spec.py::test_summary",
            },
        ],
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "spec heading missing coverage entry" in combined
    assert "contracts.md" in combined


def test_heading_coverage_tolerates_malformed_registry_entries(*, tmp_path: Path) -> None:
    """Entries with non-string fields are skipped silently."""
    _write_spec_file(
        tmp_path=tmp_path, rel_path="SPECIFICATION/spec.md", body="# Title\n\n## Foo\n"
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "heading-coverage.json").write_text(
        json.dumps(
            [
                {
                    "heading": "## Foo",
                    "spec_root": "SPECIFICATION",
                    "spec_file": "spec.md",
                    "test": "tests/foo.py::test_foo",
                },
                {"heading": 42, "spec_root": "SPECIFICATION", "spec_file": "spec.md", "test": "x"},
            ]
        ),
        encoding="utf-8",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_heading_coverage_tolerates_object_top_level_registry(*, tmp_path: Path) -> None:
    """Non-list top-level coverage JSON is treated as no entries."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "heading-coverage.json").write_text("{}", encoding="utf-8")
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_heading_coverage_accepts_pre_phase_6_empty(*, tmp_path: Path) -> None:
    """An empty `[]` registry with NO spec tree passes (exit 0)."""
    _write_registry(tmp_path=tmp_path, entries=[])
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_heading_coverage_accepts_no_coverage_file(*, tmp_path: Path) -> None:
    """Repo without `tests/heading-coverage.json` passes (exit 0)."""
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_heading_coverage_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking `main()`."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "heading_coverage_for_import_test",
        str(_HEADING_COVERAGE),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)
