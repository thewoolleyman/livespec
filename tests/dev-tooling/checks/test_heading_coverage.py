"""Outside-in test for `dev-tooling/checks/heading_coverage.py` — every spec heading has a coverage entry.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-heading-coverage` row), every `##`
heading in every spec tree (main + each sub-spec under
`SPECIFICATION/templates/<name>/`) MUST have a corresponding
entry in `tests/heading-coverage.json` whose `spec_root` field
matches the heading's tree. Tolerates an empty `[]` array
pre-Phase-6, before any spec tree exists; from Phase 6 onward
emptiness is a failure if any spec tree exists.

Cycle 166 implements the structural check at the pre-Phase-6
empty state: empty heading-coverage.json with no spec tree
on disk passes. A spec tree with `## Foo` heading but no
matching entry fails.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_HEADING_COVERAGE = _REPO_ROOT / "dev-tooling" / "checks" / "heading_coverage.py"


def test_heading_coverage_rejects_uncovered_heading(*, tmp_path: Path) -> None:
    """A spec heading without a matching entry in heading-coverage.json fails."""
    spec_dir = tmp_path / "SPECIFICATION"
    spec_dir.mkdir(parents=True)
    (spec_dir / "main.md").write_text(
        "# Title\n\n## Foo\n\nbody\n",
        encoding="utf-8",
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "heading-coverage.json").write_text("[]", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_HEADING_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"heading_coverage should reject uncovered heading; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "Foo" in combined, (
        f"heading_coverage diagnostic does not surface heading `## Foo`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_heading_coverage_accepts_covered_heading(*, tmp_path: Path) -> None:
    """A spec heading WITH a matching entry passes."""
    spec_dir = tmp_path / "SPECIFICATION"
    spec_dir.mkdir(parents=True)
    (spec_dir / "main.md").write_text(
        "# Title\n\n## Foo\n\nbody\n",
        encoding="utf-8",
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "heading-coverage.json").write_text(
        '[{"heading": "## Foo", "spec_root": "SPECIFICATION", "test": "tests/foo.py"}]',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_HEADING_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"heading_coverage should accept covered heading; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_heading_coverage_tolerates_malformed_coverage_entries(*, tmp_path: Path) -> None:
    """Coverage JSON with mixed valid/invalid entries handles each entry gracefully.

    Fixture: heading-coverage.json contains one valid entry,
    one entry with non-string heading (gets skipped), and a
    top-level shape that's still a list. Combined with a
    spec heading that matches the valid entry, the check
    passes. Closes the `if isinstance(heading, str) and ...`
    False branch (an entry whose heading is non-string).
    """
    spec_dir = tmp_path / "SPECIFICATION"
    spec_dir.mkdir(parents=True)
    (spec_dir / "main.md").write_text(
        "# Title\n\n## Foo\n\nbody\n",
        encoding="utf-8",
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "heading-coverage.json").write_text(
        '[{"heading": "## Foo", "spec_root": "SPECIFICATION", "test": "tests/foo.py"},'
        ' {"heading": 42, "spec_root": "SPECIFICATION", "test": "x"}]',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_HEADING_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"heading_coverage should tolerate malformed coverage entries; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_heading_coverage_tolerates_object_top_level_coverage_json(*, tmp_path: Path) -> None:
    """Coverage JSON with object (not list) top-level treated as no entries.

    Closes the `if isinstance(parsed, list):` False branch.
    The fixture has a non-list coverage JSON AND no spec
    tree, so check still exits 0.
    """
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "heading-coverage.json").write_text("{}", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_HEADING_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"heading_coverage should tolerate object top-level coverage JSON; "
        f"got returncode={result.returncode}"
    )


def test_heading_coverage_accepts_pre_phase_6_empty(*, tmp_path: Path) -> None:
    """An empty `[]` heading-coverage.json with NO spec tree passes (exit 0).

    Pre-Phase-6 baseline: the SPECIFICATION/ tree doesn't
    exist yet. The check tolerates emptiness in this case.
    """
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "heading-coverage.json").write_text("[]", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_HEADING_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"heading_coverage should accept pre-Phase-6 empty state; "
        f"got returncode={result.returncode}"
    )


def test_heading_coverage_accepts_no_coverage_file(*, tmp_path: Path) -> None:
    """Repo without `tests/heading-coverage.json` passes (exit 0)."""
    result = subprocess.run(
        [sys.executable, str(_HEADING_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"heading_coverage should accept missing coverage file; "
        f"got returncode={result.returncode}"
    )


def test_heading_coverage_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "heading_coverage_for_import_test",
        str(_HEADING_COVERAGE),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
