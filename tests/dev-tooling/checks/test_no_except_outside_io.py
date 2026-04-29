"""Outside-in test for `dev-tooling/checks/no_except_outside_io.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` line 2081:

    AST: catching exceptions outside `io/**` permitted only in
    supervisor bug-catchers (top-level `try/except Exception`
    in `main()` of `commands/*.py` and `doctor/run_static.py`).

The intent: domain-meaningful exceptions are wrapped at the IO
boundary into the Result railway; pure layers (parse, validate)
NEVER catch exceptions because there's nothing to catch (no
raise sites in those layers). Supervisors carry the one
permitted catch-all `except Exception` for bug-class crashes.

Cycle 40 pins the canonical violation: a `try/except` block in
a pure (non-`io/`, non-supervisor) module is rejected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NO_EXCEPT = _REPO_ROOT / "dev-tooling" / "checks" / "no_except_outside_io.py"


def test_no_except_outside_io_rejects_try_except_in_pure_module(*, tmp_path: Path) -> None:
    """`try/except` inside a non-`io/` non-supervisor module is rejected.

    Fixture: `.claude-plugin/scripts/livespec/parse/parser.py`
    contains a `try: ... except Exception: ...` block. The
    parse layer is pure-railway; catching exceptions there
    violates the discipline. The check, invoked with
    `cwd=tmp_path`, must walk the livespec tree, detect the
    `Try` node, exit non-zero, and surface the offending
    module path.
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
        "    try:\n"
        "        return 1\n"
        "    except Exception:\n"
        "        return 0\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_EXCEPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_except_outside_io should reject try/except in non-io module; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/parse/parser.py"
    assert expected_path in combined, (
        f"no_except_outside_io diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_except_outside_io_accepts_try_except_in_io_module(*, tmp_path: Path) -> None:
    """`try/except` inside `livespec/io/**` is accepted.

    Per spec line 2081 the `io/**` subtree is the legitimate
    catch-site (it wraps third-party domain-meaningful
    exceptions into Result/IOResult). Fixture: `livespec/io/
    fs.py` with a `try/except FileNotFoundError`. The check
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
        "    try:\n"
        "        return 1\n"
        "    except FileNotFoundError:\n"
        "        return 0\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_EXCEPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_except_outside_io should accept try/except in livespec/io/; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_except_outside_io_accepts_supervisor_bug_catcher(*, tmp_path: Path) -> None:
    """Supervisor `main()` in `commands/<cmd>.py` may carry a `try/except Exception` bug-catcher.

    Per spec line 2081 the bug-catcher pattern is permitted
    only inside `main()` of `commands/<cmd>.py` and
    `doctor/run_static.py`. Fixture: `livespec/commands/seed.py`
    whose `def main() -> int:` body wraps the chain in
    `try/except Exception`. The check must NOT flag it.
    """
    cmd_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "seed.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["main"]\n'
        "\n"
        "\n"
        "def main() -> int:\n"
        "    try:\n"
        "        return 0\n"
        "    except Exception:\n"
        "        return 1\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_EXCEPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_except_outside_io should accept supervisor bug-catcher in commands/<cmd>.py; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
