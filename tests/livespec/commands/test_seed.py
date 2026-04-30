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


def test_seed_build_parser_accepts_seed_json_flag() -> None:
    """The pure argparse factory accepts `--seed-json <path>` and binds it.

    Per PROPOSAL.md §"`seed`" lines 1937-1942 (`bin/seed.py
    --seed-json <path>` is the sole wrapper entry point) and
    style doc §"CLI argument parsing seam" (commands/<cmd>.py
    exposes a pure `build_parser() -> ArgumentParser` factory
    that constructs but does NOT parse). Constructing-only lets
    us introspect the parser shape without effectful invocation.
    """
    parser = seed.build_parser()
    namespace = parser.parse_args(["--seed-json", "/tmp/payload.json"])
    assert namespace.seed_json == "/tmp/payload.json"
