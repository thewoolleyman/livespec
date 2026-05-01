"""Outside-in test for `dev-tooling/checks/no_inheritance.py` — direct-parent allowlist enforcement.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-no-inheritance` row), `class X(Y):` in
`.claude-plugin/scripts/livespec/**` is forbidden when `Y` is
not in the direct-parent allowlist `{Exception, BaseException,
LivespecError, Protocol, NamedTuple, TypedDict}`. Codifies
flat-composition direction; `LivespecError` itself remains an
open extension point. `LivespecError` subclasses are NOT
acceptable bases (v013 M5 tightening — `class
RateLimitError(UsageError):` is rejected even though
`UsageError` is itself a `LivespecError` subclass).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NO_INHERITANCE = _REPO_ROOT / "dev-tooling" / "checks" / "no_inheritance.py"


def test_no_inheritance_rejects_disallowed_base_class(*, tmp_path: Path) -> None:
    """A `class Foo(Bar):` with `Bar` outside the allowlist fails the check.

    Fixture: `.claude-plugin/scripts/livespec/foo.py` defines
    `class Foo(Bar):` where `Bar` is a hand-rolled application
    class (not in the closed allowlist). The check, invoked
    with `cwd=tmp_path`, must walk the livespec subtree, parse
    the file, detect the disallowed base, exit non-zero, and
    surface the offending file plus line number.
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
        "class Bar:\n"
        "    pass\n"
        "\n"
        "\n"
        "class Foo(Bar):\n"
        "    pass\n",
        encoding="utf-8",
    )

    # S603: argv is fixed; no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_INHERITANCE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_inheritance should reject `class Foo(Bar):` with non-zero exit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/foo.py"
    assert expected_path in combined, (
        f"no_inheritance diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    # Line 10 is the `class Foo(Bar):` line in the fixture.
    assert "10" in combined, (
        f"no_inheritance diagnostic does not surface offending line number 10; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_inheritance_accepts_allowlisted_base_classes(*, tmp_path: Path) -> None:
    """Classes deriving from `Exception`, `Protocol`, etc., pass the check (exit 0).

    Pass-case: each of the allowlist entries (Exception,
    BaseException, LivespecError, Protocol, NamedTuple,
    TypedDict) is a permitted direct parent. Fixture writes a
    file using `class FooError(Exception):` and `class
    FooProto(Protocol):`. The check walks the file and exits 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from typing import Protocol\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "class FooError(Exception):\n"
        "    pass\n"
        "\n"
        "\n"
        "class FooProto(Protocol):\n"
        "    def bar(self) -> None: ...\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_INHERITANCE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_inheritance should accept allowlist parents with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_inheritance_accepts_tree_without_livespec_directory(*, tmp_path: Path) -> None:
    """A repo cwd without `.claude-plugin/scripts/livespec/` passes the check (exit 0).

    Closes the `if livespec_root.is_dir():` False arm: tmp_path
    is empty, so main() short-circuits without walking.
    """
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_INHERITANCE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_inheritance should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_inheritance_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main().

    Closes the `_VENDOR_DIR` already-present branch and the
    `if __name__ == "__main__":` else-arm for per-file 100%.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "no_inheritance_for_import_test", str(_NO_INHERITANCE),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
