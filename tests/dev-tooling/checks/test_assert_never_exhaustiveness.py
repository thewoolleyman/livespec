"""Outside-in test for `dev-tooling/checks/assert_never_exhaustiveness.py` — Phase 4 enforcement.

Per `python-skill-script-style-requirements.md` lines 1051-1068
every `match` statement in `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, and `<repo-root>/dev-tooling/**`
MUST terminate with `case _: assert_never(<subject>)` regardless
of subject type.

Rationale: `assert_never(x)` requires `x` to have type `Never`.
When all variants of a closed-union subject are handled, the
residual type at the default arm is `Never` and pyright accepts
the call. Adding a new variant without updating the dispatch
site narrows the residual to the unhandled variant and
`assert_never(x)` becomes a compile-time error.

Cycle 42 pins the canonical violation: a `match` ending without
`case _: assert_never(<subject>)` is rejected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_ASSERT_NEVER = _REPO_ROOT / "dev-tooling" / "checks" / "assert_never_exhaustiveness.py"


def test_assert_never_rejects_match_without_terminator(*, tmp_path: Path) -> None:
    """A `match` without `case _: assert_never(<subj>)` terminator is rejected.

    Fixture: `.claude-plugin/scripts/livespec/dispatch.py`
    contains `match value: case 1: ... case 2: ...` with no
    default arm. The check, invoked with `cwd=tmp_path`, must
    walk the in-scope trees, detect the missing terminator,
    exit non-zero, and surface the offending module path.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "dispatch.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["dispatch"]\n'
        "\n"
        "\n"
        "def dispatch(*, value: int) -> int:\n"
        "    match value:\n"
        "        case 1:\n"
        "            return 10\n"
        "        case 2:\n"
        "            return 20\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_ASSERT_NEVER)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"assert_never_exhaustiveness should reject match without terminator; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/dispatch.py"
    assert expected_path in combined, (
        f"assert_never_exhaustiveness diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_assert_never_accepts_match_with_terminator(*, tmp_path: Path) -> None:
    """A `match` ending in `case _: assert_never(<subject>)` is accepted.

    Fixture: a livespec module with a properly-terminated
    match. The check must walk the tree and exit 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "dispatch.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "from typing_extensions import assert_never\n"
        "\n"
        '__all__: list[str] = ["dispatch"]\n'
        "\n"
        "\n"
        "def dispatch(*, value: int) -> int:\n"
        "    match value:\n"
        "        case 1:\n"
        "            return 10\n"
        "        case 2:\n"
        "            return 20\n"
        "        case _:\n"
        "            assert_never(value)\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_ASSERT_NEVER)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"assert_never_exhaustiveness should accept terminated match; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
