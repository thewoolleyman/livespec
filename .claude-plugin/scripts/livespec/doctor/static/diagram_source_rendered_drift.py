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
"""Static-phase doctor check: diagram-source-rendered-drift.

Per `SPECIFICATION/spec.md` §"Template manifest" →
"Heading-coverage and doctor-static rewiring": warn when a
`diagram_rendered` file's mtime predates its `derived_from`
source's mtime (the spec-sanctioned cheap proxy for "the rendered
output does not match a fresh re-render"). The check catches the
case where someone edits diagram source manually outside the
revise flow and forgets to re-render.

Manifest-driven via the `_template_manifest` shared loader: the
pairings come from the active template's `spec_files` manifest
(every `kind: diagram_rendered` entry's `derived_from`). Sub-spec
trees and v1/no-manifest templates yield a `skipped` finding.
Pairs whose files are absent on disk are silently skipped —
file-presence is `template_files_present`'s invariant, and double
reporting would be noise.

`warn` (not `fail`) per the spec's SHOULD-warn wording: drift is a
housekeeping nudge (productivity-grade), not a structural
contract violation; the wrapper exit code is unaffected.
"""

from __future__ import annotations

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.doctor.static._template_manifest import (
    is_main_spec_root,
    load_active_template_spec_files,
)
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding
from livespec.schemas.dataclasses.template_config import SpecFileDecl
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-diagram-source-rendered-drift")


def _finding(*, ctx: DoctorContext, status: str, message: str) -> Finding:
    """Construct this check's Finding with the canonical payload shape."""
    return Finding(
        check_id=SLUG,
        status=status,
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _rendered_pairs(
    *,
    spec_files: dict[str, SpecFileDecl] | None,
) -> list[tuple[str, str]]:
    """Enumerate `(rendered_rel, source_rel)` pairs from the manifest, sorted.

    A `diagram_rendered` entry without `derived_from` cannot occur
    in a schema-valid manifest (the validator enforces presence and
    resolution), but the guard keeps the enumeration total.
    """
    if spec_files is None:
        return []
    return sorted(
        (rendered_rel, decl.derived_from)
        for rendered_rel, decl in spec_files.items()
        if decl.kind == "diagram_rendered" and decl.derived_from is not None
    )


def _collect_stale(
    *,
    ctx: DoctorContext,
    pairs: list[tuple[str, str]],
) -> IOResult[list[str], LivespecError]:
    """Fold the pairs into the list of stale-pair descriptions.

    A pair is stale when both files exist and the rendered output's
    mtime is strictly older than the source's mtime. Pairs with
    absent files are skipped (presence is template_files_present's
    invariant).
    """
    accumulator: IOResult[list[str], LivespecError] = IOResult.from_value([])
    for rendered_rel, source_rel in pairs:
        rendered_path = ctx.spec_root / rendered_rel
        source_path = ctx.spec_root / source_rel
        if not (rendered_path.is_file() and source_path.is_file()):
            continue
        accumulator = accumulator.bind(
            lambda stale,
            rendered_path=rendered_path,
            source_path=source_path,
            rendered_rel=rendered_rel,
            source_rel=source_rel: fs.stat_mtime(path=source_path).bind(
                lambda source_mtime,
                rendered_path=rendered_path,
                rendered_rel=rendered_rel,
                source_rel=source_rel,
                stale=stale: fs.stat_mtime(path=rendered_path).map(
                    lambda rendered_mtime: (
                        [*stale, f"{rendered_rel} predates {source_rel}"]
                        if rendered_mtime < source_mtime
                        else stale
                    ),
                ),
            ),
        )
    return accumulator


def _evaluate(
    *,
    ctx: DoctorContext,
    spec_files: dict[str, SpecFileDecl] | None,
) -> IOResult[Finding, LivespecError]:
    """Evaluate the manifest's rendered pairings into a Finding."""
    pairs = _rendered_pairs(spec_files=spec_files)
    if not pairs:
        return IOSuccess(
            _finding(
                ctx=ctx,
                status="skipped",
                message=(
                    "diagram-source-rendered-drift: the active template declares "
                    "no diagram_source/diagram_rendered pairings"
                ),
            ),
        )
    return _collect_stale(ctx=ctx, pairs=pairs).map(
        lambda stale: _verdict(ctx=ctx, stale=stale),
    )


def _verdict(*, ctx: DoctorContext, stale: list[str]) -> Finding:
    """Fold the stale-pair list into the final warn/pass Finding."""
    if stale:
        return _finding(
            ctx=ctx,
            status="warn",
            message=(
                f"diagram-source-rendered-drift: {len(stale)} rendered "
                f"output(s) predate their source: {'; '.join(stale)}. "
                f"Corrective action: re-render via a revise pass that "
                f"touches the source (or run the project's render command "
                f"directly)"
            ),
        )
    return _finding(
        ctx=ctx,
        status="pass",
        message=(
            "diagram-source-rendered-drift: every declared diagram_rendered "
            "output is at least as fresh as its diagram_source"
        ),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the diagram-source-rendered-drift check against `ctx`.

    Sub-spec trees yield `skipped` (no template manifest); the main
    tree loads the active template's manifest and evaluates every
    `diagram_rendered`/`derived_from` pairing's mtimes.
    """
    if not is_main_spec_root(ctx=ctx):
        return IOSuccess(
            _finding(
                ctx=ctx,
                status="skipped",
                message=(
                    "diagram-source-rendered-drift: sub-spec trees carry " "no template manifest"
                ),
            ),
        )
    return load_active_template_spec_files(project_root=ctx.project_root).bind(
        lambda spec_files: _evaluate(ctx=ctx, spec_files=spec_files),
    )
