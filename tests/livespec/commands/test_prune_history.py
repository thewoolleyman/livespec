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


def test_prune_history_main_accepts_skip_pre_check_flag() -> None:
    """`--skip-pre-check` is a recognized optional flag (exit 0).

    Per v012 §"Wrapper CLI surface" prune-history row: the wrapper
    accepts `--skip-pre-check` as one half of the mutually-exclusive
    flag pair codified in v012 spec.md §"Pre-step skip control".
    The Phase-3 minimum-viable parser knows nothing about this
    flag; exit 0 here pins the post-cycle-6.c.1 contract.
    """
    exit_code = prune_history.main(argv=["--skip-pre-check"])
    assert exit_code == 0


def test_prune_history_main_accepts_run_pre_check_flag() -> None:
    """`--run-pre-check` is a recognized optional flag (exit 0).

    Per v012 §"Wrapper CLI surface" prune-history row: the wrapper
    accepts `--run-pre-check` as the override-config half of the
    mutually-exclusive flag pair codified in v012 spec.md
    §"Pre-step skip control".
    """
    exit_code = prune_history.main(argv=["--run-pre-check"])
    assert exit_code == 0


def test_prune_history_main_rejects_both_skip_and_run_pre_check_flags_together() -> None:
    """Passing both `--skip-pre-check` AND `--run-pre-check` exits 2.

    Per v012 spec.md §"Pre-step skip control" rule (4): both flags
    set together MUST result in argparse mutually-exclusive usage
    error, lifting to exit 2 via `IOFailure(UsageError)`. Drives
    the `add_mutually_exclusive_group` enforcement.
    """
    exit_code = prune_history.main(argv=["--skip-pre-check", "--run-pre-check"])
    assert exit_code == 2


def test_prune_history_main_accepts_project_root_flag() -> None:
    """`--project-root <path>` is a recognized optional flag (exit 0).

    Per v012 contracts.md §"Wrapper CLI surface" prune-history row
    + the universal `--project-root <path>` baseline (PROPOSAL.md
    §"Project-root detection contract" explicitly enumerates
    `bin/prune_history.py` as a project-state wrapper that accepts
    the flag). The actual project-root resolution + spec-root
    upward-walk happens in later cycles when the wrapper body is
    wired.
    """
    exit_code = prune_history.main(argv=["--project-root", "/tmp"])
    assert exit_code == 0
