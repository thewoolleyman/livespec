"""Outside-in test for `dev-tooling/checks/match_keyword_only.py` — keyword-pattern destructuring on livespec classes.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-match-keyword-only` row), every
`match` statement's class pattern resolving to a livespec-
authored class binds via keyword sub-patterns (`Foo(x=x)`),
not positional (`Foo(x)`). Third-party library class
destructures (the `returns` package's types — `Success`,
`Failure`, `IOSuccess`, `IOFailure`) are permitted
positionally because their `__match_args__` is fixed by
upstream.

Cycle 155 implements the core rule: detect positional class
patterns where the class name is NOT in the third-party
allowlist.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_MATCH_KEYWORD_ONLY = _REPO_ROOT / "dev-tooling" / "checks" / "match_keyword_only.py"


def test_match_keyword_only_rejects_positional_class_pattern_for_livespec_class(
    *, tmp_path: Path,
) -> None:
    """A `case Foo(x):` (positional) on a livespec class fails the check.

    Fixture: a livespec module with `match val: case Foo(x):
    ...` where `Foo` is a hand-rolled application class.
    Banned — keyword-pattern destructuring is required.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from typing_extensions import assert_never\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "class Foo:\n"
        "    pass\n"
        "\n"
        "\n"
        "def handle(val: object) -> int:\n"
        "    match val:\n"
        "        case Foo(x):\n"
        "            return x\n"
        "        case _:\n"
        "            assert_never(val)\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_MATCH_KEYWORD_ONLY)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"match_keyword_only should reject positional class pattern; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/foo.py"
    assert expected_path in combined, (
        f"match_keyword_only diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_match_keyword_only_accepts_keyword_class_pattern(*, tmp_path: Path) -> None:
    """A `case Foo(x=x):` (keyword) on a livespec class passes (exit 0).

    Pass-case: keyword-pattern destructuring binds via kwargs
    rather than positional `__match_args__`.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from typing_extensions import assert_never\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "class Foo:\n"
        "    pass\n"
        "\n"
        "\n"
        "def handle(val: object) -> int:\n"
        "    match val:\n"
        "        case Foo(x=x):\n"
        "            return x\n"
        "        case _:\n"
        "            assert_never(val)\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_MATCH_KEYWORD_ONLY)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"match_keyword_only should accept keyword class pattern with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_match_keyword_only_accepts_returns_positional_class_pattern(
    *, tmp_path: Path,
) -> None:
    """A `case Success(x):` / `case IOSuccess(x):` (positional) is permitted.

    Pass-case: third-party `returns`-package types are
    explicitly allowed positional destructuring (their
    `__match_args__` is upstream-fixed).
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from returns.io import IOFailure, IOSuccess\n"
        "from returns.result import Failure, Success\n"
        "from typing_extensions import assert_never\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def handle(val: object) -> int:\n"
        "    match val:\n"
        "        case Success(x):\n"
        "            return 0\n"
        "        case Failure(x):\n"
        "            return 1\n"
        "        case IOSuccess(x):\n"
        "            return 2\n"
        "        case IOFailure(x):\n"
        "            return 3\n"
        "        case _:\n"
        "            assert_never(val)\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_MATCH_KEYWORD_ONLY)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"match_keyword_only should accept returns-package positional patterns; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_match_keyword_only_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes the check (exit 0)."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_MATCH_KEYWORD_ONLY)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"match_keyword_only should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_match_keyword_only_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "match_keyword_only_for_import_test", str(_MATCH_KEYWORD_ONLY),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
