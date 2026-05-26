"""Tests for livespec.doctor.static.copier_template_workflow_coverage.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
invariants" → §"`copier-template-workflow-coverage`": every
consumer repository governed by livespec MUST contain a
`.github/workflows/` directory whose set of workflow files is a
SUPERSET of the required-file list enumerated in §"Shared
content sync — copier template". The check fires `fail` for
every required file missing from the consumer's
`.github/workflows/`; each fail finding names the missing
file(s) and directs the user to run `copier update`.

Acceptance scenarios from work-item li-dctwfc:

  - Fixture with ALL required workflows present → `pass`.
  - Fixture with one required workflow file deleted → `fail`
    naming that file.
  - Fixture with multiple required workflow files missing →
    one `fail` finding naming every missing file. (The check
    returns ONE `IOResult[Finding, ...]` per the orchestrator
    contract; the message enumerates all missing files.)
  - Edge case: project with `.github/workflows/` absent
    entirely → one `fail` finding naming every required file.
    Documented choice: bundle all required files into one
    finding because the corrective action (`copier update`)
    is identical to the partial-miss case; emitting N
    per-file findings would be noisy and would not change the
    user's remediation step.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import copier_template_workflow_coverage
from livespec.doctor.static.copier_template_workflow_coverage import (
    REQUIRED_WORKFLOW_FILES,
)
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def _seed_project(*, tmp_path: Path) -> tuple[Path, Path]:
    """Create a fresh project root + spec root pair under tmp_path."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    return project_root, spec_root


def _seed_workflows(*, project_root: Path, names: tuple[str, ...]) -> None:
    """Create `.github/workflows/<name>` for every name in `names`."""
    workflows_dir = project_root / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    for name in names:
        _ = (workflows_dir / name).write_text("# fixture workflow\n", encoding="utf-8")


def test_required_workflow_files_enumerates_seven_canonical_entries() -> None:
    """REQUIRED_WORKFLOW_FILES matches the canonical contracts.md list.

    The seven enumerated files in §"Shared content sync — copier
    template" are pinned here as a contract regression guard. If
    the contract list ever drifts the test fails loudly so the
    drift is caught at PR review.
    """
    assert REQUIRED_WORKFLOW_FILES == (
        "auto-enable-merge.yml",
        "auto-update-branches.yml",
        "bump-pin-from-dispatch.yml",
        "ci.yml",
        "copier-update-drift.yml",
        "pin-freshness.yml",
        "release-dispatch.yml",
    )


def test_copier_template_workflow_coverage_passes_when_every_required_file_present(
    *,
    tmp_path: Path,
) -> None:
    """(a) `pass` when every required workflow file is present."""
    project_root, spec_root = _seed_project(tmp_path=tmp_path)
    _seed_workflows(project_root=project_root, names=REQUIRED_WORKFLOW_FILES)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = copier_template_workflow_coverage.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-copier-template-workflow-coverage",
        status="pass",
        message=(
            f"copier-template-workflow-coverage: all "
            f"{len(REQUIRED_WORKFLOW_FILES)} required workflow file(s) "
            f"are present in `.github/workflows/`"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_copier_template_workflow_coverage_passes_when_extra_files_present(
    *,
    tmp_path: Path,
) -> None:
    """(b) `pass` when every required file present plus consumer-local extras.

    Per the contract: "Workflow files in the consumer's
    `.github/workflows/` that are NOT in the required-list
    (consumer-local workflows) MUST NOT fire fail — they are out
    of scope for this invariant."
    """
    project_root, spec_root = _seed_project(tmp_path=tmp_path)
    extra_names = (*REQUIRED_WORKFLOW_FILES, "consumer-local.yml", "another-local.yml")
    _seed_workflows(project_root=project_root, names=extra_names)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = copier_template_workflow_coverage.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-copier-template-workflow-coverage",
        status="pass",
        message=(
            f"copier-template-workflow-coverage: all "
            f"{len(REQUIRED_WORKFLOW_FILES)} required workflow file(s) "
            f"are present in `.github/workflows/`"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_copier_template_workflow_coverage_fails_when_one_required_file_missing(
    *,
    tmp_path: Path,
) -> None:
    """(c) `fail` naming the single missing file when one file is absent."""
    project_root, spec_root = _seed_project(tmp_path=tmp_path)
    present = tuple(name for name in REQUIRED_WORKFLOW_FILES if name != "auto-enable-merge.yml")
    _seed_workflows(project_root=project_root, names=present)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = copier_template_workflow_coverage.run(ctx=ctx)
    expected_message = (
        "copier-template-workflow-coverage: "
        "1 required workflow file(s) missing from "
        "`.github/workflows/`: auto-enable-merge.yml. Corrective action: run "
        "`copier update` to re-sync the copier template (see "
        '`contracts.md` §"Shared content sync — copier template" for '
        "the canonical required-file list)."
    )
    expected = Finding(
        check_id="doctor-copier-template-workflow-coverage",
        status="fail",
        message=expected_message,
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_copier_template_workflow_coverage_fails_when_multiple_files_missing(
    *,
    tmp_path: Path,
) -> None:
    """(d) `fail` naming every missing file when multiple files absent.

    Multiple missing files surface as a single `fail` finding
    whose message enumerates all the missing files in canonical
    order. The check returns ONE `IOResult[Finding, ...]` per the
    orchestrator's stdout contract; the message body carries the
    per-file detail.
    """
    project_root, spec_root = _seed_project(tmp_path=tmp_path)
    missing_names = (
        "auto-enable-merge.yml",
        "auto-update-branches.yml",
        "pin-freshness.yml",
    )
    present = tuple(name for name in REQUIRED_WORKFLOW_FILES if name not in missing_names)
    _seed_workflows(project_root=project_root, names=present)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = copier_template_workflow_coverage.run(ctx=ctx)
    expected_message = (
        "copier-template-workflow-coverage: "
        "3 required workflow file(s) missing from "
        "`.github/workflows/`: "
        "auto-enable-merge.yml, auto-update-branches.yml, pin-freshness.yml. "
        "Corrective action: run "
        "`copier update` to re-sync the copier template (see "
        '`contracts.md` §"Shared content sync — copier template" for '
        "the canonical required-file list)."
    )
    expected = Finding(
        check_id="doctor-copier-template-workflow-coverage",
        status="fail",
        message=expected_message,
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_copier_template_workflow_coverage_fails_when_workflows_dir_absent(
    *,
    tmp_path: Path,
) -> None:
    """(e) `fail` naming every required file when `.github/workflows/` absent.

    Documented choice: when the workflows directory does not
    exist at all, the check emits one `fail` finding listing
    every required file. The corrective action (run `copier
    update` to re-sync) is identical to the partial-miss case,
    so emitting N per-file findings would be noisy. The message
    explicitly calls out that the directory is absent so the
    user sees the structural cause, not only the file list.
    """
    project_root, spec_root = _seed_project(tmp_path=tmp_path)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = copier_template_workflow_coverage.run(ctx=ctx)
    missing_joined = ", ".join(REQUIRED_WORKFLOW_FILES)
    expected_message = (
        "copier-template-workflow-coverage: "
        "`.github/workflows/` directory is absent from project root; "
        f"all {len(REQUIRED_WORKFLOW_FILES)} required workflow file(s) are missing: "
        f"{missing_joined}. Corrective action: run `copier update` to "
        "re-sync the copier template (see `contracts.md` "
        '§"Shared content sync — copier template" for the canonical '
        "required-file list)."
    )
    expected = Finding(
        check_id="doctor-copier-template-workflow-coverage",
        status="fail",
        message=expected_message,
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_copier_template_workflow_coverage_ignores_subdirectories_inside_workflows(
    *,
    tmp_path: Path,
) -> None:
    """`is_file()` filter excludes subdirectories of `.github/workflows/`.

    Some consumers may carry subdirectories under
    `.github/workflows/` for action-template snippets. The check
    must inspect only direct files, not recurse, and must not
    confuse a subdirectory named e.g. `ci.yml` (unlikely but
    possible) with a workflow file.
    """
    project_root, spec_root = _seed_project(tmp_path=tmp_path)
    _seed_workflows(project_root=project_root, names=REQUIRED_WORKFLOW_FILES)
    nested = project_root / ".github" / "workflows" / "snippets"
    nested.mkdir()
    _ = (nested / "shared-step.yml").write_text("# nested\n", encoding="utf-8")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = copier_template_workflow_coverage.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-copier-template-workflow-coverage",
        status="pass",
        message=(
            f"copier-template-workflow-coverage: all "
            f"{len(REQUIRED_WORKFLOW_FILES)} required workflow file(s) "
            f"are present in `.github/workflows/`"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_copier_template_workflow_coverage_registered_in_static_checks() -> None:
    """The check module is registered in STATIC_CHECKS and applies to main tree."""
    from livespec.doctor.static import APPLICABILITY_BY_TREE_KIND, STATIC_CHECKS

    assert copier_template_workflow_coverage in STATIC_CHECKS
    assert copier_template_workflow_coverage in APPLICABILITY_BY_TREE_KIND["main"]


def test_copier_template_workflow_coverage_pure_no_monkeypatch_needed(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`monkeypatch.chdir` is unnecessary because the check uses `ctx.project_root` directly.

    Regression guard against `Path.cwd()` creeping into the
    implementation: every test above seeds an isolated
    project_root under `tmp_path` and passes it into `ctx`
    explicitly, then asserts that the check produces the
    expected finding without any cwd manipulation. If a future
    rewrite reaches for `Path.cwd()` instead of `ctx.project_root`,
    this test fails by emitting a finding that reflects the
    surrounding repo's `.github/workflows/` state rather than
    the empty tmp_path fixture's.
    """
    project_root, spec_root = _seed_project(tmp_path=tmp_path)
    monkeypatch.chdir(tmp_path)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = copier_template_workflow_coverage.run(ctx=ctx)
    missing_joined = ", ".join(REQUIRED_WORKFLOW_FILES)
    expected_message = (
        "copier-template-workflow-coverage: "
        "`.github/workflows/` directory is absent from project root; "
        f"all {len(REQUIRED_WORKFLOW_FILES)} required workflow file(s) are missing: "
        f"{missing_joined}. Corrective action: run `copier update` to "
        "re-sync the copier template (see `contracts.md` "
        '§"Shared content sync — copier template" for the canonical '
        "required-file list)."
    )
    expected = Finding(
        check_id="doctor-copier-template-workflow-coverage",
        status="fail",
        message=expected_message,
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
