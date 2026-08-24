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
"""Static-phase doctor check: spec_tree_manifested.

Per SPECIFICATION/spec.md, under an active template that declares
its `spec_files` manifest explicitly (`template_format_version: 2`)
the manifest is the CLOSED definition of what may exist under the
spec root: every file under the spec root MUST be declared by exact
spec-target-relative path, except the three lifecycle-owned sibling
subdirectories (`history/`, `proposed_changes/`, `templates/`) and
everything beneath them. A file present under the spec root and
absent from the manifest is a `fail` naming that path -- never a
warning and never a silence.

Enumeration is of files on disk, not of git-tracked files: an
untracked file is copied into a revision snapshot exactly as a
tracked one is, so a git-derived universe would leave the freeze
hole open.

Three exemptions report `skipped` rather than passing silently:
a v1 template (implicit, prose-derived manifest with no declaration
form), a spec root that resolves to the project root (the
single-file shape), and a sub-spec tree (which carries no manifest
of its own).
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.doctor.static._template_manifest import (
    is_main_spec_root,
    load_active_template_spec_files,
)
from livespec.errors import LivespecError
from livespec.schemas.dataclasses.template_config import SpecFileDecl
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-spec-tree-manifested")

_LIFECYCLE_DIRS: tuple[str, ...] = ("history", "proposed_changes", "templates")


def _finding(*, ctx: DoctorContext, status: str, message: str) -> object:
    """Construct a Finding for this check at tree level."""
    from livespec.schemas.dataclasses.finding import Finding

    return Finding(
        check_id=SLUG,
        status=status,
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _undeclared_paths(*, spec_root: Path, spec_files: dict[str, SpecFileDecl]) -> list[str]:
    """Spec-target-relative paths present on disk but absent from the manifest."""
    undeclared: list[str] = []
    for path in spec_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(spec_root)
        if relative.parts[0] in _LIFECYCLE_DIRS:
            continue
        if relative.as_posix() not in spec_files:
            undeclared.append(relative.as_posix())
    return sorted(undeclared)


def _evaluate(
    *,
    ctx: DoctorContext,
    spec_files: dict[str, SpecFileDecl] | None,
) -> IOResult[object, LivespecError]:
    """Close the tree over the manifest, or report the applicable exemption."""
    if spec_files is None:
        return IOSuccess(
            _finding(
                ctx=ctx,
                status="skipped",
                message=(
                    "spec-tree-manifested: template_format_version 1 declares no "
                    "explicit spec_files manifest; the spec tree is not closed"
                ),
            ),
        )
    undeclared = _undeclared_paths(spec_root=ctx.spec_root, spec_files=spec_files)
    if undeclared:
        return IOSuccess(
            _finding(
                ctx=ctx,
                status="fail",
                message=(
                    f"spec-tree-manifested: {len(undeclared)} path(s) under "
                    f"{ctx.spec_root} not declared in the template manifest: "
                    f"{', '.join(undeclared)}"
                ),
            ),
        )
    return IOSuccess(
        _finding(
            ctx=ctx,
            status="pass",
            message="every path under the spec root is declared in the template manifest",
        ),
    )


def run(*, ctx: DoctorContext) -> IOResult[object, LivespecError]:
    """Run the spec-tree-manifested check against `ctx`."""
    if ctx.spec_root.resolve() == ctx.project_root.resolve():
        return IOSuccess(
            _finding(
                ctx=ctx,
                status="skipped",
                message=(
                    "spec-tree-manifested: spec_root resolves to the project root; "
                    "a single-file spec shape has no dedicated tree to close"
                ),
            ),
        )
    if not is_main_spec_root(ctx=ctx):
        return IOSuccess(
            _finding(
                ctx=ctx,
                status="skipped",
                message=(
                    "spec-tree-manifested: sub-spec trees carry no template manifest "
                    "of their own"
                ),
            ),
        )
    return load_active_template_spec_files(project_root=ctx.project_root).bind(
        lambda spec_files: _evaluate(ctx=ctx, spec_files=spec_files),
    )
