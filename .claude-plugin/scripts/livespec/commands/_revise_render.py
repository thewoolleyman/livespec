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
"""Render-lifecycle railway stages for the `revise` sub-command.

Per `SPECIFICATION/spec.md` §"Template manifest" → "Rendering in
the revise lifecycle" + `contracts.md` §"Template manifest wire
contract" → ".livespec.jsonc render-commands shape":

- When a revise pass writes updated `diagram_source` content via
  `resulting_files[]`, the wrapper MUST invoke the project-declared
  render command — an argv-form array (never a shell string) with
  `{source}` and `{output_dir}` substituted as project-root-relative
  paths, run with cwd at the project root.
- The pass MUST be transactional: sources are staged to a working
  location under the project root and rendered THERE; a non-zero
  render exit fails the entire revision (PreconditionError → exit 3)
  with `<spec-target>/` untouched. Only on full success do the
  rendered outputs get committed into the spec tree (after the
  per-decision writes, before the history snapshot).

`_prepare_render_plan` runs BEFORE any spec-tree mutation and
yields a `_RenderPlan`:

- `staging_root` — the staging directory (None when no
  diagram_source writes are present);
- `rendered_copies` — `(staged_abs, final_abs)` pairs to commit
  after the per-decision writes;
- `manifest_paths` — every manifest-declared relative path (used
  by the history snapshot's all-three-kinds axis even on
  markdown-only passes).

Template-manifest resolution duplicates the small loader shape in
`doctor/static/_template_manifest.py` — the layered-architecture
import-linter contract treats `commands` and `doctor` as
independent siblings that cannot import each other.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from returns.io import IOResult

from livespec.commands._revise_render_config import (
    _load_render_argv,
    _load_spec_files,
)
from livespec.errors import LivespecError, PreconditionError
from livespec.io import fs, proc
from livespec.schemas.dataclasses.revise_input import RevisionInput
from livespec.schemas.dataclasses.template_config import SpecFileDecl

__all__: list[str] = [
    "_RenderPlan",
    "_apply_rendered_outputs",
    "_cleanup_render_staging",
    "_prepare_render_plan",
]


_STAGING_PREFIX = ".livespec-render-staging-"


@dataclass(frozen=True, kw_only=True, slots=True)
class _RenderPlan:
    """The pre-mutation render outcome threaded through the revise railway."""

    staging_root: Path | None = None
    rendered_copies: tuple[tuple[Path, Path], ...] = ()
    manifest_paths: tuple[str, ...] = ()


def _diagram_source_writes(
    *,
    revise_input: RevisionInput,
    spec_files: dict[str, SpecFileDecl],
) -> list[tuple[str, str]]:
    """Collect `(rel_path, content)` resulting_files writes of kind diagram_source."""
    writes: list[tuple[str, str]] = []
    for decision in revise_input.decisions:
        if str(decision.get("decision", "")) not in ("accept", "modify"):
            continue
        resulting_files = decision.get("resulting_files", [])
        if not isinstance(resulting_files, list):
            continue
        for entry in resulting_files:
            if not isinstance(entry, dict):
                continue
            rel_path = str(entry.get("path", ""))
            decl = spec_files.get(rel_path)
            if decl is not None and decl.kind == "diagram_source":
                writes.append((rel_path, str(entry.get("content", ""))))
    return writes


def _rendered_outputs_for_source(
    *,
    source_rel: str,
    spec_files: dict[str, SpecFileDecl],
) -> list[str]:
    """Manifest-declared rendered relative paths derived from `source_rel`."""
    return sorted(
        rendered_rel
        for rendered_rel, decl in spec_files.items()
        if decl.kind == "diagram_rendered" and decl.derived_from == source_rel
    )


def _substituted_argv(
    *,
    render_argv: list[str],
    source_rel_to_project: str,
    output_dir_rel_to_project: str,
) -> list[str]:
    """Substitute `{source}` and `{output_dir}` literally in the argv."""
    return [
        arg.replace("{source}", source_rel_to_project).replace(
            "{output_dir}",
            output_dir_rel_to_project,
        )
        for arg in render_argv
    ]


def _render_one(
    *,
    staging_root: Path,
    project_root: Path,
    source_rel: str,
    render_argv: list[str],
) -> IOResult[None, LivespecError]:
    """Run the render command against one staged source; non-zero exit fails."""
    source_rel_to_project = (staging_root.relative_to(project_root) / source_rel).as_posix()
    output_dir_rel_to_project = str(PurePosixPath(source_rel_to_project).parent)
    argv = _substituted_argv(
        render_argv=render_argv,
        source_rel_to_project=source_rel_to_project,
        output_dir_rel_to_project=output_dir_rel_to_project,
    )
    return proc.run_subprocess(
        argv=argv, cwd=project_root
    ).bind(
        lambda completed: (  # pyright: ignore[reportArgumentType]
            IOResult.from_value(None)
            if completed.returncode == 0
            else IOResult.from_failure(
                PreconditionError(
                    f"revise: render command failed (exit "
                    f"{completed.returncode}) for {source_rel}: "
                    f"{completed.stderr.strip()[-500:]}",
                ),
            )
        ),
    )


def _verify_staged_outputs(
    *,
    rendered_copies: tuple[tuple[Path, Path], ...],
) -> IOResult[None, LivespecError]:
    """Every manifest-declared rendered output MUST exist in staging."""
    missing = sorted(str(staged) for staged, _final in rendered_copies if not staged.is_file())
    if missing:
        return IOResult.from_failure(
            PreconditionError(
                f"revise: render command succeeded but the manifest-declared "
                f"rendered output(s) were not produced: {', '.join(missing)}",
            ),
        )
    return IOResult.from_value(None)


def _cleanup_then_fail(
    *,
    staging_root: Path,
    err: LivespecError,
) -> IOResult[_RenderPlan, LivespecError]:
    """Best-effort staging removal, then surface the ORIGINAL error."""
    return (
        fs.rmtree(path=staging_root)
        .lash(lambda _cleanup_err: IOResult.from_value(None))
        .bind(lambda _none: IOResult.from_failure(err))
    )


def _stage_and_render(
    *,
    source_writes: list[tuple[str, str]],
    spec_files: dict[str, SpecFileDecl],
    spec_target: Path,
    project_root: Path,
    render_argv: list[str],
    manifest_paths: tuple[str, ...],
) -> IOResult[_RenderPlan, LivespecError]:
    """Write staged sources, render each, verify outputs, yield the plan.

    The staging directory sits under the project root so the
    substituted `{source}` / `{output_dir}` argv values stay
    project-root-relative per the wire contract. Any failure
    removes the staging directory and re-surfaces the failure —
    `<spec-target>/` has not been touched at this point.
    """
    staging_root = project_root / f"{_STAGING_PREFIX}{uuid.uuid4().hex}"
    rendered_copies: list[tuple[Path, Path]] = []
    for source_rel, _content in source_writes:
        for rendered_rel in _rendered_outputs_for_source(
            source_rel=source_rel,
            spec_files=spec_files,
        ):
            staged = staging_root / Path(source_rel).parent / Path(rendered_rel).name
            rendered_copies.append((staged, spec_target / rendered_rel))
    plan = _RenderPlan(
        staging_root=staging_root,
        rendered_copies=tuple(rendered_copies),
        manifest_paths=manifest_paths,
    )
    railway: IOResult[None, LivespecError] = IOResult.from_value(None)
    for source_rel, content in source_writes:
        railway = railway.bind(
            lambda _none, source_rel=source_rel, content=content: fs.write_text(
                path=staging_root / source_rel,
                text=content,
            ),
        )
    for source_rel, _content in source_writes:
        railway = railway.bind(
            lambda _none, source_rel=source_rel: _render_one(
                staging_root=staging_root,
                project_root=project_root,
                source_rel=source_rel,
                render_argv=render_argv,
            ),
        )
    return (
        railway.bind(
            lambda _none: _verify_staged_outputs(
                rendered_copies=plan.rendered_copies,
            ),
        )
        .map(lambda _none: plan)
        .lash(
            lambda err: _cleanup_then_fail(staging_root=staging_root, err=err),
        )
    )


def _plan_for_manifest(
    *,
    revise_input: RevisionInput,
    spec_target: Path,
    project_root: Path,
    spec_files: dict[str, SpecFileDecl] | None,
) -> IOResult[_RenderPlan, LivespecError]:
    """Build the render plan once the manifest (or its absence) is known."""
    if spec_files is None:
        return IOResult.from_value(_RenderPlan())
    manifest_paths = tuple(sorted(spec_files))
    source_writes = _diagram_source_writes(
        revise_input=revise_input,
        spec_files=spec_files,
    )
    if not source_writes:
        return IOResult.from_value(_RenderPlan(manifest_paths=manifest_paths))
    return _load_render_argv(project_root=project_root).bind(
        lambda render_argv: _stage_and_render(
            source_writes=source_writes,
            spec_files=spec_files,
            spec_target=spec_target,
            project_root=project_root,
            render_argv=render_argv,
            manifest_paths=manifest_paths,
        ),
    )


def _prepare_render_plan(
    *,
    revise_input: RevisionInput,
    spec_target: Path,
    project_root: Path,
) -> IOResult[_RenderPlan, LivespecError]:
    """Stage + render every diagram_source write BEFORE any tree mutation.

    Sub-spec targets and projects without a resolvable v2 manifest
    yield the no-op plan (today's behavior, zero overhead). The
    main tree under a v2 manifest always carries `manifest_paths`
    (the history snapshot's all-three-kinds axis applies even to
    markdown-only passes); diagram_source writes additionally
    stage + render, failing transactionally on any render error.
    """
    if spec_target.resolve() != (project_root / "SPECIFICATION").resolve():
        return IOResult.from_value(_RenderPlan())
    return _load_spec_files(project_root=project_root).bind(
        lambda spec_files: _plan_for_manifest(
            revise_input=revise_input,
            spec_target=spec_target,
            project_root=project_root,
            spec_files=spec_files,
        ),
    )


def _apply_rendered_outputs(
    *,
    render_plan: _RenderPlan,
) -> IOResult[None, LivespecError]:
    """Commit the staged rendered outputs into the spec tree (post-writes)."""
    railway: IOResult[None, LivespecError] = IOResult.from_value(None)
    for staged, final in render_plan.rendered_copies:
        railway = railway.bind(
            lambda _none, staged=staged, final=final: fs.copy_file(
                source=staged,
                target=final,
            ),
        )
    return railway


def _cleanup_render_staging(
    *,
    render_plan: _RenderPlan,
) -> IOResult[None, LivespecError]:
    """Remove the staging directory (no-op for plan-less passes)."""
    if render_plan.staging_root is None:
        return IOResult.from_value(None)
    return fs.rmtree(path=render_plan.staging_root)
