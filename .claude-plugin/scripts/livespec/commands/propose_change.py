"""propose-change sub-command (Phase 3 minimum-viable per v019 Q1).

Stages an LLM-authored change proposal at
`<spec-target>/proposed_changes/<topic>.md`. The wrapper:

1. Reads + parses + schema-validates the findings JSON payload
   against `proposal_findings.schema.json` (exit 4 on validation
   failure — retryable).
2. Validates the inbound `<topic>` is already canonical
   (lowercase kebab-case, length ≤ 64). Phase 3 minimum-viable
   REJECTS non-canonical topics with exit 4 ("topic not
   canonical"); Phase 7 widens this to silent canonicalization
   per PROPOSAL §"Topic canonicalization (v015 O3)".
3. Resolves `--spec-target` (defaults to the main spec root,
   derived from `.livespec.jsonc`'s template field via the same
   built-in mapping as seed: livespec → `<project_root>/
   SPECIFICATION/`; minimal → `<project_root>`).
4. Checks for collision at `<spec-target>/proposed_changes/
   <topic>.md`; exits 3 PreconditionError if the file already
   exists (Phase 7 widens to v014 N6 monotonic-suffix
   disambiguation).
5. Resolves the author per the simplest two-source rule (CLI
   `--author` → `LIVESPEC_AUTHOR_LLM` env → `unknown-llm`
   fallback). Phase 7 widens to the full unified precedence
   including the payload's optional `author` field.
6. Writes the proposed-change file: YAML front-matter (topic,
   author, created_at) + one `## Proposal: <name>` section per
   payload finding, mapping fields one-to-one per PROPOSAL
   §"propose-change" lines 2236-2242.

Out of Phase-3 scope (per plan line 1175-1184): topic
canonicalization, reserve-suffix canonicalization, full unified
author precedence (payload-author lookup), collision
disambiguation prompts, single-canonicalization invariant
routing — all Phase 7.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn

from returns.io import IOFailure, IOResult, IOSuccess
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.errors import (
    HelpRequested,
    LivespecError,
    PreconditionError,
    ValidationError,
)
from livespec.io.cli import parse_args
from livespec.io.fastjsonschema_facade import compile_schema
from livespec.io.fs import (
    find_upward,
    mkdir_p,
    path_exists,
    read_text,
    write_text,
)
from livespec.io.structlog_facade import get_logger
from livespec.parse.jsonc import parse as parse_jsonc
from livespec.schemas.dataclasses.proposal_findings import (
    ProposalFinding,
    ProposalFindings,
)
from livespec.validate import livespec_config as validate_livespec_config
from livespec.validate import proposal_findings as validate_proposal_findings

__all__: list[str] = [
    "build_parser",
    "main",
    "run",
]


_LIVESPEC_JSONC = ".livespec.jsonc"
_AUTHOR_ENV = "LIVESPEC_AUTHOR_LLM"
_AUTHOR_FALLBACK = "unknown-llm"
_CANONICAL_TOPIC_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
_TOPIC_MAX_LEN = 64


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="livespec propose-change",
        description="Stage an LLM-authored change proposal at <spec-target>/proposed_changes/.",
        exit_on_error=False,
    )
    parser.add_argument(
        "topic",
        type=str,
        help="Canonical kebab-case topic (lowercase, length <= 64).",
    )
    parser.add_argument(
        "--findings-json",
        dest="findings_json",
        type=Path,
        required=True,
        help="Path to the findings-JSON payload produced by prompts/propose-change.md.",
    )
    parser.add_argument(
        "--author",
        type=str,
        default=None,
        help="Author identifier (highest-precedence; overrides env and payload).",
    )
    parser.add_argument(
        "--spec-target",
        dest="spec_target",
        type=Path,
        default=None,
        help="Target spec tree (default: main spec root via .livespec.jsonc).",
    )
    parser.add_argument(
        "--project-root",
        dest="project_root",
        type=Path,
        default=None,
        help="Project root for .livespec.jsonc lookup (default: cwd).",
    )
    return parser


def _schema_path(*, name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "schemas" / f"{name}.schema.json"


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_author(*, cli_author: str | None) -> str:
    """Phase 3 minimum-viable two-source precedence: CLI -> env -> fallback."""
    if cli_author:
        return cli_author
    env_value = os.environ.get(_AUTHOR_ENV)
    if env_value:
        return env_value
    return _AUTHOR_FALLBACK


def run(*, argv: Sequence[str]) -> IOResult[Path, LivespecError]:
    parser = build_parser()
    return parse_args(parser=parser, argv=argv).bind(_orchestrate)


def _orchestrate(namespace: argparse.Namespace) -> IOResult[Path, LivespecError]:
    project_root: Path = (
        namespace.project_root
        if namespace.project_root is not None
        else Path.cwd()
    )
    topic: str = namespace.topic
    if not _is_canonical_topic(topic):
        return IOFailure(
            ValidationError(
                f"topic not canonical (Phase 3 minimum-viable): {topic!r}; "
                f"expected lowercase kebab-case, length <= {_TOPIC_MAX_LEN}",
            ),
        )
    author = _resolve_author(cli_author=namespace.author)
    return (
        read_text(path=namespace.findings_json)
        .bind(_parse_and_validate_findings)
        .bind(lambda findings: _resolve_target_then_write(
            namespace=namespace,
            project_root=project_root,
            topic=topic,
            author=author,
            findings=findings,
        ))
    )


def _is_canonical_topic(topic: str) -> bool:
    if len(topic) == 0 or len(topic) > _TOPIC_MAX_LEN:
        return False
    return bool(_CANONICAL_TOPIC_RE.match(topic))


def _parse_and_validate_findings(
    text: str,
) -> IOResult[ProposalFindings, LivespecError]:
    parsed = parse_jsonc(text=text)
    match parsed:
        case Failure(err):
            return IOFailure(err)
        case Success(payload):
            return _validate_findings_payload(payload=payload)
        case _:
            assert_never(parsed)


def _validate_findings_payload(
    *,
    payload: dict[str, Any],
) -> IOResult[ProposalFindings, LivespecError]:
    return read_text(path=_schema_path(name="proposal_findings")).bind(
        lambda schema_text: _compile_findings_validator(
            schema_text=schema_text,
            payload=payload,
        ),
    )


def _compile_findings_validator(
    *,
    schema_text: str,
    payload: dict[str, Any],
) -> IOResult[ProposalFindings, LivespecError]:
    schema_parsed = parse_jsonc(text=schema_text)
    match schema_parsed:
        case Failure(err):
            return IOFailure(err)
        case Success(schema_dict):
            fast_validator = compile_schema(
                schema_id="proposal_findings.schema.json",
                schema=schema_dict,
            )
            validator = validate_proposal_findings.make_validator(
                fast_validator=fast_validator,
            )
            validated = validator(payload)
            match validated:
                case Failure(err):
                    return IOFailure(err)
                case Success(findings):
                    return IOSuccess(findings)
                case _:
                    assert_never(validated)
        case _:
            assert_never(schema_parsed)


def _resolve_target_then_write(
    *,
    namespace: argparse.Namespace,
    project_root: Path,
    topic: str,
    author: str,
    findings: ProposalFindings,
) -> IOResult[Path, LivespecError]:
    if namespace.spec_target is not None:
        spec_target_abs = (project_root / namespace.spec_target).resolve()
        return _check_collision_then_write(
            spec_target=spec_target_abs,
            topic=topic,
            author=author,
            findings=findings,
        )
    return _resolve_default_spec_target(project_root=project_root).bind(
        lambda spec_target: _check_collision_then_write(
            spec_target=spec_target,
            topic=topic,
            author=author,
            findings=findings,
        ),
    )


def _resolve_default_spec_target(
    *,
    project_root: Path,
) -> IOResult[Path, LivespecError]:
    """Walk upward for .livespec.jsonc, derive main spec root from template field."""
    return (
        find_upward(start=project_root, name=_LIVESPEC_JSONC)
        .bind(lambda jsonc_path: read_text(path=jsonc_path))
        .bind(_parse_and_validate_jsonc)
        .map(lambda config: _spec_root_for_template(
            template=config.template,
            project_root=project_root,
        ))
    )


def _parse_and_validate_jsonc(text: str) -> IOResult[Any, LivespecError]:
    parsed = parse_jsonc(text=text)
    match parsed:
        case Failure(err):
            return IOFailure(err)
        case Success(jsonc_dict):
            return read_text(path=_schema_path(name="livespec_config")).bind(
                lambda schema_text: _validate_jsonc_against_schema(
                    schema_text=schema_text,
                    jsonc_dict=jsonc_dict,
                ),
            )
        case _:
            assert_never(parsed)


def _validate_jsonc_against_schema(
    *,
    schema_text: str,
    jsonc_dict: dict[str, Any],
) -> IOResult[Any, LivespecError]:
    schema_parsed = parse_jsonc(text=schema_text)
    match schema_parsed:
        case Failure(err):
            return IOFailure(err)
        case Success(schema_dict):
            fast_validator = compile_schema(
                schema_id="livespec_config.schema.json",
                schema=schema_dict,
            )
            validator = validate_livespec_config.make_validator(
                fast_validator=fast_validator,
            )
            validated = validator(jsonc_dict)
            match validated:
                case Failure(err):
                    return IOFailure(err)
                case Success(config):
                    return IOSuccess(config)
                case _:
                    assert_never(validated)
        case _:
            assert_never(schema_parsed)


def _spec_root_for_template(*, template: str, project_root: Path) -> Path:
    """Phase 3 minimum-viable: hardcoded for v1 built-ins (matches seed.py)."""
    if template == "minimal":
        return project_root
    return project_root / "SPECIFICATION"


def _check_collision_then_write(
    *,
    spec_target: Path,
    topic: str,
    author: str,
    findings: ProposalFindings,
) -> IOResult[Path, LivespecError]:
    target_path = spec_target / "proposed_changes" / f"{topic}.md"
    return path_exists(path=target_path).bind(
        lambda exists: _write_proposed_change(
            target_path=target_path,
            exists=exists,
            topic=topic,
            author=author,
            findings=findings,
        ),
    )


def _write_proposed_change(
    *,
    target_path: Path,
    exists: bool,
    topic: str,
    author: str,
    findings: ProposalFindings,
) -> IOResult[Path, LivespecError]:
    if exists:
        return IOFailure(
            PreconditionError(
                f"proposed-change collision at {target_path}; Phase 3 minimum-viable "
                f"refuses to overwrite (Phase 7 widens to v014 N6 monotonic-suffix disambiguation)",
            ),
        )
    content = _render_proposed_change(
        topic=topic,
        author=author,
        findings=findings,
        created_at=_now_iso(),
    )
    return mkdir_p(path=target_path.parent).bind(
        lambda _: write_text(path=target_path, content=content),
    ).map(lambda _: target_path)


def _render_proposed_change(
    *,
    topic: str,
    author: str,
    findings: ProposalFindings,
    created_at: str,
) -> str:
    proposals_block = "\n\n".join(_render_proposal(f) for f in findings.findings)
    return (
        f"---\n"
        f"topic: {topic}\n"
        f"author: {author}\n"
        f"created_at: {created_at}\n"
        f"---\n"
        f"\n"
        f"{proposals_block}\n"
    )


def _render_proposal(finding: ProposalFinding) -> str:
    targets_block = "\n".join(f"- {p}" for p in finding.target_spec_files)
    return (
        f"## Proposal: {finding.name}\n"
        f"\n"
        f"### Target specification files\n"
        f"\n"
        f"{targets_block}\n"
        f"\n"
        f"### Summary\n"
        f"\n"
        f"{finding.summary}\n"
        f"\n"
        f"### Motivation\n"
        f"\n"
        f"{finding.motivation}\n"
        f"\n"
        f"### Proposed Changes\n"
        f"\n"
        f"{finding.proposed_changes}\n"
    )


def main(*, argv: Sequence[str] | None = None) -> int:
    log = get_logger(__name__)
    actual_argv: Sequence[str] = list(argv) if argv is not None else sys.argv[1:]
    try:
        return _dispatch(actual_argv=actual_argv)
    except Exception as exc:
        log.exception(
            "propose_change internal error",
            exception_type=type(exc).__name__,
            exception_repr=repr(exc),
        )
        return 1


def _dispatch(*, actual_argv: Sequence[str]) -> int:
    log = get_logger(__name__)
    result = run(argv=actual_argv)
    inner = unsafe_perform_io(result)
    match inner:
        case Success(_):
            return 0
        case Failure(HelpRequested(text=text)):
            sys.stdout.write(text)
            return 0
        case Failure(err):
            log.error(
                "propose_change failed",
                error_type=type(err).__name__,
                error_message=str(err),
            )
            return type(err).exit_code
        case _ as unreachable:
            _unreachable(unreachable)


def _unreachable(value: object) -> NoReturn:
    assert_never(value)  # type: ignore[arg-type]
