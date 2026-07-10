"""Private helpers for `no_cross_spec_reference`.

Extracts the pure parsing/resolution layer (regex patterns, the
`_Resolver` value-object, heading collection, code-span detection,
allowlist flattening, citation resolution, and Finding
construction) from the parent module so the public check wrapper
stays below the LLOC ceiling. The parent re-exports the helpers it
and the tests reference, so the test surface is unchanged.

This module performs NO I/O — every function here is pure — so it
carries no returns-library bind chains and needs neither the
HKT-erosion pragma nor a railway type. The parent module owns the
`fs`-touching railway composition.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Set
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from livespec.context import DoctorContext
from livespec.doctor.static._no_cross_spec_reference_allowlist import (
    _CITATION_PATTERN,
    _allowlist_match,
    _flatten_allowlist,
)
from livespec.doctor.static._no_cross_spec_reference_findings import (
    SLUG,
    _fail_finding,
    _pass_finding,
)
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = [
    "SLUG",
    "_MINIMAL_SHAPE_FILENAME",
    "_Resolver",
    "_allowlist_match",
    "_build_finding_from_scan",
    "_collect_headings",
    "_config_allowlist_value",
    "_fail_finding",
    "_flatten_allowlist",
    "_inline_code_ranges",
    "_is_inside_code",
    "_pass_finding",
    "_prose_lines",
    "_same_tree_match",
    "_scan_all",
    "_scan_text_for_violation",
]

# The minimal-template's single-file end-user output marker (per
# the sibling anchor_reference_resolution check's same
# convention). A `minimal`-rooted project carries
# `SPECIFICATION.md` directly at the spec_root.
_MINIMAL_SHAPE_FILENAME: str = "SPECIFICATION.md"

# Pattern matching a Markdown ATX heading line: one-to-six leading
# `#` characters followed by required whitespace and the heading
# text. Group 1 is the heading text (trailing whitespace stripped
# in the caller).
_HEADING_PATTERN: re.Pattern[str] = re.compile(r"^#{1,6}\s+(.+?)\s*$")

# Pattern matching the opening/closing of a fenced code block
# (triple backtick or triple tilde). The optional info-string
# after the fence is irrelevant for fence detection.
_FENCE_PATTERN: re.Pattern[str] = re.compile(r"^\s*(?:```|~~~)")

# Pattern matching an inline code span: a run of backtick-delimited
# text. Used to compute the character ranges a prose line devotes to
# inline code, so a citation whose section sign falls INSIDE such a
# span — the Reference discipline section's own backticked
# illustrative citation-shape examples — is skipped, while a REAL
# citation that merely contains a backtick fragment inside its
# quoted heading still resolves.
_INLINE_CODE_PATTERN: re.Pattern[str] = re.compile(r"`[^`]*`")


@dataclass(frozen=True, kw_only=True, slots=True)
class _Resolver:
    """The resolution context a single-file scan needs.

    Bundles the union heading set (`all_headings`), the per-file
    heading sets (`headings_by_file`), and the flattened allowlist
    sets (`entry_strings` for file-prefixed comparison,
    `entry_headings` for bare-citation comparison) so the per-file
    scan helpers take one value-object instead of four loose
    parameters.
    """

    all_headings: frozenset[str]
    headings_by_file: dict[str, frozenset[str]]
    entry_strings: frozenset[str]
    entry_headings: frozenset[str]


def _collect_headings(*, text: str) -> set[str]:
    """Return the set of ATX heading texts from `text`, fences excluded.

    A simple state machine toggles `inside_fence` on every fence
    line. Heading texts are collected only outside fences and are
    compared by exact (trailing-whitespace-stripped) text — the
    section-sign citation form names headings verbatim, not by GFM
    slug.
    """
    headings: set[str] = set()
    inside_fence = False
    for line in text.splitlines():
        if _FENCE_PATTERN.match(line):
            inside_fence = not inside_fence
            continue
        if inside_fence:
            continue
        match = _HEADING_PATTERN.match(line)
        if match is not None:
            headings.add(match.group(1))
    return headings


def _inline_code_ranges(*, line: str) -> list[tuple[int, int]]:
    """Return the `[start, end)` character ranges of inline code spans.

    Each run of backtick-delimited text on `line` contributes one
    `(start, end)` half-open range. A citation whose section sign
    sits inside any such range is illustrative syntax and skipped.
    """
    return [(m.start(), m.end()) for m in _INLINE_CODE_PATTERN.finditer(line)]


def _is_inside_code(*, position: int, ranges: list[tuple[int, int]]) -> bool:
    """Return True iff `position` falls inside any inline-code range."""
    return any(start <= position < end for start, end in ranges)


def _prose_lines(*, text: str) -> list[str]:
    """Blank fenced-block lines line-by-line, preserving prose verbatim.

    Returns one entry per source line (1:1 with the original line
    numbering). Fenced-code lines and the fence markers themselves
    become empty strings; prose lines are returned verbatim so a
    citation can be located by character offset against the line's
    own inline-code ranges.
    """
    out: list[str] = []
    inside_fence = False
    for line in text.splitlines():
        if _FENCE_PATTERN.match(line):
            inside_fence = not inside_fence
            out.append("")
            continue
        if inside_fence:
            out.append("")
            continue
        out.append(line)
    return out


def _citation_text(*, file_prefix: str | None, heading: str) -> str:
    """Reconstruct the literal citation text for messages/matching."""
    return f'§"{heading}"' if file_prefix is None else f'{file_prefix} §"{heading}"'


def _same_tree_match(
    *,
    file_prefix: str | None,
    heading: str,
    all_headings: Set[str],
    headings_by_file: Mapping[str, Set[str]],
) -> bool:
    """Return True iff this citation resolves inside the same spec tree.

    A bare citation resolves when its heading text appears anywhere
    in the tree (`all_headings`). A file-prefixed citation resolves
    when `<name>.md` is a bare sibling (no path separator) present
    in the walk-set AND the heading exists in that sibling.
    """
    if file_prefix is None:
        return heading in all_headings
    return "/" not in file_prefix and heading in headings_by_file.get(file_prefix, set())


def _scan_text_for_violation(
    *,
    text: str,
    resolver: _Resolver,
) -> tuple[int, str, str] | None:
    """Scan one file's text for the first unresolved section citation.

    Walks each prose line (fenced blocks blanked) and, for each
    section-sign citation whose section sign is NOT inside an inline
    code span, tries same-tree resolution then allowlist resolution.
    The first citation that resolves neither way yields
    `(line_number, citation_text, suggested_entry)`. Returns None
    when every citation in the file resolves.
    """
    for line_index, line_text in enumerate(_prose_lines(text=text), start=1):
        code_ranges = _inline_code_ranges(line=line_text)
        for match in _CITATION_PATTERN.finditer(line_text):
            section_sign_position = match.start("head") - 2
            if _is_inside_code(position=section_sign_position, ranges=code_ranges):
                continue
            file_prefix = match.group("file")
            heading = match.group("head")
            if _same_tree_match(
                file_prefix=file_prefix,
                heading=heading,
                all_headings=resolver.all_headings,
                headings_by_file=resolver.headings_by_file,
            ):
                continue
            if _allowlist_match(
                file_prefix=file_prefix,
                heading=heading,
                entry_strings=resolver.entry_strings,
                entry_headings=resolver.entry_headings,
            ):
                continue
            citation = _citation_text(file_prefix=file_prefix, heading=heading)
            suggested = _citation_text(
                file_prefix=file_prefix if file_prefix is not None else "SPECIFICATION/<file>.md",
                heading=heading,
            )
            return (line_index, citation, suggested)
    return None


def _build_finding_from_scan(
    *,
    ctx: DoctorContext,
    file_path: Path,
    text: str,
    resolver: _Resolver,
) -> Finding | None:
    """Translate one file's scan result into a fail-Finding or None."""
    violation = _scan_text_for_violation(text=text, resolver=resolver)
    if violation is None:
        return None
    line_number, citation, suggested = violation
    return _fail_finding(
        ctx=ctx,
        file_path=file_path,
        line_number=line_number,
        citation=citation,
        suggested_entry=suggested,
    )


def _config_allowlist_value(*, config: Any) -> Any:
    """Extract the `external_references` value from a parsed config.

    A non-dict config (parser returned a list/scalar) has no
    `external_references` key, so the helper yields None — which
    `_flatten_allowlist` treats as "no allowlist".
    """
    if isinstance(config, dict):
        return cast("dict[str, object]", config).get("external_references")
    return None


def _scan_all(
    *,
    ctx: DoctorContext,
    texts: dict[Path, str],
    external_references: Any,
) -> Finding:
    """Resolve every citation across the walk-set; return first violation.

    Flattens the allowlist once, builds the union heading set +
    per-file heading sets, then scans files in sorted path order.
    The first file with an unresolved citation yields its
    fail-Finding (short-circuit); when every file is clean, the
    pass-Finding is returned.
    """
    entry_strings, entry_headings, entry_strings_by_repo = _flatten_allowlist(
        external_references=external_references,
    )
    scoped_entry_strings = entry_strings | {
        f"{repo_slug}/{entry}"
        for repo_slug, entries in entry_strings_by_repo.items()
        for entry in entries
    }
    headings_by_file: dict[str, frozenset[str]] = {
        path.name: frozenset(_collect_headings(text=text)) for path, text in texts.items()
    }
    all_headings: set[str] = set()
    for headings in headings_by_file.values():
        all_headings |= headings
    resolver = _Resolver(
        all_headings=frozenset(all_headings),
        headings_by_file=headings_by_file,
        entry_strings=frozenset(scoped_entry_strings),
        entry_headings=frozenset(entry_headings),
    )
    for file_path in sorted(texts):
        finding = _build_finding_from_scan(
            ctx=ctx,
            file_path=file_path,
            text=texts[file_path],
            resolver=resolver,
        )
        if finding is not None:
            return finding
    return _pass_finding(ctx=ctx)
