"""Outside-in test for `dev-tooling/checks/no_raise_outside_io.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` line 2080
(and lines 554-560 of the railway-vs-bugs split):

    AST: raising of `LivespecError` subclasses (domain errors)
    at runtime restricted to `io/**` and `errors.py`. Raising
    bug-class exceptions (TypeError, NotImplementedError,
    AssertionError, etc.) permitted anywhere. **Raise-site
    enforcement is the sole enforcement point for the
    raise-discipline (v017 Q3 retraction of the v012 L15a
    import-surface delegation).**

Per v017 Q3 the check is raise-site only; Import-Linter does
NOT cover the import surface for `livespec.errors`. Type-
annotation imports of `LivespecError` subclasses are permitted
anywhere (they don't raise).

Each cycle pins one specific violation pattern. Cycle 39 pins
the canonical case: a `raise LivespecError(...)` inside a
livespec module that is NOT `livespec/io/**` and NOT
`livespec/errors.py` is rejected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NO_RAISE = _REPO_ROOT / "dev-tooling" / "checks" / "no_raise_outside_io.py"


def test_no_raise_outside_io_rejects_livespec_error_in_pure_module(*, tmp_path: Path) -> None:
    """`raise LivespecError(...)` inside a non-`io/` non-`errors.py` module is rejected.

    Fixture: `.claude-plugin/scripts/livespec/parse/parser.py`
    contains a `raise LivespecError("nope")` call. Per spec
    lines 554-560 the parse layer is purely on the Result
    railway; raising a domain error there violates the
    raise-discipline. The check, invoked with `cwd=tmp_path`,
    must walk the livespec tree, detect the violation, exit
    non-zero, and surface the offending module path.
    """
    parse_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    parse_dir.mkdir(parents=True)
    (parse_dir / "parser.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["parse"]\n'
        "\n"
        "\n"
        "def parse() -> int:\n"
        '    raise LivespecError("nope")\n',
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_RAISE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_raise_outside_io should reject `raise LivespecError(...)` in non-io module; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/parse/parser.py"
    assert expected_path in combined, (
        f"no_raise_outside_io diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_raise_outside_io_accepts_livespec_error_in_io_module(*, tmp_path: Path) -> None:
    """`raise LivespecError(...)` inside `livespec/io/**` is accepted.

    Per spec line 555 the `io/**` subtree is the legitimate
    raise-site for `LivespecError` subclasses. Fixture: a
    `livespec/io/fs.py` raising `LivespecError(...)`. The check
    must walk the tree and exit 0.
    """
    io_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "io"
    io_dir.mkdir(parents=True)
    (io_dir / "fs.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["read"]\n'
        "\n"
        "\n"
        "def read() -> int:\n"
        '    raise LivespecError("io error")\n',
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_RAISE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_raise_outside_io should accept LivespecError raise in livespec/io/; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_raise_outside_io_accepts_bug_class_exception_anywhere(*, tmp_path: Path) -> None:
    """`raise TypeError(...)` etc. (bug-class exceptions) are accepted anywhere.

    Per spec lines 556-560 bug-class exceptions (TypeError,
    NotImplementedError, AssertionError, RuntimeError, etc.)
    are permitted ANYWHERE because they signal bugs, not
    domain failures. The check must distinguish these from
    LivespecError subclasses by name.

    Fixture: `livespec/parse/parser.py` raising `TypeError("...")`
    — accepted because `TypeError` is a bug-class name.
    """
    parse_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    parse_dir.mkdir(parents=True)
    (parse_dir / "parser.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["parse"]\n'
        "\n"
        "\n"
        "def parse() -> int:\n"
        '    raise TypeError("bug")\n',
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_RAISE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_raise_outside_io should accept `raise TypeError(...)` anywhere; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
