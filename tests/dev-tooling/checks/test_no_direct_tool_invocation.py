"""Outside-in test for `dev-tooling/checks/no_direct_tool_invocation.py` — `lefthook.yml` + CI only call `just <target>`.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-no-direct-tool-invocation` row),
`lefthook.yml` and `.github/workflows/*.yml` only invoke
`just <target>` — no direct calls to `uv run`, `pytest`,
`ruff`, `pyright`, `lint-imports`, etc. The justfile is the
single source of truth for how dev tools are invoked.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NO_DIRECT_TOOL = _REPO_ROOT / "dev-tooling" / "checks" / "no_direct_tool_invocation.py"


def test_no_direct_tool_invocation_rejects_uv_run_in_lefthook(*, tmp_path: Path) -> None:
    """A `lefthook.yml` containing `uv run` fails the check."""
    lefthook = tmp_path / "lefthook.yml"
    lefthook.write_text(
        "pre-commit:\n" "  commands:\n" "    pytest:\n" "      run: uv run pytest\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_DIRECT_TOOL)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_direct_tool_invocation should reject uv-run in lefthook.yml; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "lefthook.yml" in combined, (
        f"diagnostic does not surface offending file `lefthook.yml`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_direct_tool_invocation_rejects_pytest_in_workflow(*, tmp_path: Path) -> None:
    """A workflow YAML calling `pytest` directly fails the check."""
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    workflow = workflow_dir / "ci.yml"
    workflow.write_text(
        "jobs:\n" "  test:\n" "    runs-on: ubuntu-latest\n" "    steps:\n" "      - run: pytest\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_DIRECT_TOOL)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_direct_tool_invocation should reject `pytest` in workflow; "
        f"got returncode={result.returncode}"
    )


def test_no_direct_tool_invocation_accepts_just_only_lefthook(*, tmp_path: Path) -> None:
    """A `lefthook.yml` invoking only `just <target>` passes (exit 0).

    Fixture includes blank lines and `#`-prefixed comments to
    exercise the `if not stripped or stripped.startswith("#")`
    skip branch.
    """
    lefthook = tmp_path / "lefthook.yml"
    lefthook.write_text(
        "# Top-level comment skipped by the line scan.\n"
        "\n"
        "pre-commit:\n"
        "  commands:\n"
        "    check:\n"
        "      # nested comment\n"
        "      run: just check\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NO_DIRECT_TOOL)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_direct_tool_invocation should accept just-only lefthook; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_direct_tool_invocation_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes (exit 0)."""
    result = subprocess.run(
        [sys.executable, str(_NO_DIRECT_TOOL)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_direct_tool_invocation should accept empty tree; "
        f"got returncode={result.returncode}"
    )


def test_no_direct_tool_invocation_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "no_direct_tool_invocation_for_import_test",
        str(_NO_DIRECT_TOOL),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
