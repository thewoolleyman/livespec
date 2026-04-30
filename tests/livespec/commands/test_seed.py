"""Tests for livespec.commands.seed.

The seed sub-command is the Phase 3 outermost rail per the
briefing's outside-in walking direction. Cycles drive its
behavior step-by-step from the supervisor entrypoint
(`main(argv)`) inward.
"""

from __future__ import annotations

from livespec.commands import seed

__all__: list[str] = []


def test_seed_main_exists_and_returns_int() -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/seed.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature. Subsequent cycles widen the body
    behavior-by-behavior.
    """
    exit_code = seed.main(argv=[])
    assert isinstance(exit_code, int)
