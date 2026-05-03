"""Outside-in test for `dev-tooling/checks/no_write_direct.py` — bans `sys.stdout.write`/`sys.stderr.write`.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-no-write-direct` row), `sys.stdout.
write(...)` and `sys.stderr.write(...)` calls are banned in
`.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/
bin/**`, and `<repo-root>/dev-tooling/**`. The full ban tier
pairs with ruff `T20` (which bans `print` / `pprint`).

Three documented exemption surfaces, all file-scope (each
supervisor file owns the private helpers its main()
dispatches to):

- `bin/_bootstrap.py` (pre-import version-check stderr).
- `livespec/doctor/run_static.py` (findings JSON stdout —
  main() calls a private `_emit_findings_json` helper).
- Every `.py` under `livespec/commands/**` (supervisor
  surface for each command).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NO_WRITE_DIRECT = _REPO_ROOT / "dev-tooling" / "checks" / "no_write_direct.py"


def test_no_write_direct_rejects_sys_stdout_write_in_livespec(*, tmp_path: Path) -> None:
    """A `sys.stdout.write(...)` call inside livespec/ fails the check.

    Fixture: `.claude-plugin/scripts/livespec/foo.py` calls
    `sys.stdout.write("hello\\n")` inside a function. The
    check, invoked with `cwd=tmp_path`, must walk the
    livespec/bin/dev-tooling subtrees, parse each file, detect
    the banned call, exit non-zero, and surface the offending
    file plus line number.
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
        "def main() -> int:\n"
        '    sys.stdout.write("hello\\n")\n'
        "    return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_WRITE_DIRECT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_write_direct should reject sys.stdout.write call; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/foo.py"
    assert expected_path in combined, (
        f"no_write_direct diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "9" in combined, (
        f"no_write_direct diagnostic does not surface offending line number 9; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_write_direct_rejects_sys_stderr_write_in_dev_tooling(*, tmp_path: Path) -> None:
    """A `sys.stderr.write(...)` call inside dev-tooling/ fails the check.

    Fixture: `dev-tooling/checks/foo.py` calls `sys.stderr.
    write(...)`. Confirms the check covers all three roots
    (livespec, bin, dev-tooling).
    """
    package_dir = tmp_path / "dev-tooling" / "checks"
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
        "def main() -> int:\n"
        '    sys.stderr.write("oops\\n")\n'
        "    return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_WRITE_DIRECT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_write_direct should reject sys.stderr.write call in dev-tooling/; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = "dev-tooling/checks/foo.py"
    assert expected_path in combined, (
        f"no_write_direct diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_write_direct_accepts_module_without_banned_calls(*, tmp_path: Path) -> None:
    """A module with no `sys.{stdout,stderr}.write` calls passes the check (exit 0).

    Pass-case: a livespec module that uses the structlog facade
    instead of direct sys.{stdout,stderr}.write. The check
    walks every relevant subtree and exits 0.
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
        "def main() -> int:\n"
        "    return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_WRITE_DIRECT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_write_direct should accept clean module with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_write_direct_accepts_bin_bootstrap_file_scope_exemption(*, tmp_path: Path) -> None:
    """`bin/_bootstrap.py` is exempted file-scope; `sys.stderr.write` permitted.

    Pass-case: `.claude-plugin/scripts/bin/_bootstrap.py`
    contains the canonical pre-import version-check stderr
    write. The check skips the file entirely (file-scope
    exemption) and exits 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "bin"
    package_dir.mkdir(parents=True)
    source = package_dir / "_bootstrap.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "import sys\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def bootstrap() -> None:\n"
        '    sys.stderr.write("python too old\\n")\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_WRITE_DIRECT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_write_direct should exempt bin/_bootstrap.py with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_write_direct_accepts_doctor_run_static_file_scope(*, tmp_path: Path) -> None:
    """`livespec/doctor/run_static.py` is file-scope exempt.

    Pass-case: `.claude-plugin/scripts/livespec/doctor/
    run_static.py` calls `sys.stdout.write(...)` from inside
    its private helper `_emit_findings_json`, which the
    supervisor's `main()` dispatches to (findings JSON
    contract). File-scope exemption covers the helper.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "doctor"
    package_dir.mkdir(parents=True)
    source = package_dir / "run_static.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "import sys\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def _emit_findings_json() -> None:\n"
        '    _ = sys.stdout.write("{\\"findings\\": []}\\n")\n'
        "\n"
        "\n"
        "def main() -> int:\n"
        "    _emit_findings_json()\n"
        "    return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_WRITE_DIRECT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_write_direct should exempt doctor/run_static.py file-scope with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_write_direct_accepts_commands_file_scope(*, tmp_path: Path) -> None:
    """Files under `livespec/commands/**` are file-scope exempt.

    Pass-case: `.claude-plugin/scripts/livespec/commands/
    seed.py` calls `sys.stdout.write(...)` from a private
    helper. File-scope exemption covers the entire commands
    subtree (each command supervisor owns its private
    helpers).
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "commands"
    package_dir.mkdir(parents=True)
    source = package_dir / "seed.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "import sys\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def _render_help() -> None:\n"
        '    _ = sys.stdout.write("usage: seed ...\\n")\n'
        "\n"
        "\n"
        "def main() -> int:\n"
        "    _render_help()\n"
        "    return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_WRITE_DIRECT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_write_direct should exempt commands/ file-scope with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_write_direct_accepts_empty_tree(*, tmp_path: Path) -> None:
    """A repo cwd without any in-scope subtrees passes the check (exit 0).

    Closes the `if root.is_dir():` False arm for every covered
    subtree.
    """
    result = subprocess.run(
        [sys.executable, str(_NO_WRITE_DIRECT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_write_direct should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_write_direct_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "no_write_direct_for_import_test",
        str(_NO_WRITE_DIRECT),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
