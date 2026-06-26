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
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

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


SLUG: CheckId = CheckId("doctor-no-cross-spec-reference")

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

# Pattern matching a section citation: an optional `<path>.md`
# file prefix, then the section sign followed by a double-quoted
# heading. Group `file` is the optional file prefix (None for a
# bare citation); group `head` is the heading text between the
# quotes. The heading body is `[^"]*` — the first closing quote
# terminates it (a nested citation inside the quotes resolves to
# the truncated head, which simply fails to resolve and surfaces
# as the actionable violation rather than silently passing).
_CITATION_PATTERN: re.Pattern[str] = re.compile(
    r'(?:(?P<file>[^\s"`()]+\.md)\s+)?§"(?P<head>[^"]*)"',
)


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


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message=(
            "every section citation resolves same-tree or via the external_references allowlist"
        ),
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _fail_finding(
    *,
    ctx: DoctorContext,
    file_path: Path,
    line_number: int,
    citation: str,
    suggested_entry: str,
) -> Finding:
    """Construct a fail-status Finding naming the unresolved citation.

    `citation` is the literal offending citation text; `line_number`
    is 1-indexed per editor convention; `suggested_entry` is the
    file-plus-heading string the user would add under an
    `external_references` repo key to allowlist the reference.
    """
    return Finding(
        check_id=SLUG,
        status="fail",
        message=(
            f"{file_path.name}:{line_number} section citation "
            f"'{citation}' does not resolve to a heading in the same "
            f"SPECIFICATION/ tree and is not allowlisted; add "
            f"'{suggested_entry}' under an external_references repo key "
            f"in .livespec.jsonc to allow it"
        ),
        path=str(file_path),
        line=line_number,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


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


def _flatten_allowlist(*, external_references: Any) -> tuple[set[str], set[str]]:
    """Flatten the `external_references` block into matchable sets.

    Returns `(entry_strings, entry_headings)`:
      - `entry_strings`: every file-plus-heading allowlist string
        verbatim, used to match a file-prefixed citation by its
        reconstructed basename-plus-heading form;
      - `entry_headings`: the heading text of every allowlist
        entry, used to match a BARE citation (prose citations of a
        sibling-repo heading frequently omit the `<file>` prefix).

    A malformed block (not a dict, or a value that is not a list of
    strings) contributes nothing — a parse-shape fault degrades to
    "no allowlist", which can only make the check stricter, never
    spuriously pass.
    """
    entry_strings: set[str] = set()
    entry_headings: set[str] = set()
    if not isinstance(external_references, dict):
        return (entry_strings, entry_headings)
    block = cast("dict[str, object]", external_references)
    for entries in block.values():
        if not isinstance(entries, list):
            continue
        items = cast("list[object]", entries)
        for entry in items:
            if not isinstance(entry, str):
                continue
            entry_strings.add(entry)
            head_match = _CITATION_PATTERN.search(entry)
            if head_match is not None:
                entry_headings.add(head_match.group("head"))
    return (entry_strings, entry_headings)


def _citation_text(*, file_prefix: str | None, heading: str) -> str:
    """Reconstruct the literal citation text for messages/matching."""
    if file_prefix is None:
        return f'§"{heading}"'
    return f'{file_prefix} §"{heading}"'


def _allowlist_match(
    *,
    file_prefix: str | None,
    heading: str,
    entry_strings: Set[str],
    entry_headings: Set[str],
) -> bool:
    """Return True iff this citation is covered by the allowlist.

    A BARE citation (no file prefix) matches when its heading text
    is the heading of any allowlist entry — prose citations of a
    sibling-repo heading frequently omit the `<file>` prefix, so the
    heading text alone is the matchable key.

    A FILE-PREFIXED citation matches by the precise
    basename-plus-heading comparison: its reconstructed
    basename-plus-heading string must equal an allowlist entry's own
    basename-plus-heading form. This is stricter than the bare
    case on purpose — a file-prefixed citation naming the WRONG file
    must not pass just because its heading text coincides with a
    differently-filed allowlist entry. (The allowlist may spell the
    file with a `SPECIFICATION/` directory prefix; basename
    comparison makes the two spellings agree.)
    """
    if file_prefix is None:
        return heading in entry_headings
    citation_basename = Path(file_prefix).name
    target = f'{citation_basename} §"{heading}"'
    for entry in entry_strings:
        entry_match = _CITATION_PATTERN.search(entry)
        if entry_match is None:
            continue
        entry_file = entry_match.group("file")
        if entry_file is None:
            continue
        if f'{Path(entry_file).name} §"{entry_match.group("head")}"' == target:
            return True
    return False


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
    if "/" in file_prefix:
        return False
    sibling_headings = headings_by_file.get(file_prefix)
    if sibling_headings is None:
        return False
    return heading in sibling_headings


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
    entry_strings, entry_headings = _flatten_allowlist(
        external_references=external_references,
    )
    headings_by_file: dict[str, frozenset[str]] = {
        path.name: frozenset(_collect_headings(text=text)) for path, text in texts.items()
    }
    all_headings: set[str] = set()
    for headings in headings_by_file.values():
        all_headings |= headings
    resolver = _Resolver(
        all_headings=frozenset(all_headings),
        headings_by_file=headings_by_file,
        entry_strings=frozenset(entry_strings),
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
