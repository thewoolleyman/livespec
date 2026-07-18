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
"""Propose-change sub-command supervisor.

Per and Plan
: the wrapper validates the inbound
`--findings-json <path>` payload, composes a proposed-change
file from the findings, and writes it to
`<spec-target>/proposed_changes/<canonical-topic>.md`.
sub-step 3.c widens the wrapper to full feature parity per
SPECIFICATION/spec.md "Topic canonicalization",
"Reserve-suffix canonicalization", and the
remaining/N6 + rules (collision disambiguation
and unified author precedence land in subsequent cycles).

`build_parser()` is the pure argparse factory per the style doc;
`main()` is the supervisor that threads argv through the railway
and pattern-matches the final IOResult to derive the exit code.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.commands._propose_change_write import (
    _resolve_spec_target as _resolve_spec_target_impl,
)
from livespec.commands._propose_change_write import (
    _write_proposed_change,
)
from livespec.errors import LivespecError
from livespec.io import cli, fs
from livespec.parse import jsonc
from livespec.validate import proposal_findings as validate_proposal_findings_module

__all__: list[str] = ["_resolve_spec_target", "build_parser", "main"]


_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
_PROPOSAL_FINDINGS_SCHEMA_PATH = _SCHEMAS_DIR / "proposal_findings.schema.json"


def build_parser() -> argparse.ArgumentParser:
    """Construct the propose-change argparse parser without parsing.

    Per the style doc CLI argument parsing seam:
    `exit_on_error=False` lets argparse signal errors via
    `argparse.ArgumentError` rather than `SystemExit`. The
    parser exposes `--findings-json <path>` (required), a
    positional `<topic>`, optional `--author <id>`, and
    `--spec-target <path>`.
    """
    parser = argparse.ArgumentParser(prog="propose-change", exit_on_error=False)
    _ = parser.add_argument("--findings-json", required=True)
    _ = parser.add_argument("topic")
    _ = parser.add_argument("--author", default=None)
    _ = parser.add_argument("--reserve-suffix", default=None)
    _ = parser.add_argument("--spec-target", default=None)
    _ = parser.add_argument("--project-root", default=None)
    return parser


def _pattern_match_io_result(
    *,
    io_result: IOResult[Any, LivespecError],
) -> int:
    """Pattern-match the final railway IOResult onto an exit code.

    Success(<value>) -> exit 0 per the style doc exit code
    contract. Failure(LivespecError) lifts via err.exit_code;
    assert_never closes the match.
    """
    unwrapped = unsafe_perform_io(io_result)  # pyright: ignore[reportArgumentType]
    match unwrapped:
        case Success(_):
            return 0
        case Failure(LivespecError() as err):
            return cli.emit_livespec_failure(command="propose-change", err=err)
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
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
    railway: IOResult[Any, LivespecError] = parse_result.bind(
        lambda namespace: (  # pyright: ignore[reportArgumentType]
            fs.read_text(path=Path(namespace.findings_json))
            .bind(
                lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
            )
            .bind(lambda payload: _validate_payload(payload=payload))
            .bind(
                lambda findings: _write_proposed_change(
                    findings=findings,
                    namespace=namespace,
                ),
            )
        ),
    )
    return _pattern_match_io_result(io_result=railway)


def _resolve_spec_target(*, namespace: argparse.Namespace) -> Path:
    """Compatibility wrapper for tests around the extracted helper."""
    return _resolve_spec_target_impl(namespace=namespace)


def _validate_payload(*, payload: dict[str, Any]) -> IOResult[Any, LivespecError]:
    """Read proposal_findings.schema.json and validate the payload.

    Composes fs.read_text(schema) -> jsonc.loads(schema-text) ->
    validate_proposal_findings(payload, schema-dict). Failures
    bubble via the IOResult track: schema-file missing ->
    PreconditionError; schema malformed -> ValidationError;
    payload schema-violation -> ValidationError.
    """
    return (
        fs.read_text(path=_PROPOSAL_FINDINGS_SCHEMA_PATH)
        .bind(
            lambda schema_text: IOResult.from_result(jsonc.loads(text=schema_text)),  # pyright: ignore[reportArgumentType]
        )
        .bind(
            lambda schema_dict: IOResult.from_result(  # pyright: ignore[reportArgumentType]
                validate_proposal_findings_module.validate_proposal_findings(
                    payload=payload,
                    schema=schema_dict,
                ),
            ),
        )
    )
