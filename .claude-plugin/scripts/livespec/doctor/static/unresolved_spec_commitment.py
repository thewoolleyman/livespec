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
"""Static-phase doctor check: unresolved_spec_commitment.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
invariants" → §"`unresolved-spec-commitment`":

  Every accepted propose-change's declared cross-boundary
  obligation MUST resolve to a filed work-item. The check walks
  every `<spec-target>/history/vNNN/proposed_changes/<stem>.md`
  whose paired `<stem>-revision.md` carries `decision: accept` or
  `decision: modify`, reads the `<stem>.md`'s front-matter
  `spec_commitments.impl_followups[]` (per `spec.md` §"Proposed-
  change and revision file formats" → "Spec→impl commitment
  declaration"), and for each entry's `id_hint` queries the
  active impl-plugin's `list-work-items --json` thin-transport
  skill for a work-item carrying `spec_commitment_hint:
  <id_hint>`. The check fires `fail` when any entry's `id_hint`
  is absent from the work-items store.

  Propose-changes with `decision: reject` are exempt; PCs that
  omit `spec_commitments` entirely are exempt vacuously.
  Supersession: later PCs declaring `spec_commitments.supersedes:
  [<earlier-id_hint>, ...]` exempt the listed id_hints.

Cross-boundary mechanism:

  The work-items are acquired by invoking the ACTIVE impl-plugin's
  `list-work-items` thin-transport wrapper (resolved from
  `LIVESPEC_IMPL_LIST_WORK_ITEMS` into `ctx.work_items_provider`),
  NOT a direct JSONL file read. This is plugin-agnostic (plaintext +
  beads + any future backend): every impl-plugin's `--json` view
  exposes the `spec_commitment_hint` field this check matches
  against. When no live provider is configured, or the provider is
  unreachable, the check returns a `skipped` Finding (never `fail`).
  See `_work_items_provider.py`.

Helper module: see `_unresolved_spec_commitment_helpers.py` for
the front-matter parser, history walker, and hint extractor. This
module orchestrates the railway and renders the Finding messages.
"""

from __future__ import annotations

from returns.io import IOResult
from typing_extensions import assert_never

from livespec.context import DoctorContext
from livespec.doctor.static._unresolved_spec_commitment_helpers import (
    Unresolved,
    collect_obligations_and_supersedes,
    hints_from_index,
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


SLUG: CheckId = CheckId("doctor-unresolved-spec-commitment")
_SLUG_PREFIX: str = "unresolved-spec-commitment"


def _pass(*, ctx: DoctorContext, message: str) -> Finding:
    """Build a pass-status Finding."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _skipped(*, ctx: DoctorContext, message: str) -> Finding:
    """Build a skipped-status Finding."""
    return Finding(
        check_id=SLUG,
        status="skipped",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _fail(*, ctx: DoctorContext, message: str, path: str | None) -> Finding:
    """Build a fail-status Finding."""
    return Finding(
        check_id=SLUG,
        status="fail",
        message=message,
        path=path,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _render_pass_no_obligations(*, ctx: DoctorContext) -> Finding:
    """Vacuous-pass finding: no PC declares spec_commitments at all."""
    return _pass(
        ctx=ctx,
        message=(
            "unresolved-spec-commitment: no propose-changes declare "
            "spec_commitments.impl_followups[]; nothing to verify"
        ),
    )


def _render_pass_all_resolved(*, ctx: DoctorContext, obligation_count: int) -> Finding:
    """Pass finding: every obligation resolved against a work-item or superseded."""
    return _pass(
        ctx=ctx,
        message=(
            f"unresolved-spec-commitment: every declared spec_commitments."
            f"impl_followups[] id_hint resolves to a work-item with matching "
            f"spec_commitment_hint or has been superseded "
            f"({obligation_count} obligation(s) scanned)"
        ),
    )


def _render_fail(
    *,
    ctx: DoctorContext,
    unresolved: list[Unresolved],
) -> Finding:
    """Fail finding: at least one obligation unresolved + not superseded."""
    summaries = "; ".join(
        f"{entry.id_hint} (from {entry.version_label}/{entry.pc_stem}.md)" for entry in unresolved
    )
    return _fail(
        ctx=ctx,
        message=(
            f"unresolved-spec-commitment: {len(unresolved)} declared "
            f"spec_commitments.impl_followups[] id_hint(s) have no matching "
            f"work-item with spec_commitment_hint in the active impl-plugin's "
            f"work-items store: {summaries}. Corrective action: file each "
            f"missing work-item via the active impl-plugin's "
            f"`capture-work-item` skill, passing `--spec-commitment-hint "
            f"<id_hint>` so the work-item carries the pairing field."
        ),
        path=str(ctx.work_items_provider),
    )


def _evaluate_against_hints(
    *,
    ctx: DoctorContext,
    work_item_hints: set[str],
) -> Finding:
    """Compute the final Finding from collected obligations + work-item hint set."""
    obligations, superseded_set = collect_obligations_and_supersedes(spec_root=ctx.spec_root)
    if not obligations:
        return _render_pass_no_obligations(ctx=ctx)
    unresolved = [
        obligation
        for obligation in obligations
        if obligation.id_hint not in superseded_set and obligation.id_hint not in work_item_hints
    ]
    if not unresolved:
        return _render_pass_all_resolved(ctx=ctx, obligation_count=len(obligations))
    return _render_fail(ctx=ctx, unresolved=unresolved)


def _interpret(*, ctx: DoctorContext, outcome: ProviderOutcome) -> Finding:
    """Map the provider outcome to a Finding (skip on unset/unreachable)."""
    match outcome:
        case ProviderUnset() | ProviderUnreachable():
            return _skipped(
                ctx=ctx,
                message=skip_message(slug_prefix=_SLUG_PREFIX, outcome=outcome),
            )
        case WorkItemsIndex(index=index):
            return _evaluate_against_hints(
                ctx=ctx,
                work_item_hints=hints_from_index(index=index),
            )
        case _:
            assert_never(outcome)


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run unresolved-spec-commitment against `ctx`.

    Acquires work-items via the active impl-plugin's `list-work-items`
    wrapper (per `ctx.work_items_provider`), materializes the
    `spec_commitment_hint` set, walks every `<spec-root>/history/
    vNNN/proposed_changes/<stem>.md` whose paired
    `<stem>-revision.md` carries `decision: accept` or `decision:
    modify`, extracts each declared `spec_commitments.impl_followups[]`
    id_hint, exempts those listed in any later `supersedes[]`, and
    fires `fail` for the remainder. A connection-class failure or an
    unset provider yields a `skipped` Finding.
    """
    return load_work_items_index(ctx=ctx).map(
        lambda outcome: _interpret(ctx=ctx, outcome=outcome),
    )
