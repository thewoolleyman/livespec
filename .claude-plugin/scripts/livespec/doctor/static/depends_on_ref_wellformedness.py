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
"""Static-phase doctor check: depends_on_ref_wellformedness.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants"
→ §"`depends_on-ref-wellformedness`":

  For every OPEN work-item's `depends_on` array, the invariant
  enforces:

  1. Discriminator present. Every entry MUST have a `kind` field
     whose value is one of `local`, `sibling_work_item`,
     `pull_request`, `branch`. Missing or unknown `kind` fires
     `fail`.
  2. Per-kind required fields present. `local` requires
     `work_item_id`; `sibling_work_item` requires `repo` and
     `work_item_id`; `pull_request` requires `repo` and `number`;
     `branch` requires `repo` and `name`. Missing required fields
     fire `fail` with the entry's index in the array.
  3. `repo` resolves to a configured target. For every entry with
     a `repo` field, the value MUST be a key in `.livespec.jsonc`'s
     `cross_repo_targets` block. Unresolvable `repo` values fire
     `fail` with the value and a hint pointing to the manifest.

  Closed records are out of scope (legacy bare-string entries and
  historical typed entries are tolerated to keep audit trail
  readable). Bare-string entries on open records fire `fail` under
  (1) since they lack a `kind` field; this overlaps with
  `no-orphan-dependency`'s data-migration narration but the two
  signals are complementary (well-formedness vs resolvability).

Cross-boundary mechanism: the work-items are acquired by invoking
the ACTIVE impl-plugin's `list-work-items` thin-transport wrapper
(resolved from `LIVESPEC_IMPL_LIST_WORK_ITEMS` into
`ctx.work_items_provider`), NOT a direct JSONL file read. This is
plugin-agnostic (plaintext + beads + any future backend). When no
live provider is configured, or the provider is unreachable, the
check returns a `skipped` Finding (never `fail`). See
`_work_items_provider.py`. The `cross_repo_targets` manifest is
still read from `.livespec.jsonc` (best-effort).
"""

from __future__ import annotations

from typing import Any

from livespec_runtime.cross_repo.types import CrossRepoManifest
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


SLUG: CheckId = CheckId("doctor-depends_on-ref-wellformedness")
_SLUG_PREFIX: str = "depends_on-ref-wellformedness"


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


def _entry_repo(*, entry: object) -> str | None:
    """Return the `repo` attribute if present, else None (LocalDependency has no repo)."""
    repo = getattr(entry, "repo", None)
    if isinstance(repo, str):
        return repo
    return None


def _check_entry(
    *,
    item_id: str,
    index_position: int,
    raw: Any,
    manifest: CrossRepoManifest,
) -> str | None:
    """Validate a single depends_on entry; return a failure narration or None."""
    if not isinstance(raw, dict):
        return (
            f"{item_id}#{index_position}: entry is not a typed object "
            f"(got {type(raw).__name__}); v072 requires typed-dict form"
        )
    parsed_result = cross_repo_parse.parse_entry(parsed=raw)
    if not isinstance(parsed_result, Success):
        err = parsed_result.failure()
        return f"{item_id}#{index_position}: {err}"
    entry = parsed_result.unwrap()
    repo = _entry_repo(entry=entry)
    if repo is not None and repo not in manifest.targets:
        return (
            f"{item_id}#{index_position}: repo {repo!r} not in "
            f".livespec.jsonc's `cross_repo_targets` block"
        )
    return None


def _find_failures(
    *,
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> list[str]:
    """Walk every OPEN record's depends_on; return sorted failure narrations."""
    failures: list[str] = []
    for item_id, record in index.items():
        status_value = record.get("status")
        if status_value != "open":
            continue
        deps = record.get("depends_on")
        if not isinstance(deps, list):
            continue
        for position, raw in enumerate(deps):
            failure = _check_entry(
                item_id=item_id,
                index_position=position,
                raw=raw,
                manifest=manifest,
            )
            if failure is not None:
                failures.append(failure)
    return sorted(failures)


def _evaluate_index(
    *,
    ctx: DoctorContext,
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> Finding:
    """Apply the invariant against the materialized work-items index."""
    failures = _find_failures(index=index, manifest=manifest)
    if not failures:
        return _make_finding(
            ctx=ctx,
            status="pass",
            message=(
                f"depends_on-ref-wellformedness: every open work-item's depends_on "
                f"entries are well-formed ({len(index)} work-items scanned)"
            ),
        )
    joined = "; ".join(failures)
    return _make_finding(
        ctx=ctx,
        status="fail",
        message=(
            f"depends_on-ref-wellformedness: {len(failures)} ill-formed depends_on "
            f"entry(ies): {joined}."
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
    """Run depends_on-ref-wellformedness against `ctx`.

    Reads the `cross_repo_targets` manifest from `.livespec.jsonc`
    (best-effort), acquires work-items via the active impl-plugin's
    `list-work-items` wrapper (per `ctx.work_items_provider`), and
    applies the well-formedness predicate. A connection-class failure
    or an unset provider yields a `skipped` Finding; only an actual
    ill-formed entry yields `fail`. The IO track is lashed back to a
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
                _make_finding(
                    ctx=ctx,
                    status="skipped",
                    message=(
                        f"depends_on-ref-wellformedness: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                )
            )
        )
    )
