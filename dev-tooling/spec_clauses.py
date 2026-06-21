"""spec_clauses — the shared spec-clause extractor + gap-id primitive.

This is the single-source-of-truth implementation of the
livespec family's behavior-clause detection: it enumerates the
`MUST` / `MUST NOT` / `SHOULD` / `SHOULD NOT` rule lines in a spec
markdown body and derives a stable `gap-<8>` id for each, keyed on
`spec_file \x1f heading_path \x1f rule_text`.

The module is PURE STDLIB and PURE FUNCTIONS — no I/O, no argument
parsing, no process exit, no spec-tree walking. Callers supply the
already-read file content (a string) and the spec-file path label.

Consumers (single-sourced from here so the gap-id derivation can
never drift between them):

- `livespec`'s own `dev-tooling/checks/behavior_scenario_link.py`
  advisory check (extracts clauses from the live spec, derives
  gap-ids, and WARNs for any clause lacking a `clauses[]` scenario
  link in `tests/heading-coverage.json`).
- `livespec-orchestrator-beads-fabro`'s `/livespec-orchestrator-beads-fabro:detect-impl-gaps`
  thin-transport command, which VENDORS a byte-identical copy of
  this module into its plugin runtime bundle (the plugin runtime
  carries no dev dependencies, so it resolves the import from the
  vendored `_vendor/` tree rather than from this dev-tooling copy).
  A gap-id parity test on each side pins the two copies together.

Because the gap-id is a content hash, any change to the extraction
rules or the derivation here is a cross-repo coordinated change: the
parity tests on both sides are the mechanical drift guard.
"""

from __future__ import annotations

import hashlib
import re
from base64 import b32encode
from dataclasses import dataclass

__all__ = [
    "RuleMatch",
    "derive_gap_id",
    "extract_rules_from_file",
]

_RULE_KEYWORD_PATTERN = re.compile(r"\b(MUST NOT|SHOULD NOT|MUST|SHOULD)\b")
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_CODE_FENCE_PATTERN = re.compile(r"^\s*```")
_GAP_ID_LENGTH = 8


@dataclass(frozen=True, kw_only=True)
class RuleMatch:
    """A single MUST/SHOULD rule detected in a spec file."""

    spec_file: str
    heading_path: str
    line_text: str
    gap_id: str


def extract_rules_from_file(*, spec_file: str, content: str) -> list[RuleMatch]:
    """Enumerate the MUST/SHOULD rule lines in a single spec file's content.

    `spec_file` is the path label baked into each rule's gap-id (it
    is part of the hash payload, so callers MUST pass the same label
    they want reflected in the id — e.g. the spec-root-relative file
    name). `content` is the file body.

    Lines inside fenced code blocks are skipped; markdown headings
    build the `heading_path` (a ` > `-joined breadcrumb) that scopes
    each rule. Returns rules in document order.
    """
    rules: list[RuleMatch] = []
    heading_stack: list[str] = []
    in_code_fence = False
    for raw_line in content.splitlines():
        if _CODE_FENCE_PATTERN.match(raw_line):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        heading_match = _HEADING_PATTERN.match(raw_line)
        if heading_match is not None:
            level = len(heading_match.group(1))
            title = heading_match.group(2)
            _push_heading(stack=heading_stack, level=level, title=title)
            continue
        if _RULE_KEYWORD_PATTERN.search(raw_line) is None:
            continue
        rule_text = raw_line.strip()
        heading_path = " > ".join(heading_stack) if heading_stack else "(top)"
        gap_id = derive_gap_id(
            spec_file=spec_file,
            heading_path=heading_path,
            rule_text=rule_text,
        )
        rules.append(
            RuleMatch(
                spec_file=spec_file,
                heading_path=heading_path,
                line_text=rule_text,
                gap_id=gap_id,
            )
        )
    return rules


def derive_gap_id(*, spec_file: str, heading_path: str, rule_text: str) -> str:
    """Derive the stable `gap-<8>` id for a single rule.

    The id is the first `_GAP_ID_LENGTH` lowercase base32 characters
    of `sha256(spec_file \x1f heading_path \x1f rule_text)`. Pure
    function of its inputs — the same triple always yields the same
    id across runs, platforms, and repos.
    """
    payload = f"{spec_file}\x1f{heading_path}\x1f{rule_text}".encode()
    digest = hashlib.sha256(payload).digest()
    suffix = b32encode(digest).decode("ascii").rstrip("=").lower()[:_GAP_ID_LENGTH]
    return f"gap-{suffix}"


def _push_heading(*, stack: list[str], level: int, title: str) -> None:
    while len(stack) >= level:
        _ = stack.pop()
    while len(stack) < level - 1:
        stack.append("")
    stack.append(title)
