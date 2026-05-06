"""Static-phase doctor check: anchor_reference_resolution.

Per Plan Phase 7 sub-step 7.d +: this check verifies that every Markdown
intra-document anchor reference (a link of the form
`[text](#slug)`) resolves to an actual heading in the SAME file
via the GFM slug algorithm. Cross-file references and external
links are out of scope at the static layer (their resolution
moves to the LLM-driven phase per).

GFM slug algorithm (per):
  1. Lowercase the heading text.
  2. Strip punctuation EXCEPT `-` and `_` (whitespace is preserved
     for the next step).
  3. Replace internal whitespace with single hyphens.
  4. Collapse consecutive hyphens to a single hyphen.
  5. Strip leading and trailing hyphens.

Headings inside fenced code blocks (` ``` ` or `~~~`) are NOT
considered headings. Explicit `{#custom-id}` syntax is NOT
supported in v1.

Applies to all spec-text-bearing trees (main + each sub-spec).
The walk-set semantic matches the sibling Phase-7 checks:
livespec-shape spec_roots walk `<spec_root>/*.md`
top-level files only; minimal-shape spec_roots scan only
`<spec_root>/SPECIFICATION.md`. Neither shape recurses into
`history/`, `proposed_changes/`, or `templates/` subtrees —
those snapshots inherit the live spec's well-formedness via the
seed/revise byte-identical write discipline.

Detection rules (v1 minimum scope):
  - For every Markdown link `[text](#slug)` whose target starts
    with `#`, compute the set of valid slugs from every
    heading in the SAME file (excluding headings inside fenced
    code blocks). The reference resolves iff its `#`-stripped
    target is in that set.
  - Cross-file references (target containing `/` or starting
    with a non-`#` character before any `#`) are ignored.
  - The first violation found (lexicographically-sorted file,
    first matching reference) is surfaced; the check short-
    circuits on the first hit so the user sees one offense at
    a time.
"""

from __future__ import annotations

import re
from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-anchor-reference-resolution"

# The minimal-template's single-file end-user output marker (per
# the sibling gherkin-blank-line-format check's same convention).
# A `minimal`-rooted project carries `SPECIFICATION.md` directly
# at the spec_root; presence at the spec_root distinguishes
# minimal-shape from the multi-file livespec layout.
_MINIMAL_SHAPE_FILENAME: str = "SPECIFICATION.md"

# Pattern matching a Markdown ATX heading line: one-to-six leading
# `#` characters followed by required whitespace and the heading
# text. The captured group 1 is the heading text (post-`#`
# whitespace included; we strip both ends in `_slugify`).
_HEADING_PATTERN: re.Pattern[str] = re.compile(r"^#{1,6}\s+(.+?)\s*$")

# Pattern matching the opening of a fenced code block (triple
# backtick or triple tilde). The optional info-string after the
# fence is irrelevant for fence detection.
_FENCE_OPEN_PATTERN: re.Pattern[str] = re.compile(r"^\s*(?:```|~~~)")

# Pattern matching a Markdown link with an intra-document anchor
# target: `[text](#slug)`. Group 1 is the bracketed link text;
# group 2 is the slug WITHOUT the leading `#`. The target must
# start with `#` and contain no `/` (which would indicate a
# cross-file reference) — we filter cross-file references via the
# more permissive link-pattern below + an explicit predicate.
_ANCHOR_LINK_PATTERN: re.Pattern[str] = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

# Characters retained when slugifying punctuation per the GFM
# rule: `-` and `_` survive; everything else is stripped (after
# whitespace has been converted to `-`). Alphanumerics survive
# trivially via the inverted character-class.
_SLUG_PUNCTUATION_PATTERN: re.Pattern[str] = re.compile(r"[^\w\s-]")

# Pattern collapsing one-or-more whitespace runs into a single
# hyphen during slugification.
_SLUG_WHITESPACE_PATTERN: re.Pattern[str] = re.compile(r"\s+")

# Pattern collapsing consecutive hyphens into a single hyphen
# (final cleanup step of the GFM slug algorithm).
_SLUG_HYPHEN_RUN_PATTERN: re.Pattern[str] = re.compile(r"-+")


def _slugify(*, heading_text: str) -> str:
    """Apply the GFM slug algorithm to `heading_text`.

    1. Lowercase the heading text.
    2. Strip punctuation except `-` and `_` (alphanumerics +
       whitespace + `-` + `_` survive).
    3. Replace internal whitespace with single hyphens.
    4. Collapse consecutive hyphens to one.
    5. Strip leading and trailing hyphens.
    """
    lowered = heading_text.lower()
    sans_punct = _SLUG_PUNCTUATION_PATTERN.sub("", lowered)
    hyphenated = _SLUG_WHITESPACE_PATTERN.sub("-", sans_punct)
    collapsed = _SLUG_HYPHEN_RUN_PATTERN.sub("-", hyphenated)
    return collapsed.strip("-")


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="every anchor reference resolves to a heading in the same file",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _fail_finding(
    *,
    ctx: DoctorContext,
    file_path: Path,
    line_number: int,
    target: str,
) -> Finding:
    """Construct a fail-status Finding naming the unresolved anchor target.

    The Finding's `path` field embeds the absolute file path so
    the user can locate the violation without re-scanning.
    `line_number` is 1-indexed per editor convention. `target`
    is the literal `#`-prefixed slug that did not resolve.
    """
    return Finding(
        check_id=SLUG,
        status="fail",
        message=(
            f"{file_path.name}:{line_number} anchor reference "
            f"'{target}' does not resolve to any heading in the same file"
        ),
        path=str(file_path),
        line=line_number,
        spec_root=str(ctx.spec_root),
    )


def _is_fence_line(*, line: str) -> bool:
    """Return True iff `line` opens or closes a fenced code block.

    Both ` ``` ` and `~~~` fence markers count. Per CommonMark,
    fences toggle a fenced-block state — the check uses this for
    a simple toggle to skip headings encountered inside fences.
    """
    return _FENCE_OPEN_PATTERN.match(line) is not None


def _collect_heading_slugs(*, lines: list[str]) -> set[str]:
    """Walk `lines` and return the set of GFM slugs from non-fenced headings.

    A simple state machine toggles `inside_fence` on every line
    matching the fence-open/close pattern. Heading lines are
    only collected outside fences. Slugify each heading's text
    via the GFM rule.
    """
    slugs: set[str] = set()
    inside_fence = False
    for line in lines:
        if _is_fence_line(line=line):
            inside_fence = not inside_fence
            continue
        if inside_fence:
            continue
        match = _HEADING_PATTERN.match(line)
        if match is not None:
            slugs.add(_slugify(heading_text=match.group(1)))
    return slugs


def _is_intra_file_anchor_target(*, target: str) -> bool:
    """Return True iff `target` is an intra-file anchor reference.

    An intra-file target starts with `#` and contains no `/`
    character (which would indicate a cross-file path reference
    such as `other.md#slug`). Out-of-scope cross-file targets
    are ignored at the static layer.
    """
    return target.startswith("#") and "/" not in target


def _scan_text_for_violation(
    *,
    text: str,
) -> tuple[int, str] | None:
    """Scan `text` for the first unresolved intra-file anchor reference.

    Splits `text` into lines, collects the heading-slug set, and
    walks each line for `[text](#slug)` link syntax. The first
    intra-file anchor reference whose `#`-stripped target is NOT
    in the heading-slug set yields `(line_number, target)`.
    Cross-file references and external links are skipped.
    """
    lines = text.splitlines()
    heading_slugs = _collect_heading_slugs(lines=lines)
    for line_index, line_text in enumerate(lines, start=1):
        for match in _ANCHOR_LINK_PATTERN.finditer(line_text):
            target = match.group(2)
            if not _is_intra_file_anchor_target(target=target):
                continue
            slug = target[1:]
            if slug not in heading_slugs:
                return (line_index, target)
    return None


def _build_finding_from_scan(
    *,
    ctx: DoctorContext,
    file_path: Path,
    text: str,
) -> Finding | None:
    """Translate a scan result into a fail-Finding or None.

    Pure helper: maps the `_scan_text_for_violation` tuple
    output to the canonical fail-Finding shape, or None when
    the file has no unresolved anchor references.
    """
    violation = _scan_text_for_violation(text=text)
    if violation is None:
        return None
    line_number, target = violation
    return _fail_finding(
        ctx=ctx,
        file_path=file_path,
        line_number=line_number,
        target=target,
    )


def _scan_one_file(
    *,
    ctx: DoctorContext,
    file_path: Path,
) -> IOResult[Finding | None, LivespecError]:
    """Scan one `.md` file for the first anchor-resolution violation.

    Reads the file via `fs.read_text` and applies
    `_scan_text_for_violation`. Returns:
      - IOSuccess(Finding(status='fail', ...)) when a violation
        is found (first match short-circuit);
      - IOSuccess(None) when every anchor reference in the file
        resolves (or the file has no anchor references at all).
    """
    return fs.read_text(path=file_path).map(
        lambda text: _build_finding_from_scan(
            ctx=ctx,
            file_path=file_path,
            text=text,
        ),
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


def _list_top_level_md_files(
    *,
    spec_root: Path,
) -> IOResult[list[Path], LivespecError]:
    """List `<spec_root>/*.md` top-level files in sorted order.

    Per the v018 Q1 walk-set semantic: the check inspects only
    the top-level `*.md` files at `spec_root`. `fs.list_dir`
    yields every immediate child sorted by name; this helper
    filters to `.md` files and excludes directories.
    """
    return fs.list_dir(path=spec_root).map(
        lambda children: [child for child in children if child.is_file() and child.suffix == ".md"],
    )


def _is_minimal_shape(*, spec_root: Path) -> bool:
    """Detect minimal-template single-file shape at `spec_root`.

    Per the sibling gherkin-blank-line-format check's same
    convention: a minimal-rooted project carries
    `SPECIFICATION.md` directly at the spec_root. The presence
    of that file is the v1 detection signal — it distinguishes
    minimal-shape from livespec-shape (which has no top-level
    `SPECIFICATION.md` and instead carries `spec.md`,
    `contracts.md`, etc. as separate files).
    """
    return (spec_root / _MINIMAL_SHAPE_FILENAME).is_file()


def _run_minimal_shape(
    *,
    ctx: DoctorContext,
) -> IOResult[Finding, LivespecError]:
    """Apply the minimal-shape branch: scan only `SPECIFICATION.md`.

    Lists the single-file walk set (`[<spec_root>/SPECIFICATION.md]`)
    and folds the same per-file scan as the livespec-shape
    branch, yielding a single pass-or-fail Finding.
    """
    spec_md_path = ctx.spec_root / _MINIMAL_SHAPE_FILENAME
    return _scan_files_for_first_violation(ctx=ctx, files=[spec_md_path])


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
    """Run the anchor-reference-resolution check against `ctx`.

    Branches on the spec_root shape: minimal-shape (single-file
    `SPECIFICATION.md`) scans that single file; livespec-shape
    walks every top-level `*.md` (sorted) and folds each file's
    scan into a single first-violation Finding. On no violation
    yields IOSuccess(Finding(status='pass')); on first violation
    yields IOSuccess(Finding(status='fail', ...)) naming the
    offending file + 1-indexed line + unresolved target.
    """
    if _is_minimal_shape(spec_root=ctx.spec_root):
        return _run_minimal_shape(ctx=ctx)
    return _run_livespec_shape(ctx=ctx)
