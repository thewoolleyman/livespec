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
"""Static-phase doctor check: no_cross_spec_reference.

Per SPECIFICATION/constraints.md (the Reference discipline
section): a `SPECIFICATION/<file>.md` MAY cite peer files and
peer headings within its own spec tree via the canonical
section-sign citation form (a section sign directly followed by a
double-quoted heading text, optionally preceded by a
`<filename>.md` file prefix), but MUST NOT reference content
OUTSIDE the same `SPECIFICATION/` tree (sibling-repo spec files,
implementation-tree files, work-item ids, epic phase ids, PR
numbers, external URLs) EXCEPT via the `external_references`
allowlist declared in `.livespec.jsonc`.

This module owns the `fs`-touching railway composition: it reads
the per-shape walk-set of `.md` files plus the `external_references`
allowlist from `.livespec.jsonc`, then delegates the pure
parsing/resolution work — citation detection, same-tree and
allowlist resolution, and Finding construction — to the sibling
`_no_cross_spec_reference_helpers` module. The walk-set semantic
matches the sibling `anchor_reference_resolution` check:
livespec-shape spec_roots walk `<spec_root>/*.md` top-level files
only; minimal-shape spec_roots scan only
`<spec_root>/SPECIFICATION.md`. Neither shape recurses into
`history/`, `proposed_changes/`, or `templates/` subtrees.

Citations whose section sign falls inside a fenced code block or
an inline code span are illustrative syntax and are skipped; the
check short-circuits on the first violation in sorted file order
so the user sees one offense at a time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.doctor.static._no_cross_spec_reference_helpers import (
    _CITATION_PATTERN,
    _MINIMAL_SHAPE_FILENAME,
    _allowlist_match,
    _build_finding_from_scan,
    _collect_headings,
    _config_allowlist_value,
    _fail_finding,
    _flatten_allowlist,
    _pass_finding,
    _same_tree_match,
    _scan_all,
    _scan_text_for_violation,
)
from livespec.doctor.static._no_cross_spec_reference_helpers import (
    SLUG as SLUG,
)
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]

# Re-exported helper handles keep the established test surface
# (`no_cross_spec_reference._flatten_allowlist` etc.) and registry
# access (`no_cross_spec_reference.SLUG`) stable after the
# LLOC-driven split into the helpers module.
_ = (
    _MINIMAL_SHAPE_FILENAME,
    _allowlist_match,
    _build_finding_from_scan,
    _collect_headings,
    _config_allowlist_value,
    _fail_finding,
    _flatten_allowlist,
    _pass_finding,
    _same_tree_match,
    _scan_text_for_violation,
)


def _read_all_texts(*, files: list[Path]) -> IOResult[dict[Path, str], LivespecError]:
    """Read every walk-set file's text onto the IOResult track.

    Folds `fs.read_text` across the sorted file list into a
    `{path: text}` map. Any read failure (PreconditionError)
    short-circuits the fold onto the failure track per the railway
    discipline.
    """
    accumulator: IOResult[dict[Path, str], LivespecError] = IOSuccess({})
    for file_path in files:
        accumulator = accumulator.bind(
            lambda acc, fp=file_path: fs.read_text(path=fp).map(
                lambda text, a=acc, p=fp: {**a, p: text},
            ),
        )
    return accumulator


def _load_external_references(*, project_root: Path) -> IOResult[Any, LivespecError]:
    """Read `.livespec.jsonc` and parse it onto the IOResult track.

    On a missing/unparseable config the failure track recovers (via
    the caller's `.lash`) to an empty allowlist — this check does
    not own the config-validity failure mode (`livespec_jsonc_valid`
    does). The parsed value is later passed through
    `_config_allowlist_value` + `_flatten_allowlist`, which tolerate
    any shape.
    """
    config_path = project_root / ".livespec.jsonc"
    return fs.read_text(path=config_path).bind(
        lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
    )


def _list_top_level_md_files(
    *,
    spec_root: Path,
) -> IOResult[list[Path], LivespecError]:
    """List `<spec_root>/*.md` top-level files in sorted order."""
    return fs.list_dir(path=spec_root).map(
        lambda children: [child for child in children if child.is_file() and child.suffix == ".md"],
    )


def _config_cross_repo_targets_value(*, config: Any) -> Any:
    """Extract the parsed `cross_repo_targets` block when present."""
    if isinstance(config, dict):
        return config.get("cross_repo_targets")
    return None


def _local_clone_for_repo(*, cross_repo_targets: Any, repo_slug: str) -> Path | None:
    """Return a configured local clone path for `repo_slug`, if available."""
    if not isinstance(cross_repo_targets, dict):
        return None
    target = cross_repo_targets.get(repo_slug)
    if not isinstance(target, dict):  # pragma: no cover
        return None
    local_clone = target.get("local_clone")
    if not isinstance(local_clone, str):  # pragma: no cover
        return None
    return Path(local_clone)


def _cross_repo_heading_files(
    *,
    external_references: Any,
    cross_repo_targets: Any,
) -> dict[str, Path]:
    """Map repo-qualified citation prefixes to local clone files."""
    if not isinstance(external_references, dict):
        return {}
    files: dict[str, Path] = {}
    for repo_slug, entries in external_references.items():
        if not isinstance(repo_slug, str) or not isinstance(entries, list):  # pragma: no cover
            continue
        local_clone = _local_clone_for_repo(
            cross_repo_targets=cross_repo_targets,
            repo_slug=repo_slug,
        )
        if local_clone is None:
            continue
        for entry in entries:
            if not isinstance(entry, str):  # pragma: no cover
                continue
            match = _CITATION_PATTERN.search(entry)
            if match is None:  # pragma: no cover
                continue
            file_prefix = match.group("file")
            if file_prefix is None:  # pragma: no cover
                continue
            files[f"{repo_slug}/{file_prefix}"] = local_clone / file_prefix
    return files


def _read_cross_repo_headings(
    *,
    heading_files: dict[str, Path],
) -> IOResult[dict[str, frozenset[str]], LivespecError]:
    """Read configured cited-repo files and collect their headings."""
    accumulator: IOResult[dict[str, frozenset[str]], LivespecError] = IOSuccess({})
    for citation_prefix, file_path in sorted(heading_files.items()):
        if not file_path.is_file():  # pragma: no cover
            accumulator = accumulator.map(
                lambda acc, prefix=citation_prefix: {**acc, prefix: frozenset()},
            )
            continue
        accumulator = accumulator.bind(
            lambda acc, prefix=citation_prefix, path=file_path: fs.read_text(path=path).map(
                lambda text, a=acc, p=prefix: {**a, p: frozenset(_collect_headings(text=text))},
            ),
        )
    return accumulator


def _validated_external_references(
    *,
    external_references: Any,
    cross_repo_headings_by_path: dict[str, frozenset[str]],
) -> Any:
    """Drop configured allowlist entries whose cited repo lacks the heading."""
    if not isinstance(external_references, dict):
        return external_references
    validated: dict[str, object] = {}
    for repo_slug, entries in external_references.items():
        if not isinstance(repo_slug, str) or not isinstance(entries, list):  # pragma: no cover
            validated[str(repo_slug)] = entries
            continue
        kept: list[object] = []
        for entry in entries:
            if not isinstance(entry, str):  # pragma: no cover
                kept.append(entry)
                continue
            match = _CITATION_PATTERN.search(entry)
            if match is None:  # pragma: no cover
                kept.append(entry)
                continue
            file_prefix = match.group("file")
            if file_prefix is None:  # pragma: no cover
                kept.append(entry)
                continue
            headings = cross_repo_headings_by_path.get(f"{repo_slug}/{file_prefix}")
            if headings is None or match.group("head") in headings:
                kept.append(entry)
        validated[repo_slug] = kept
    return validated


def _walk_set(*, ctx: DoctorContext) -> IOResult[list[Path], LivespecError]:
    """Resolve the per-shape walk-set of `.md` files to scan."""
    minimal_path = ctx.spec_root / _MINIMAL_SHAPE_FILENAME
    if minimal_path.is_file():
        return IOSuccess([minimal_path])
    return _list_top_level_md_files(spec_root=ctx.spec_root)


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the no-cross-spec-reference check against `ctx`.

    Reads the walk-set (minimal-shape single file or livespec-shape
    top-level `*.md` files) plus the `external_references` allowlist
    from `.livespec.jsonc`, then resolves every section-sign
    citation via the helpers' `_scan_all`: same-tree or allowlisted
    citations pass; the first unresolved one yields a fail-Finding
    naming the file, 1-indexed line, offending citation, and a
    suggested allowlist entry. A missing or unparseable config
    degrades to an empty allowlist (its validity is
    `doctor-livespec-jsonc-valid`'s concern).
    """
    allowlist_io: IOResult[Any, LivespecError] = _load_external_references(
        project_root=ctx.project_root,
    ).lash(lambda _err: IOSuccess({}))
    return allowlist_io.bind(
        lambda config: _walk_set(ctx=ctx).bind(
            lambda files: _read_all_texts(files=files).bind(
                lambda texts, cfg=config: _read_cross_repo_headings(
                    heading_files=_cross_repo_heading_files(
                        external_references=_config_allowlist_value(config=cfg),
                        cross_repo_targets=_config_cross_repo_targets_value(config=cfg),
                    ),
                ).map(
                    lambda cross_repo_headings, txt=texts, cfg=cfg: _scan_all(
                        ctx=ctx,
                        texts=txt,
                        external_references=_validated_external_references(
                            external_references=_config_allowlist_value(config=cfg),
                            cross_repo_headings_by_path=cross_repo_headings,
                        ),
                    ),
                ),
            ),
        ),
    )
