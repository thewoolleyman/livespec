"""Outside-in test for `dev-tooling/checks/assert_never_exhaustiveness.py` — `case _: assert_never(<subject>)` terminator.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-assert-never-exhaustiveness` row),
every `match` statement in `livespec/**` MUST terminate with
`case _: assert_never(<subject>)` where `<subject>` is the
match-statement's subject expression. Conservative scope:
every match, regardless of subject type.

Cycle 156 pins the rejection of a match without a final
`case _:` arm.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_ASSERT_NEVER_EXHAUSTIVENESS = (
    _REPO_ROOT / "dev-tooling" / "checks" / "assert_never_exhaustiveness.py"
)


def test_assert_never_exhaustiveness_rejects_match_missing_case_underscore(
    *,
    tmp_path: Path,
) -> None:
    """A `match` lacking a final `case _: assert_never(...)` arm fails the check.

    Fixture: a livespec module with a match statement that
    handles two specific cases but does not terminate with
    `case _: assert_never(val)`. Banned — the universal
    terminator is required.
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
        "def handle(val: int) -> int:\n"
        "    match val:\n"
        "        case 0:\n"
        "            return 1\n"
        "        case 1:\n"
        "            return 2\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_ASSERT_NEVER_EXHAUSTIVENESS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"assert_never_exhaustiveness should reject match without case _: assert_never; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/foo.py"
    assert expected_path in combined, (
        f"assert_never_exhaustiveness diagnostic does not surface offending file "
        f"`{expected_path}`; stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_assert_never_exhaustiveness_rejects_case_underscore_with_non_assert_never_body(
    *,
    tmp_path: Path,
) -> None:
    """A `case _: pass` (or anything other than `assert_never(<subject>)`) fails the check.

    Fixture: match terminates with `case _: return 0` instead
    of `assert_never(val)`. Banned — the body must be
    `assert_never(<subject>)` exactly.
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
        "def handle(val: int) -> int:\n"
        "    match val:\n"
        "        case 0:\n"
        "            return 1\n"
        "        case _:\n"
        "            return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_ASSERT_NEVER_EXHAUSTIVENESS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"assert_never_exhaustiveness should reject `case _:` with non-assert_never body; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_assert_never_exhaustiveness_accepts_proper_match_terminator(
    *,
    tmp_path: Path,
) -> None:
    """A match ending with `case _: assert_never(val)` passes the check (exit 0).

    Pass-case: the canonical terminator pattern.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from typing_extensions import assert_never\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "def handle(val: int) -> int:\n"
        "    match val:\n"
        "        case 0:\n"
        "            return 1\n"
        "        case _:\n"
        "            assert_never(val)\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_ASSERT_NEVER_EXHAUSTIVENESS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"assert_never_exhaustiveness should accept proper terminator with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_assert_never_exhaustiveness_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes the check (exit 0)."""
    result = subprocess.run(
        [sys.executable, str(_ASSERT_NEVER_EXHAUSTIVENESS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"assert_never_exhaustiveness should accept empty tree with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_assert_never_exhaustiveness_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "assert_never_exhaustiveness_for_import_test",
        str(_ASSERT_NEVER_EXHAUSTIVENESS),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
