# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# Type erosion from generic dict[str, Any] payloads parsed out of
# JSONL and JSONC: pyright cannot narrow the type of values pulled
# from dict-typed payloads through .get() chains. Mirrors the same
# pragma applied to sibling `no_stalled_epic.py` and friends — the
# helper file's job is to walk and pattern-match against unstructured
# wire payloads, so flow-narrowing through Any-typed dict access is
# expected and tolerated. Non-vendor-payload code in this tree
# retains full enforcement.
"""Pure helpers extracted from `unresolved_spec_commitment.run`.

Sibling-to the per-check module under the `_<check>_helpers.py`
convention used by `_no_orphan_dependency_helpers.py`. Holds the
front-matter `spec_commitments` block parser, the history-walk
helpers, and the JSONL hint-materialization helper. Keeping these
in a separate module keeps `unresolved_spec_commitment.py` under
the 250-line hard ceiling enforced by `check-complexity`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from returns.result import Success

from livespec.parse import front_matter as front_matter_parse

__all__: list[str] = [
    "HISTORY_SUBDIR",
    "PROPOSED_CHANGES_DIR",
    "PRUNED_MARKER",
    "REVISION_SUFFIX",
    "ParsedCommitments",
    "Unresolved",
    "collect_obligations_and_supersedes",
    "hints_from_index",
]


HISTORY_SUBDIR = "history"
PROPOSED_CHANGES_DIR = "proposed_changes"
REVISION_SUFFIX = "-revision.md"
PRUNED_MARKER = "PRUNED_HISTORY.json"
_VERSION_RE = re.compile(r"^v(\d+)$")


@dataclass(frozen=True, kw_only=True, slots=True)
class ParsedCommitments:
    """Subset of front-matter spec_commitments parsed from a PC file.

    `impl_followups_id_hints` is the list of id_hint strings declared
    in `spec_commitments.impl_followups[]`. `supersedes` is the list
    of earlier id_hint values declared in
    `spec_commitments.supersedes[]` (empty when absent).
    """

    impl_followups_id_hints: list[str]
    supersedes: list[str]


@dataclass(frozen=True, kw_only=True, slots=True)
class Unresolved:
    """One unresolved id_hint plus the version label that introduced it."""

    id_hint: str
    version_label: str
    pc_stem: str


def _split_front_matter_block(*, text: str) -> list[str] | None:
    """Return the front-matter body lines (between leading + closing `---\\n`).

    Returns None when no front-matter block is found.
    """
    if not text.startswith("---\n"):
        return None
    lines = text.split("\n")
    for index in range(1, len(lines)):
        if lines[index] == "---":
            return lines[1:index]
    return None


def _leading_spaces(*, line: str) -> int:
    """Return the count of leading space characters in `line`.

    Equivalent to `len(line) - len(line.lstrip(" "))`. The
    one-statement expression keeps the branch graph minimal so
    100% coverage holds without a contrived all-spaces fixture
    (call sites in this module always filter blank lines via
    `.strip() == ""` before invoking this helper, so the
    "every char is a space" case never reaches it).
    """
    return len(line) - len(line.lstrip(" "))


def _take_indented_block(*, body_lines: list[str], start_index: int) -> list[str]:
    """Return the lines indented under the line at start_index.

    Walks forward from `start_index + 1` and collects lines whose
    leading-space count is strictly greater than the start line's.
    Stops on the first non-blank line at the start-line indent or
    less.
    """
    start_indent = _leading_spaces(line=body_lines[start_index])
    collected: list[str] = []
    for index in range(start_index + 1, len(body_lines)):
        candidate = body_lines[index]
        if candidate.strip() == "":
            collected.append(candidate)
            continue
        if _leading_spaces(line=candidate) <= start_indent:
            break
        collected.append(candidate)
    return collected


def _slice_subheader(*, block_lines: list[str], header_name: str) -> list[str]:
    """Return the indented lines under `<header_name>:` inside block_lines."""
    header_line = f"{header_name}:"
    start_index: int | None = None
    header_indent = 0
    for index, line in enumerate(block_lines):
        if line.strip() == header_line:
            start_index = index
            header_indent = _leading_spaces(line=line)
            break
    if start_index is None:
        return []
    collected: list[str] = []
    for index in range(start_index + 1, len(block_lines)):
        candidate = block_lines[index]
        if candidate.strip() == "":
            collected.append(candidate)
            continue
        if _leading_spaces(line=candidate) <= header_indent:
            break
        collected.append(candidate)
    return collected


def _extract_impl_followups_id_hints(*, lines: list[str]) -> list[str]:
    """Extract `id_hint:` values from `impl_followups[]` entries."""
    impl_block = _slice_subheader(block_lines=lines, header_name="impl_followups")
    hints: list[str] = []
    for line in impl_block:
        stripped = line.strip()
        if stripped.startswith("- id_hint:"):
            value = stripped[len("- id_hint:") :].strip()
            if value:
                hints.append(value)
    return hints


def _extract_supersedes_after_header(*, block_lines: list[str]) -> list[str]:
    """Extract bare-slug list items from the `supersedes:` sub-section.

    A line.strip().startswith("- ") implies the stripped line has a
    non-whitespace character at index 2 or later (since .strip() removes
    trailing whitespace); therefore `stripped[2:].strip()` is always
    non-empty when the predicate passes, and no defensive empty-value
    guard is needed.
    """
    super_block = _slice_subheader(block_lines=block_lines, header_name="supersedes")
    slugs: list[str] = []
    for line in super_block:
        stripped = line.strip()
        if stripped.startswith("- "):
            slugs.append(stripped[2:].strip())
    return slugs


def _parse_spec_commitments(*, body_lines: list[str]) -> ParsedCommitments | None:
    """Parse the `spec_commitments` block from front-matter body lines.

    Returns None when the front-matter does not declare a
    `spec_commitments` block. The parser recognizes ONLY the exact
    shape the propose-change wrapper emits.
    """
    block_start: int | None = None
    for index, line in enumerate(body_lines):
        if line.rstrip() == "spec_commitments:":
            block_start = index
            break
    if block_start is None:
        return None
    block_lines = _take_indented_block(body_lines=body_lines, start_index=block_start)
    return ParsedCommitments(
        impl_followups_id_hints=_extract_impl_followups_id_hints(lines=block_lines),
        supersedes=_extract_supersedes_after_header(block_lines=block_lines),
    )


def _read_pc_file_commitments(*, pc_path: Path) -> ParsedCommitments | None:
    """Read a propose-change file and extract its spec_commitments block."""
    text = pc_path.read_text(encoding="utf-8")
    body_lines = _split_front_matter_block(text=text)
    if body_lines is None:
        return None
    return _parse_spec_commitments(body_lines=body_lines)


def _read_revision_decision(*, revision_path: Path) -> str | None:
    """Return the `decision:` value from a revision file's front-matter."""
    text = revision_path.read_text(encoding="utf-8")
    parse_result = front_matter_parse.parse_front_matter(text=text)
    if not isinstance(parse_result, Success):
        return None
    decision = parse_result.unwrap().get("decision")
    if isinstance(decision, str):
        return decision
    return None


def _parse_version_number(*, path: Path) -> int | None:
    """Extract NNN from a `vNNN` directory name, or None on shape mismatch."""
    match = _VERSION_RE.match(path.name)
    if match is None:
        return None
    return int(match.group(1))


def _list_version_dirs(*, history_path: Path) -> list[tuple[int, Path]]:
    """Return a sorted list of `(N, vNNN-dir)` pairs under history/, skipping pruned markers."""
    if not history_path.is_dir():
        return []
    pairs: list[tuple[int, Path]] = []
    for child in sorted(history_path.iterdir()):
        if not child.is_dir():
            continue
        n = _parse_version_number(path=child)
        if n is None:
            continue
        if (child / PRUNED_MARKER).is_file():
            continue
        pairs.append((n, child))
    pairs.sort(key=lambda pair: pair[0])
    return pairs


def _list_pc_stems(*, version_dir: Path) -> list[str]:
    """Return the sorted list of PC filename stems (no `-revision.md`) in version_dir."""
    proposed_changes = version_dir / PROPOSED_CHANGES_DIR
    if not proposed_changes.is_dir():
        return []
    stems: list[str] = []
    for entry in sorted(proposed_changes.iterdir()):
        if not entry.is_file():
            continue
        if entry.name.endswith(REVISION_SUFFIX):
            continue
        if not entry.name.endswith(".md"):
            continue
        stems.append(entry.name[: -len(".md")])
    return stems


def hints_from_index(*, index: dict[str, dict[str, Any]]) -> set[str]:
    """Return the set of non-null `spec_commitment_hint` values in `index`.

    `index` is the materialized latest-record-per-id work-items view
    acquired from the active impl-plugin's `list-work-items` wrapper
    (per `_work_items_provider.py`). Records lacking the field, or
    carrying `null`, or carrying a non-string value contribute
    nothing.
    """
    hints: set[str] = set()
    for record in index.values():
        hint = record.get("spec_commitment_hint")
        if isinstance(hint, str) and hint:
            hints.add(hint)
    return hints


def collect_obligations_and_supersedes(
    *,
    spec_root: Path,
) -> tuple[list[Unresolved], set[str]]:
    """Walk history/vNNN/ and collect declared obligations + supersedes set.

    Returns `(obligations, superseded_set)` where:
      - `obligations` is the list of accepted-or-modified `Unresolved`
        candidates (id_hint + originating version label + PC stem);
        ALL such obligations are collected, including ones later
        superseded — supersession is applied as a second pass.
      - `superseded_set` is the union of every `supersedes[]` entry
        across the entire history. Membership in this set EXEMPTS
        the corresponding id_hint from the coverage check, per
        the contracts.md supersession rule.
    """
    history_path = spec_root / HISTORY_SUBDIR
    obligations: list[Unresolved] = []
    superseded_set: set[str] = set()
    for _n, version_dir in _list_version_dirs(history_path=history_path):
        for pc_stem in _list_pc_stems(version_dir=version_dir):
            pc_path = version_dir / PROPOSED_CHANGES_DIR / f"{pc_stem}.md"
            revision_path = version_dir / PROPOSED_CHANGES_DIR / f"{pc_stem}{REVISION_SUFFIX}"
            if not revision_path.is_file():
                continue
            decision = _read_revision_decision(revision_path=revision_path)
            if decision not in ("accept", "modify"):
                continue
            commitments = _read_pc_file_commitments(pc_path=pc_path)
            if commitments is None:
                continue
            for hint in commitments.impl_followups_id_hints:
                obligations.append(
                    Unresolved(
                        id_hint=hint,
                        version_label=version_dir.name,
                        pc_stem=pc_stem,
                    ),
                )
            for slug in commitments.supersedes:
                superseded_set.add(slug)
    return obligations, superseded_set
