"""Outside-in test for `dev-tooling/checks/global_writes.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` line 2077:

    AST: no module-level mutable state writes from functions.

Mutating module-level state from inside a function body
introduces hidden coupling: callers can't reason about a
function's effect from its arguments alone. The check enforces
that pure modules stay pure.

Cycle 45 pins the canonical violation: a function body
declaring `global x` (Python's syntactic marker for intent to
mutate a module-level binding) and then assigning to `x` is
rejected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_GLOBAL_WRITES = _REPO_ROOT / "dev-tooling" / "checks" / "global_writes.py"


def test_global_writes_rejects_function_with_global_declaration(*, tmp_path: Path) -> None:
    """A function body with a `global x` declaration is rejected.

    Fixture: `.claude-plugin/scripts/livespec/mutator.py` has
    a function declaring `global counter` and assigning to it.
    The check, invoked with `cwd=tmp_path`, must walk the
    livespec tree, detect the `Global` node, exit non-zero,
    and surface the offending module path.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "mutator.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["increment"]\n'
        "\n"
        "counter: int = 0\n"
        "\n"
        "\n"
        "def increment() -> None:\n"
        "    global counter\n"
        "    counter += 1\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_GLOBAL_WRITES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"global_writes should reject function declaring `global counter`; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/mutator.py"
    assert expected_path in combined, (
        f"global_writes diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_global_writes_accepts_module_with_pure_functions(*, tmp_path: Path) -> None:
    """A livespec module whose functions don't touch module-level state is accepted.

    Fixture: a livespec module with a pure function (no
    `global` declaration, all writes local to the function
    frame). The check must walk the tree and exit 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "pure.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["compute"]\n'
        "\n"
        "\n"
        "def compute(*, x: int) -> int:\n"
        "    y = x * 2\n"
        "    return y\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_GLOBAL_WRITES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"global_writes should accept pure function with no global writes; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
