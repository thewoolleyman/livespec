"""livespec.commands.critique — supervisor for `bin/critique.py`.

v032 TDD redo cycle 17: smallest impl that drives the cycle-16
outside-in integration test to Green by internally delegating to
`livespec.commands.propose_change.run_propose_change` per
PROPOSAL.md §"`critique`" lines 2280-2333 + Plan §"Phase 3"
lines 1408-1416. The supervisor:

1. Parses `--findings-json <path> [--author <id>] [--spec-target <path>]`
   via argparse. There is NO positional `<topic>` arg — the topic
   is DERIVED from the resolved author per PROPOSAL.md lines
   2307-2325.
2. Resolves the author at Phase 3 minimum-viable scope using the
   simplest two-source rule per cycle-11 / cycle-13 precedent:
   `--author` flag if non-empty, else the cycle-8
   `livespec.io.git.current_user_or_unknown()` fallback. Full
   4-source precedence (CLI → env var `LIVESPEC_AUTHOR_LLM` →
   payload `author` field → `"unknown-llm"` per PROPOSAL.md
   lines 2294-2301) is Phase 7 widening.
3. Slugs the resolved author per PROPOSAL.md lines 2218-2226:
   lowercase → replace runs of `[^a-z0-9]` with single hyphen →
   strip leading/trailing hyphens → truncate to 64 chars. The
   slug-rule helper is currently inlined in this module
   (`_slug_author`); lift to `livespec/parse/slug.py` when a
   second consumer appears (likely candidates: revise's stem
   derivation when it gains the propose-change-style topic
   handling beyond Phase 3 minimum, or `out-of-band-edits`
   backfill in Phase 7).
4. Composes the canonical critique topic by appending the
   reserve-suffix `"-critique"` (v016 P3) to the slugged author.
   Full reserve-suffix algorithm with truncation + pre-attached
   suffix handling (PROPOSAL.md lines 2174-2193) is Phase 7
   widening; the cycle-17 minimum naively concatenates and
   relies on author-stem-only (no `-critique` already present)
   inputs.
5. Calls `run_propose_change(findings_path=..., topic=..., author=...,
   spec_target=...)` and returns its int. The internal call
   skips its own pre/post doctor cycle since the outer critique
   wrapper's ROP chain already covers the whole operation
   (PROPOSAL.md lines 2322-2325 — Phase 7 ROP-lift work).

Out of Phase 3 scope per Plan lines 1408-1416:
- Payload schema validation against `proposal_findings.schema.json`
  (deferred until a failure-path test forces it; same pattern
  as cycle 11 / cycle 13).
- Full reserve-suffix canonicalization (truncation /
  pre-attached-suffix handling).
- Author env-var precedence + payload-self-declared author.
- Collision disambiguation `-N` suffix per PROPOSAL.md lines
  2326-2331.
- Pre/post doctor-static lifecycle integration.
- ROP plumbing (`@impure_safe`, `IOResult`).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from livespec.commands.propose_change import run_propose_change
from livespec.io.git import current_user_or_unknown

__all__: list[str] = ["main"]

_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_SLUG_MAX_LENGTH = 64


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="critique", exit_on_error=False)
    parser.add_argument("--findings-json", required=True, type=Path)
    parser.add_argument("--author", default=None)
    parser.add_argument("--spec-target", default="SPECIFICATION")
    return parser


def _resolve_author(*, cli_author: str | None) -> str:
    if cli_author is not None and cli_author != "":
        return cli_author
    return current_user_or_unknown()


def _slug_author(*, raw_author: str) -> str:
    lowered = raw_author.lower()
    hyphenated = _SLUG_NON_ALNUM.sub("-", lowered).strip("-")
    return hyphenated[:_SLUG_MAX_LENGTH]


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:])
    resolved_author = _resolve_author(cli_author=args.author)
    slug = _slug_author(raw_author=resolved_author)
    topic = f"{slug}-critique"
    return run_propose_change(
        findings_path=args.findings_json,
        topic=topic,
        author=resolved_author,
        spec_target=args.spec_target,
    )
