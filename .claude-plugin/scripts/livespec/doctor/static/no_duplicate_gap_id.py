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
"""Static-phase doctor check: no_duplicate_gap_id.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" → §"`no-duplicate-gap-id`":

  No two open work items MAY claim the same gap-id label. The check
  fires `fail` when two or more open items share a gap-id. Closed
  items sharing a historical gap-id with an open item are exempt;
  this is the dual of `gap-tracking-one-to-one` viewed from the
  work-items-store side.

Cross-boundary mechanism: the check acquires work-items by invoking
the ACTIVE impl-plugin's `list-work-items` thin-transport wrapper
(resolved from `LIVESPEC_IMPL_LIST_WORK_ITEMS` into
`ctx.work_items_provider`), NOT a direct JSONL file read. This is
plugin-agnostic (plaintext + beads + any future backend). When no
live provider is configured, or the provider is unreachable, the
check returns a `skipped` Finding (never `fail`). See
`_work_items_provider.py`.
"""

from __future__ import annotations

from typing import Any

from returns.io import IOResult
from typing_extensions import assert_never

from livespec.context import DoctorContext
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


SLUG: CheckId = CheckId("doctor-no-duplicate-gap-id")
_SLUG_PREFIX: str = "no-duplicate-gap-id"
_OPEN_STATUSES: frozenset[str] = frozenset({"open", "in_progress", "blocked"})
_DUPLICATE_THRESHOLD: int = 2


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


def _find_duplicate_gap_ids(
    *,
    index: dict[str, dict[str, Any]],
) -> list[tuple[str, list[str]]]:
    """Return sorted (gap_id, [item_ids]) pairs where ≥2 open items share gap_id."""
    grouped: dict[str, list[str]] = {}
    for item_id, record in index.items():
        status = record.get("status")
        if status not in _OPEN_STATUSES:
            continue
        gap_id = record.get("gap_id")
        if not isinstance(gap_id, str):
            continue
        grouped.setdefault(gap_id, []).append(item_id)
    duplicates: list[tuple[str, list[str]]] = []
    for gap_id, item_ids in grouped.items():
        if len(item_ids) >= _DUPLICATE_THRESHOLD:
            duplicates.append((gap_id, sorted(item_ids)))
    return sorted(duplicates)


def _evaluate_index(*, ctx: DoctorContext, index: dict[str, dict[str, Any]]) -> Finding:
    """Apply the invariant against the materialized work-items index."""
    duplicates = _find_duplicate_gap_ids(index=index)
    if not duplicates:
        return _pass(
            ctx=ctx,
            message=(
                f"no-duplicate-gap-id: every open work-item's gap-id is unique "
                f"({len(index)} work-items scanned)"
            ),
        )
    groups_joined = "; ".join(
        f"{gap_id}: [{', '.join(item_ids)}]" for gap_id, item_ids in duplicates
    )
    return _fail(
        ctx=ctx,
        message=(
            f"no-duplicate-gap-id: {len(duplicates)} gap-id(s) claimed by multiple "
            f"open work-items: {groups_joined}. Consolidate or close the duplicates."
        ),
        path=str(ctx.work_items_provider),
    )


def _interpret(*, ctx: DoctorContext, outcome: ProviderOutcome) -> Finding:
    """Map the provider outcome to a Finding (skip on unset/unreachable)."""
    match outcome:
        case ProviderUnset() | ProviderUnreachable():
            return _skipped(
                ctx=ctx,
                message=skip_message(slug_prefix=_SLUG_PREFIX, outcome=outcome),
            )
        case WorkItemsIndex(index=index):
            return _evaluate_index(ctx=ctx, index=index)
        case _:
            assert_never(outcome)


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run no-duplicate-gap-id against `ctx`.

    Acquires work-items via the active impl-plugin's `list-work-items`
    wrapper (per `ctx.work_items_provider`) and applies the
    no-duplicate-gap-id predicate. A connection-class failure or an
    unset provider yields a `skipped` Finding; only an actual
    duplicate-gap-id violation yields `fail`.
    """
    return load_work_items_index(ctx=ctx).map(
        lambda outcome: _interpret(ctx=ctx, outcome=outcome),
    )
