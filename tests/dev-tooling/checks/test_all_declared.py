"""Outside-in test for `dev-tooling/checks/all_declared.py` — `__all__` declaration discipline.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-all-declared` row), every module
under `.claude-plugin/scripts/livespec/**` MUST declare a
module-top `__all__: list[str]` (typed annotation, list
literal). Every name in `__all__` must also be defined in the
module. Two failure modes:

- Missing `__all__` declaration entirely.
- Names in `__all__` that are not defined as module-top names
  (def, class, assignment, import).

Cycle 149 pins the first failure mode (missing `__all__`).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_ALL_DECLARED = _REPO_ROOT / "dev-tooling" / "checks" / "all_declared.py"


def test_all_declared_rejects_module_missing_all_declaration(*, tmp_path: Path) -> None:
    """A livespec module without `__all__: list[str] = ...` fails the check.

    Fixture: `.claude-plugin/scripts/livespec/foo.py` contains
    only `from __future__ import annotations` plus a function
    definition — no `__all__` declaration. The check, invoked
    with `cwd=tmp_path`, must walk the livespec subtree, parse
    the file, detect the missing declaration, exit non-zero,
    and surface the offending file path.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_ALL_DECLARED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"all_declared should reject module without `__all__` with non-zero exit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/foo.py"
    assert expected_path in combined, (
        f"all_declared diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_all_declared_rejects_undefined_name_in_all(*, tmp_path: Path) -> None:
    """An `__all__` entry not defined in the module fails the check.

    Fixture: `.claude-plugin/scripts/livespec/foo.py` declares
    `__all__: list[str] = ["bogus"]` but does not define
    `bogus`. The check exits non-zero and surfaces both the
    file path and the offending name.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["bogus"]\n'
        "\n"
        "\n"
        "def real_thing() -> int:\n"
        "    return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_ALL_DECLARED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"all_declared should reject undefined name in `__all__` with non-zero exit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "bogus" in combined, (
        f"all_declared diagnostic does not surface undefined name `bogus`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_all_declared_accepts_module_with_complete_all_declaration(*, tmp_path: Path) -> None:
    """A livespec module with valid `__all__` listing all defined exports passes (exit 0).

    Pass-case: `__all__: list[str] = ["main"]` and `def main()`
    is defined. The check walks the file, finds the
    declaration, verifies every listed name is defined, exits 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    # Pass-case fixture exercises every recognized definition
    # form: `import os` (`Import`), `from typing import Any`
    # (`ImportFrom`), `CONST = 1` (`Assign`), `x: int = 0`
    # (`AnnAssign`), `def fn` (`FunctionDef`), `class Cls`
    # (`ClassDef`). Exercises every elif arm of
    # _module_top_defined_names so per-file 100% branch
    # coverage holds.
    source.write_text(
        '"""Module docstring exercises the top-level Expr fall-through arm."""\n'
        "from __future__ import annotations\n"
        "\n"
        "import os\n"
        "from typing import Any\n"
        "\n"
        '__all__: list[str] = ["fn", "Cls", "CONST", "x", "os", "Any"]\n'
        "\n"
        "CONST = 1\n"
        "x: int = 0\n"
        "# Tuple-unpacking assign exercises the target-not-Name branch.\n"
        "(a, b) = (1, 2)\n"
        "\n"
        "\n"
        "def fn() -> Any:\n"
        "    return os.getcwd()\n"
        "\n"
        "\n"
        "class Cls:\n"
        "    pass\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_ALL_DECLARED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"all_declared should accept valid module with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_all_declared_accepts_tree_without_livespec_directory(*, tmp_path: Path) -> None:
    """A repo cwd without `.claude-plugin/scripts/livespec/` passes the check (exit 0).

    Closes the `if livespec_root.is_dir():` False arm.
    """
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_ALL_DECLARED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"all_declared should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_all_declared_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "all_declared_for_import_test", str(_ALL_DECLARED),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"


def test_module_top_defined_names_helpers_cover_each_node_kind() -> None:
    """The five `_names_from_*` helpers each return the expected name set.

    Cycle 4b refactor extracted per-node-kind helpers from
    `_module_top_defined_names` to bring the dispatcher under
    ruff's C901 cyclomatic-complexity threshold. This test
    exercises each helper directly so coverage no longer
    depends solely on the integration test.
    """
    import ast
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "all_declared_for_helpers_test", str(_ALL_DECLARED),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    func_node = ast.parse("def foo() -> None: pass").body[0]
    assert isinstance(func_node, ast.FunctionDef)
    assert module._names_from_def(node=func_node) == {"foo"}  # noqa: SLF001

    assign_node = ast.parse("x = 1").body[0]
    assert isinstance(assign_node, ast.Assign)
    assert module._names_from_assign(node=assign_node) == {"x"}  # noqa: SLF001

    annassign_node = ast.parse("y: int = 2").body[0]
    assert isinstance(annassign_node, ast.AnnAssign)
    assert module._names_from_annassign(node=annassign_node) == {"y"}  # noqa: SLF001

    # AnnAssign whose target is NOT an `ast.Name` (e.g.,
    # `self.x: int = 1` parses as Attribute target). The
    # helper returns empty set; this case pins the fall-
    # through branch so per-file coverage stays at 100%.
    annassign_attr_node = ast.parse("self.x: int = 1").body[0]
    assert isinstance(annassign_attr_node, ast.AnnAssign)
    assert module._names_from_annassign(node=annassign_attr_node) == set()  # noqa: SLF001

    importfrom_node = ast.parse("from os import path").body[0]
    assert isinstance(importfrom_node, ast.ImportFrom)
    assert module._names_from_import_from(node=importfrom_node) == {"path"}  # noqa: SLF001

    import_node = ast.parse("import json").body[0]
    assert isinstance(import_node, ast.Import)
    assert module._names_from_import(node=import_node) == {"json"}  # noqa: SLF001
