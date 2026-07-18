# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Next sub-command supervisor.

Per `SPECIFICATION/contracts.md`: a pure-function-of-file-state
ranker over the spec-side queue state. Reads
`<spec-target>/proposed_changes/` (one entry per pending
proposal, with `created_at` from each proposal's
restricted-YAML front-matter) and `<spec-target>/history/`
(count of `vNNN/` version directories), enumerates ALL ripe
candidates, and emits a `next_output.schema.json`-conforming
JSON payload on stdout with top-level `candidates` (array of
`{action, reason, urgency, target?}`) and `pagination`
(`{offset, limit, total, has_more}`). No LLM in the ranking
path; no impl-side store reads (cross-side composition is the
project-local orchestration layer's job per `spec.md`).

In addition to the wrapper CLI surface flags, the wrapper
accepts `--limit <count>` (positive integer, default 5) and
`--offset <count>` (non-negative integer, default 0); a
non-positive limit or negative offset exits 2 (UsageError). Per
`SPECIFICATION/contracts.md`, the wrapper reads
`next.prune_history_threshold` from the project root's
`.livespec.jsonc` on each invocation (positive integer; default
20 when absent; exit 3 with a PreconditionError naming the
offending key and value otherwise). The candidate enumeration,
urgency bucketing, sorting, and pagination live in the sibling
`_next_ranking` module; an empty `candidates` array is the
no-work signal.

`build_parser()` is the pure argparse factory per the style doc;
`main()` is the supervisor that
threads argv through the railway and pattern-matches the final
IOResult to derive the exit code + emit the JSON payload on
stdout (per `commands/CLAUDE.md` exception list: supervisor
`main()` functions are the only place outside `bin/` and
`livespec/doctor/run_static.py` where `sys.stdout.write` is
permitted).
"""

from __future__ import annotations

import argparse
import sys

from returns.io import IOResult, IOSuccess
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.commands._next_payload import _ranked_payload, _validate_window_flags
from livespec.errors import LivespecError
from livespec.io import cli, streams

__all__: list[str] = ["build_parser", "main"]


_DEFAULT_LIMIT = 5
_DEFAULT_OFFSET = 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the next argparse parser without parsing.

    Per `SPECIFICATION/contracts.md`: `--project-root <path>`
    (default `Path.cwd()`), `--spec-target <path>` (defaults to
    `<project-root>/SPECIFICATION/` when omitted),
    `--limit <count>` (default 5), and `--offset <count>`
    (default 0). `exit_on_error=False` lets argparse signal
    errors via `argparse.ArgumentError` rather than `SystemExit`,
    per the style doc.
    """
    parser = argparse.ArgumentParser(prog="next", exit_on_error=False)
    _ = parser.add_argument("--project-root", default=None)
    _ = parser.add_argument("--spec-target", default=None)
    _ = parser.add_argument("--limit", type=int, default=_DEFAULT_LIMIT)
    _ = parser.add_argument("--offset", type=int, default=_DEFAULT_OFFSET)
    return parser


def _emit_payload(*, payload: str) -> IOResult[str, LivespecError]:
    """Write the JSON payload + newline to stdout per the wire contract."""
    _ = streams.write_stdout(text=f"{payload}\n")
    return IOSuccess(payload)


def main(*, argv: list[str] | None = None) -> int:
    """Next supervisor entry point. Returns the exit code.

    Threads argv through parse_argv → window-flag gate → resolve
    `.livespec.jsonc` threshold → resolve spec-target →
    file-state reads → candidate enumeration → pagination →
    schema-validate → JSON-serialize → stdout emit.
    Failure(LivespecError) lifts via err.exit_code; Success
    exits 0 after the JSON payload + trailing newline is
    written.
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
    railway: IOResult[str, LivespecError] = parse_result.bind(
        lambda namespace: _validate_window_flags(namespace=namespace).bind(  # pyright: ignore[reportArgumentType]
            lambda window: _ranked_payload(namespace=namespace, window=window),
        ),
    ).bind(
        lambda payload: _emit_payload(payload=payload),  # pyright: ignore[reportArgumentType]
    )
    unwrapped = unsafe_perform_io(railway)  # pyright: ignore[reportArgumentType]
    match unwrapped:
        case Success(_):
            return 0
        case Failure(LivespecError() as err):
            return cli.emit_livespec_failure(command="next", err=err)
        case _:
            assert_never(unwrapped)
