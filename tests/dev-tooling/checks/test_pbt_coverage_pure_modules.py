"""Outside-in test for `dev-tooling/checks/pbt_coverage_pure_modules.py`.

Per `python-skill-script-style-requirements.md` §"Property-based
testing for pure modules" (lines 1216-1247) and the canonical-
target table line 2093:

    AST: each test module under `tests/livespec/parse/` and
    `tests/livespec/validate/` declares at least one
    `@given(...)`-decorated test function.

Cycle 50 pins the canonical violation: a test module under
`tests/livespec/parse/` (or `tests/livespec/validate/`) with
zero `@given(...)`-decorated functions is rejected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_PBT_COVERAGE_PURE_MODULES = _REPO_ROOT / "dev-tooling" / "checks" / "pbt_coverage_pure_modules.py"


def test_pbt_coverage_pure_modules_rejects_test_without_given(*, tmp_path: Path) -> None:
    """A `tests/livespec/parse/test_*.py` with no `@given` is rejected.

    Fixture: `tests/livespec/parse/test_jsonc.py` exists, but
    declares only one plain function with no `@given(...)`
    decorator. The check must walk the parse subtree, observe
    the missing `@given`, exit non-zero, and surface the offending
    path.
    """
    parse_dir = tmp_path / "tests" / "livespec" / "parse"
    parse_dir.mkdir(parents=True)
    (parse_dir / "test_jsonc.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def test_plain() -> None:\n"
        "    assert True\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PBT_COVERAGE_PURE_MODULES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"pbt_coverage_pure_modules should reject parse-tree test with no @given; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = "tests/livespec/parse/test_jsonc.py"
    assert expected_path in combined, (
        f"pbt_coverage_pure_modules diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_pbt_coverage_pure_modules_accepts_test_with_given(*, tmp_path: Path) -> None:
    """A `tests/livespec/validate/test_*.py` with at least one `@given` is accepted.

    Fixture: `tests/livespec/validate/test_finding.py` declares
    one `@given(...)`-decorated test function. The check must
    walk, observe the decorator, and exit 0.
    """
    validate_dir = tmp_path / "tests" / "livespec" / "validate"
    validate_dir.mkdir(parents=True)
    (validate_dir / "test_finding.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "from hypothesis import given\n"
        "from hypothesis import strategies as st\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@given(x=st.integers())\n"
        "def test_property(*, x: int) -> None:\n"
        "    assert isinstance(x, int)\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_PBT_COVERAGE_PURE_MODULES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"pbt_coverage_pure_modules should accept validate-tree test with @given; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
