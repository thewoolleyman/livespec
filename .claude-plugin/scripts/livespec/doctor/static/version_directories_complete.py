"""Static-phase doctor check: version_directories_complete.

Per Plan Phase 3 line 1596-1602 + PROPOSAL.md §"`doctor` →
Static-phase checks": this check asserts that every
`<spec_root>/history/vNNN/` directory contains its expected
sub-structure.

Phase-3 minimum scope: verifies every existing `history/v*/`
directory contains a `proposed_changes/` subdirectory. The
template-specific "main-file" presence (PROPOSAL.md or
equivalent) is deferred to Phase 7.

Cycle 138 lands the pass arm. Subsequent cycles add the
fail arm for version-directory shape violations.
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


def _verify_version_dirs(
    *,
    ctx: DoctorContext,
    version_paths: list[Path],
) -> IOResult[Finding, LivespecError]:
    """Verify each version dir has its proposed_changes/ subdirectory.

    Composes a fold over the version directories, listing each
    one's `proposed_changes/` to assert presence. The first
    failing dir short-circuits the fold via fs.list_dir's
    PreconditionError. Cycle 138 lands the success path; the
    next cycle adds the .lash recovery into a fail-Finding.
    """
    accumulator: IOResult[Finding, LivespecError] = IOSuccess(_pass_finding(ctx=ctx))
    for version_path in version_paths:
        proposed_changes_path = version_path / "proposed_changes"
        accumulator = accumulator.bind(
            lambda finding, p=proposed_changes_path: fs.list_dir(path=p).map(
                lambda _: finding,
            ),
        )
    return accumulator


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the version-directories-complete check against `ctx`.

    Lists `<ctx.spec_root>/history/`, then for each child
    directory verifies that `<vNNN>/proposed_changes/` exists.
    On all-present yields IOSuccess(Finding(status='pass')).
    The fail arm lands in subsequent cycles.
    """
    history_path = ctx.spec_root / "history"
    return fs.list_dir(path=history_path).bind(
        lambda version_paths: _verify_version_dirs(
            ctx=ctx, version_paths=version_paths,
        ),
    )
