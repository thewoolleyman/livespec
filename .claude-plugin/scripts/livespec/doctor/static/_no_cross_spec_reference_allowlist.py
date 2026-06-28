"""Allowlist parsing and matching for `no_cross_spec_reference`."""

from __future__ import annotations

import re
from collections.abc import Set
from pathlib import Path
from typing import Any, cast

__all__: list[str] = [
    "_CITATION_PATTERN",
    "_allowlist_match",
    "_flatten_allowlist",
]

# Pattern matching a section citation: an optional `<path>.md`
# file prefix, then the section sign followed by a double-quoted
# heading. Group `file` is the optional file prefix (None for a
# bare citation); group `head` is the heading text between the
# quotes.
_CITATION_PATTERN: re.Pattern[str] = re.compile(
    r'(?:(?P<file>[^\s"`()]+\.md)\s+)?§"(?P<head>[^"]*)"',
)


def _flatten_allowlist(
    *,
    external_references: Any,
) -> tuple[set[str], set[str], dict[str, set[str]]]:
    """Flatten `external_references` into global and per-repo match sets."""
    entry_strings: set[str] = set()
    entry_headings: set[str] = set()
    entry_strings_by_repo: dict[str, set[str]] = {}
    if not isinstance(external_references, dict):
        return (entry_strings, entry_headings, entry_strings_by_repo)
    block = cast("dict[str, object]", external_references)
    for repo_slug, entries in block.items():
        repo_entries: set[str] = set()
        if not isinstance(entries, list):
            continue
        items = cast("list[object]", entries)
        for entry in items:
            if not isinstance(entry, str):
                continue
            entry_strings.add(entry)
            repo_entries.add(entry)
            head_match = _CITATION_PATTERN.search(entry)
            if head_match is not None:
                entry_headings.add(head_match.group("head"))
        entry_strings_by_repo[repo_slug] = repo_entries
    return (entry_strings, entry_headings, entry_strings_by_repo)


def _allowlist_match(
    *,
    file_prefix: str | None,
    heading: str,
    entry_strings: Set[str],
    entry_headings: Set[str],
) -> bool:
    """Return True iff this citation is covered by the allowlist."""
    if file_prefix is None:
        return heading in entry_headings
    target_file = file_prefix if "/" in file_prefix else Path(file_prefix).name
    target = f'{target_file} §"{heading}"'
    for entry in entry_strings:
        entry_match = _CITATION_PATTERN.search(entry)
        if entry_match is None:
            continue
        entry_file = entry_match.group("file")
        if entry_file is None:
            continue
        entry_key = entry_file if "/" in file_prefix else Path(entry_file).name
        if f'{entry_key} §"{entry_match.group("head")}"' == target:
            return True
    return False
