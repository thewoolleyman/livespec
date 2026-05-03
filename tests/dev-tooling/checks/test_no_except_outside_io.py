"""Outside-in test for `dev-tooling/checks/no_except_outside_io.py` — exception catches confined to io+supervisor.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-no-except-outside-io` row), catching
exceptions (`try/except`) outside `livespec/io/**` is
permitted only in **supervisor bug-catchers** — the top-level
`try/except Exception` block inside `main()` of
`livespec/commands/*.py` and `livespec/doctor/run_static.py`.
Anywhere else under `livespec/**`, `try/except` is banned —
pure layers handle expected failures via the ROP railway
(`Result.bind`, `Result.alt`), not Python exception handling.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NO_EXCEPT_OUTSIDE_IO = _REPO_ROOT / "dev-tooling" / "checks" / "no_except_outside_io.py"


def test_no_except_outside_io_rejects_try_except_in_pure_layer(*, tmp_path: Path) -> None:
    """A `try/except` inside `livespec/parse/foo.py` fails the check.

    Fixture: a parse-layer module wraps work in `try/except
    ValueError`. Banned — pure layers use ROP railway. The
    check must surface the offending file plus line number.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "parse"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def parse_thing() -> None:\n"
        "    try:\n"
        "        x = 1\n"
        "    except ValueError:\n"
        "        x = 2\n"
        "    _ = x\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_EXCEPT_OUTSIDE_IO)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_except_outside_io should reject try/except in parse/; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/parse/foo.py"
    assert expected_path in combined, (
        f"no_except_outside_io diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_except_outside_io_accepts_try_except_in_io_layer(*, tmp_path: Path) -> None:
    """A `try/except` inside `livespec/io/fs.py` passes (exit 0).

    Pass-case: io/ is the side-effect boundary that
    legitimately catches exceptions to lift them onto the
    IOResult railway via `@impure_safe(...)`.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "io"
    package_dir.mkdir(parents=True)
    source = package_dir / "fs.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def read_text() -> None:\n"
        "    try:\n"
        "        x = 1\n"
        "    except FileNotFoundError:\n"
        "        x = 2\n"
        "    _ = x\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_EXCEPT_OUTSIDE_IO)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_except_outside_io should accept try/except in io/ with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_except_outside_io_accepts_supervisor_bug_catcher(*, tmp_path: Path) -> None:
    """A `try/except Exception` inside `commands/seed.py::main()` passes (exit 0).

    Pass-case: the supervisor bug-catcher exemption — top-
    level `try/except Exception` inside `main()` of
    commands/*.py is permitted. The check exempts this
    function-scope.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "commands"
    package_dir.mkdir(parents=True)
    source = package_dir / "seed.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    try:\n"
        "        return 0\n"
        "    except Exception:\n"
        "        return 1\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_EXCEPT_OUTSIDE_IO)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_except_outside_io should accept supervisor bug-catcher with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_except_outside_io_accepts_supervisor_bug_catcher_in_run_static(*, tmp_path: Path) -> None:
    """A `try/except Exception` inside `doctor/run_static.py::main()` passes (exit 0).

    Pass-case: the second supervisor bug-catcher surface.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "doctor"
    package_dir.mkdir(parents=True)
    source = package_dir / "run_static.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    try:\n"
        "        return 0\n"
        "    except Exception:\n"
        "        return 1\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_EXCEPT_OUTSIDE_IO)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_except_outside_io should accept run_static.py main bug-catcher; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_except_outside_io_rejects_try_except_in_helper_in_commands(*, tmp_path: Path) -> None:
    """A `try/except` in a private helper of commands/seed.py still fails the check.

    The supervisor bug-catcher exemption applies only to the
    top-level body of `main()`, not to private helpers like
    `_run_pipeline`. A `try/except` inside `_render_help`
    fails.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "commands"
    package_dir.mkdir(parents=True)
    source = package_dir / "seed.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def _helper() -> None:\n"
        "    try:\n"
        "        x = 1\n"
        "    except ValueError:\n"
        "        x = 2\n"
        "    _ = x\n"
        "\n"
        "\n"
        "def main() -> int:\n"
        "    _helper()\n"
        "    return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_EXCEPT_OUTSIDE_IO)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_except_outside_io should reject try/except in helper of commands/seed.py; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_except_outside_io_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes the check (exit 0)."""
    result = subprocess.run(
        [sys.executable, str(_NO_EXCEPT_OUTSIDE_IO)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_except_outside_io should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_except_outside_io_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "no_except_outside_io_for_import_test", str(_NO_EXCEPT_OUTSIDE_IO),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
