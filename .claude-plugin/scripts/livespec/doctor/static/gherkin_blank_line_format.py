"""Static-phase doctor check: gherkin_blank_line_format.

Per Plan Phase 7 sub-step 7.c + PROPOSAL.md §"`doctor` →
Static-phase checks": this check verifies that fenced
` ```gherkin ` blocks in spec-text-bearing markdown files are
surrounded by blank lines (one blank line above the opening
fence, one blank line below the closing fence). Start-of-file
is implicit-blank-above; end-of-file is implicit-blank-below.

Per `SPECIFICATION/templates/minimal/constraints.md`
§"Gherkin blank-line format check exemption" (Phase 7
widening): the check MUST exempt `minimal`-rooted spec_roots
(single-file `SPECIFICATION.md` shape per `spec_root: "./"`)
whose `SPECIFICATION.md` does NOT contain any fenced
` ```gherkin ` blocks — emit `status='skipped'`. When
`SPECIFICATION.md` does contain gherkin blocks, the check
applies normally and may yield pass or fail.

Per v018 Q1: applies to all spec-text-bearing trees (main +
each sub-spec). The walk-set semantic matches
`bcp14-keyword-wellformedness`: livespec-shape spec_roots
(multi-file layout) walk `<spec_root>/*.md` top-level files
sorted by name; minimal-shape spec_roots scan only
`<spec_root>/SPECIFICATION.md`. Neither shape recurses into
`history/`, `proposed_changes/`, or `templates/` subtrees —
those snapshots inherit the live spec's well-formedness via
the seed/revise byte-identical write discipline.

Detection rules (v1 minimum scope per the deferred-items.md
`static-check-semantics` entry on `gherkin-blank-line-format`'s
fenced-block detection algorithm):
  - For every line opening a fenced ` ```gherkin ` block:
      - The line immediately before the opening fence MUST
        be blank, OR the opening fence MUST be the very first
        line of the file (start-of-file is implicit-blank-
        above).
      - The line immediately after the matching closing
        fence MUST be blank, OR the closing fence MUST be
        the very last line of the file (end-of-file is
        implicit-blank-below).
  - The closing fence is the next line whose content is
    exactly ` ``` ` (three backticks, optional trailing
    whitespace).
  - An unmatched opening fence (no closing fence found before
    end-of-file) yields no closing-side violation; the v1
    minimum scope treats the broader markdown well-formedness
    as out of scope for this check.
  - The first violation found (lexicographically-sorted file,
    first matching line) is surfaced; the check short-circuits
    on the first hit so the user sees one offense at a time.
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.doctor.static._gherkin_helpers import (
    _CLOSING_FENCE_PATTERN,
    _MINIMAL_SHAPE_FILENAME,
    _OPENING_FENCE_PATTERN,
    _find_closing_fence,
    _has_gherkin_fence,
    _is_blank_above,
    _is_blank_below,
    _is_minimal_shape,
    _list_top_level_md_files,
    _scan_text_for_violation,
)
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-gherkin-blank-line-format"
_ = (
    _CLOSING_FENCE_PATTERN,
    _OPENING_FENCE_PATTERN,
    _find_closing_fence,
    _is_blank_above,
    _is_blank_below,
)


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="fenced gherkin blocks are surrounded by blank lines",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _skipped_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical skipped-status Finding for the minimal-rooted exemption.

    Per `SPECIFICATION/templates/minimal/constraints.md`
    §"Gherkin blank-line format check exemption": minimal-shape
    spec_roots whose `SPECIFICATION.md` has no fenced gherkin
    blocks are exempt from this check. The skipped Finding
    documents the exemption in the canonical findings JSON
    payload so the orchestrator's union-of-statuses exit-code
    derivation treats it as non-failing.
    """
    return Finding(
        check_id=SLUG,
        status="skipped",
        message=("minimal-shape spec_root has no fenced ```gherkin " "blocks — exemption applies"),
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _opening_fence_finding(
    *,
    ctx: DoctorContext,
    file_path: Path,
    line_number: int,
) -> Finding:
    """Construct a fail-status Finding for a touching-prose-above opening fence.

    The Finding's `path` field embeds the absolute file path
    so the user can locate the violation without re-scanning;
    `line_number` is 1-indexed per editor convention.
    """
    return Finding(
        check_id=SLUG,
        status="fail",
        message=(
            f"{file_path.name}:{line_number} fenced ```gherkin block "
            f"opening fence is not preceded by a blank line"
        ),
        path=str(file_path),
        line=line_number,
        spec_root=str(ctx.spec_root),
    )


def _closing_fence_finding(
    *,
    ctx: DoctorContext,
    file_path: Path,
    line_number: int,
) -> Finding:
    """Construct a fail-status Finding for a touching-prose-below closing fence.

    The Finding's `path` field embeds the absolute file path
    so the user can locate the violation without re-scanning;
    `line_number` is 1-indexed per editor convention.
    """
    return Finding(
        check_id=SLUG,
        status="fail",
        message=(
            f"{file_path.name}:{line_number} fenced ```gherkin block "
            f"closing fence is not followed by a blank line"
        ),
        path=str(file_path),
        line=line_number,
        spec_root=str(ctx.spec_root),
    )


def _build_finding_from_violation(
    *,
    ctx: DoctorContext,
    file_path: Path,
    violation: tuple[str, int],
) -> Finding:
    """Translate a `_scan_text_for_violation` tuple into a fail-Finding.

    The tuple's first element discriminates between the
    opening-fence and closing-fence violation kinds; the second
    is the 1-indexed offending line number.
    """
    kind, line_number = violation
    if kind == "opening":
        return _opening_fence_finding(
            ctx=ctx,
            file_path=file_path,
            line_number=line_number,
        )
    return _closing_fence_finding(
        ctx=ctx,
        file_path=file_path,
        line_number=line_number,
    )


def _scan_one_file(
    *,
    ctx: DoctorContext,
    file_path: Path,
) -> IOResult[Finding | None, LivespecError]:
    """Scan one `.md` file for the first fence blank-line violation.

    Reads the file via `fs.read_text` and applies
    `_scan_text_for_violation`. Returns:
      - IOSuccess(Finding(status='fail', ...)) when a violation
        is found (first match short-circuit);
      - IOSuccess(None) when the file is well-formed (caller
        continues to the next file).
    """
    return fs.read_text(path=file_path).map(
        lambda text: _maybe_finding_for_text(
            ctx=ctx,
            file_path=file_path,
            text=text,
        ),
    )


def _maybe_finding_for_text(
    *,
    ctx: DoctorContext,
    file_path: Path,
    text: str,
) -> Finding | None:
    """Map one file's text to a fail-Finding or None.

    Pure helper: combines `_scan_text_for_violation` with
    `_build_finding_from_violation` to produce the canonical
    fail-Finding shape, or None when the file is clean.
    """
    violation = _scan_text_for_violation(text=text)
    if violation is None:
        return None
    return _build_finding_from_violation(
        ctx=ctx,
        file_path=file_path,
        violation=violation,
    )


def _select_first_finding(
    *,
    current_finding: Finding,
    maybe_new_finding: Finding | None,
) -> Finding:
    """Choose between the running accumulator and a new scan result.

    First-violation precedence: if the accumulator already
    holds a fail-Finding, keep it. Otherwise, if the new scan
    yielded a fail-Finding, promote it. A clean new scan
    (None) leaves the accumulator unchanged.
    """
    if current_finding.status == "fail":
        return current_finding
    if maybe_new_finding is None:
        return current_finding
    return maybe_new_finding


def _absorb_file_scan(
    *,
    ctx: DoctorContext,
    current_finding: Finding,
    file_path: Path,
) -> IOResult[Finding, LivespecError]:
    """Merge one file's scan result into the running accumulator.

    Always reads the file and applies `_scan_one_file`; the
    accumulator-replacement rule preserves the first fail-
    Finding (i.e., once a fail is in the accumulator, a later
    file's fail does NOT overwrite it). A clean file leaves
    the accumulator unchanged.
    """
    return _scan_one_file(ctx=ctx, file_path=file_path).map(
        lambda maybe_finding: _select_first_finding(
            current_finding=current_finding,
            maybe_new_finding=maybe_finding,
        ),
    )


def _scan_files_for_first_violation(
    *,
    ctx: DoctorContext,
    files: list[Path],
) -> IOResult[Finding, LivespecError]:
    """Scan files in sorted order; return the first violation Finding.

    Folds the per-file scan: each file's `_scan_one_file` yields
    IOSuccess(Finding | None). The accumulator carries the
    pass-Finding initially; the first file that produces a
    fail-Finding replaces it (short-circuit semantics — once a
    fail is in the accumulator, subsequent files are still
    visited but their results are ignored via the
    accumulator-precedence pattern). When every file is clean,
    the pass-Finding survives and is returned.
    """
    accumulator: IOResult[Finding, LivespecError] = IOSuccess(_pass_finding(ctx=ctx))
    for file_path in files:
        accumulator = accumulator.bind(
            lambda current_finding, fp=file_path: _absorb_file_scan(
                ctx=ctx,
                current_finding=current_finding,
                file_path=fp,
            ),
        )
    return accumulator


def _run_minimal_shape(
    *,
    ctx: DoctorContext,
) -> IOResult[Finding, LivespecError]:
    """Apply the minimal-shape branch: skipped exemption or single-file scan.

    Reads `<spec_root>/SPECIFICATION.md`. If the content has
    no opening gherkin fence, emit the skipped Finding per
    the constraints.md exemption. Otherwise apply the normal
    scan to that single file via `_scan_files_for_first_violation`.
    """
    spec_md_path = ctx.spec_root / _MINIMAL_SHAPE_FILENAME
    return fs.read_text(path=spec_md_path).bind(
        lambda text: _classify_minimal_text(
            ctx=ctx,
            file_path=spec_md_path,
            text=text,
        ),
    )


def _classify_minimal_text(
    *,
    ctx: DoctorContext,
    file_path: Path,
    text: str,
) -> IOResult[Finding, LivespecError]:
    """Decide skipped vs scan-and-emit for a minimal-shape SPECIFICATION.md.

    No fenced gherkin block in the file → emit the skipped
    Finding. At least one opening fence present → run the
    standard fence blank-line scan against this single file
    and return the resulting pass/fail Finding.
    """
    if not _has_gherkin_fence(text=text):
        return IOSuccess(_skipped_finding(ctx=ctx))
    maybe_finding = _maybe_finding_for_text(
        ctx=ctx,
        file_path=file_path,
        text=text,
    )
    if maybe_finding is None:
        return IOSuccess(_pass_finding(ctx=ctx))
    return IOSuccess(maybe_finding)


def _run_livespec_shape(
    *,
    ctx: DoctorContext,
) -> IOResult[Finding, LivespecError]:
    """Apply the livespec-shape branch: walk every top-level `*.md` and scan.

    Lists `<spec_root>/*.md` (sorted), then folds the per-file
    scan via `_scan_files_for_first_violation`. Yields the
    first violation Finding or the pass-Finding when every
    file is well-formed.
    """
    return _list_top_level_md_files(spec_root=ctx.spec_root).bind(
        lambda files: _scan_files_for_first_violation(ctx=ctx, files=files),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the gherkin-blank-line-format check against `ctx`.

    Branches on the spec_root shape: minimal-shape (single-file
    `SPECIFICATION.md`) takes the exemption-aware path that
    emits `skipped` when the file has no fenced gherkin blocks;
    livespec-shape walks every top-level `*.md` (sorted) and
    folds each file's scan into a single first-violation
    Finding. On no violation yields IOSuccess(Finding(status=
    'pass')); on first violation yields IOSuccess(Finding(
    status='fail', ...)) naming the offending file + 1-indexed
    line + violation kind.
    """
    if _is_minimal_shape(spec_root=ctx.spec_root):
        return _run_minimal_shape(ctx=ctx)
    return _run_livespec_shape(ctx=ctx)
