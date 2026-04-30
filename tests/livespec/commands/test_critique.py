"""Tests for livespec.commands.critique.

Per PROPOSAL.md §"`critique`" (line ~2280) and Plan Phase 3
(lines 1524-1532): critique is minimum-viable per v019 Q1 —
invokes propose_change internally with the `-critique`
reserve-suffix appended. Full LLM-driven critique flow lives at
SKILL.md prose level, not in the wrapper.
"""

from __future__ import annotations

from livespec.commands import critique

__all__: list[str] = []


def test_critique_main_exists_and_returns_int() -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/critique.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature.
    """
    exit_code = critique.main(argv=[])
    assert isinstance(exit_code, int)
