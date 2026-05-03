"""Outside-in test for `dev-tooling/checks/private_calls.py` — no cross-module `_`-prefixed calls.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-private-calls` row), no cross-module
calls to `_`-prefixed functions defined elsewhere are
permitted in `livespec/**`. Within a single module, calling
`_helper()` is fine; from another module, calling
`other_module._helper()` is banned (the leading underscore
declares module-private intent).

Cycle 157 implements the structural check: find any
`Attribute` access on a function call where the attribute
name starts with `_` and the receiver is an imported module
(not `self` or `cls`).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_PRIVATE_CALLS = _REPO_ROOT / "dev-tooling" / "checks" / "private_calls.py"


def test_private_calls_rejects_cross_module_underscore_call(*, tmp_path: Path) -> None:
    """A call to `othermod._helper()` (cross-module private) fails the check.

    Fixture: a livespec module imports `from livespec import
    other` and calls `other._helper()`. Banned — leading
    underscore declares module-private.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from livespec import other\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    return other._helper()\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_PRIVATE_CALLS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"private_calls should reject cross-module _-call; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/foo.py"
    assert expected_path in combined, (
        f"private_calls diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "_helper" in combined, (
        f"private_calls diagnostic does not surface attribute `_helper`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_private_calls_accepts_self_underscore_method_call(*, tmp_path: Path) -> None:
    """A call to `self._helper()` (intra-class private) passes (exit 0).

    Pass-case: methods on classes legitimately call private
    helpers via `self._foo()` or `cls._bar()`.
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
        "class Foo:\n"
        "    def _helper(self) -> int:\n"
        "        return 0\n"
        "\n"
        "    def main(self) -> int:\n"
        "        return self._helper()\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_PRIVATE_CALLS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"private_calls should accept self._foo() with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_private_calls_accepts_intra_module_underscore_call(*, tmp_path: Path) -> None:
    """A call to `_helper()` (intra-module private) passes (exit 0).

    Pass-case: calling `_helper()` directly within the same
    module is permitted — the leading underscore declares
    intent, not enforcement boundary.
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
        "def _helper() -> int:\n"
        "    return 0\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    return _helper()\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_PRIVATE_CALLS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"private_calls should accept intra-module _helper() with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_private_calls_accepts_cross_module_public_call(*, tmp_path: Path) -> None:
    """A call to `othermod.helper()` (cross-module public) passes (exit 0).

    Pass-case: cross-module call to a non-underscore name is
    fine — public functions are the supported surface.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from livespec import other\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    return other.helper()\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_PRIVATE_CALLS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"private_calls should accept cross-module public call with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_private_calls_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes the check (exit 0)."""
    result = subprocess.run(
        [sys.executable, str(_PRIVATE_CALLS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"private_calls should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_private_calls_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "private_calls_for_import_test",
        str(_PRIVATE_CALLS),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
