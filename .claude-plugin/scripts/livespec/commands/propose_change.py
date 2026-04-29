"""livespec.commands.propose_change — supervisor for `bin/propose_change.py`.

Stub at v032 TDD redo cycle 10. Returns 0 so the wrapper imports
cleanly and the outside-in integration test
(`tests/bin/test_propose_change.py`) advances past the
"wrapper file does not exist" failure mode to the next failure:
`<spec-root>/proposed_changes/<topic>.md` is not written. Subsequent
cycles drive that assertion forward by authoring the actual
railway pipeline per PROPOSAL.md §"`propose-change`" lines
2134-2278 (CLI parsing, payload schema validation, topic
canonicalization, finding → proposal section field-copy mapping,
collision disambiguation, author resolution, and the file write).
"""

from __future__ import annotations

__all__: list[str] = ["main"]


def main() -> int:
    return 0
