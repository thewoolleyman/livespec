"""Outside-in test for `dev-tooling/checks/keyword_only_args.py` — `*`-separator + strict-dataclass triple.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-keyword-only-args` row), every `def`
in `livespec/**` uses `*` as the first separator (all
parameters keyword-only); every `@dataclass` declares
`frozen=True, kw_only=True, slots=True`. Exempts Python-
mandated dunder signatures and `__init__` of Exception
subclasses that forward to `super().__init__(msg)`.

Cycle 154 implements the `def`-level check (kw-only
separator on every regular function); subsequent cycles can
widen to the dataclass-strict-triple verification when
fixtures demand it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_KEYWORD_ONLY_ARGS = _REPO_ROOT / "dev-tooling" / "checks" / "keyword_only_args.py"


def test_keyword_only_args_rejects_def_with_positional_arg(*, tmp_path: Path) -> None:
    """A `def fn(x: int):` (positional arg, no `*` separator) fails the check.

    Fixture: `.claude-plugin/scripts/livespec/foo.py` defines
    `def fn(x: int) -> int`. The check must walk the livespec
    subtree, parse the file, detect the missing `*`, exit
    non-zero, and surface the file plus line number plus
    function name.
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
        "def fn(x: int) -> int:\n"
        "    return x\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_KEYWORD_ONLY_ARGS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"keyword_only_args should reject positional arg with non-zero exit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/foo.py"
    assert expected_path in combined, (
        f"keyword_only_args diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "fn" in combined, (
        f"keyword_only_args diagnostic does not surface offending function name `fn`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_keyword_only_args_accepts_def_with_kw_only_separator(*, tmp_path: Path) -> None:
    """A `def fn(*, x: int):` (kw-only separator present) passes the check (exit 0).

    Pass-case: a livespec function with the `*` separator and
    every parameter keyword-only.
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
        "def fn(*, x: int) -> int:\n"
        "    return x\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_KEYWORD_ONLY_ARGS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"keyword_only_args should accept kw-only def with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_keyword_only_args_accepts_zero_arg_def(*, tmp_path: Path) -> None:
    """A `def fn() -> int` (no args) passes the check (exit 0).

    Zero-arg functions are trivially keyword-only-safe.
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
        "def fn() -> int:\n"
        "    return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_KEYWORD_ONLY_ARGS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"keyword_only_args should accept zero-arg def with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_keyword_only_args_accepts_dunder_methods(*, tmp_path: Path) -> None:
    """Dunder methods (`__init__`, `__call__`, etc.) are exempt from the check.

    Pass-case: `def __init__(self, msg: str) -> None` is
    Python-mandated positional and exempt per the canonical
    row's exemption clause.
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
        "    def __init__(self, msg: str) -> None:\n"
        "        self.msg = msg\n"
        "\n"
        "    def __repr__(self) -> str:\n"
        '        return f"Foo({self.msg!r})"\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_KEYWORD_ONLY_ARGS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"keyword_only_args should exempt dunder methods with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_keyword_only_args_accepts_method_with_self_then_kw_only(*, tmp_path: Path) -> None:
    """A method `def m(self, *, x: int)` (self + kw-only) passes the check (exit 0).

    Methods on classes have an implicit positional `self` (or
    `cls` for classmethods). The check tolerates a single
    `self`/`cls` first parameter when followed by the `*`
    separator and all-keyword-only thereafter.
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
        "    def m(self, *, x: int) -> int:\n"
        "        return x\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_KEYWORD_ONLY_ARGS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"keyword_only_args should accept self+kw-only method with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_keyword_only_args_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes the check (exit 0)."""
    result = subprocess.run(
        [sys.executable, str(_KEYWORD_ONLY_ARGS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"keyword_only_args should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_keyword_only_args_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "keyword_only_args_for_import_test",
        str(_KEYWORD_ONLY_ARGS),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
