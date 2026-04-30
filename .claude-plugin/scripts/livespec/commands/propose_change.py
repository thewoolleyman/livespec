"""Propose-change sub-command supervisor.

Per PROPOSAL.md §"`propose-change`" (line ~2134) and Plan Phase 3
(lines 1505-1523): the wrapper validates the inbound
`--findings-json <path>` payload, composes a proposed-change
file from the findings, and writes it to
`<spec-target>/proposed_changes/<topic>.md`. Phase-3 scope is
minimum-viable per v019 Q1 — topic canonicalization, reserve-
suffix handling, collision disambiguation, and unified author
precedence are deferred to Phase 7.

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
    """Construct the propose-change argparse parser without parsing.

    Per style doc §"CLI argument parsing seam":
    `exit_on_error=False` lets argparse signal errors via
    `argparse.ArgumentError` rather than `SystemExit`. The
    parser exposes `--findings-json <path>` (required), a
    positional `<topic>`, optional `--author <id>`, and
    `--spec-target <path>` per PROPOSAL.md §"propose-change".
    """
    parser = argparse.ArgumentParser(prog="propose-change", exit_on_error=False)
    _ = parser.add_argument("--findings-json", required=True)
    _ = parser.add_argument("topic")
    _ = parser.add_argument("--author", default=None)
    _ = parser.add_argument("--spec-target", default=None)
    _ = parser.add_argument("--project-root", default=None)
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
    """Propose-change supervisor entry point. Returns the process exit code.

    When `argv` is None (the wrapper's default invocation), reads
    sys.argv[1:]. Threads argv through the railway:
      parse_argv -> (subsequent stages)

    UsageError (parse) -> exit 2. Subsequent cycles widen the
    railway under outside-in pressure: read --findings-json ->
    jsonc.loads -> validate against proposal_findings.schema.json
    -> compose proposed-change file -> write to disk.
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    railway: IOResult[Any, LivespecError] = cli.parse_argv(
        parser=parser, argv=resolved_argv,
    )
    return _pattern_match_io_result(io_result=railway)
