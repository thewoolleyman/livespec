"""Outside-in test for `dev-tooling/checks/all_declared.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` §"Module API
surface" (lines 943-960) every module under
`.claude-plugin/scripts/livespec/**` MUST declare a module-top
`__all__: list[str]` listing the public API names. The check
walks the package and verifies (a) the assignment exists, and
(b) every name in `__all__` is actually defined in the module.

Each cycle pins one specific failure mode. Cycle 36 pins the
canonical "missing `__all__`" violation: a livespec module with
no `__all__` assignment is rejected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_ALL_DECLARED = _REPO_ROOT / "dev-tooling" / "checks" / "all_declared.py"


def test_all_declared_rejects_livespec_module_without_all(*, tmp_path: Path) -> None:
    """A livespec module missing `__all__` is rejected.

    Fixture: `.claude-plugin/scripts/livespec/no_all.py` with a
    public function but no `__all__: list[str]` assignment.
    The check, invoked with `cwd=tmp_path`, must walk the
    livespec tree, detect the missing declaration, exit
    non-zero, and surface the offending module path.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "no_all.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "\n"
        "def public_fn() -> int:\n"
        "    return 0\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_ALL_DECLARED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"all_declared should reject livespec module without `__all__` declaration; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/no_all.py"
    assert expected_path in combined, (
        f"all_declared diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_all_declared_accepts_livespec_module_with_all(*, tmp_path: Path) -> None:
    """A livespec module with `__all__: list[str]` is accepted.

    Fixture: `.claude-plugin/scripts/livespec/with_all.py`
    declaring `__all__: list[str] = ["public_fn"]` and
    defining the listed name. The check must walk the tree and
    exit 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "with_all.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["public_fn"]\n'
        "\n"
        "\n"
        "def public_fn() -> int:\n"
        "    return 0\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_ALL_DECLARED)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"all_declared should accept livespec module with `__all__`; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
