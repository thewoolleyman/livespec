"""Seed sub-command supervisor.

Per PROPOSAL.md §"`seed`" + briefing "outside-in walking
direction": this is the wrapper entry-point importing
`livespec.commands.seed.main`. Drives the seed flow:
load+validate `--seed-json` payload, write `.livespec.jsonc`,
materialize the main + sub-spec trees, auto-capture the seed
proposed-change, run post-step doctor.

`build_parser()` is the pure argparse factory per style doc
§"CLI argument parsing seam"; `main()` is the supervisor that
threads argv through the railway and pattern-matches the final
IOResult to derive the exit code.
"""

from __future__ import annotations

import argparse

__all__: list[str] = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    """Construct the seed argparse parser without parsing.

    Pure: returns the configured parser; the caller (the io/cli
    facade) drives `parse_args()`. Per style doc §"CLI argument
    parsing seam", `exit_on_error=False` lets argparse signal
    errors via `argparse.ArgumentError` rather than `SystemExit`.
    """
    parser = argparse.ArgumentParser(prog="seed", exit_on_error=False)
    _ = parser.add_argument("--seed-json", required=True)
    return parser


def main(*, argv: list[str]) -> int:
    """Seed supervisor entry point. Returns the process exit code.

    Currently a not-yet-implemented stub: returns 1 (the open-
    base `LivespecError.exit_code`) until the next cycle drives
    a more specific failure mode (UsageError on missing argv,
    ValidationError on bad payload, etc.).
    """
    del argv
    return 1
