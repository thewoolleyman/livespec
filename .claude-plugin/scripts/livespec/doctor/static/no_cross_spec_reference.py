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
            lambda files: _read_all_texts(files=files).map(
                lambda texts, cfg=config: _scan_all(
                    ctx=ctx,
                    texts=texts,
                    external_references=_config_allowlist_value(config=cfg),
                ),
            ),
        ),
    )
