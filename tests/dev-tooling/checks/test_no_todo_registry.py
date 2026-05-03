"""Outside-in test for `dev-tooling/checks/no_todo_registry.py` — `tests/heading-coverage.json` no TODO entries.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-no-todo-registry` row), no entry in
`tests/heading-coverage.json` may have `test: "TODO"`.
Release-gate only — paired with `check-mutation` on the
release-tag CI workflow.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NO_TODO_REGISTRY = _REPO_ROOT / "dev-tooling" / "checks" / "no_todo_registry.py"


def test_no_todo_registry_rejects_todo_entry(*, tmp_path: Path) -> None:
    """An entry with `test: "TODO"` fails the check."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    coverage_json = tests_dir / "heading-coverage.json"
    coverage_json.write_text(
        '[{"heading": "## Foo", "spec_root": "/", "test": "TODO"}]',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_TODO_REGISTRY)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_todo_registry should reject TODO entry; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "## Foo" in combined or "Foo" in combined, (
        f"diagnostic does not surface offending heading; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_todo_registry_accepts_no_todo_entries(*, tmp_path: Path) -> None:
    """Coverage JSON with no TODO entries passes (exit 0)."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    coverage_json = tests_dir / "heading-coverage.json"
    coverage_json.write_text(
        '[{"heading": "## Foo", "spec_root": "/", "test": "tests/foo.py"}]',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_TODO_REGISTRY)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_todo_registry should accept TODO-free coverage with exit 0; "
        f"got returncode={result.returncode}"
    )


def test_no_todo_registry_accepts_object_top_level(*, tmp_path: Path) -> None:
    """Coverage JSON whose top-level is not a list passes (exit 0).

    Closes the `if isinstance(parsed, list):` False branch.
    Pre-Phase-6 the file is an empty `[]`; in degenerate
    cases (empty object, etc.), the check should not crash.
    """
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    coverage_json = tests_dir / "heading-coverage.json"
    coverage_json.write_text("{}", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_NO_TODO_REGISTRY)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_todo_registry should accept object top-level with exit 0; "
        f"got returncode={result.returncode}"
    )


def test_no_todo_registry_accepts_missing_coverage_file(*, tmp_path: Path) -> None:
    """Repo without `tests/heading-coverage.json` passes (exit 0)."""
    result = subprocess.run(
        [sys.executable, str(_NO_TODO_REGISTRY)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_todo_registry should accept missing coverage file with exit 0; "
        f"got returncode={result.returncode}"
    )


def test_no_todo_registry_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "no_todo_registry_for_import_test", str(_NO_TODO_REGISTRY),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
