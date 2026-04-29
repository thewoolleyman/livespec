"""livespec.commands.critique — supervisor for `bin/critique.py`.

Stub at v032 TDD redo cycle 16. Returns 0 so the wrapper imports
cleanly and the outside-in integration test
(`tests/bin/test_critique.py`) advances past the "wrapper file
does not exist" failure mode to the next failure: the
`<slugged-author>-critique.md` file is not written. Subsequent
cycles drive that assertion forward by authoring the actual
internal-delegation pipeline per PROPOSAL.md §"`critique`" lines
2280-2333 + Plan §"Phase 3" lines 1408-1416 (post-Case-B
reconciliation already aligned).

Phase 3 minimum-viable scope per Plan lines 1408-1416:
- Validate `--findings-json <path>` payload against
  `proposal_findings.schema.json` (skill-owned).
- Resolve author via the unified 4-source precedence (CLI →
  env → payload → "unknown-llm"); Phase 3 minimum may collapse
  to two-source per the seed/propose-change precedent.
- Slug the resolved author stem and combine with the
  reserve-suffix `"-critique"` (v016 P3) to produce the
  canonical critique topic.
- Internally delegate to `livespec.commands.propose_change`'s
  Python logic with the canonical topic and forwarded
  `--spec-target <path>`. The internal call skips its own
  pre/post doctor cycle since the outer critique wrapper's
  ROP chain already covers the whole operation (PROPOSAL.md
  lines 2322-2325).

Out of Phase 3 scope: full reserve-suffix canonicalization
algorithm with truncation/pre-attached-suffix handling
(PROPOSAL.md lines 2174-2193; codified in deferred-items.md's
`static-check-semantics` entry per v017 Q1) — Phase 7 widening.
"""

from __future__ import annotations

__all__: list[str] = ["main"]


def main() -> int:
    return 0
