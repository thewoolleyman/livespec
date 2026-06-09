# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Static-phase doctor check: no_orphan_dependency.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" → §"`no-orphan-dependency`":

  Every work item's declared `depends_on` entries MUST resolve
  cleanly. The check fires `fail` when any `DependsOnEntry` with
  `kind == "local"` references a `work_item_id` that does not
  exist in the materialized work-items store. For `kind` values
  `sibling_work_item`, `pull_request`, and `branch`, the
  invariant defers to `livespec_runtime.cross_repo.resolve_ref`
  and fires `fail` ONLY when the runtime returns `unknown` AND
  the entry's `repo` key is present in `cross_repo_targets`; a
  successful `open` or `closed` resolution is NOT a doctor
  failure.

Cross-boundary mechanism: the work-items are acquired by invoking
the ACTIVE impl-plugin's `list-work-items` thin-transport wrapper
(resolved from `LIVESPEC_IMPL_LIST_WORK_ITEMS` into
`ctx.work_items_provider`), NOT a direct JSONL file read. This is
plugin-agnostic (plaintext + beads + any future backend). When no
live provider is configured, or the provider is unreachable, the
check returns a `skipped` Finding (never `fail`). See
`_work_items_provider.py`. The `cross_repo_targets` manifest is
still read from `.livespec.jsonc` (best-effort; an absent or
malformed block yields an empty manifest).

Legacy bare-string entries (pre-v072 format) are tolerated for
closed records (treated as implicit local lookups); open records
with bare-string entries fire `fail` because v072 requires the
typed-dict form. The impl-plugin's data-migration step is the
proper place to convert legacy entries; this tolerance exists to
keep historical records readable.

The helper extraction in `_no_orphan_dependency_helpers.py`
keeps this module under the 250-LLOC hard ceiling enforced by
`dev-tooling/checks/file_lloc.py`.
"""

from __future__ import annotations

from typing import Any

from livespec_runtime.cross_repo.types import CrossRepoManifest
from returns.io import IOResult, IOSuccess
from typing_extensions import assert_never

from livespec.context import DoctorContext
from livespec.doctor.static._no_orphan_dependency_helpers import (
    find_orphans,
    load_manifest_io,
)
from livespec.doctor.static._work_items_provider import (
    ProviderOutcome,
    ProviderUnreachable,
    ProviderUnset,
    WorkItemsIndex,
    load_work_items_index,
    skip_message,
)
from livespec.errors import LivespecError
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-no-orphan-dependency")
_SLUG_PREFIX: str = "no-orphan-dependency"


def _make_finding(
    *,
    ctx: DoctorContext,
    status: str,
    message: str,
    path: str | None = None,
) -> Finding:
    """Build a Finding with the check's SLUG + spec_root."""
    return Finding(
        check_id=SLUG,
        status=status,
        message=message,
        path=path,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _evaluate_index(
    *,
    ctx: DoctorContext,
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> Finding:
    """Apply the invariant against the materialized work-items index."""
    orphans = find_orphans(index=index, manifest=manifest)
    if not orphans:
        return _make_finding(
            ctx=ctx,
            status="pass",
            message=(
                f"no-orphan-dependency: every depends_on reference resolves "
                f"({len(index)} work-items scanned)"
            ),
        )
    pairs_joined = ", ".join(f"{item_id}→{missing}" for item_id, missing in orphans)
    return _make_finding(
        ctx=ctx,
        status="fail",
        message=(
            f"no-orphan-dependency: {len(orphans)} unresolved depends_on "
            f"reference(s): {pairs_joined}. Either add the missing work-item(s) "
            "or remove the stale depends_on entry."
        ),
        path=str(ctx.work_items_provider),
    )


def _interpret(
    *,
    ctx: DoctorContext,
    outcome: ProviderOutcome,
    manifest: CrossRepoManifest,
) -> Finding:
    """Map the provider outcome to a Finding (skip on unset/unreachable)."""
    match outcome:
        case ProviderUnset() | ProviderUnreachable():
            return _make_finding(
                ctx=ctx,
                status="skipped",
                message=skip_message(slug_prefix=_SLUG_PREFIX, outcome=outcome),
            )
        case WorkItemsIndex(index=index):
            return _evaluate_index(ctx=ctx, index=index, manifest=manifest)
        case _:
            assert_never(outcome)


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run no-orphan-dependency against `ctx`.

    Reads the `cross_repo_targets` manifest from `.livespec.jsonc`
    (best-effort), acquires work-items via the active impl-plugin's
    `list-work-items` wrapper (per `ctx.work_items_provider`), and
    applies the no-orphan-dependency predicate. A connection-class
    failure or an unset provider yields a `skipped` Finding; only an
    actual orphan reference yields `fail`. The IO track is lashed back
    to a `skipped` Finding so the orchestrator's stdout contract stays
    uniform.
    """
    return (
        load_manifest_io(ctx=ctx)
        .bind(
            lambda manifest: load_work_items_index(ctx=ctx).map(
                lambda outcome: _interpret(ctx=ctx, outcome=outcome, manifest=manifest),
            ),
        )
        .lash(
            lambda err: IOSuccess(
                _make_finding(
                    ctx=ctx,
                    status="skipped",
                    message=(
                        f"no-orphan-dependency: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                )
            )
        )
    )
