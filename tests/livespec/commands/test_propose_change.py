"""Tests for livespec.commands.propose_change.

Per PROPOSAL.md §"`propose-change`" (line ~2134) and Plan
Phase 3 (lines 1505-1523), propose-change is the second
sub-command authored under TDD. Phase-3 minimum-viable scope:
validate the inbound `--findings-json <path>` payload against
proposal_findings.schema.json, compose a proposed-change file
from the findings, write it to
`<spec-target>/proposed_changes/<topic>.md`. Topic-canonical-
ization is OUT OF SCOPE for Phase 3.
"""

from __future__ import annotations

from livespec.commands import propose_change

__all__: list[str] = []


def test_propose_change_main_exists_and_returns_int() -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/propose_change.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature.
    """
    exit_code = propose_change.main(argv=[])
    assert isinstance(exit_code, int)
