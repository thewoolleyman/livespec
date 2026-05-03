"""Critique sub-command supervisor.

Per PROPOSAL.md §"`critique`" (line ~2280) and Plan Phase 3
(lines 1524-1532): critique is minimum-viable per v019 Q1 —
invokes propose_change internally with the `-critique`
reserve-suffix appended (the simplest delegation shape; full
reserve-suffix algorithm lives at Phase 7). Accepts
`--findings-json <path>` plus the same flags propose_change
takes; routes the delegation with the same target.

`build_parser()` is the pure argparse factory per style doc
§"CLI argument parsing seam"; `main()` is the supervisor that
threads argv through the railway and pattern-matches the final
IOResult to derive the exit code. Cycle 118 wires
build_parser + parse_argv + UsageError exit-code mapping;
subsequent cycles widen the railway to load the findings
payload and delegate to propose_change.
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

from livespec.commands import propose_change
from livespec.errors import LivespecError
from livespec.io import cli, fs
from livespec.parse import jsonc
from livespec.validate import proposal_findings as validate_proposal_findings_module

__all__: list[str] = ["build_parser", "main"]


_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
_PROPOSAL_FINDINGS_SCHEMA_PATH = _SCHEMAS_DIR / "proposal_findings.schema.json"


def build_parser() -> argparse.ArgumentParser:
    """Construct the critique argparse parser without parsing.

    Per style doc §"CLI argument parsing seam":
    `exit_on_error=False` lets argparse signal errors via
    `argparse.ArgumentError` rather than `SystemExit`. The
    parser exposes `--findings-json <path>` (required), and the
    same optional `--author`, `--spec-target`, `--project-root`
    flags propose_change takes per PROPOSAL.md §"critique".
    """
    parser = argparse.ArgumentParser(prog="critique", exit_on_error=False)
    _ = parser.add_argument("--findings-json", required=True)
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


def _resolve_author(*, namespace: argparse.Namespace) -> str:
    """Resolve --author to a string, defaulting to "unknown-llm".

    Per PROPOSAL.md §"`critique`" lines 2294-2306, author
    precedence is CLI --author -> env LIVESPEC_AUTHOR_LLM ->
    payload-level `author` field -> "unknown-llm". Phase-3
    minimum-viable supports only the CLI -> fallback steps; env
    var + payload-level author land under consumer pressure in
    later phases.
    """
    if namespace.author is not None and namespace.author != "":
        return str(namespace.author)
    return "unknown-llm"


def main(*, argv: list[str] | None = None) -> int:
    """Critique supervisor entry point. Returns the process exit code.

    Cycle 118 wires parse_argv; cycle 119 appends fs.read_text on
    the --findings-json path so a missing file lifts to exit 3
    via PreconditionError. Cycle 120 lifts the pure jsonc.loads
    onto the IOResult track so a malformed payload lifts to
    exit 4 via ValidationError. Cycle 121 appends schema
    validation against proposal_findings.schema.json (a
    schema-violating payload also lifts to exit 4). Cycle 122
    delegates to propose_change.main on validation success with
    topic = `<author>-critique` per PROPOSAL.md §"`critique`"
    lines 2307-2325 (Phase-3 minimum-viable scope: full
    reserve-suffix canonicalization is deferred to Phase 7).
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
    railway: IOResult[Any, LivespecError] = parse_result.bind(
        lambda namespace: (
            fs.read_text(path=Path(namespace.findings_json))
            .bind(lambda text: IOResult.from_result(jsonc.loads(text=text)))
            .bind(lambda payload: _validate_payload(payload=payload))
        ),
    )
    pre_delegation_exit = _pattern_match_io_result(io_result=railway)
    if pre_delegation_exit != 0:
        return pre_delegation_exit
    namespace = parser.parse_args(resolved_argv)
    topic = f"{_resolve_author(namespace=namespace)}-critique"
    delegated_argv: list[str] = ["--findings-json", str(namespace.findings_json), topic]
    if namespace.spec_target is not None:
        delegated_argv.extend(["--spec-target", str(namespace.spec_target)])
    if namespace.project_root is not None:
        delegated_argv.extend(["--project-root", str(namespace.project_root)])
    return propose_change.main(argv=delegated_argv)


def _validate_payload(*, payload: dict[str, Any]) -> IOResult[Any, LivespecError]:
    """Read proposal_findings.schema.json and validate the payload.

    Composes fs.read_text(schema) -> jsonc.loads(schema-text) ->
    validate_proposal_findings(payload, schema-dict). Mirrors
    propose_change's same stage; failures bubble via the IOResult
    track (schema-file missing -> PreconditionError; schema
    malformed -> ValidationError; payload schema-violation ->
    ValidationError).
    """
    return (
        fs.read_text(path=_PROPOSAL_FINDINGS_SCHEMA_PATH)
        .bind(lambda schema_text: IOResult.from_result(jsonc.loads(text=schema_text)))
        .bind(
            lambda schema_dict: IOResult.from_result(
                validate_proposal_findings_module.validate_proposal_findings(
                    payload=payload,
                    schema=schema_dict,
                ),
            ),
        )
    )
