"""Outside-in test for `dev-tooling/checks/no_inheritance.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` line 2088:

    AST: forbids `class X(Y):` in
    `.claude-plugin/scripts/livespec/**` where `Y` is not in
    the **direct-parent allowlist** `{Exception, BaseException,
    LivespecError, Protocol, NamedTuple, TypedDict}`.
    `LivespecError` subclasses are NOT acceptable bases (v013
    M5 tightening enforces leaf-closed intent); `class
    RateLimitError(UsageError):` is rejected even though
    `UsageError` is itself a `LivespecError` subclass.

The rule encodes the no-inheritance discipline. Each cycle pins
one specific violation pattern. Cycle 38 pins the canonical
case: a class extending an arbitrary user class (not in the
allowlist) inside `.claude-plugin/scripts/livespec/**` is
rejected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NO_INHERITANCE = _REPO_ROOT / "dev-tooling" / "checks" / "no_inheritance.py"


def test_no_inheritance_rejects_subclass_of_arbitrary_class(*, tmp_path: Path) -> None:
    """`class Bar(Foo):` where `Foo` is not in the allowlist is rejected.

    Fixture: `.claude-plugin/scripts/livespec/has_inheritance.py`
    declares `class Bar(Foo):` where `Foo` is a user class
    declared in the same module. `Foo` is NOT in the allowlist
    `{Exception, BaseException, LivespecError, Protocol,
    NamedTuple, TypedDict}`, so the inheritance is forbidden.
    The check, invoked with `cwd=tmp_path`, must walk the
    livespec tree, detect the violation, exit non-zero, and
    surface the offending module path.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "has_inheritance.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["Bar"]\n'
        "\n"
        "\n"
        "class Foo:\n"
        "    pass\n"
        "\n"
        "\n"
        "class Bar(Foo):\n"
        "    pass\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_INHERITANCE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_inheritance should reject `class Bar(Foo):` where Foo is not in allowlist; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/has_inheritance.py"
    assert expected_path in combined, (
        f"no_inheritance diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_inheritance_accepts_class_with_no_bases(*, tmp_path: Path) -> None:
    """A `class Foo:` with no explicit bases is accepted.

    Fixture: `.claude-plugin/scripts/livespec/clean.py`
    declares `class Foo:` (implicitly subclasses `object`,
    which is the no-inheritance default and not under the rule's
    purview). The check must walk the tree and exit 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "clean.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["Foo"]\n'
        "\n"
        "\n"
        "class Foo:\n"
        "    pass\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_INHERITANCE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_inheritance should accept `class Foo:` with no explicit bases; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_inheritance_accepts_subclass_of_protocol(*, tmp_path: Path) -> None:
    """`class Foo(Protocol):` is accepted (Protocol is in the allowlist).

    Per spec line 2088 the direct-parent allowlist explicitly
    includes `Protocol`. Structural typing via `typing.Protocol`
    is the canonical no-inheritance livespec pattern, so the
    check must NOT flag a `class X(Protocol):` declaration.

    Fixture: a livespec module with `from typing import
    Protocol` and `class Foo(Protocol):`. The check must walk
    the tree and exit 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "with_protocol.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "from typing import Protocol\n"
        "\n"
        '__all__: list[str] = ["Foo"]\n'
        "\n"
        "\n"
        "class Foo(Protocol):\n"
        "    def x(self) -> int: ...\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_INHERITANCE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_inheritance should accept `class Foo(Protocol):`; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
