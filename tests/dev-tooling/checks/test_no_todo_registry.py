"""Outside-in test for `dev-tooling/checks/no_todo_registry.py`.

Per `python-skill-script-style-requirements.md` §"Mutation testing
as release-gate" line 2116:

    Rejects any `test: "TODO"` entry in
    `tests/heading-coverage.json` (v013 M8). Release-gate only;
    paired with `check-mutation` on release-tag CI workflow.
    Ensures every release ships with full rule-test coverage.

Cycle 53 pins the canonical violation: a registry entry with
`test: "TODO"`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NO_TODO_REGISTRY = _REPO_ROOT / "dev-tooling" / "checks" / "no_todo_registry.py"


def test_no_todo_registry_rejects_todo_entry(*, tmp_path: Path) -> None:
    """A heading-coverage entry with `test: "TODO"` is rejected.

    Fixture: `tests/heading-coverage.json` carries one TODO
    entry with a reason. The release-gate check must reject it
    regardless of reason, exit non-zero, and surface the offending
    heading text.
    """
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "heading-coverage.json").write_text(
        "[\n"
        "  {\n"
        '    "spec_root": "SPECIFICATION",\n'
        '    "spec_file": "spec.md",\n'
        '    "heading": "Foo rule",\n'
        '    "test": "TODO",\n'
        '    "reason": "rule added in v015; test pending"\n'
        "  }\n"
        "]\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_TODO_REGISTRY)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_todo_registry should reject TODO registry entry; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "Foo rule" in combined, (
        f"no_todo_registry diagnostic does not surface offending heading 'Foo rule'; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_todo_registry_accepts_only_real_test_entries(*, tmp_path: Path) -> None:
    """A heading-coverage with no TODO entries is accepted.

    Fixture: every entry has a real `test:` pytest node id. The
    check must walk and exit 0.
    """
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "heading-coverage.json").write_text(
        "[\n"
        "  {\n"
        '    "spec_root": "SPECIFICATION",\n'
        '    "spec_file": "spec.md",\n'
        '    "heading": "Foo rule",\n'
        '    "test": "tests/test_foo.py::test_foo_rule"\n'
        "  }\n"
        "]\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_TODO_REGISTRY)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_todo_registry should accept registry with real test entries; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
