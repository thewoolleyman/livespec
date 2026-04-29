"""livespec.commands.seed — supervisor for `bin/seed.py`.

Stub at cycle 1 of the v032 retroactive TDD redo. Returns 0 so the
wrapper imports cleanly and the outside-in integration test
(`tests/bin/test_seed.py`) advances past the FileNotFoundError
failure mode to the next failure: `.livespec.jsonc` is not
written. Subsequent cycles drive that assertion forward by
authoring the actual railway pipeline per PROPOSAL.md §"`seed`"
lines 1992-2042 (the deterministic file-shaping work order).
"""

from __future__ import annotations

__all__: list[str] = ["main"]


def main() -> int:
    return 0
