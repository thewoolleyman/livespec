"""Outside-in test for `dev-tooling/checks/rop_pipeline_shape.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` lines 581-618 and 2078:

    AST: every class decorated with `@rop_pipeline` carries
    exactly one public method (the entry point); other methods
    are `_`-prefixed; dunders aren't counted. Enforces the
    Command / Use Case Interactor pattern at the class level.

Cycle 46 pins the canonical violation: a class decorated with
`@rop_pipeline` exposing two non-dunder, non-underscored methods
is rejected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_ROP_PIPELINE_SHAPE = _REPO_ROOT / "dev-tooling" / "checks" / "rop_pipeline_shape.py"


def test_rop_pipeline_shape_rejects_class_with_two_public_methods(*, tmp_path: Path) -> None:
    """A `@rop_pipeline` class with two non-private methods is rejected.

    Fixture: `.claude-plugin/scripts/livespec/seedy.py` contains
    a class decorated with `@rop_pipeline` exposing two public
    methods (`run` and `also_run`). The check must walk the
    livespec tree, detect the second public method, exit
    non-zero, and surface the offending module path.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "seedy.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "from livespec.types import rop_pipeline\n"
        "\n"
        '__all__: list[str] = ["Seedy"]\n'
        "\n"
        "\n"
        "@rop_pipeline\n"
        "class Seedy:\n"
        "    def run(self) -> int:\n"
        "        return 0\n"
        "\n"
        "    def also_run(self) -> int:\n"
        "        return 1\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_ROP_PIPELINE_SHAPE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"rop_pipeline_shape should reject @rop_pipeline class with two public methods; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/seedy.py"
    assert expected_path in combined, (
        f"rop_pipeline_shape diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_rop_pipeline_shape_accepts_class_with_one_public_and_private_helpers(
    *, tmp_path: Path,
) -> None:
    """A `@rop_pipeline` class with one public method + private helpers is accepted.

    Fixture: a class decorated with `@rop_pipeline` exposing
    one public method (`run`), one `_`-prefixed helper, and a
    `__init__` dunder. The check must walk the tree and exit 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "seedy.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "from livespec.types import rop_pipeline\n"
        "\n"
        '__all__: list[str] = ["Seedy"]\n'
        "\n"
        "\n"
        "@rop_pipeline\n"
        "class Seedy:\n"
        "    def __init__(self, *, x: int) -> None:\n"
        "        self.x = x\n"
        "\n"
        "    def run(self) -> int:\n"
        "        return self._compute()\n"
        "\n"
        "    def _compute(self) -> int:\n"
        "        return self.x * 2\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_ROP_PIPELINE_SHAPE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"rop_pipeline_shape should accept class with one public method + private helpers; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
