"""Outside-in test for `dev-tooling/checks/tests_mirror_pairing.py` — v033 D1 mirror-pairing enforcement.

Per PROPOSAL.md §"Test pyramid" (post-v033) and the v033 D1
revision file at `brainstorming/approach-2-nlspec-based/history/
v033/proposed_changes/critique-fix-v032-revision.md`, every covered
`.py` file under `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, and `<repo-root>/dev-tooling/
checks/**` MUST have a paired test file at the mirror path under
`tests/` containing at least one `def test_*` function. Closed
exemption set: `_vendor/**`, `bin/_bootstrap.py` (covered by the
preserved `tests/bin/test_bootstrap.py`), and `__init__.py` files
containing only `from __future__ import annotations` plus
`__all__: list[str] = []` with no executable logic.

This module holds the OUTERMOST behavioral test for that
mirror-pairing rule. Each cycle advances one specific failure
mode: cycle 1 pins the missing-paired-file rejection (a source
under livespec/** without a paired test file fails the check
with exit non-zero, the offending source path surfaced AND the
expected paired-test path surfaced so the developer can author
the pair). Subsequent cycles pin the empty-paired-file rejection
(file exists but no `def test_*`), the closed exemption set
(_vendor, _bootstrap, empty-init), and the bin/dev-tooling-checks
mirror trees.

The check is invoked as a subprocess with the repo root at
`cwd=tmp_path`, matching the contract at
`dev-tooling/checks/CLAUDE.md`. Subprocess invocation exercises
the script's `__main__` plumbing end-to-end exactly as the
`justfile` invokes it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_TESTS_MIRROR_PAIRING = _REPO_ROOT / "dev-tooling" / "checks" / "tests_mirror_pairing.py"


def test_tests_mirror_pairing_rejects_livespec_source_without_paired_test(
    *, tmp_path: Path
) -> None:
    """A `livespec/foo/bar.py` source file without `tests/livespec/foo/test_bar.py` fails the check.

    The fixture builds a synthetic project root mirroring the real
    layout: `.claude-plugin/scripts/livespec/foo/bar.py` is a
    Python file with a trivial body (a single assignment + the
    canonical __all__). No `tests/livespec/foo/test_bar.py`
    exists. The check, invoked with `cwd=tmp_path`, must walk the
    in-scope source trees, detect the missing pair, exit non-zero,
    and surface BOTH the source path
    (`.claude-plugin/scripts/livespec/foo/bar.py`) AND the
    expected paired-test path (`tests/livespec/foo/test_bar.py`)
    in its diagnostic output so the developer can locate and
    create the missing pair.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "foo"
    package_dir.mkdir(parents=True)
    source = package_dir / "bar.py"
    source.write_text(
        "from __future__ import annotations\n" "\n" "__all__: list[str] = []\n" "\n" "x = 0\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(
        [sys.executable, str(_TESTS_MIRROR_PAIRING)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"tests_mirror_pairing should reject livespec/foo/bar.py without paired test "
        f"with non-zero exit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    source_path = ".claude-plugin/scripts/livespec/foo/bar.py"
    expected_pair = "tests/livespec/foo/test_bar.py"
    assert source_path in combined, (
        f"tests_mirror_pairing diagnostic does not surface offending source path "
        f"`{source_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert expected_pair in combined, (
        f"tests_mirror_pairing diagnostic does not surface expected paired-test path "
        f"`{expected_pair}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_tests_mirror_pairing_accepts_paired_source_and_test(*, tmp_path: Path) -> None:
    """A source file with a paired test file passes the check (exit 0).

    Pass-case companion to the rejection test. Fixture: a source
    file at `.claude-plugin/scripts/livespec/foo/bar.py` AND a
    paired test at `tests/livespec/foo/test_bar.py`. The check,
    invoked with `cwd=tmp_path`, walks the source tree, finds the
    expected pair on disk, leaves the offenders list empty, and
    exits 0.

    Drives the success-path return on line 99 (`return 0`) and
    the no-offenders branch (87->83 in coverage's branch report:
    when the loop body's `if not expected_pair.is_file()` arm is
    NOT taken, control returns to the loop header).
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "foo"
    package_dir.mkdir(parents=True)
    source = package_dir / "bar.py"
    source.write_text(
        "from __future__ import annotations\n__all__: list[str] = []\nx = 0\n",
        encoding="utf-8",
    )
    test_dir = tmp_path / "tests" / "livespec" / "foo"
    test_dir.mkdir(parents=True)
    test_file = test_dir / "test_bar.py"
    test_file.write_text(
        "from __future__ import annotations\n__all__: list[str] = []\n"
        "def test_bar() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_TESTS_MIRROR_PAIRING)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"tests_mirror_pairing should accept paired source+test with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_tests_mirror_pairing_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main().

    Closes branch 37->40 (the `if str(_VENDOR_DIR) not in sys.path`
    already-present branch — pytest's pythonpath has pre-populated
    sys.path) and branch 102->exit (`if __name__ == "__main__":`
    else-arm — module imported, not run as a script).
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "tests_mirror_pairing_for_import_test",
        str(_TESTS_MIRROR_PAIRING),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
