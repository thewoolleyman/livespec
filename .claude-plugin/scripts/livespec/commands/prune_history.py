"""Prune-history sub-command supervisor.

Per PROPOSAL.md §"`prune-history`" (line ~2454): prune-history
trims historical revisions from `<spec-target>/history/vNNN/`
down to a caller-specified retention horizon, preserving the
contiguous-version invariant. Phase 3 lands the parser shape +
the parse_argv-only railway returning 0 on success; the full
prune mechanic widens in Phase 7.

`build_parser()` is the pure argparse factory per style doc
§"CLI argument parsing seam"; `main()` is the supervisor that
threads argv through the railway and pattern-matches the final
IOResult to derive the exit code.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.errors import LivespecError
from livespec.io import cli

__all__: list[str] = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    """Construct the prune-history argparse parser without parsing.

    Per PROPOSAL.md §"`prune-history`" lines 2458-2462: the
    wrapper accepts ONLY the mutually-exclusive `--skip-pre-check`
    / `--run-pre-check` flag pair (per §"Pre-step skip control");
    no other arguments in v1. Phase 3 lands the bare parser; the
    pre-check logic widens in Phase 7 once the mutually-exclusive
    flag pair is enforced.
    """
    parser = argparse.ArgumentParser(prog="prune-history", exit_on_error=False)
    return parser


def _pattern_match_io_result(
    *,
    io_result: IOResult[Any, LivespecError],
) -> int:
    """Pattern-match the final railway IOResult onto an exit code.

    Success(<value>) -> exit 0 per style doc §"Exit code
    contract". Failure(LivespecError) lifts via err.exit_code;
    assert_never closes the match.
    """
    unwrapped = unsafe_perform_io(io_result)
    match unwrapped:
        case Success(_):
            return 0
        case Failure(LivespecError() as err):
            return err.exit_code
        case _:
            assert_never(unwrapped)


def main(*, argv: list[str] | None = None) -> int:
    """Prune-history supervisor entry point. Returns the process exit code.

    Cycle 130 wires the parse_argv stage onto the railway: a
    UsageError (unknown flag) lifts to exit 2 via err.exit_code;
    success returns IOSuccess(namespace) which the pattern-match
    maps to 0. Phase 7 will widen this to invoke the actual
    prune mechanic.
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    railway: IOResult[Any, LivespecError] = cli.parse_argv(
        parser=parser, argv=resolved_argv,
    )
    return _pattern_match_io_result(io_result=railway)
