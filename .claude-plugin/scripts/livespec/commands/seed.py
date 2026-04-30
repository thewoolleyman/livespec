"""Seed sub-command supervisor.

Per PROPOSAL.md §"`seed`" + briefing "outside-in walking
direction": this is the wrapper entry-point importing
`livespec.commands.seed.main`. Drives the seed flow:
load+validate `--seed-json` payload, write `.livespec.jsonc`,
materialize the main + sub-spec trees, auto-capture the seed
proposed-change, run post-step doctor.

Cycle 65 lands the bare `main()` supervisor stub returning a
fixed exit code; subsequent cycles widen behavior-by-behavior
under consumer pressure (argv parsing, payload validation,
filesystem writes, post-step doctor).
"""

from __future__ import annotations

__all__: list[str] = ["main"]


def main(*, argv: list[str]) -> int:
    """Seed supervisor entry point. Returns the process exit code.

    Currently a not-yet-implemented stub: returns 1 (the open-
    base `LivespecError.exit_code`) until the next cycle drives
    a more specific failure mode (UsageError on missing argv,
    ValidationError on bad payload, etc.).
    """
    del argv
    return 1
