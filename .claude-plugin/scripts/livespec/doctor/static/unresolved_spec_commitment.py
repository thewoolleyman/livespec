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
  [<earlier-id_hint>, ...]` exempt the listed id_hints. When
  `.livespec.jsonc` lacks an impl-plugin in `SUPPORTED_PLUGINS`,
  the invariant surfaces a `skipped` finding rather than fail.

Cross-boundary mechanism:

  The spec describes this check as "querying the active impl-
  plugin's `list-work-items --json` thin-transport skill". In v1
  (matching no-stalled-epic / no-orphan-dependency /
  no-duplicate-gap-id), the check reads the impl-plugin's
  configured work-items store directly via the path declared in
  `.livespec.jsonc`. Only the `livespec-impl-plaintext` backend
  is supported in v1.

Cross-repo dependency:

  The `spec_commitment_hint` field on impl-plaintext work-item
  records is delivered by sibling work-item li-4szyct (impl-
  plaintext-side, not yet landed at the time this check is
  authored). The check queries by JSON path; absence-from-record
  is no-match (= fail finding). Once li-4szyct lands, records
  start carrying the hint and the check resolves successfully.

Helper module: see `_unresolved_spec_commitment_helpers.py` for
the front-matter parser, history walker, and JSONL hint
materializer. This module orchestrates the railway and renders
the Finding messages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.doctor.static._unresolved_spec_commitment_helpers import (
    Unresolved,
    collect_obligations_and_supersedes,
    materialize_work_item_hints,
    resolve_work_items_path,
)
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-unresolved-spec-commitment")


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
    work_items_path: Path,
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
            f"work-item with spec_commitment_hint in "
            f"{work_items_path}: {summaries}. Corrective action: file each "
            f"missing work-item via the active impl-plugin's "
            f"`capture-work-item` skill, passing `--spec-commitment-hint "
            f"<id_hint>` so the work-item carries the pairing field."
        ),
        path=str(work_items_path),
    )


def _evaluate_against_work_items(
    *,
    ctx: DoctorContext,
    work_items_path: Path,
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
    return _render_fail(ctx=ctx, work_items_path=work_items_path, unresolved=unresolved)


def _evaluate(*, ctx: DoctorContext, parsed: Any) -> IOResult[Finding, LivespecError]:
    """Resolve the work-items path and evaluate the invariant."""
    if not isinstance(parsed, dict):
        return IOSuccess(
            _skipped(
                ctx=ctx,
                message=(
                    "unresolved-spec-commitment: .livespec.jsonc root is not an "
                    "object; check skipped"
                ),
            ),
        )
    work_items_path = resolve_work_items_path(project_root=ctx.project_root, config=parsed)
    if work_items_path is None:
        return IOSuccess(
            _skipped(
                ctx=ctx,
                message=(
                    "unresolved-spec-commitment: active impl-plugin is not in the "
                    "v1 supported set (livespec-impl-plaintext) or .livespec.jsonc "
                    "lacks an `implementation` block; check skipped"
                ),
            ),
        )
    if not work_items_path.exists():
        return IOSuccess(
            _evaluate_against_work_items(
                ctx=ctx,
                work_items_path=work_items_path,
                work_item_hints=set(),
            ),
        )
    return fs.read_text(path=work_items_path).bind(
        lambda text: IOSuccess(
            _evaluate_against_work_items(
                ctx=ctx,
                work_items_path=work_items_path,
                work_item_hints=materialize_work_item_hints(jsonl_text=text),
            ),
        ),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run unresolved-spec-commitment against `ctx`.

    Reads `<ctx.project_root>/.livespec.jsonc`, resolves the
    active impl-plugin's work-items JSONL path, materializes the
    `spec_commitment_hint` set, walks every `<spec-root>/history/
    vNNN/proposed_changes/<stem>.md` whose paired
    `<stem>-revision.md` carries `decision: accept` or `decision:
    modify`, extracts each declared `spec_commitments.impl_followups[]`
    id_hint, exempts those listed in any later `supersedes[]`, and
    fires `fail` for the remainder. Failures on the IO track are
    lashed into a skipped-status Finding so the orchestrator's
    stdout contract stays uniform.
    """
    config_path = ctx.project_root / ".livespec.jsonc"
    return (
        fs.read_text(path=config_path)
        .bind(
            lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
        )
        .bind(lambda parsed: _evaluate(ctx=ctx, parsed=parsed))
        .lash(
            lambda err: IOSuccess(
                _skipped(
                    ctx=ctx,
                    message=(
                        f"unresolved-spec-commitment: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                ),
            ),
        )
    )
