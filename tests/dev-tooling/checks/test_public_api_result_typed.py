"""Outside-in test for `dev-tooling/checks/public_api_result_typed.py` — pure-layer public APIs are Result-typed.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-public-api-result-typed` row), every
public function (per `__all__` declaration) in pure layers
returns `Result` or `IOResult` per annotation OR carries a
railway-lifting decorator (`@impure_safe(...)` lifts to
`IOResult`, `@safe(...)` lifts to `Result`). Cycle 169
implements the minimum-viable subset: parse and validate
layers' public functions must be Result-typed or
@safe-decorated.

Documented exemptions (a-f per the canonical row) are NOT
yet implemented; subsequent cycles widen as concrete files
surface.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_PUBLIC_API_RESULT_TYPED = (
    _REPO_ROOT / "dev-tooling" / "checks" / "public_api_result_typed.py"
)


def test_public_api_result_typed_rejects_non_result_public_function(*, tmp_path: Path) -> None:
    """A public function in `parse/` returning bare `int` (not Result) fails the check."""
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["compute"]\n'
        "\n"
        "\n"
        "def compute(*, x: int) -> int:\n"
        "    return x\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PUBLIC_API_RESULT_TYPED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"public_api_result_typed should reject non-Result public; "
        f"got returncode={result.returncode}"
    )
    combined = result.stdout + result.stderr
    assert "compute" in combined, (
        f"diagnostic does not surface offending name `compute`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_public_api_result_typed_accepts_result_typed_function(*, tmp_path: Path) -> None:
    """A public function returning `Result[...]` passes (exit 0)."""
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from returns.result import Result\n"
        "\n"
        '__all__: list[str] = ["compute"]\n'
        "\n"
        "\n"
        "def compute(*, x: int) -> Result[int, str]:\n"
        "    return Result.from_value(x)\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PUBLIC_API_RESULT_TYPED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"public_api_result_typed should accept Result-typed public function; "
        f"got returncode={result.returncode}"
    )


def test_public_api_result_typed_accepts_safe_decorated_function(*, tmp_path: Path) -> None:
    """A public function decorated with `@safe(...)` passes (exit 0).

    Fixture stacks a non-railway decorator BEFORE the
    `@safe(...)` to exercise the `for decorator in
    decorator_list:` loop continuation past a non-matching
    name (closes branch 89->88).
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from functools import wraps\n"
        "from returns.result import safe\n"
        "\n"
        '__all__: list[str] = ["compute"]\n'
        "\n"
        "\n"
        "def passthrough(fn):\n"
        "    return fn\n"
        "\n"
        "\n"
        "@passthrough\n"
        "@safe(exceptions=(ValueError,))\n"
        "def compute(*, x: int) -> int:\n"
        "    return x\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PUBLIC_API_RESULT_TYPED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"public_api_result_typed should accept @safe-decorated public function; "
        f"got returncode={result.returncode}"
    )


def test_public_api_result_typed_skips_private_filename(*, tmp_path: Path) -> None:
    """A package-private module (`_*.py`) is wholly skipped.

    Closes the `if py_file.name.startswith("_"):` filename
    skip branch. The file's bare-int public function would
    otherwise fail; the filename skip protects it.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    package_dir.mkdir(parents=True)
    source = package_dir / "_helpers.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["raw"]\n'
        "\n"
        "\n"
        "def raw(*, x: int) -> int:\n"
        "    return x\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PUBLIC_API_RESULT_TYPED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"public_api_result_typed should skip _-prefixed filenames; "
        f"got returncode={result.returncode}"
    )


def test_public_api_result_typed_skips_module_without_all(*, tmp_path: Path) -> None:
    """A module without `__all__` declaration has empty declared set; nothing surfaces.

    Closes the `_all_value_names` returns-empty-list branch.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "\n"
        "def compute(*, x: int) -> int:\n"
        "    return x\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PUBLIC_API_RESULT_TYPED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"public_api_result_typed should skip modules without __all__; "
        f"got returncode={result.returncode}"
    )


def test_public_api_result_typed_accepts_bare_safe_decorator(*, tmp_path: Path) -> None:
    """A `@safe` (bare, not Call form) decorator passes the check.

    Closes the `_decorator_terminal_name` non-Call branch
    (decorator IS a Name, not a Call).
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from returns.result import safe\n"
        "\n"
        '__all__: list[str] = ["compute"]\n'
        "\n"
        "\n"
        "@safe\n"
        "def compute(*, x: int) -> int:\n"
        "    return x\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PUBLIC_API_RESULT_TYPED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"public_api_result_typed should accept bare @safe decorator; "
        f"got returncode={result.returncode}"
    )


def test_public_api_result_typed_rejects_function_without_return_annotation(
    *, tmp_path: Path,
) -> None:
    """A public function without a return annotation fails the check.

    Closes the `if func.returns is None: return False` branch.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["compute"]\n'
        "\n"
        "\n"
        "def compute(*, x):\n"  # No return annotation
        "    return x\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PUBLIC_API_RESULT_TYPED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"public_api_result_typed should reject return-less function; "
        f"got returncode={result.returncode}"
    )


def test_public_api_result_typed_ignores_private_function(*, tmp_path: Path) -> None:
    """A `_`-prefixed function is private and ignored by the check.

    Even if `_helper` returns `int` directly, it's not in
    `__all__`, so the check skips it.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = []\n'
        "\n"
        "\n"
        "def _helper(*, x: int) -> int:\n"
        "    return x\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PUBLIC_API_RESULT_TYPED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"public_api_result_typed should ignore private function; "
        f"got returncode={result.returncode}"
    )


def test_public_api_result_typed_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes (exit 0)."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PUBLIC_API_RESULT_TYPED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"public_api_result_typed should accept empty tree; got returncode={result.returncode}"
    )


def test_public_api_result_typed_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "public_api_result_typed_for_import_test", str(_PUBLIC_API_RESULT_TYPED),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
