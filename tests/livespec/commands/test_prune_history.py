"""Tests for livespec.commands.prune_history.

Per PROPOSAL.md §"`prune-history`" (line ~2454): prune-history
trims the historical revisions from history/vNNN/ down to a
caller-specified retention horizon. Phase 3 lands the stub
shape only; the full implementation widens in Phase 7.
"""

from __future__ import annotations

from livespec.commands import prune_history

__all__: list[str] = []


def test_prune_history_main_exists_and_returns_int() -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/prune_history.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature.
    """
    exit_code = prune_history.main(argv=[])
    assert isinstance(exit_code, int)
