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
from pathlib import Path

from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.errors import LivespecError
from livespec.io import cli, fs

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


def _load_seed_json(*, namespace: argparse.Namespace) -> IOResult[str, LivespecError]:
    """Read the --seed-json payload from disk; railway-stage 2.

    Threads the namespace's `seed_json` attribute into
    fs.read_text. Failure-track LivespecError values bubble
    untouched.
    """
    return fs.read_text(path=Path(namespace.seed_json))


def _pattern_match_io_result(
    *,
    io_result: IOResult[str, LivespecError],
) -> int:
    """Pattern-match the final railway IOResult onto an exit code.

    The success branch currently returns 1 (not-yet-implemented
    stub for the seed-flow body); subsequent cycles drive the
    payload-validation, file-shaping, and post-step pipeline
    that produces a real success exit (0).
    """
    unwrapped = unsafe_perform_io(io_result)
    match unwrapped:
        case Success(_):
            return 1
        case Failure(LivespecError() as err):
            return err.exit_code
        case _:
            assert_never(unwrapped)


def main(*, argv: list[str]) -> int:
    """Seed supervisor entry point. Returns the process exit code.

    Threads argv through the railway:
      parse_argv -> read --seed-json file -> (subsequent stages)

    UsageError (parse) -> exit 2; PreconditionError (missing
    file) -> exit 3; success branch is still stubbed at exit 1
    until the next cycle drives payload parsing.
    """
    parser = build_parser()
    railway = cli.parse_argv(parser=parser, argv=argv).bind(
        lambda namespace: _load_seed_json(namespace=namespace),
    )
    return _pattern_match_io_result(io_result=railway)
