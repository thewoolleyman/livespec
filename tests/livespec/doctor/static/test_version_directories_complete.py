"""Tests for livespec.doctor.static.version_directories_complete.

Per Plan Phase 3 +: this is the fifth of the eight Phase-3
minimum-subset doctor checks. It asserts that every
`<spec_root>/history/vNNN/` directory contains its expected
sub-structure (the main-file + the `proposed_changes/`
subdirectory).

Phase-3 minimum scope: pass arm. The check verifies that every
existing `history/v*/` directory has a `proposed_changes/`
subdirectory. The "main-file" presence (PROPOSAL.md or
template-specific equivalent) is template-aware and lands at
Phase 7. Cycle 138 lands the success arm; subsequent cycles
add the missing-subdirectory failure arm.

Phase 7 prereq.B widens the rule with the pruned-marker
exemption per SPECIFICATION/v013 spec.md §"Pruning history":
a v-directory whose contents are EXACTLY `PRUNED_HISTORY.json`
(single file at the directory root, no subdirs, no other
files) is exempt from the standard "must have proposed_changes/
subdir + template-required files" requirement. Any v-dir that
carries `PRUNED_HISTORY.json` AND extra entries is a malformed
marker and yields a `status='fail'` Finding naming the rule
violation. v-dirs lacking `PRUNED_HISTORY.json` fall through
to the existing standard check (proposed_changes/ presence).
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import version_directories_complete
from livespec.errors import PreconditionError
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess
from returns.result import Failure
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def test_version_directories_complete_run_returns_pass_for_well_formed_history(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when every vNNN/ has proposed_changes/.

    Seeds a project root with a populated spec_root containing
    `history/v001/proposed_changes/` and
    `history/v002/proposed_changes/` (two contiguous version
    directories, each fully formed). Asserts the check yields
    a pass-status Finding.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_path = spec_root / "history"
    history_path.mkdir()
    (history_path / "v001" / "proposed_changes").mkdir(parents=True)
    (history_path / "v002" / "proposed_changes").mkdir(parents=True)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-version-directories-complete",
        status="pass",
        message="every history/vNNN/ contains its proposed_changes/ subdir",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert version_directories_complete.run(ctx=ctx) == IOSuccess(expected)


def test_version_directories_complete_run_skips_non_version_entries_in_history(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) ignores non-`v*` entries (files + dirs) under history/.

    Per the seed wrapper's per-tree skill-owned `history/README.md`
    directory-description (Plan Phase 6, 3174-3175,
    3194-3195), the seeded `<spec_root>/history/` directory contains
    a `README.md` file alongside the `vNNN/` version directories.
    The check must walk only `v*` directories when verifying the
    `proposed_changes/` subdir presence; non-`v*` siblings (file or
    dir) are skill-owned scaffolding outside the per-version-dir
    contract and must not be probed.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_path = spec_root / "history"
    history_path.mkdir()
    (history_path / "v001" / "proposed_changes").mkdir(parents=True)
    (history_path / "README.md").write_text(
        "Skill-owned directory description.\n",
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-version-directories-complete",
        status="pass",
        message="every history/vNNN/ contains its proposed_changes/ subdir",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert version_directories_complete.run(ctx=ctx) == IOSuccess(expected)


def test_version_directories_complete_run_passes_for_pruned_marker_only(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when an oldest v-dir is a pruned-marker.

    Per SPECIFICATION/v013 spec.md §"`version-directories-complete`
    pruned-marker exemption": a v-directory whose contents are
    EXACTLY `PRUNED_HISTORY.json` (single file, no subdirs, no
    other files) is exempt from the standard "every v-dir contains
    template-required spec files + a `proposed_changes/` subdir"
    requirement. The fixture pins `v001/PRUNED_HISTORY.json` as the
    sole pruned-marker oldest-surviving directory followed by a
    fully-formed `v002/proposed_changes/` standard v-dir. The
    check must yield a pass-Finding (the marker is exempt; v002
    satisfies the standard rule).
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_path = spec_root / "history"
    history_path.mkdir()
    (history_path / "v001").mkdir()
    (history_path / "v001" / "PRUNED_HISTORY.json").write_text(
        '{"pruned_range": [1, 1]}\n',
        encoding="utf-8",
    )
    (history_path / "v002" / "proposed_changes").mkdir(parents=True)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-version-directories-complete",
        status="pass",
        message="every history/vNNN/ contains its proposed_changes/ subdir",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert version_directories_complete.run(ctx=ctx) == IOSuccess(expected)


def test_version_directories_complete_run_fails_for_marker_with_extra_file(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) for a v-dir mixing marker + extra file.

    Per SPECIFICATION/v013 spec.md §"`version-directories-complete`
    pruned-marker exemption": the marker exemption is strict — the
    pruned-marker v-dir MUST contain ONLY `PRUNED_HISTORY.json`.
    A v-dir carrying `PRUNED_HISTORY.json` AND an extra file
    (here a stray `spec.md`) is a malformed marker and yields a
    `status='fail'` Finding naming the offending v-dir.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_path = spec_root / "history"
    history_path.mkdir()
    v001 = history_path / "v001"
    v001.mkdir()
    (v001 / "PRUNED_HISTORY.json").write_text(
        '{"pruned_range": [1, 1]}\n',
        encoding="utf-8",
    )
    (v001 / "spec.md").write_text("# stray\n", encoding="utf-8")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-version-directories-complete",
        status="fail",
        message=(
            "history/v001/ carries PRUNED_HISTORY.json plus extra entries; "
            "pruned-marker dirs MUST contain ONLY PRUNED_HISTORY.json"
        ),
        path=str(v001),
        line=None,
        spec_root=str(spec_root),
    )
    assert version_directories_complete.run(ctx=ctx) == IOSuccess(expected)


def test_version_directories_complete_run_fails_for_marker_with_extra_subdir(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) for a v-dir mixing marker + extra subdir.

    Drives the second mode of malformed-marker: a v-dir carrying
    both `PRUNED_HISTORY.json` AND a `proposed_changes/` subdir.
    The strict-only-marker rule treats this as a malformed marker
    (a partial-prune state where the producer didn't fully replace
    the directory contents), yielding a `status='fail'` Finding.
    Distinguishes from the extra-file mode: this fixture exercises
    the subdir branch of the iterdir scan.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_path = spec_root / "history"
    history_path.mkdir()
    v001 = history_path / "v001"
    (v001 / "proposed_changes").mkdir(parents=True)
    (v001 / "PRUNED_HISTORY.json").write_text(
        '{"pruned_range": [1, 1]}\n',
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-version-directories-complete",
        status="fail",
        message=(
            "history/v001/ carries PRUNED_HISTORY.json plus extra entries; "
            "pruned-marker dirs MUST contain ONLY PRUNED_HISTORY.json"
        ),
        path=str(v001),
        line=None,
        spec_root=str(spec_root),
    )
    assert version_directories_complete.run(ctx=ctx) == IOSuccess(expected)


def test_version_directories_complete_run_fails_for_standard_v_dir_missing_proposed_changes(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOFailure(PreconditionError) for non-marker v-dir without proposed_changes/.

    Pins the existing failure-arm behavior: a v-dir that does NOT
    carry `PRUNED_HISTORY.json` (so the pruned-marker exemption
    does NOT apply) and ALSO lacks the `proposed_changes/` subdir
    fails the standard rule. The IOFailure(PreconditionError)
    track is the existing behavior — the orchestrator's
    pattern-match treats this as a check-level error rather than
    a fail-Finding. This test pins that behavior so the
    pruned-marker widening doesn't accidentally swallow the
    non-marker missing-proposed_changes failure into a pass.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_path = spec_root / "history"
    history_path.mkdir()
    (history_path / "v001").mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = version_directories_complete.run(ctx=ctx)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(
                f"expected IOFailure(PreconditionError), got {result!r}",
            )
