"""Outside-in test for `dev-tooling/checks/pbt_coverage_pure_modules.py` — `@given` PBT in pure-layer tests.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-pbt-coverage-pure-modules` row), each
test module under `tests/livespec/parse/` and `tests/livespec/
validate/` declares at least one `@given(...)`-decorated test
function. Hypothesis property-based testing is the canonical
PBT mechanism for pure layers.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_PBT_COVERAGE = _REPO_ROOT / "dev-tooling" / "checks" / "pbt_coverage_pure_modules.py"


def test_pbt_coverage_rejects_parse_test_without_given_decorator(*, tmp_path: Path) -> None:
    """A `tests/livespec/parse/test_foo.py` without `@given(...)` fails the check."""
    test_dir = tmp_path / "tests" / "livespec" / "parse"
    test_dir.mkdir(parents=True)
    test_file = test_dir / "test_foo.py"
    test_file.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def test_foo() -> None:\n"
        "    assert True\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PBT_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"pbt_coverage should reject parse-layer test without @given; "
        f"got returncode={result.returncode}"
    )
    combined = result.stdout + result.stderr
    expected_path = "tests/livespec/parse/test_foo.py"
    assert expected_path in combined, (
        f"pbt_coverage diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_pbt_coverage_accepts_parse_test_with_given_decorator(*, tmp_path: Path) -> None:
    """A `tests/livespec/parse/test_foo.py` WITH a `@given(...)`-decorated function passes."""
    test_dir = tmp_path / "tests" / "livespec" / "parse"
    test_dir.mkdir(parents=True)
    test_file = test_dir / "test_foo.py"
    test_file.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from hypothesis import given\n"
        "from hypothesis import strategies as st\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@given(st.text())\n"
        "def test_foo_property(*, s: str) -> None:\n"
        "    assert isinstance(s, str)\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PBT_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"pbt_coverage should accept parse-layer test with @given; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_pbt_coverage_accepts_validate_test_with_given_decorator(*, tmp_path: Path) -> None:
    """A `tests/livespec/validate/test_foo.py` WITH a `@given(...)` passes.

    Fixture exercises additional decorator-shape branches:
    - `@pytest.mark.parametrize` (a bare `Attribute` access,
      not a `Call`) on the first function — covers the
      `decorator` non-Call branch of
      `_decorator_terminal_name`.
    - A non-given decorated function comes BEFORE the given-
      decorated one, exercising the loop continuation past a
      non-matching name.
    """
    test_dir = tmp_path / "tests" / "livespec" / "validate"
    test_dir.mkdir(parents=True)
    test_file = test_dir / "test_foo.py"
    test_file.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from hypothesis import given, strategies\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def helper() -> None:\n"
        "    pass\n"
        "\n"
        "\n"
        "@helper\n"
        "def test_first() -> None:\n"
        "    assert True\n"
        "\n"
        "\n"
        "@given(strategies.text())\n"
        "def test_foo(*, s: str) -> None:\n"
        "    assert s == s\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PBT_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"pbt_coverage should accept validate-layer test with @given; "
        f"got returncode={result.returncode}"
    )


def test_pbt_coverage_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes (exit 0)."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PBT_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"pbt_coverage should accept empty tree; got returncode={result.returncode}"
    )


def test_pbt_coverage_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "pbt_coverage_pure_modules_for_import_test", str(_PBT_COVERAGE),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
