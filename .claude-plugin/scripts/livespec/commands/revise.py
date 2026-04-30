"""Revise sub-command supervisor.

Per PROPOSAL.md §"`revise`" (line ~2335) and Plan Phase 3
(lines 1533-1553): revise is minimum-viable per v019 Q1 —
validates `--revise-json <path>` against revise_input.schema.json,
processes per-proposal `decisions[]` in payload order, writes
the paired `<stem>-revision.md` per decision, moves each
processed `<spec-target>/proposed_changes/<stem>.md` byte-
identically into `<spec-target>/history/vNNN/proposed_changes/
<stem>.md`, and on any `accept`/`modify` cuts a new
`<spec-target>/history/vNNN/` materialized from the active
template's versioned spec files. Accepts `--spec-target <path>`.

`build_parser()` is the pure argparse factory per style doc
§"CLI argument parsing seam"; `main()` is the supervisor that
threads argv through the railway and pattern-matches the final
IOResult to derive the exit code. Cycle 123 wires
build_parser + parse_argv + UsageError exit-code mapping;
subsequent cycles widen the railway.
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
    """Construct the revise argparse parser without parsing.

    Per style doc §"CLI argument parsing seam":
    `exit_on_error=False` lets argparse signal errors via
    `argparse.ArgumentError` rather than `SystemExit`. The
    parser exposes `--revise-json <path>` (required), and the
    optional `--author`, `--spec-target`, `--project-root` flags
    per PROPOSAL.md §"revise" lines 2375-2410.
    """
    parser = argparse.ArgumentParser(prog="revise", exit_on_error=False)
    _ = parser.add_argument("--revise-json", required=True)
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
    """Revise supervisor entry point. Returns the process exit code.

    Cycle 123 wires the parse_argv stage onto the railway: a
    UsageError (missing required flag, unknown flag) lifts to
    exit 2; success returns IOSuccess(namespace) which the
    pattern-match maps to 0 until subsequent cycles append the
    revise-json-load + schema-validate + decisions-processing
    stages.
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    railway: IOResult[Any, LivespecError] = cli.parse_argv(
        parser=parser, argv=resolved_argv,
    )
    return _pattern_match_io_result(io_result=railway)
