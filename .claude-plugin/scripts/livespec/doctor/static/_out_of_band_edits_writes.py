"""Auto-backfill artifact-writing helpers for `out_of_band_edits.run`.

Extracted from `out_of_band_edits.py` at cycle 7.a.v-redo so the
parent file's LLOC stays under the 250-LLOC hard ceiling enforced
by `dev-tooling/checks/file_lloc.py`. Mirrors the
`_seed_railway_emits.py` / `_revise_railway_emits.py` precedent
(extracting compose-and-write helpers from a parent supervisor /
check that would otherwise blow the file-LLOC ceiling).

Per: when divergence is detected against the HEAD-history-vN
baseline, the check writes three classes of artifacts under
`<spec_root>/history/v(N+1)/`:

  1. `proposed_changes/out-of-band-edit-<TIMESTAMP>.md` — paired
     proposed-change file, livespec-doctor authored, body carries
     the unified diff per file.
  2. `proposed_changes/out-of-band-edit-<TIMESTAMP>-revision.md` —
     paired revision file, decision: accept, both authors
     livespec-doctor.
  3. `<file>` — for every file present at HEAD-active under the
     enumeration domain, copy HEAD-committed bytes byte-identically.
     Files NOT at HEAD-active (i.e., divergence kind is missing-
     active) are skipped.

The PROPOSAL "moves the proposed-change and revision into
history/v(N+1)/proposed_changes/" step is implemented as direct
write into `history/v(N+1)/proposed_changes/` rather than write +
move — the destination is the same in either order, and the
single-write path is cleaner. The pre-backfill guard's leftover-
detection covers the partial-write case the spec's move-step
phrasing was guarding against.

TIMESTAMP-FILENAME format: `%Y-%m-%dt%H-%M-%Sz` (lowercase t/z,
all hyphens) so the resulting filename satisfies both the topic
schema's kebab-case regex (`^[a-z][a-z0-9]*(-[a-z0-9]+)*$`) and
the proposed-change filename convention. Field VALUES (created_at,
revised_at) use the canonical ISO-8601 `%Y-%m-%dT%H:%M:%SZ` per
the schema's `format: date-time`.

Author identifier `livespec-doctor` is the literal reserved skill-
tool prefix from; the doctor is the
sole author for auto-backfill artifacts (no resolution from CLI /
env / payload).

Per memory `feedback_keyword_only_python`: every def uses `*`
keyword-only separator. Per memory `feedback_domain_errors_vs_bugs`:
all expected failures (path missing at HEAD, parent-dir-creation
failure, etc.) flow as `IOFailure(LivespecError)` on the railway;
bugs propagate as raised exceptions.
"""

from __future__ import annotations

import difflib
from collections.abc import Callable
from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.doctor.static._out_of_band_edits_compose import (
    _compose_proposed_change_body,
    _compose_revision_body,
    _next_version_label,
    _now_utc_field_timestamp,
    _now_utc_filename_timestamp,
    _resulting_files_listing,
)
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.io.git import show_at_head
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["route_drift_outcome", "write_auto_backfill_artifacts"]


# Type alias for the parent module's `_make_finding` callable, threaded
# through `route_drift_outcome` so this module does not duplicate the
# Finding-construction formula. Keyword-only signature mirrors the
# parent helper one-to-one.
_MakeFinding = Callable[..., Finding]


_HISTORY_SUBDIR_NAME: str = "history"
_PROPOSED_CHANGES_SUBDIR_NAME: str = "proposed_changes"


def _show_or_none(
    *,
    ctx: DoctorContext,
    repo_relative_path: Path,
) -> IOResult[bytes | None, LivespecError]:
    """IOSuccess(bytes) when path is at HEAD; IOSuccess(None) when absent.

    `.lash` absorbs path-missing-at-HEAD failure (the only failure
    mode the artifact-writing treats as a domain signal — a
    missing-active or missing-history divergence) into None on
    the success rail. Mirrors the same-named helper in
    `out_of_band_edits.py`.
    """
    return show_at_head(
        project_root=ctx.project_root,
        repo_relative_path=repo_relative_path,
    ).lash(lambda _err: IOSuccess(None))


def _format_unified_diff_for_file(
    *,
    file_basename: str,
    history_bytes: bytes | None,
    active_bytes: bytes | None,
) -> str:
    """Render unified-diff between history-vN and active sides of a file.

    `None` on either side ⇒ "absent at HEAD on that side"
    (missing-active or missing-history divergence); stdlib
    `difflib.unified_diff` accepts empty sequences so an absent
    side flows in as `[]` — diff shows the file as fully added
    or deleted.
    """
    history_text = (history_bytes or b"").decode("utf-8", errors="replace")
    active_text = (active_bytes or b"").decode("utf-8", errors="replace")
    diff_lines = difflib.unified_diff(
        history_text.splitlines(keepends=True),
        active_text.splitlines(keepends=True),
        fromfile=f"history/vN/{file_basename}",
        tofile=f"active/{file_basename}",
    )
    return "".join(diff_lines)


def _collect_full_diff(
    *,
    ctx: DoctorContext,
    spec_root_repo_rel: Path,
    history_repo_rel: Path,
    enumerated_files: tuple[str, ...],
) -> IOResult[str, LivespecError]:
    """Aggregate per-file unified diffs into one diff text for the proposal body."""
    accumulator: IOResult[str, LivespecError] = IOSuccess("")
    for basename in enumerated_files:
        active_path = spec_root_repo_rel / basename
        history_path = history_repo_rel / basename
        accumulator = accumulator.bind(
            lambda current, b=basename, ap=active_path, hp=history_path: _show_or_none(
                ctx=ctx,
                repo_relative_path=ap,
            ).bind(
                lambda active, c=current, b=b, hp=hp: _show_or_none(
                    ctx=ctx,
                    repo_relative_path=hp,
                ).map(
                    lambda history, c=c, b=b, active=active: c
                    + _format_unified_diff_for_file(
                        file_basename=b,
                        history_bytes=history,
                        active_bytes=active,
                    ),
                ),
            ),
        )
    return accumulator


def _write_all_snapshots(
    *,
    ctx: DoctorContext,
    spec_root_repo_rel: Path,
    enumerated_files: tuple[str, ...],
    snapshot_dir: Path,
) -> IOResult[None, LivespecError]:
    """Snapshot HEAD-active bytes for every enumerated file into `snapshot_dir`.

    Files absent from HEAD-active (missing-active divergences) are
    skipped — there's no HEAD blob to copy. UTF-8 decode + write
    is byte-identical because the spec contract requires UTF-8
    text under `<spec_root>/`.
    """
    accumulator: IOResult[None, LivespecError] = IOSuccess(None)
    for basename in enumerated_files:
        active_path = spec_root_repo_rel / basename
        target = snapshot_dir / basename
        accumulator = accumulator.bind(
            lambda _value, ap=active_path, t=target: _show_or_none(
                ctx=ctx,
                repo_relative_path=ap,
            ).bind(
                lambda active_bytes, t=t: IOSuccess(None)
                if active_bytes is None
                else fs.write_text(path=t, text=active_bytes.decode("utf-8")),
            ),
        )
    return accumulator


def write_auto_backfill_artifacts(
    *,
    ctx: DoctorContext,
    latest_version_label: str,
    enumerated_files: tuple[str, ...],
) -> IOResult[None, LivespecError]:
    """Write proposed-change + revision + per-file snapshots for the auto-backfill.

    Composes:
      1. resolve the v(N+1) directory name + the OOB topic +
         filenames + timestamps;
      2. collect the unified diff for every enumerated file;
      3. write the proposed-change file under
         `<spec_root>/history/v(N+1)/proposed_changes/`;
      4. write the paired revision file alongside it;
      5. snapshot every HEAD-active-present file into
         `<spec_root>/history/v(N+1)/<file>`.

    `enumerated_files` is the comparison's union enumeration of
    file basenames present at HEAD on either side. The caller
    (`out_of_band_edits.run`) computes this via the same primitive
    (`_enumerate_union_file_basenames`) used for the divergence
    decision, so the same set drives both diff body and snapshot.
    """
    next_label = _next_version_label(latest_version_label=latest_version_label)
    filename_timestamp = _now_utc_filename_timestamp()
    field_timestamp = _now_utc_field_timestamp()
    topic = f"out-of-band-edit-{filename_timestamp}"
    proposal_filename = f"{topic}.md"
    revision_filename = f"{topic}-revision.md"

    v_next_dir = ctx.spec_root / _HISTORY_SUBDIR_NAME / next_label
    v_next_proposed_changes = v_next_dir / _PROPOSED_CHANGES_SUBDIR_NAME
    proposed_change_path = v_next_proposed_changes / proposal_filename
    revision_path = v_next_proposed_changes / revision_filename

    spec_root_repo_rel = ctx.spec_root.relative_to(ctx.project_root)
    history_repo_rel = spec_root_repo_rel / _HISTORY_SUBDIR_NAME / latest_version_label

    revision_body = _compose_revision_body(
        proposal_filename=proposal_filename,
        revised_at=field_timestamp,
        resulting_files_listing=_resulting_files_listing(
            enumerated_files=enumerated_files,
        ),
    )

    return (
        _collect_full_diff(
            ctx=ctx,
            spec_root_repo_rel=spec_root_repo_rel,
            history_repo_rel=history_repo_rel,
            enumerated_files=enumerated_files,
        )
        .bind(
            lambda diff_text: fs.write_text(
                path=proposed_change_path,
                text=_compose_proposed_change_body(
                    topic=topic,
                    created_at=field_timestamp,
                    diff_text=diff_text,
                ),
            ),
        )
        .bind(
            lambda _value: fs.write_text(path=revision_path, text=revision_body),
        )
        .bind(
            lambda _value: _write_all_snapshots(
                ctx=ctx,
                spec_root_repo_rel=spec_root_repo_rel,
                enumerated_files=enumerated_files,
                snapshot_dir=v_next_dir,
            ),
        )
    )


def route_drift_outcome(
    *,
    ctx: DoctorContext,
    make_finding: _MakeFinding,
    latest_version_label: str,
    enumerated_files: tuple[str, ...],
    diverging_files: list[str],
) -> IOResult[Finding, LivespecError]:
    """Translate the drift-outcome list into a Finding, auto-backfilling on drift.

    No drift → IOSuccess(pass-Finding). Drift → write artifacts
    (proposed-change + revision + v(N+1)/ snapshots) then return
    IOSuccess(fail-Finding). The
    `make_finding` callable is the parent module's Finding-construction
    formula so this module does not duplicate the per-check check_id +
    spec_root payload shape.
    """
    if not diverging_files:
        return IOSuccess(
            make_finding(
                ctx=ctx,
                status="pass",
                message=("no out-of-band edits detected (HEAD-active matches HEAD-history-vN)"),
            ),
        )
    files_csv = ", ".join(diverging_files)
    fail_message = (
        f"out-of-band edits detected at HEAD against "
        f"history/{latest_version_label}: {files_csv}"
    )
    return write_auto_backfill_artifacts(
        ctx=ctx,
        latest_version_label=latest_version_label,
        enumerated_files=enumerated_files,
    ).map(
        lambda _value: make_finding(
            ctx=ctx,
            status="fail",
            message=fail_message,
        ),
    )
