"""Outside-in test for `dev-tooling/checks/tests_mirror_pairing.py` — v033 D1 mirror-pairing enforcement.

Per `SPECIFICATION/spec.md` §"Testing approach" (post-v006), every
covered `.py` file MUST have a paired test file at the mirror path
EXCEPT (a) private-helper modules (filename starts with `_`, NOT
`__init__.py`); (b) boilerplate `__init__.py` files (only docstring +
`from __future__ import annotations` + `__all__: list[str] = []`);
(c) `bin/_bootstrap.py` (covered by `tests/bin/test_bootstrap.py`).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_TESTS_MIRROR_PAIRING = _REPO_ROOT / "dev-tooling" / "checks" / "tests_mirror_pairing.py"


def _run_check(*, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_TESTS_MIRROR_PAIRING)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def _write_py(*, tmp_path: Path, rel_path: str, body: str) -> None:
    full = tmp_path / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(body, encoding="utf-8")


def test_tests_mirror_pairing_rejects_livespec_source_without_paired_test(
    *, tmp_path: Path
) -> None:
    """A `livespec/foo/bar.py` source file (with a function definition) without `tests/livespec/foo/test_bar.py` fails."""
    _write_py(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/foo/bar.py",
        body="from __future__ import annotations\n\n__all__: list[str] = []\n\n"
        "def do_thing() -> int:\n    return 0\n",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert ".claude-plugin/scripts/livespec/foo/bar.py" in combined
    assert "tests/livespec/foo/test_bar.py" in combined


def test_tests_mirror_pairing_accepts_paired_source_and_test(*, tmp_path: Path) -> None:
    """Two source files with paired tests pass (exit 0); covers the pair-found loop continuation."""
    _write_py(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/foo/bar.py",
        body="from __future__ import annotations\n__all__: list[str] = []\n\n"
        "def do_thing() -> int:\n    return 0\n",
    )
    _write_py(
        tmp_path=tmp_path,
        rel_path="tests/livespec/foo/test_bar.py",
        body="from __future__ import annotations\n__all__: list[str] = []\n"
        "def test_bar() -> None:\n    assert True\n",
    )
    _write_py(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/foo/baz.py",
        body="from __future__ import annotations\n__all__: list[str] = []\n\n"
        "def other() -> int:\n    return 1\n",
    )
    _write_py(
        tmp_path=tmp_path,
        rel_path="tests/livespec/foo/test_baz.py",
        body="from __future__ import annotations\n__all__: list[str] = []\n"
        "def test_baz() -> None:\n    assert True\n",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_tests_mirror_pairing_exempts_private_helper_module(*, tmp_path: Path) -> None:
    """A `_helper.py` private-helper module (not `__init__.py`) does NOT need a paired test."""
    _write_py(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/commands/_helper.py",
        body="from __future__ import annotations\n__all__: list[str] = []\nx = 0\n",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_tests_mirror_pairing_exempts_pure_declaration_init(*, tmp_path: Path) -> None:
    """An `__init__.py` whose body has no FunctionDef is exempt under the pure-declaration rule."""
    _write_py(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/commands/__init__.py",
        body='"""commands package."""\nfrom __future__ import annotations\n__all__: list[str] = []\n',
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_tests_mirror_pairing_exempts_pure_dataclass_module(*, tmp_path: Path) -> None:
    """A pure dataclass module (decorated class, no FunctionDef anywhere) is exempt."""
    _write_py(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/schemas/dataclasses/finding.py",
        body='"""Finding dataclass."""\nfrom __future__ import annotations\n'
        "from dataclasses import dataclass\n"
        '__all__: list[str] = ["Finding"]\n\n'
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class Finding:\n"
        '    """The Finding wire dataclass."""\n'
        "    check_id: str\n",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_tests_mirror_pairing_rejects_non_pure_init_without_paired_test(*, tmp_path: Path) -> None:
    """An `__init__.py` with a FunctionDef requires a paired test."""
    _write_py(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/__init__.py",
        body='"""livespec package."""\nfrom __future__ import annotations\n'
        "__all__: list[str] = []\n\n"
        "def configure() -> int:\n    return 0\n",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "__init__.py" in combined


def test_tests_mirror_pairing_exempts_bootstrap(*, tmp_path: Path) -> None:
    """`bin/_bootstrap.py` is special-cased (covered by tests/bin/test_bootstrap.py)."""
    _write_py(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/bin/_bootstrap.py",
        body="from __future__ import annotations\n__all__: list[str] = []\nx = 0\n",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0


def test_tests_mirror_pairing_rejects_module_with_function_def_without_paired_test(
    *, tmp_path: Path
) -> None:
    """A module with a `def` (any function definition) requires a paired test."""
    _write_py(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/foo/has_logic.py",
        body="from __future__ import annotations\n__all__: list[str] = []\n\n"
        "def f() -> int:\n    return 1\n",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0


def test_tests_mirror_pairing_rejects_module_with_async_function_def_without_paired_test(
    *, tmp_path: Path
) -> None:
    """A module with an `async def` requires a paired test."""
    _write_py(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/foo/has_async.py",
        body="from __future__ import annotations\n__all__: list[str] = []\n\n"
        "async def f() -> int:\n    return 1\n",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0


def test_tests_mirror_pairing_rejects_class_with_method_def_without_paired_test(
    *, tmp_path: Path
) -> None:
    """A class definition containing a method (FunctionDef inside ClassDef) is NOT exempt."""
    _write_py(
        tmp_path=tmp_path,
        rel_path=".claude-plugin/scripts/livespec/foo/with_class.py",
        body="from __future__ import annotations\n__all__: list[str] = []\n\n"
        "class Foo:\n    def bar(self) -> int:\n        return 1\n",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0


def test_tests_mirror_pairing_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "tests_mirror_pairing_for_import_test",
        str(_TESTS_MIRROR_PAIRING),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)
