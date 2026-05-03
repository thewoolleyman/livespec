"""Outside-in test for `dev-tooling/checks/rop_pipeline_shape.py` — `@rop_pipeline` class shape.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-rop-pipeline-shape` row), every class
decorated with `@rop_pipeline` carries exactly one public
method (the entry point); other methods are `_`-prefixed;
dunders aren't counted. Enforces the Command / Use Case
Interactor pattern at the class level.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_ROP_PIPELINE_SHAPE = _REPO_ROOT / "dev-tooling" / "checks" / "rop_pipeline_shape.py"


def test_rop_pipeline_shape_rejects_class_with_two_public_methods(*, tmp_path: Path) -> None:
    """A `@rop_pipeline` class with two non-underscore methods fails the check."""
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from livespec.types import rop_pipeline\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@rop_pipeline\n"
        "class Pipeline:\n"
        "    def run(self) -> int:\n"
        "        return 0\n"
        "\n"
        "    def also_run(self) -> int:\n"
        "        return 1\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_ROP_PIPELINE_SHAPE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"rop_pipeline_shape should reject two-public-methods class; "
        f"got returncode={result.returncode}"
    )
    combined = result.stdout + result.stderr
    assert "Pipeline" in combined, (
        f"diagnostic does not surface offending class `Pipeline`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_rop_pipeline_shape_accepts_class_with_one_public_method(*, tmp_path: Path) -> None:
    """A `@rop_pipeline()` class with one public method + private helpers passes (exit 0).

    Uses the `@rop_pipeline()` Call form (decorator with
    parens) to exercise the `if isinstance(decorator, ast.
    Call):` True arm of `_decorator_terminal_name`.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from livespec.types import rop_pipeline\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@rop_pipeline()\n"
        "class Pipeline:\n"
        "    def __init__(self) -> None:\n"
        "        pass\n"
        "\n"
        "    def run(self) -> int:\n"
        "        return self._helper()\n"
        "\n"
        "    def _helper(self) -> int:\n"
        "        return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_ROP_PIPELINE_SHAPE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"rop_pipeline_shape should accept one-public-method class with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_rop_pipeline_shape_accepts_bare_decorator_and_class_attributes(
    *, tmp_path: Path,
) -> None:
    """A `@rop_pipeline` class with class attributes (not methods) and bare decorator passes.

    Closes the `_decorator_terminal_name` non-Call branch
    (decorator is a bare Name, not a Call) and the
    `_count_public_methods` non-FunctionDef body-stmt branch
    (the class has an `Assign` body member alongside its
    methods).
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from livespec.types import rop_pipeline\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@rop_pipeline\n"
        "class Pipeline:\n"
        "    CONST: int = 0\n"
        "\n"
        "    def run(self) -> int:\n"
        "        return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_ROP_PIPELINE_SHAPE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"rop_pipeline_shape should accept class with attributes; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_rop_pipeline_shape_ignores_undecorated_classes(*, tmp_path: Path) -> None:
    """A class without the `@rop_pipeline` decorator is ignored."""
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "class Plain:\n"
        "    def m1(self) -> int:\n"
        "        return 0\n"
        "\n"
        "    def m2(self) -> int:\n"
        "        return 1\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_ROP_PIPELINE_SHAPE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"rop_pipeline_shape should ignore undecorated classes; "
        f"got returncode={result.returncode}"
    )


def test_rop_pipeline_shape_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes (exit 0)."""
    result = subprocess.run(
        [sys.executable, str(_ROP_PIPELINE_SHAPE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"rop_pipeline_shape should accept empty tree; got returncode={result.returncode}"
    )


def test_rop_pipeline_shape_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "rop_pipeline_shape_for_import_test", str(_ROP_PIPELINE_SHAPE),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
