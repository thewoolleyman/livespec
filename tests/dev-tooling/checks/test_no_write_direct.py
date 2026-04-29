"""Outside-in test for `dev-tooling/checks/no_write_direct.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` line 2092:

    AST: bans `sys.stdout.write` and `sys.stderr.write` calls
    in `.claude-plugin/scripts/livespec/**`,
    `.claude-plugin/scripts/bin/**`,
    `<repo-root>/dev-tooling/**`. Three exemptions:
    `bin/_bootstrap.py` (pre-import version-check stderr);
    supervisor `main()` functions in
    `livespec/commands/**.py` (any documented stdout contract);
    `livespec/doctor/run_static.py::main()` (findings JSON
    stdout). Pairs with ruff `T20` which bans `print` / `pprint`.

Cycle 43 pins the canonical violation: a `sys.stderr.write(...)`
call in a non-exempt module is rejected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NO_WRITE = _REPO_ROOT / "dev-tooling" / "checks" / "no_write_direct.py"


def test_no_write_direct_rejects_sys_stderr_write_in_pure_module(*, tmp_path: Path) -> None:
    """`sys.stderr.write(...)` in a non-exempt livespec module is rejected.

    Fixture: `.claude-plugin/scripts/livespec/parse/parser.py`
    contains a `sys.stderr.write("oops")` call. The check,
    invoked with `cwd=tmp_path`, must walk the in-scope trees,
    detect the violation, exit non-zero, and surface the
    offending module path.
    """
    parse_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    parse_dir.mkdir(parents=True)
    (parse_dir / "parser.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "import sys\n"
        "\n"
        '__all__: list[str] = ["parse"]\n'
        "\n"
        "\n"
        "def parse() -> int:\n"
        '    sys.stderr.write("oops")\n'
        "    return 0\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_WRITE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_write_direct should reject `sys.stderr.write(...)` in non-exempt module; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/parse/parser.py"
    assert expected_path in combined, (
        f"no_write_direct diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_write_direct_accepts_clean_module(*, tmp_path: Path) -> None:
    """A livespec module without any `sys.std{out,err}.write` is accepted.

    Fixture: a livespec module declaring a function that does
    NOT call `sys.stderr.write` or `sys.stdout.write`. The
    check must walk the tree and exit 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "clean.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["f"]\n'
        "\n"
        "\n"
        "def f(*, x: int) -> int:\n"
        "    return x\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_WRITE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_write_direct should accept module with no direct stream writes; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_write_direct_accepts_bootstrap_stderr_write(*, tmp_path: Path) -> None:
    """`sys.stderr.write(...)` in `bin/_bootstrap.py` is permitted (exemption).

    Per spec line 2092 the first exemption is
    `bin/_bootstrap.py` for the pre-import version-check error
    message. structlog has not been configured at that point,
    so direct stderr write is the only option. The check must
    walk the bin tree and exit 0 even when `_bootstrap.py`
    carries the call.
    """
    bin_dir = tmp_path / ".claude-plugin" / "scripts" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "_bootstrap.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "import sys\n"
        "\n"
        '__all__: list[str] = ["bootstrap"]\n'
        "\n"
        "\n"
        "def bootstrap() -> None:\n"
        '    sys.stderr.write("python 3.10+ required\\n")\n',
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_WRITE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_write_direct should accept `sys.stderr.write` in bin/_bootstrap.py; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
