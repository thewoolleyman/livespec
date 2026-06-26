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
"""Static-phase doctor check: agents_ai_reference_resolution.

Per the Fleet agent-instruction core contract in
SPECIFICATION/contracts.md: a member's `AGENTS.md` MAY progressively
disclose detail into sibling `.ai/<topic>.md` files that it references,
and every `.ai/<topic>.md` path an `AGENTS.md` references MUST resolve
to an existing file, at every directory level that declares one.

This is a CROSS-BOUNDARY invariant: it inspects the project's
agent-instruction surface (`AGENTS.md` files anywhere under the project
root) rather than the spec tree. The check walks every `AGENTS.md`
under `ctx.project_root` (EXCLUDING any path that descends through a
segment named `archive`, `_vendor`, `__pycache__`, `.git`, `.venv`, or
`node_modules`, and EXCLUDING the spec tree at `ctx.spec_root`), reads
each one, and resolves every CONCRETE `.ai/<topic>.md` reference it
carries relative to that `AGENTS.md`'s own directory.

A concrete reference is the literal `.ai/<some-path>.md` form. The
placeholder `.ai/<topic>.md` (with angle-bracketed `<topic>`) that the
convention prose uses to DESCRIBE the pattern is NOT a concrete
reference — the angle brackets are excluded from the reference grammar
— so prose that merely documents the convention does not need a backing
file. An `AGENTS.md` that references zero concrete `.ai/` files PASSES.

The single `fs.list_tree` walk yields BOTH the set of candidate
`AGENTS.md` files AND the resolution set (every non-excluded file under
the project root), so a reference resolves iff `agents_md.parent / ref`
is a member of that set. The check short-circuits on the first
unresolved reference in sorted `AGENTS.md` order (then line order),
naming the offending `AGENTS.md`, the 1-indexed line, the reference,
and the expected target path.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-agents-ai-reference-resolution")

# A CONCRETE `.ai/<topic>.md` reference: the literal `.ai/` directory
# segment followed by a topic path ending in `.md`. The negative
# lookbehind `(?<![\w-])` rejects a `.ai` that is the tail of a larger
# token (e.g. `foo.ai/x.md`), so only a standalone `.ai/` path counts.
# The character class deliberately EXCLUDES `<` and `>`, so the
# convention's placeholder `.ai/<topic>.md` is NOT matched — the
# angle-bracketed placeholder documents the pattern rather than naming
# a real file.
_AI_REFERENCE = re.compile(r"(?<![\w-])\.ai/[A-Za-z0-9._/-]+\.md")

# Path segments whose presence anywhere in a file's path excludes it
# from the scan: vendored third-party code, byte-cache dirs, the git
# db, node deps, the project virtualenv, and frozen historical
# artifacts.
_EXCLUDED_SEGMENTS: frozenset[str] = frozenset(
    {"archive", "_vendor", "__pycache__", ".git", ".venv", "node_modules"},
)

# Top-level directories handed to `fs.list_tree`'s exclude set so the
# recursive walk never descends into them at all. The spec-root
# basename is added dynamically per `ctx`.
_EXCLUDED_TOP_LEVEL: frozenset[str] = frozenset(
    {"archive", ".git", ".venv", "node_modules"},
)

# The canonical agent-instruction filename a member declares at any
# directory level.
_AGENTS_FILENAME: str = "AGENTS.md"


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="every AGENTS.md-referenced .ai/<topic>.md path resolves to an existing file",
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _fail_finding(
    *,
    ctx: DoctorContext,
    agents_md: Path,
    line_number: int,
    reference: str,
    target: Path,
) -> Finding:
    """Construct a fail-status Finding naming the unresolved reference.

    `line_number` is 1-indexed; `reference` is the literal
    `.ai/<topic>.md` text; `target` is the path it was expected to
    resolve to (relative to the `AGENTS.md`'s own directory).
    """
    return Finding(
        check_id=SLUG,
        status="fail",
        message=(
            f"{agents_md.relative_to(ctx.project_root)}:{line_number} references "
            f"'{reference}' but no such file exists (expected {target})"
        ),
        path=str(agents_md),
        line=line_number,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _is_excluded(*, path: Path, spec_root: Path) -> bool:
    """Return True iff `path` falls under an excluded segment or the spec tree.

    A path is excluded when any of its segments is in
    `_EXCLUDED_SEGMENTS`, or when it lives inside `spec_root` (the spec
    tree is the domain of the spec-side checks, not this
    agent-instruction-surface check).
    """
    if any(segment in _EXCLUDED_SEGMENTS for segment in path.parts):
        return True
    return spec_root in path.parents or path == spec_root


def _iter_ai_references(*, text: str) -> Iterator[tuple[int, str]]:
    """Yield `(1-indexed line, reference)` for every concrete `.ai/` reference.

    Scans `text` line by line and surfaces each `_AI_REFERENCE` match;
    the placeholder `.ai/<topic>.md` produces no match because the
    grammar excludes the angle brackets.
    """
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in _AI_REFERENCE.finditer(line):
            yield (line_number, match.group(0))


def _first_unresolved(
    *,
    ctx: DoctorContext,
    agents_md: Path,
    text: str,
    file_set: frozenset[Path],
) -> Finding | None:
    """Return a fail-Finding for the first unresolved reference, or None.

    Each reference resolves relative to `agents_md`'s own directory; a
    reference is resolved iff `agents_md.parent / reference` is a member
    of `file_set` (the walked project file set). The first reference
    that does not resolve yields a fail-Finding; an `AGENTS.md` whose
    every reference resolves (or which carries none) yields None.
    """
    for line_number, reference in _iter_ai_references(text=text):
        target = agents_md.parent / reference
        if target not in file_set:
            return _fail_finding(
                ctx=ctx,
                agents_md=agents_md,
                line_number=line_number,
                reference=reference,
                target=target,
            )
    return None


def _agents_md_files(*, files: list[Path], spec_root: Path) -> list[Path]:
    """Select the non-excluded `AGENTS.md` files from the walked file list.

    `files` is already sorted (per `fs.list_tree`), so the returned list
    preserves sorted order for first-violation precedence.
    """
    return [
        f
        for f in files
        if f.name == _AGENTS_FILENAME and not _is_excluded(path=f, spec_root=spec_root)
    ]


def _scan_one_agents_md(
    *,
    ctx: DoctorContext,
    agents_md: Path,
    file_set: frozenset[Path],
) -> IOResult[Finding | None, LivespecError]:
    """Read one `AGENTS.md` and resolve its `.ai/` references.

    Reading is an IO call (`fs.read_text`); the resolution against the
    already-walked `file_set` is pure. Yields IOSuccess(fail-Finding)
    on the first unresolved reference, IOSuccess(None) when every
    reference resolves.
    """
    return fs.read_text(path=agents_md).map(
        lambda text: _first_unresolved(
            ctx=ctx,
            agents_md=agents_md,
            text=text,
            file_set=file_set,
        ),
    )


def _select_first(*, current: Finding, candidate: Finding | None) -> Finding:
    """First-violation precedence: keep an existing fail over a later one."""
    if current.status == "fail":
        return current
    if candidate is None:
        return current
    return candidate


def _fold_scan(
    *,
    ctx: DoctorContext,
    agents_files: list[Path],
    file_set: frozenset[Path],
) -> IOResult[Finding, LivespecError]:
    """Fold the per-`AGENTS.md` scan into the first-violation Finding.

    The accumulator carries the pass-Finding initially; the first
    `AGENTS.md` producing a fail-Finding replaces it and subsequent
    files' results are ignored via the first-violation-precedence rule.
    """
    accumulator: IOResult[Finding, LivespecError] = IOSuccess(_pass_finding(ctx=ctx))
    for agents_md in agents_files:
        accumulator = accumulator.bind(
            lambda current, am=agents_md: _scan_one_agents_md(
                ctx=ctx,
                agents_md=am,
                file_set=file_set,
            ).map(
                lambda candidate, c=current: _select_first(current=c, candidate=candidate),
            ),
        )
    return accumulator


def _walk_project_files(*, ctx: DoctorContext) -> IOResult[list[Path], LivespecError]:
    """List every non-excluded file under `project_root` in sorted order.

    The single walk excludes the obvious top-level non-source dirs plus
    the spec-root basename; the returned list serves BOTH as the
    `AGENTS.md` discovery set and (as a frozenset) as the reference
    resolution set.
    """
    exclude_top_level = _EXCLUDED_TOP_LEVEL | {ctx.spec_root.name}
    return fs.list_tree(
        root=ctx.project_root,
        exclude_top_level=frozenset(exclude_top_level),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the agents-ai-reference-resolution check against `ctx`.

    Walks `project_root` for every non-excluded file, then folds each
    discovered `AGENTS.md`'s `.ai/<topic>.md` reference resolution into
    a single first-violation Finding. On no unresolved reference yields
    IOSuccess(Finding(status='pass')); on the first unresolved reference
    yields IOSuccess(Finding(status='fail')) naming the `AGENTS.md`,
    1-indexed line, reference, and expected target.
    """
    return _walk_project_files(ctx=ctx).bind(
        lambda files: _fold_scan(
            ctx=ctx,
            agents_files=_agents_md_files(files=files, spec_root=ctx.spec_root),
            file_set=frozenset(files),
        ),
    )
