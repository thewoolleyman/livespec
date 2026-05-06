"""Critique sub-command supervisor.

Per PROPOSAL.md §"`critique`" and SPECIFICATION/spec.md
§"`critique` internal delegation" + §"Author identifier resolution":
critique validates the inbound `--findings-json` payload then
resolves the author identifier via the unified four-step precedence
(`--author <id>` > `LIVESPEC_AUTHOR_LLM` env > payload `author` field
> `"unknown-llm"`) and delegates to `propose-change` with the
un-slugged resolved-author stem as topic-hint AND the literal string
`"-critique"` as the reserve-suffix parameter. propose-change's v016
P3 / v017 Q1 reserve-suffix canonicalization composes the two so the
`-critique` suffix is preserved intact at the 64-char filename cap.

`build_parser()` is the pure argparse factory per style doc
§"CLI argument parsing seam"; `main()` is the supervisor that
threads argv through the railway and pattern-matches the final
IOResult to derive both the exit code and the post-validation
work (delegating to propose_change with the composed argv).
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
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
from livespec.schemas.dataclasses.proposal_findings import ProposalFindings
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


def _resolve_author(
    *,
    namespace: argparse.Namespace,
    payload: ProposalFindings,
    env_lookup: Callable[[str], str | None],
) -> str:
    """Resolve the author identifier per spec.md §"Author identifier resolution".

    Four-step precedence: `--author <id>` (CLI) > `LIVESPEC_AUTHOR_LLM`
    (env) > `payload.author` (LLM self-declaration) > literal
    `"unknown-llm"` fallback. The first non-empty value in this order
    wins. The fallback path is also where livespec narrates the
    "running with unknown LLM identifier" warning in skill prose; the
    Python wrapper just returns the literal. Body is identical to
    `propose_change._resolve_author` (DRY-violation accepted between
    two private module-internal helpers; cross-module calls into
    private helpers would violate the module-private boundary).
    """
    if namespace.author:
        return str(namespace.author)
    env_value = env_lookup("LIVESPEC_AUTHOR_LLM")
    if env_value:
        return env_value
    if payload.author:
        return payload.author
    return "unknown-llm"


def _build_delegated_argv(
    *,
    namespace: argparse.Namespace,
    resolved_author: str,
) -> list[str]:
    """Compose the argv list passed to `propose_change.main`.

    Per spec.md §"`critique` internal delegation": the un-slugged
    resolved-author stem is the trailing positional topic-hint;
    `--reserve-suffix=-critique` is the separate parameter so
    propose_change's v016 P3 / v017 Q1 algorithm preserves the
    suffix at the 64-char cap; `--author=<resolved>` ensures
    propose_change's own front-matter author resolution
    short-circuits at step 1 and matches critique's resolved
    value exactly. `--spec-target` and `--project-root` are
    forwarded when present so the delegation routes against the
    same target.
    """
    argv: list[str] = [
        "--findings-json",
        str(namespace.findings_json),
        "--reserve-suffix=-critique",
        "--author",
        resolved_author,
    ]
    if namespace.spec_target is not None:
        argv.extend(["--spec-target", str(namespace.spec_target)])
    if namespace.project_root is not None:
        argv.extend(["--project-root", str(namespace.project_root)])
    argv.append(resolved_author)
    return argv


def _validate_with_namespace(
    *,
    namespace: argparse.Namespace,
) -> IOResult[tuple[argparse.Namespace, ProposalFindings], LivespecError]:
    """Thread the parsed namespace through the validation railway.

    Composes fs.read_text -> jsonc.loads -> _validate_payload and
    pairs the validated `ProposalFindings` with the namespace so
    the supervisor's Success arm has both available without
    re-parsing argv.
    """
    return (
        fs.read_text(path=Path(namespace.findings_json))
        .bind(lambda text: IOResult.from_result(jsonc.loads(text=text)))
        .bind(lambda payload: _validate_payload(payload=payload))
        .map(lambda findings: (namespace, findings))
    )


def main(*, argv: list[str] | None = None) -> int:
    """Critique supervisor entry point. Returns the process exit code.

    Threads argv through parse_argv -> fs.read_text ->
    jsonc.loads -> validate, pairs the validated payload with
    the namespace, then pattern-matches: Failure(LivespecError)
    lifts to err.exit_code; Success extracts (namespace,
    findings), resolves the author per the four-step precedence,
    composes the delegated argv with `--reserve-suffix=-critique`
    + un-slugged author stem as topic-hint, and re-enters
    `propose_change.main(argv=...)` whose exit code becomes
    critique's exit code. critique does NOT run revise.
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
    railway: IOResult[tuple[argparse.Namespace, ProposalFindings], LivespecError] = (
        parse_result.bind(lambda namespace: _validate_with_namespace(namespace=namespace))
    )
    unwrapped = unsafe_perform_io(railway)
    match unwrapped:
        case Success(value):
            namespace, findings = value
            resolved_author = _resolve_author(
                namespace=namespace,
                payload=findings,
                env_lookup=os.environ.get,
            )
            delegated_argv = _build_delegated_argv(
                namespace=namespace,
                resolved_author=resolved_author,
            )
            return propose_change.main(argv=delegated_argv)
        case Failure(LivespecError() as err):
            return err.exit_code
        case _:
            assert_never(unwrapped)


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
