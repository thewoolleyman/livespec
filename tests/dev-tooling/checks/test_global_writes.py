"""Outside-in test for `dev-tooling/checks/global_writes.py` — no module-level mutable writes from functions.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-global-writes` row), no module-level
mutable state writes from functions are permitted in
`livespec/**`. The `global` keyword is the canonical
declarator for writing module state from a function body and
is banned. The `nonlocal` keyword (writing enclosing-scope
state from nested functions) is also banned for the same
reason.

Cycle 158 implements the structural check: ban `global` and
`nonlocal` statements anywhere in `livespec/**`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_GLOBAL_WRITES = _REPO_ROOT / "dev-tooling" / "checks" / "global_writes.py"


def test_global_writes_rejects_global_statement(*, tmp_path: Path) -> None:
    """A `global x` statement inside a function fails the check.

    Fixture: a livespec module with `def fn(): global x; x =
    1`. Banned — writes to module state from a function are
    forbidden.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "x = 0\n"
        "\n"
        "\n"
        "def fn() -> None:\n"
        "    global x\n"
        "    x = 1\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_GLOBAL_WRITES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"global_writes should reject `global` statement; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/foo.py"
    assert expected_path in combined, (
        f"global_writes diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_global_writes_rejects_nonlocal_statement(*, tmp_path: Path) -> None:
    """A `nonlocal x` statement inside a nested function fails the check.

    Fixture: nested function uses `nonlocal x`. Banned — same
    rationale as `global`.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def outer() -> None:\n"
        "    x = 0\n"
        "    def inner() -> None:\n"
        "        nonlocal x\n"
        "        x = 1\n"
        "    inner()\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_GLOBAL_WRITES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"global_writes should reject `nonlocal` statement; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_global_writes_accepts_clean_module(*, tmp_path: Path) -> None:
    """A livespec module with no `global`/`nonlocal` passes the check (exit 0)."""
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "X = 0\n"
        "\n"
        "\n"
        "def fn() -> int:\n"
        "    return X + 1\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_GLOBAL_WRITES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"global_writes should accept clean module with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_global_writes_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes the check (exit 0)."""
    result = subprocess.run(
        [sys.executable, str(_GLOBAL_WRITES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"global_writes should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_global_writes_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "global_writes_for_import_test", str(_GLOBAL_WRITES),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
