"""Outside-in test for `dev-tooling/checks/match_keyword_only.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` line 2087:

    AST: every `match` statement's class pattern resolving to a
    livespec-authored class binds via keyword sub-patterns
    (`Foo(x=x)`), not positional (`Foo(x)`). Third-party
    library class destructures (`returns`-package types) are
    permitted positionally.

The intent: positional class destructures rely on
`__match_args__` ordering, which is fragile and tightly couples
the producer's field order to every consumer call site. Keyword
destructures decouple them and make the dependency explicit.

Cycle 41 pins the canonical violation: a `case Foo(x):`
positional class pattern (where `Foo` is a livespec-authored
name — recognized by being neither a `returns`-package type
nor a Python builtin) is rejected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_MATCH_KW = _REPO_ROOT / "dev-tooling" / "checks" / "match_keyword_only.py"


def test_match_keyword_only_rejects_positional_class_pattern(*, tmp_path: Path) -> None:
    """`case Foo(x):` (positional class pattern) on a livespec class is rejected.

    Fixture: `.claude-plugin/scripts/livespec/handlers.py`
    contains a `match value: case Foo(x): ...` block. The
    positional sub-pattern `(x)` is the violation. The check,
    invoked with `cwd=tmp_path`, must walk the livespec tree,
    detect the pattern, exit non-zero, and surface the
    offending module path.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "handlers.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["dispatch"]\n'
        "\n"
        "\n"
        "class Foo:\n"
        '    __match_args__ = ("x",)\n'
        "    x: int\n"
        "\n"
        "\n"
        "def dispatch(*, value: object) -> int:\n"
        "    match value:\n"
        "        case Foo(x):\n"
        "            return x\n"
        "        case _:\n"
        "            return -1\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_MATCH_KW)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"match_keyword_only should reject `case Foo(x):` positional pattern; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/handlers.py"
    assert expected_path in combined, (
        f"match_keyword_only diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_match_keyword_only_accepts_keyword_class_pattern(*, tmp_path: Path) -> None:
    """`case Foo(x=x):` (keyword class pattern) is accepted.

    Fixture: same module as above but the case uses
    `case Foo(x=x):` (keyword sub-pattern). The check must
    walk the tree and exit 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "handlers.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["dispatch"]\n'
        "\n"
        "\n"
        "class Foo:\n"
        "    x: int\n"
        "\n"
        "\n"
        "def dispatch(*, value: object) -> int:\n"
        "    match value:\n"
        "        case Foo(x=x):\n"
        "            return x\n"
        "        case _:\n"
        "            return -1\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_MATCH_KW)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"match_keyword_only should accept `case Foo(x=x):` keyword pattern; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_match_keyword_only_accepts_returns_lib_positional(*, tmp_path: Path) -> None:
    """`case IOSuccess(value):` (returns-package type) is permitted positionally.

    Per spec line 2087: "Third-party library class destructures
    (`returns`-package types) are permitted positionally."
    Fixture: a livespec module destructuring `IOSuccess(value)`
    positionally — the dry-python/returns ROP types are the
    canonical exemption.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "handlers.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "from returns.io import IOFailure, IOSuccess\n"
        "\n"
        '__all__: list[str] = ["dispatch"]\n'
        "\n"
        "\n"
        "def dispatch(*, value: object) -> int:\n"
        "    match value:\n"
        "        case IOSuccess(v):\n"
        "            return 0\n"
        "        case IOFailure(e):\n"
        "            return 1\n"
        "        case _:\n"
        "            return -1\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_MATCH_KW)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"match_keyword_only should accept positional returns-pkg destructures; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
