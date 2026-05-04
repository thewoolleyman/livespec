"""Tests for livespec.commands.prune_history.

Per PROPOSAL.md §"`prune-history`": prune-history
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


def test_prune_history_main_returns_zero_on_valid_argv() -> None:
    """prune-history with no flags returns exit code 0.

    Per PROPOSAL.md §"`prune-history`": the
    Phase-3 minimum scope just establishes the parser. Phase 7
    widens to the actual prune mechanic (pruning the oldest
    `<spec-target>/history/v*/` directories down to a caller-
    specified retention horizon). Phase-3 success path returns 0
    so the lifecycle orchestration layer can advance.
    """
    exit_code = prune_history.main(argv=[])
    assert exit_code == 0


def test_prune_history_main_returns_usage_exit_code_on_unknown_flag() -> None:
    """Unknown CLI flag returns exit code 2.

    Drives the parse_argv stage on the railway: an unknown flag
    surfaces as an argparse SystemExit, which io/cli's
    @impure_safe maps to UsageError and the supervisor's
    pattern-match lifts to exit 2 via err.exit_code.
    """
    exit_code = prune_history.main(argv=["--no-such-flag"])
    assert exit_code == 2
