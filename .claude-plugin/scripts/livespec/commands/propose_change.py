"""Propose-change sub-command supervisor.

Per PROPOSAL.md §"`propose-change`" (line ~2134) and Plan Phase 3
(lines 1505-1523): the wrapper validates the inbound
`--findings-json <path>` payload, composes a proposed-change
file from the findings, and writes it to
`<spec-target>/proposed_changes/<canonical-topic>.md`. Phase 7
sub-step 3.c widens the wrapper to full feature parity per
SPECIFICATION/spec.md "Topic canonicalization (v015 O3)",
"Reserve-suffix canonicalization (v016 P3 / v017 Q1)", and the
remaining v014 N5/N6 + v016 P4 rules (collision disambiguation
and unified author precedence land in subsequent cycles).

`build_parser()` is the pure argparse factory per style doc
§"CLI argument parsing seam"; `main()` is the supervisor that
threads argv through the railway and pattern-matches the final
IOResult to derive the exit code.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.errors import LivespecError, UsageError
from livespec.io import cli, fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.proposal_findings import ProposalFindings
from livespec.validate import proposal_findings as validate_proposal_findings_module

__all__: list[str] = ["build_parser", "main"]


_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
_PROPOSAL_FINDINGS_SCHEMA_PATH = _SCHEMAS_DIR / "proposal_findings.schema.json"


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
    _ = parser.add_argument("--reserve-suffix", default=None)
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
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
    railway: IOResult[Any, LivespecError] = parse_result.bind(
        lambda namespace: (
            fs.read_text(path=Path(namespace.findings_json))
            .bind(lambda text: IOResult.from_result(jsonc.loads(text=text)))
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


def _canonical_alnum_run_strip(*, text: str) -> str:
    """Apply v015 O3 steps 1-3: lowercase -> non-[a-z0-9]-runs-to-hyphen -> strip edges.

    Shared by both the v015 O3 base canonicalization and the v016 P3
    reserve-suffix algorithm (per deferred-items.md "Reserve-suffix
    topic canonicalization", which composes against this primitive).
    """
    lowered = text.lower()
    hyphenated = re.sub(r"[^a-z0-9]+", "-", lowered)
    return hyphenated.strip("-")


def _canonicalize_topic(*, hint: str, reserve_suffix: str | None = None) -> str | None:
    """Canonicalize a topic hint, optionally preserving a reserve suffix.

    With reserve_suffix=None (default), applies v015 O3 verbatim:
    lowercase -> non-[a-z0-9]-runs-to-hyphen -> strip edges -> truncate
    to 64. With a non-None reserve_suffix, applies v016 P3 (deferred-
    items.md "Reserve-suffix topic canonicalization"): canonicalize
    hint and suffix; strip pre-attached suffix from hint tail; truncate
    the non-suffix portion to 64 - len(<canonical-suffix>); rstrip
    trailing hyphens; re-append the canonical suffix. Returns None
    when the resulting filename would be unrooted (empty, or
    suffix-only).
    """
    canonical_hint = _canonical_alnum_run_strip(text=hint)
    if reserve_suffix is None:
        return canonical_hint[:64] or None
    canonical_suffix = f"-{_canonical_alnum_run_strip(text=reserve_suffix)}"
    if canonical_hint.endswith(canonical_suffix):
        canonical_hint = canonical_hint[: -len(canonical_suffix)]
    budget = 64 - len(canonical_suffix)
    truncated_hint = canonical_hint[:budget].rstrip("-")
    if not truncated_hint:
        return None
    return f"{truncated_hint}{canonical_suffix}"


def _resolve_spec_target(*, namespace: argparse.Namespace) -> Path:
    """Resolve --spec-target to a Path, defaulting to <project-root>/SPECIFICATION.

    Per Plan Phase 3 (lines 1505-1523): the `<spec-target>` is
    selected via the --spec-target flag, defaulting to the
    project's main spec root. With the built-in `livespec`
    template, that's <project-root>/SPECIFICATION/.
    """
    if namespace.spec_target is not None:
        return Path(namespace.spec_target)
    project_root = Path.cwd() if namespace.project_root is None else Path(namespace.project_root)
    return project_root / "SPECIFICATION"


def _compose_proposed_change_body(*, findings: ProposalFindings) -> str:
    """Compose the proposed-change file body from validated findings.

    Per PROPOSAL.md lines 2232-2242 (field-copy mapping): each
    finding becomes one `## Proposal: <name>` section with
    `### Target specification files`, `### Summary`,
    `### Motivation`, `### Proposed Changes` subsections
    populated verbatim from the finding's fields.
    """
    sections: list[str] = []
    for finding in findings.findings:
        name = str(finding.get("name", ""))
        target_files = finding.get("target_spec_files", [])
        target_files_text = "\n".join(
            f"- {entry}" for entry in target_files if isinstance(entry, str)
        )
        summary = str(finding.get("summary", ""))
        motivation = str(finding.get("motivation", ""))
        proposed_changes = str(finding.get("proposed_changes", ""))
        sections.append(
            f"## Proposal: {name}\n\n"
            f"### Target specification files\n\n{target_files_text}\n\n"
            f"### Summary\n\n{summary}\n\n"
            f"### Motivation\n\n{motivation}\n\n"
            f"### Proposed Changes\n\n{proposed_changes}\n",
        )
    return "\n".join(sections)


def _write_proposed_change(
    *,
    findings: ProposalFindings,
    namespace: argparse.Namespace,
) -> IOResult[ProposalFindings, LivespecError]:
    """Write the composed proposed-change file to disk.

    Per spec.md "Topic canonicalization (v015 O3)": the inbound `<topic>`
    is canonicalized before filename selection; an empty result lifts to
    UsageError on the railway. Writes to
    `<spec-target>/proposed_changes/<canonical-topic>.md`.
    """
    canonical = _canonicalize_topic(
        hint=str(namespace.topic),
        reserve_suffix=namespace.reserve_suffix,
    )
    if canonical is None:
        return IOResult.from_failure(
            UsageError(f"topic '{namespace.topic}' canonicalizes to empty"),
        )
    spec_target = _resolve_spec_target(namespace=namespace)
    target = spec_target / "proposed_changes" / f"{canonical}.md"
    body = _compose_proposed_change_body(findings=findings)
    return fs.write_text(path=target, text=body).map(lambda _: findings)
