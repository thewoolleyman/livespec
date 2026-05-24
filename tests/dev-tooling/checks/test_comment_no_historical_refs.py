"""Outside-in test for `dev-tooling/checks/comment_no_historical_refs.py`.

Per `SPECIFICATION/non-functional-requirements.md` §"Comment discipline"
(Rule 2 — No historical-bookkeeping references), comments in the
first-party trees MUST NOT cite version numbers, decision IDs, phase
numbers, cycle numbers, or commit references. The check greps every
in-scope file for the spec's reference regex and exits non-zero with
structured findings naming each violation site.

In-scope (per the spec): `justfile`, `lefthook.yml`,
`.github/workflows/*.yml`, `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, `dev-tooling/**`, `tests/**`.

Scope exemptions: `_vendor/**`, `SPECIFICATION/**`, `archive/**`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK = _REPO_ROOT / "dev-tooling" / "checks" / "comment_no_historical_refs.py"


def _run(*, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_CHECK)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def test_passes_on_empty_repo(*, tmp_path: Path) -> None:
    """An empty cwd passes (exit 0)."""
    result = _run(cwd=tmp_path)
    assert result.returncode == 0, (
        f"empty tree should pass; returncode={result.returncode} " f"stderr={result.stderr!r}"
    )


def test_rejects_python_comment_with_version_ref(*, tmp_path: Path) -> None:
    """A version-and-decision-marker `#` comment in a Python file fails."""
    pkg = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    pkg.mkdir(parents=True)
    (pkg / "mod.py").write_text(
        "from __future__ import annotations\n"
        "__all__: list[str] = []\n"
        "# Per v033 D1 the threshold is 100.\n"
        "X = 100\n",
        encoding="utf-8",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode != 0, (
        f"should reject version-marker comment; got returncode={result.returncode} "
        f"stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert (
        "mod.py" in combined
    ), f"diagnostic should name the offending file; stderr={result.stderr!r}"


def test_rejects_python_docstring_with_phase_ref(*, tmp_path: Path) -> None:
    """A docstring containing a phase-numbering marker fails."""
    pkg = tmp_path / "dev-tooling" / "checks"
    pkg.mkdir(parents=True)
    (pkg / "thing.py").write_text(
        '"""Per Phase 4 of the plan, this enforces X."""\n'
        "from __future__ import annotations\n"
        "__all__: list[str] = []\n",
        encoding="utf-8",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode != 0, (
        f"should reject phase-numbering marker in docstring; got returncode={result.returncode} "
        f"stderr={result.stderr!r}"
    )


def test_rejects_yaml_comment_with_cycle_ref(*, tmp_path: Path) -> None:
    """A cycle-numbering-marker comment in a workflow YAML file fails."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(
        "# cycle 117 added this job.\n" "name: ci\n" "on: [push]\n",
        encoding="utf-8",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode != 0, (
        f"should reject cycle-numbering marker in workflow comment; "
        f"got returncode={result.returncode} stderr={result.stderr!r}"
    )


def test_rejects_justfile_comment(*, tmp_path: Path) -> None:
    """A commit-reference-phrase comment in the root justfile fails."""
    (tmp_path / "justfile").write_text(
        "# this commit introduced the recipe.\n" "check:\n" "    echo ok\n",
        encoding="utf-8",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode != 0, (
        f"should reject commit-reference phrase in justfile; got returncode={result.returncode} "
        f"stderr={result.stderr!r}"
    )


def test_rejects_lefthook_comment(*, tmp_path: Path) -> None:
    """A previous-PR-reference comment in lefthook.yml fails."""
    (tmp_path / "lefthook.yml").write_text(
        "# the previous PR moved this hook.\n"
        "pre-commit:\n"
        "  commands:\n"
        "    check:\n"
        "      run: just check\n",
        encoding="utf-8",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode != 0, (
        f"should reject previous-PR reference in lefthook.yml; got returncode={result.returncode} "
        f"stderr={result.stderr!r}"
    )


def test_accepts_python_with_compliant_comments(*, tmp_path: Path) -> None:
    """A Python file with only WHY-form comments passes."""
    pkg = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    pkg.mkdir(parents=True)
    (pkg / "mod.py").write_text(
        '"""Module docstring describing the live constraint."""\n'
        "from __future__ import annotations\n"
        "__all__: list[str] = []\n"
        "# The retry budget is bounded by the upstream rate limiter.\n"
        "BUDGET = 5\n",
        encoding="utf-8",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode == 0, (
        f"should accept WHY-form comments; got returncode={result.returncode} "
        f"stderr={result.stderr!r}"
    )


def test_ignores_string_literals(*, tmp_path: Path) -> None:
    """A Python string literal containing a marker is NOT a comment and should not fail."""
    pkg = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    pkg.mkdir(parents=True)
    (pkg / "mod.py").write_text(
        "from __future__ import annotations\n"
        "__all__: list[str] = []\n"
        'LABEL = "Phase 4"  # test fixture label name\n',
        encoding="utf-8",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode == 0, (
        f"string-literal marker should not trigger the check; "
        f"got returncode={result.returncode} stderr={result.stderr!r}"
    )


def test_ignores_vendor_subtree(*, tmp_path: Path) -> None:
    """Files under `_vendor/` nested in an in-scope tree are exempt per the spec."""
    vendor = tmp_path / "dev-tooling" / "_vendor" / "thirdparty"
    vendor.mkdir(parents=True)
    (vendor / "lib.py").write_text(
        "# Per v033 D1 upstream rewrote this.\nX = 1\n",
        encoding="utf-8",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode == 0, (
        f"vendor subtree should be exempt; got returncode={result.returncode} "
        f"stderr={result.stderr!r}"
    )


def test_ignores_specification_subtree(*, tmp_path: Path) -> None:
    """Files under `SPECIFICATION/` are scope-exempt per the spec — the spec IS the historical record."""
    spec = tmp_path / "SPECIFICATION"
    spec.mkdir(parents=True)
    (spec / "spec.md").write_text(
        "# v033 D1 — original threshold cut.\n",
        encoding="utf-8",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode == 0, (
        f"SPECIFICATION subtree should be exempt; got returncode={result.returncode} "
        f"stderr={result.stderr!r}"
    )


def test_ignores_archive_subtree(*, tmp_path: Path) -> None:
    """Files under `archive/` are scope-exempt per the spec."""
    arc = tmp_path / "archive" / "old"
    arc.mkdir(parents=True)
    (arc / "notes.py").write_text(
        "# Per v033 D1 this was the original cut.\n" "X = 1\n",
        encoding="utf-8",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode == 0, (
        f"archive subtree should be exempt; got returncode={result.returncode} "
        f"stderr={result.stderr!r}"
    )


def test_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "comment_no_historical_refs_for_import_test",
        str(_CHECK),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
