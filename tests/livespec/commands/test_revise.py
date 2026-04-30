"""Tests for livespec.commands.revise.

Per PROPOSAL.md §"`revise`" (line ~2335) and Plan Phase 3
(lines 1533-1553): revise is minimum-viable per v019 Q1 —
validate `--revise-json` payload, process per-proposal
`decisions[]` in payload order, write paired
`<stem>-revision.md`, move processed proposed-change files into
`history/vNNN/proposed_changes/`, cut new `history/vNNN/`.
"""

from __future__ import annotations

from livespec.commands import revise

__all__: list[str] = []


def test_revise_main_exists_and_returns_int() -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/revise.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature.
    """
    exit_code = revise.main(argv=[])
    assert isinstance(exit_code, int)
