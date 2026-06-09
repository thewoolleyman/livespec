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
"""Static-phase doctor check: no_stalled_epic.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" → §"`no-stalled-epic`":

  A work-item with `type == "epic"` AND `status` in `{open, in_progress}`
  whose `depends_on` is non-empty AND every entry resolves to a closed
  work-item / PR / branch is "stalled" — the work it represents is
  logically complete but the epic record has not been transitioned to
  `closed`. The check fires `fail` (not `warn`) per the structural-not-
  staleness classification: an epic semantically aggregates its sub-
  tasks, so all blockers closed + epic open is a data-model
  contradiction.

  Empty `depends_on` is EXEMPT (vacuous-truth guard) — a freshly filed
  epic with no declared sub-tasks is not yet stalled.

  Unresolvable `depends_on` entries (referenced ids missing from the
  store, schema-malformed entries, or cross-repo entries resolving to
  `unknown`) MUST NOT fire `no-stalled-epic` — that drift class is
  `no-orphan-dependency`'s domain.

  When the epic's `depends_on` carries non-local typed entries
  (sibling_work_item / pull_request / branch), the check walks them
  via `livespec_runtime.cross_repo.resolve_ref` and treats any `open`
  external dependency as a legitimate stall reason (suppressing the
  fail). Resolved `closed` counts toward all-closed.

Cross-boundary mechanism:

  The work-items are acquired by invoking the ACTIVE impl-plugin's
  `list-work-items` thin-transport wrapper (resolved from
  `LIVESPEC_IMPL_LIST_WORK_ITEMS` into `ctx.work_items_provider`),
  NOT a direct JSONL file read. This is plugin-agnostic (plaintext +
  beads + any future backend). When no live provider is configured,
  or the provider is unreachable, the check returns a `skipped`
  Finding (never `fail`). See `_work_items_provider.py`. The
  `cross_repo_targets` manifest is still read from `.livespec.jsonc`
  (best-effort) for non-local-ref resolution.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from livespec_runtime.cross_repo.resolve import resolve_ref
from livespec_runtime.cross_repo.types import CrossRepoManifest, RefStatus
from returns.io import IOResult, IOSuccess
from returns.result import Success
from typing_extensions import assert_never

from livespec.context import DoctorContext
from livespec.doctor.static._no_orphan_dependency_helpers import load_manifest_io
from livespec.doctor.static._work_items_provider import (
    ProviderOutcome,
    ProviderUnreachable,
    ProviderUnset,
    WorkItemsIndex,
    load_work_items_index,
    skip_message,
)
from livespec.errors import LivespecError
from livespec.parse import cross_repo as cross_repo_parse
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-no-stalled-epic")
_SLUG_PREFIX: str = "no-stalled-epic"


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
    """Build a skipped-status Finding (preferred over fail when the provider is unavailable)."""
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


def _local_status(*, work_item_id: str, index: dict[str, dict[str, Any]]) -> RefStatus:
    """Return RefStatus for a same-repo id by scanning the materialized index."""
    record = index.get(work_item_id)
    if record is None:
        return RefStatus.UNKNOWN
    if record.get("status") == "closed":
        return RefStatus.CLOSED
    return RefStatus.OPEN


def _make_local_lookup(*, index: dict[str, dict[str, Any]]) -> Callable[[str], RefStatus]:
    """Build the local_status_lookup callable resolve_ref expects."""
    return lambda work_item_id: _local_status(work_item_id=work_item_id, index=index)


def _resolve_typed_dep(
    *,
    raw: dict[str, Any],
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> RefStatus:
    """Parse a typed-dict entry and dispatch through resolve_ref."""
    parsed_result = cross_repo_parse.parse_entry(parsed=raw)
    if not isinstance(parsed_result, Success):
        return RefStatus.UNKNOWN
    return resolve_ref(
        entry=parsed_result.unwrap(),
        manifest=manifest,
        local_status_lookup=_make_local_lookup(index=index),
    )


def _resolve_dep(
    *,
    raw: Any,
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> RefStatus:
    """Return RefStatus for a single depends_on entry (bare-string or typed-dict)."""
    if isinstance(raw, str):
        return _local_status(work_item_id=raw, index=index)
    if isinstance(raw, dict):
        return _resolve_typed_dep(raw=raw, index=index, manifest=manifest)
    return RefStatus.UNKNOWN


def _find_stalled_epics(
    *,
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> list[str]:
    """Return sorted ids of epics whose every depends_on entry resolves to CLOSED."""
    stalled: list[str] = []
    for item_id, record in index.items():
        if record.get("type") != "epic":
            continue
        status = record.get("status")
        if status not in ("open", "in_progress"):
            continue
        deps = record.get("depends_on")
        if not isinstance(deps, list) or len(deps) == 0:
            continue
        all_closed = True
        for raw in deps:
            if _resolve_dep(raw=raw, index=index, manifest=manifest) != RefStatus.CLOSED:
                all_closed = False
                break
        if all_closed:
            stalled.append(item_id)
    return sorted(stalled)


def _evaluate_index(
    *,
    ctx: DoctorContext,
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> Finding:
    """Apply the invariant against the materialized work-items index."""
    stalled = _find_stalled_epics(index=index, manifest=manifest)
    if not stalled:
        return _pass(
            ctx=ctx,
            message=(
                f"no-stalled-epic: no epics with all-closed depends_on detected "
                f"({len(index)} work-items scanned)"
            ),
        )
    ids_joined = ", ".join(stalled)
    return _fail(
        ctx=ctx,
        message=(
            f"no-stalled-epic: {len(stalled)} epic(s) with all depends_on entries closed "
            f"but epic still open/in_progress: {ids_joined}. "
            "Close the epic with an appropriate resolution OR add fresh depends_on entries."
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
            return _skipped(
                ctx=ctx,
                message=skip_message(slug_prefix=_SLUG_PREFIX, outcome=outcome),
            )
        case WorkItemsIndex(index=index):
            return _evaluate_index(ctx=ctx, index=index, manifest=manifest)
        case _:
            assert_never(outcome)


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run no-stalled-epic against `ctx`.

    Reads the `cross_repo_targets` manifest from `.livespec.jsonc`
    (best-effort), acquires work-items via the active impl-plugin's
    `list-work-items` wrapper (per `ctx.work_items_provider`), and
    applies the no-stalled-epic predicate. A connection-class failure
    or an unset provider yields a `skipped` Finding; only an actual
    stalled epic yields `fail`. The IO track is lashed back to a
    `skipped` Finding so the orchestrator's stdout contract stays
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
                _skipped(
                    ctx=ctx,
                    message=(
                        f"no-stalled-epic: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                ),
            ),
        )
    )
