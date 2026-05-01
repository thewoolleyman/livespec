"""Outside-in test for `dev-tooling/checks/main_guard.py` — bans `__main__` guard inside livespec/**.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-main-guard` row), no `if __name__ ==
"__main__":` block may appear inside any `.py` file under
`.claude-plugin/scripts/livespec/**`. Such a guard is the
hallmark of a runnable entry point; livespec's runnable entry
points live in `bin/*.py` (the shebang wrappers), and every
`bin/*.py` import goes through `livespec/commands/*.py:main`.
A `__main__` guard in `livespec/**` indicates a wrapper-style
file in the wrong tree.

This module holds the OUTERMOST behavioral test for that
rule. Cycle 147 pins the rejection case: a synthetic
`livespec/foo.py` containing `if __name__ == "__main__":` at
module top level fails the check with non-zero exit and the
diagnostic surfaces both the offending file and line number
so the developer can locate the violation.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_MAIN_GUARD = _REPO_ROOT / "dev-tooling" / "checks" / "main_guard.py"


def test_main_guard_rejects_main_guard_inside_livespec(*, tmp_path: Path) -> None:
    """A `__main__` guard inside `.claude-plugin/scripts/livespec/foo.py` fails the check.

    The fixture writes a synthetic project root mirroring the
    real layout. `.claude-plugin/scripts/livespec/foo.py`
    contains `if __name__ == "__main__":` at module level — a
    direct violation. The check, invoked with `cwd=tmp_path`,
    must walk the livespec subtree, parse the file via `ast`,
    detect the guard, exit non-zero, and surface the offending
    path and line number in its diagnostic.
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
        "    return 0\n"
        "\n"
        "\n"
        'if __name__ == "__main__":\n'
        "    raise SystemExit(main())\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_MAIN_GUARD)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"main_guard should reject livespec/foo.py with `__main__` guard with non-zero exit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/foo.py"
    assert expected_path in combined, (
        f"main_guard diagnostic does not surface offending file `{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    # Line 10 is the `if __name__ ...` line in the fixture.
    assert "10" in combined, (
        f"main_guard diagnostic does not surface offending line number 10; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_main_guard_accepts_livespec_file_without_main_guard(*, tmp_path: Path) -> None:
    """A livespec file without `__main__` guard passes the check (exit 0).

    Pass-case companion: a `.claude-plugin/scripts/livespec/
    foo.py` containing only the canonical preamble (`from
    __future__`, `__all__`) and a function definition. No
    `__main__` guard. The check walks the tree, finds no
    offenders, and exits 0.
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

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_MAIN_GUARD)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"main_guard should accept livespec file without `__main__` guard with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_main_guard_accepts_tree_without_livespec_directory(*, tmp_path: Path) -> None:
    """A repo cwd without `.claude-plugin/scripts/livespec/` passes the check (exit 0).

    Closes the `if livespec_root.is_dir():` False arm so main()
    short-circuits without walking. tmp_path is empty — no
    `.claude-plugin` directory at all — so the check has
    nothing to inspect. Exit 0 with empty offenders list.
    """
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_MAIN_GUARD)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"main_guard should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_main_guard_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main().

    Closes the `if str(_VENDOR_DIR) not in sys.path`
    already-present branch (pytest's pythonpath has
    pre-populated sys.path) and the `if __name__ ==
    "__main__":` else-arm (module imported, not run as a
    script), required for per-file 100% line+branch coverage.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "main_guard_for_import_test", str(_MAIN_GUARD),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
