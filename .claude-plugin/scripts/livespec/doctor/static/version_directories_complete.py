"""Static-phase doctor check: version_directories_complete.

Per Plan Phase 3 +: this check asserts that every
`<spec_root>/history/vNNN/` directory contains its expected
sub-structure.

Phase-3 minimum scope: verifies every existing `history/v*/`
directory contains a `proposed_changes/` subdirectory. The
template-specific "main-file" presence is deferred to Phase 7.

Cycle 138 lands the pass arm. Subsequent cycles add the
fail arm for version-directory shape violations.

Phase 7 prereq.B widens the rule with the pruned-marker
exemption per SPECIFICATION/v013 spec.md §"`version-directories-complete`
pruned-marker exemption". A v-directory whose contents are
EXACTLY `PRUNED_HISTORY.json` (single file at the directory
root, no subdirs, no other files) is exempt from the standard
"every v-dir contains template-required spec files + a
`proposed_changes/` subdir" requirement. A v-dir carrying
`PRUNED_HISTORY.json` AND extra entries is a malformed marker
and yields a `status='fail'` Finding.
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-version-directories-complete"
PRUNED_MARKER_FILENAME: str = "PRUNED_HISTORY.json"


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="every history/vNNN/ contains its proposed_changes/ subdir",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _malformed_marker_finding(*, ctx: DoctorContext, version_path: Path) -> Finding:
    """Construct a fail-status Finding for a malformed pruned-marker v-dir.

    Per SPECIFICATION/v013 spec.md §"`version-directories-complete`
    pruned-marker exemption": the marker exemption is strict — a
    v-dir carrying `PRUNED_HISTORY.json` AND extra entries (any
    other file or any subdir) is malformed and MUST be flagged.
    The Finding's `path` field embeds the offending v-dir so the
    user can locate the malformed marker without re-scanning.
    """
    return Finding(
        check_id=SLUG,
        status="fail",
        message=(
            f"history/{version_path.name}/ carries {PRUNED_MARKER_FILENAME} "
            f"plus extra entries; pruned-marker dirs MUST contain "
            f"ONLY {PRUNED_MARKER_FILENAME}"
        ),
        path=str(version_path),
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _classify_version_dir(*, version_path: Path) -> str:
    """Classify a v-directory's pruned-marker shape.

    Returns one of three classifications driving the per-v-dir
    branching in `_verify_version_dirs`:
      - "pruned_marker": EXACTLY one entry, a `PRUNED_HISTORY.json`
        file at the v-dir root. Exempt from the standard contents
        check per SPECIFICATION/v013 spec.md.
      - "malformed_marker": `PRUNED_HISTORY.json` present at the
        v-dir root AND at least one extra entry (file or subdir).
        Yields a fail-Finding short-circuit.
      - "standard": no `PRUNED_HISTORY.json` at the v-dir root.
        Falls through to the existing `proposed_changes/` probe.

    The classification uses `Path.iterdir` directly (not
    `fs.list_dir`) — this is a read-only stat-level scan with no
    failure modes the check can recover from; an OSError here
    propagates as a bug per the error-handling discipline. The
    same direct-iterdir + `is_file()` pattern is established in
    `commands/prune_history.py`.
    """
    children = list(version_path.iterdir())
    marker_path = version_path / PRUNED_MARKER_FILENAME
    if not marker_path.is_file():
        return "standard"
    if len(children) == 1:
        return "pruned_marker"
    return "malformed_marker"


def _verify_version_dirs(
    *,
    ctx: DoctorContext,
    version_paths: list[Path],
) -> IOResult[Finding, LivespecError]:
    """Verify each version dir's contents shape.

    For each v-directory the check classifies the pruned-marker
    shape via `_classify_version_dir`:
      - "pruned_marker" → exempt; advance to the next v-dir.
      - "malformed_marker" → short-circuit with a fail-Finding
        naming the offending v-dir.
      - "standard" → list `<vNNN>/proposed_changes/` to assert
        presence (existing behavior; missing dir lifts to
        IOFailure(PreconditionError) via fs.list_dir).

    The accumulator carries the pass-Finding through the fold;
    a malformed-marker v-dir replaces the accumulator with a
    fail-Finding (short-circuiting via the `bind` chain — once
    a fail-Finding lands, subsequent `bind` calls observe the
    fail-Finding accumulator but still skip pruned-marker v-dirs
    correctly because each iteration evaluates its own classify
    + branch). The first failing standard v-dir short-circuits
    the fold via fs.list_dir's PreconditionError.
    """
    accumulator: IOResult[Finding, LivespecError] = IOSuccess(_pass_finding(ctx=ctx))
    for version_path in version_paths:
        classification = _classify_version_dir(version_path=version_path)
        if classification == "pruned_marker":
            continue
        if classification == "malformed_marker":
            accumulator = IOSuccess(
                _malformed_marker_finding(ctx=ctx, version_path=version_path),
            )
            continue
        proposed_changes_path = version_path / "proposed_changes"
        accumulator = accumulator.bind(
            lambda finding, p=proposed_changes_path: fs.list_dir(path=p).map(
                lambda _: finding,
            ),
        )
    return accumulator


def _select_version_dirs(*, children: list[Path]) -> list[Path]:
    """Filter `children` to only `v*`-named entries that are directories.

    The `v*`-name + `is_dir()` filter excludes the skill-owned
    `<spec_root>/history/README.md` directory-description file
    (Plan Phase 6, 3174-3175, 3194-3195) along
    with any other non-version sibling that may live alongside
    the `vNNN/` snapshots. Without this filter the per-version
    `proposed_changes/` probe would fire against
    `history/README.md/proposed_changes`, yielding an
    IOFailure(`Not a directory`) that mis-classifies a valid
    seeded tree as failing the version-directory-shape check.
    """
    return [child for child in children if child.name.startswith("v") and child.is_dir()]


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the version-directories-complete check against `ctx`.

    Lists `<ctx.spec_root>/history/`, filters to `v*`-named
    directories, then for each verifies the per-v-dir contents
    shape: pruned-marker v-dirs are exempt, malformed-marker
    v-dirs yield a fail-Finding, standard v-dirs must contain
    `proposed_changes/`. On all-present (no malformed markers,
    every standard v-dir has `proposed_changes/`) yields
    IOSuccess(Finding(status='pass')). The standard-rule fail
    arm (missing `proposed_changes/`) lands as
    IOFailure(PreconditionError) via fs.list_dir.
    """
    history_path = ctx.spec_root / "history"
    return fs.list_dir(path=history_path).bind(
        lambda children: _verify_version_dirs(
            ctx=ctx,
            version_paths=_select_version_dirs(children=children),
        ),
    )
