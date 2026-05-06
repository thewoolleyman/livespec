"""Private helpers for `gherkin_blank_line_format`.

Extracts pure and low-level helpers from the parent module so the
public check wrapper stays below the soft LLOC ceiling while
preserving the same test surface via parent-module re-exports.
"""

from __future__ import annotations

import re
from pathlib import Path

from returns.io import IOResult

from livespec.errors import LivespecError
from livespec.io import fs

__all__: list[str] = [
    "_CLOSING_FENCE_PATTERN",
    "_MINIMAL_SHAPE_FILENAME",
    "_OPENING_FENCE_PATTERN",
    "_find_closing_fence",
    "_has_gherkin_fence",
    "_is_blank_above",
    "_is_blank_below",
    "_is_minimal_shape",
    "_list_top_level_md_files",
    "_scan_text_for_violation",
]


_MINIMAL_SHAPE_FILENAME: str = "SPECIFICATION.md"
_OPENING_FENCE_PATTERN: re.Pattern[str] = re.compile(r"^\s*```gherkin\s*$")
_CLOSING_FENCE_PATTERN: re.Pattern[str] = re.compile(r"^\s*```\s*$")


def _is_blank_above(*, lines: list[str], line_index: int) -> bool:
    """Determine whether the line above `line_index` is blank or absent.

    Returns True when `line_index == 0` (start-of-file is
    implicit-blank-above) OR when `lines[line_index - 1]`
    contains only whitespace. Returns False otherwise.
    """
    if line_index == 0:
        return True
    return lines[line_index - 1].strip() == ""


def _is_blank_below(*, lines: list[str], line_index: int) -> bool:
    """Determine whether the line below `line_index` is blank or absent.

    Returns True when `line_index == len(lines) - 1` (end-of-file
    is implicit-blank-below) OR when `lines[line_index + 1]`
    contains only whitespace. Returns False otherwise.
    """
    if line_index == len(lines) - 1:
        return True
    return lines[line_index + 1].strip() == ""


def _find_closing_fence(*, lines: list[str], opening_index: int) -> int | None:
    """Find the closing-fence line index after `opening_index`.

    Walks forward from `opening_index + 1` looking for the next
    line matching the closing-fence pattern (exactly ` ``` `
    with optional surrounding whitespace). Returns the line
    index of the closing fence on success, or None when no
    closing fence exists in the file (unmatched opener — the
    v1 minimum scope ignores the broader well-formedness).
    """
    for candidate_index in range(opening_index + 1, len(lines)):
        if _CLOSING_FENCE_PATTERN.match(lines[candidate_index]):
            return candidate_index
    return None


def _list_top_level_md_files(
    *,
    spec_root: Path,
) -> IOResult[list[Path], LivespecError]:
    """List `<spec_root>/*.md` top-level files in sorted order.

    Per the same walk-set semantic as
    `bcp14-keyword-wellformedness`: the check inspects only the
    top-level `*.md` files at `spec_root`. `fs.list_dir` yields
    every immediate child sorted by name; this helper filters
    to `.md` files and excludes directories.
    """
    return fs.list_dir(path=spec_root).map(
        lambda children: [child for child in children if child.is_file() and child.suffix == ".md"],
    )


def _is_minimal_shape(*, spec_root: Path) -> bool:
    """Detect minimal-template single-file shape at `spec_root`.

    Per `SPECIFICATION/templates/minimal/constraints.md`
    §"Single-file end-user output": a minimal-rooted project
    carries `SPECIFICATION.md` directly at the spec_root. The
    presence of that file is the v1 detection signal — it
    distinguishes minimal-shape from livespec-shape (which has
    no top-level `SPECIFICATION.md` and instead carries
    `spec.md`, `contracts.md`, etc. as separate files).
    """
    return (spec_root / _MINIMAL_SHAPE_FILENAME).is_file()


def _has_gherkin_fence(*, text: str) -> bool:
    """Detect whether `text` contains any opening gherkin fence.

    Walks the lines of `text` and returns True on the first
    match against `_OPENING_FENCE_PATTERN`. False otherwise.
    The minimal-rooted exemption check uses this signal: a
    minimal-shape `SPECIFICATION.md` with no opening fences
    triggers the skipped path; one with at least one opening
    fence falls through to the normal scan.
    """
    return any(_OPENING_FENCE_PATTERN.match(line) for line in text.splitlines())


def _scan_text_for_violation(
    *,
    text: str,
) -> tuple[str, int] | None:
    """Scan `text` for the first fence blank-line violation.

    Splits `text` into lines (preserving 1-indexed line numbers)
    and walks each line. On the first opening fence, checks the
    above-blank rule; if violated, returns ('opening', N). Then
    seeks the matching closing fence and checks the below-blank
    rule; if violated, returns ('closing', M). On no violation,
    advances past the closing fence and continues scanning for
    additional opening fences.

    Returns:
      - ('opening', line_number) when an opening fence violates
        the preceded-by-blank rule;
      - ('closing', line_number) when a closing fence violates
        the followed-by-blank rule;
      - None when every fenced block in the file is well-formed
        (or the file has no fenced gherkin blocks at all).
    """
    lines = text.splitlines()
    line_index = 0
    while line_index < len(lines):
        if _OPENING_FENCE_PATTERN.match(lines[line_index]):
            opening_line_number = line_index + 1
            if not _is_blank_above(lines=lines, line_index=line_index):
                return ("opening", opening_line_number)
            closing_index = _find_closing_fence(lines=lines, opening_index=line_index)
            if closing_index is None:
                return None
            if not _is_blank_below(lines=lines, line_index=closing_index):
                return ("closing", closing_index + 1)
            line_index = closing_index + 1
            continue
        line_index += 1
    return None
