"""Outside-in test for `dev-tooling/checks/wrapper_shape.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` lines 1937-1968
the canonical shebang-wrapper shape under
`.claude-plugin/scripts/bin/*.py` (excluding `_bootstrap.py`)
is exactly:

    #!/usr/bin/env python3
    \"\"\"Shebang wrapper for <description>. No logic; see livespec.<...> for implementation.\"\"\"

    from _bootstrap import bootstrap

    bootstrap()

    from livespec.<module>.<submodule> import main

    raise SystemExit(main())

Five top-level Python statements (docstring expression,
`ImportFrom _bootstrap`, `Expr(Call(bootstrap))`,
`ImportFrom livespec.<...>`, `Raise(Call(SystemExit, Call(main)))`)
plus the comment shebang line. The optional single blank line
between the import block and the final `raise` is permitted (per
v016 P5) but does NOT count as a statement.

`check-wrapper-shape` (line 2085) is described as AST-lite; it
verifies each `bin/*.py` (except `_bootstrap.py`) conforms. Each
cycle pins one specific violation pattern. Cycle 35 pins the
canonical "extra logic" violation: a wrapper with a stray
statement injected between `bootstrap()` and the
`from livespec.<...> import main` import is rejected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_WRAPPER_SHAPE = _REPO_ROOT / "dev-tooling" / "checks" / "wrapper_shape.py"


_CANONICAL_WRAPPER = (
    "#!/usr/bin/env python3\n"
    '"""Shebang wrapper for example. No logic; see livespec.commands."""\n'
    "\n"
    "from _bootstrap import bootstrap\n"
    "\n"
    "bootstrap()\n"
    "\n"
    "from livespec.commands.example import main\n"
    "\n"
    "raise SystemExit(main())\n"
)


def test_wrapper_shape_rejects_wrapper_with_extra_statement(*, tmp_path: Path) -> None:
    """An extra top-level statement in a `bin/*.py` wrapper is rejected.

    Fixture: `.claude-plugin/scripts/bin/example.py` whose body
    has a 6th top-level statement injected between
    `bootstrap()` and `from livespec.commands.example import main`
    (an extra `import os`). The canonical shape forbids any
    statement other than the five listed (plus shebang +
    optional blank lines), so the check must reject this with
    non-zero exit and surface the offending wrapper path.
    """
    bin_dir = tmp_path / ".claude-plugin" / "scripts" / "bin"
    bin_dir.mkdir(parents=True)
    bad_wrapper = bin_dir / "example.py"
    bad_wrapper.write_text(
        "#!/usr/bin/env python3\n"
        '"""Shebang wrapper for example. No logic; see livespec.commands."""\n'
        "\n"
        "from _bootstrap import bootstrap\n"
        "\n"
        "bootstrap()\n"
        "\n"
        "import os  # stray extra statement — violation\n"
        "\n"
        "from livespec.commands.example import main\n"
        "\n"
        "raise SystemExit(main())\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_WRAPPER_SHAPE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"wrapper_shape should reject wrapper with extra statement; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/bin/example.py"
    assert expected_path in combined, (
        f"wrapper_shape diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_wrapper_shape_accepts_canonical_wrapper(*, tmp_path: Path) -> None:
    """A `bin/example.py` matching the canonical 5-statement shape is accepted.

    Fixture: a `.claude-plugin/scripts/bin/example.py` with the
    exact canonical body (docstring, `from _bootstrap import
    bootstrap`, `bootstrap()`, `from livespec.commands.example
    import main`, `raise SystemExit(main())`) plus the optional
    blank line between the import block and the final raise
    (v016 P5). The check must walk the bin tree and exit 0.
    """
    bin_dir = tmp_path / ".claude-plugin" / "scripts" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "example.py").write_text(_CANONICAL_WRAPPER, encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_WRAPPER_SHAPE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"wrapper_shape should accept canonical wrapper with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_wrapper_shape_skips_bootstrap_module(*, tmp_path: Path) -> None:
    """`bin/_bootstrap.py` is exempt from the wrapper-shape check.

    Per spec line 1939 (`bin/*.py` shape applies "except
    `_bootstrap.py`") and the bin/CLAUDE.md ("the one exception
    to the wrapper shape"), the bootstrap module carries the
    Python-version-check + sys.path-setup logic and explicitly
    does NOT conform to the 5-statement shape. The check must
    not flag it even when it has many statements.
    """
    bin_dir = tmp_path / ".claude-plugin" / "scripts" / "bin"
    bin_dir.mkdir(parents=True)
    # `_bootstrap.py` deliberately deviates: imports + version
    # check + sys.path mutation. The check must skip it.
    (bin_dir / "_bootstrap.py").write_text(
        "#!/usr/bin/env python3\n"
        '"""Bootstrap module: sys.path setup + Python-version gate."""\n'
        "\n"
        "import sys\n"
        "\n"
        "if sys.version_info < (3, 10):\n"
        "    raise SystemExit(127)\n"
        "\n"
        "\n"
        "def bootstrap() -> None:\n"
        "    return None\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_WRAPPER_SHAPE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"wrapper_shape should skip _bootstrap.py and exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
