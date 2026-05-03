"""Outside-in test for `dev-tooling/checks/supervisor_discipline.py` — `sys.exit`/`SystemExit` confined to `bin/`.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-supervisor-discipline` row), `sys.exit
(...)` calls and `raise SystemExit(...)` statements are
permitted only in `.claude-plugin/scripts/bin/*.py` (including
`_bootstrap.py`). Anywhere else under
`.claude-plugin/scripts/livespec/**`, both forms are banned —
only the supervisor-at-the-edge surface terminates the process.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_SUPERVISOR_DISCIPLINE = _REPO_ROOT / "dev-tooling" / "checks" / "supervisor_discipline.py"


def test_supervisor_discipline_rejects_sys_exit_in_livespec(*, tmp_path: Path) -> None:
    """A `sys.exit(...)` call inside livespec/ fails the check.

    Fixture: `.claude-plugin/scripts/livespec/foo.py` calls
    `sys.exit(0)` inside a function. The check must walk the
    livespec subtree, parse the file, detect the banned call,
    exit non-zero, and surface the offending file plus line
    number.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "import sys\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def quit_now() -> None:\n"
        "    sys.exit(0)\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_SUPERVISOR_DISCIPLINE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"supervisor_discipline should reject sys.exit() in livespec; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/foo.py"
    assert expected_path in combined, (
        f"supervisor_discipline diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "9" in combined, (
        f"supervisor_discipline diagnostic does not surface offending line number 9; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_supervisor_discipline_rejects_raise_systemexit_in_livespec(*, tmp_path: Path) -> None:
    """A `raise SystemExit(...)` inside livespec/ fails the check.

    Fixture: livespec/foo.py raises SystemExit. The check
    detects this banned form and surfaces it.
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
        "def quit_now() -> None:\n"
        "    raise SystemExit(0)\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_SUPERVISOR_DISCIPLINE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"supervisor_discipline should reject raise SystemExit in livespec; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_supervisor_discipline_accepts_sys_exit_inside_bin(*, tmp_path: Path) -> None:
    """A `sys.exit(...)` call inside bin/ passes the check (exit 0).

    Pass-case: `.claude-plugin/scripts/bin/foo.py` is a
    shebang wrapper that legitimately raises SystemExit. The
    check walks the bin subtree but skips it (or treats the
    call as exempt).
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "bin"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    return 0\n"
        "\n"
        "\n"
        "raise SystemExit(main())\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_SUPERVISOR_DISCIPLINE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"supervisor_discipline should accept SystemExit in bin/ with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_supervisor_discipline_accepts_clean_livespec(*, tmp_path: Path) -> None:
    """A livespec module with no sys.exit/SystemExit passes the check (exit 0).

    Pass-case: a livespec module that follows ROP discipline,
    returning Result rather than terminating the process. The
    fixture also includes a non-SystemExit `raise` (`raise
    ValueError(...)`) and a bare `raise` inside an except
    block — both pass through the SystemExit-only filter and
    exercise the False branch of the `node.exc is not None`
    + name-match condition.
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
        "def fail() -> None:\n"
        '    raise ValueError("nope")\n'
        "\n"
        "\n"
        "def reraise() -> None:\n"
        "    try:\n"
        "        fail()\n"
        "    except ValueError:\n"
        "        raise\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_SUPERVISOR_DISCIPLINE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"supervisor_discipline should accept clean livespec with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_supervisor_discipline_accepts_empty_tree(*, tmp_path: Path) -> None:
    """A repo cwd without `.claude-plugin/scripts/livespec/` passes the check (exit 0)."""
    result = subprocess.run(
        [sys.executable, str(_SUPERVISOR_DISCIPLINE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"supervisor_discipline should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_supervisor_discipline_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "supervisor_discipline_for_import_test", str(_SUPERVISOR_DISCIPLINE),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
