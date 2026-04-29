"""Outside-in test for `dev-tooling/checks/supervisor_discipline.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` line 2079:

    AST: `sys.exit` / `raise SystemExit` only in `bin/*.py`
    (incl. `_bootstrap.py`).

The supervisor pattern: `bin/*.py` wrappers raise SystemExit
with the integer return of `main()`; the livespec library code
never directly invokes `sys.exit` or raises SystemExit. Domain
errors flow through the Result railway and are converted to
exit codes by the supervisor.

Cycle 44 pins the canonical violation: a `sys.exit(...)` call
inside `livespec/**` is rejected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_SUPERVISOR = _REPO_ROOT / "dev-tooling" / "checks" / "supervisor_discipline.py"


def test_supervisor_discipline_rejects_sys_exit_in_livespec_module(*, tmp_path: Path) -> None:
    """`sys.exit(...)` inside `livespec/**` is rejected.

    Fixture: `.claude-plugin/scripts/livespec/escape.py`
    contains a `sys.exit(1)` call. Per spec line 2079 only
    `bin/*.py` may exit; livespec library code returns through
    the Result railway. The check, invoked with `cwd=tmp_path`,
    must walk the livespec tree, detect the violation, exit
    non-zero, and surface the offending module path.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "escape.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "import sys\n"
        "\n"
        '__all__: list[str] = ["go"]\n'
        "\n"
        "\n"
        "def go() -> None:\n"
        "    sys.exit(1)\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SUPERVISOR)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"supervisor_discipline should reject `sys.exit(...)` in livespec module; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/escape.py"
    assert expected_path in combined, (
        f"supervisor_discipline diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_supervisor_discipline_rejects_raise_systemexit_in_livespec(*, tmp_path: Path) -> None:
    """`raise SystemExit(...)` inside `livespec/**` is rejected.

    Fixture: `.claude-plugin/scripts/livespec/escape2.py`
    contains a `raise SystemExit(1)` statement. Per spec line
    2079 SystemExit raises are restricted to `bin/*.py`. The
    check must reject this with non-zero exit.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "escape2.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["go"]\n'
        "\n"
        "\n"
        "def go() -> None:\n"
        "    raise SystemExit(1)\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SUPERVISOR)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"supervisor_discipline should reject `raise SystemExit(...)` in livespec module; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/escape2.py"
    assert expected_path in combined, (
        f"supervisor_discipline diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_supervisor_discipline_accepts_raise_systemexit_in_bin_wrapper(*, tmp_path: Path) -> None:
    """`raise SystemExit(main())` in `bin/<cmd>.py` is the canonical wrapper exit.

    Per spec line 2079 the `bin/*.py` tree (including
    `_bootstrap.py`) is the legitimate location for SystemExit
    raises. The 6-statement wrapper shape ends in
    `raise SystemExit(main())`. The check must walk the bin
    tree and exit 0.
    """
    bin_dir = tmp_path / ".claude-plugin" / "scripts" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "seed.py").write_text(
        "#!/usr/bin/env python3\n"
        '"""Shebang wrapper for seed."""\n'
        "\n"
        "from _bootstrap import bootstrap\n"
        "\n"
        "bootstrap()\n"
        "\n"
        "from livespec.commands.seed import main\n"
        "\n"
        "raise SystemExit(main())\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SUPERVISOR)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"supervisor_discipline should accept SystemExit in bin/<cmd>.py wrapper; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
