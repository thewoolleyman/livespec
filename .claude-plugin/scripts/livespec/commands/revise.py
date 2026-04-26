"""revise sub-command (Phase 3 minimum-viable per v019 Q1).

Processes accept/modify/reject decisions for the proposed-changes
under `<spec-target>/proposed_changes/`, cuts a new
`<spec-target>/history/vNNN/` snapshot when any decision is
accept or modify, moves processed proposed-change files into
the new vNNN/proposed_changes/, writes paired revision files,
and applies any `resulting_files` updates to the working spec.

Per PROPOSAL §"revise" lines 2365-2452 + §"Revision file format"
lines 3027-3050. CLI:

    bin/revise.py --revise-json <path> [--author <id>]
                  [--spec-target <path>] [--project-root <path>]

Pipeline:

1. Read + parse + schema-validate `--revise-json` against
   `revise_input.schema.json` (exit 4 on validation failure —
   retryable).
2. Resolve `--spec-target` (default: main spec root via the same
   `.livespec.jsonc` upward-walk + built-in template mapping
   propose_change uses).
3. Determine next vNNN by listing `<spec-target>/history/`
   directories; max existing vNNN + 1.
4. Resolve author_human via `io.git.get_git_user`
   (`GIT_USER_UNKNOWN` fallback if git is absent / config is
   incomplete).
5. Resolve author_llm: --author CLI → LIVESPEC_AUTHOR_LLM env →
   payload `author` field → "unknown-llm" fallback (PROPOSAL
   line 2390-2393 unified precedence).
6. If any decision is accept or modify: mkdir
   `<spec-target>/history/vNNN/proposed_changes/`. Apply
   `resulting_files` updates (write new content to working spec
   files in place).
7. For each decision:
   - Move (read + write + remove) the proposed-change file
     from `<spec-target>/proposed_changes/<topic>.md` to
     `<spec-target>/history/vNNN/proposed_changes/<topic>.md`.
   - Write the paired
     `<spec-target>/history/vNNN/proposed_changes/
     <topic>-revision.md` with front-matter (proposal, decision,
     revised_at, author_human, author_llm) + body sections per
     PROPOSAL §"Revision file format".
8. If any decision was accept or modify: copy current working
   spec files (post-update) into `<spec-target>/history/vNNN/`.

Out-of-Phase-3 scope (per plan line 1194-1203):
- Per-proposal LLM decision flow with delegation toggle (Phase
  7's full LLM-driven cycle).
- Richer rejection-flow audit trail beyond the simplest
  "decision: reject" front-matter line.
- Per-version README for templates whose versioned surface
  defines one (Phase 7 widens via template_config).
- v014 N6 collision-suffix handling (Phase 3 minimum-viable
  assumes simple `<topic>.md` filenames).
- Cross-filesystem move fallback (Path.rename only).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn, cast

from returns.io import IOFailure, IOResult, IOSuccess
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.errors import (
    HelpRequested,
    LivespecError,
)
from livespec.io.cli import parse_args
from livespec.io.fastjsonschema_facade import compile_schema
from livespec.io.fs import (
    find_upward,
    list_dir,
    mkdir_p,
    path_exists,
    read_text,
    remove_file,
    write_text,
)
from livespec.io.git import GIT_USER_UNKNOWN, get_git_user
from livespec.io.structlog_facade import get_logger
from livespec.parse.jsonc import parse as parse_jsonc
from livespec.schemas.dataclasses.revise_input import (
    Decision,
    ProposalDecision,
    ReviseInput,
)
from livespec.validate import livespec_config as validate_livespec_config
from livespec.validate import revise_input as validate_revise_input

__all__: list[str] = [
    "build_parser",
    "main",
    "run",
]


_LIVESPEC_JSONC = ".livespec.jsonc"
_AUTHOR_ENV = "LIVESPEC_AUTHOR_LLM"
_AUTHOR_FALLBACK = "unknown-llm"
_VNNN_RE = re.compile(r"^v(\d+)$")


@dataclass(frozen=True, kw_only=True, slots=True)
class _RevisionContext:
    """Per-invocation context bundling the resolved values that every
    decision shares: paths, timestamp, and author identifiers."""

    spec_target: Path
    history_pc: Path
    timestamp: str
    git_user: str
    author_llm: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="livespec revise",
        description="Process per-proposal decisions; cut a new history/vNNN/ snapshot.",
        exit_on_error=False,
    )
    parser.add_argument(
        "--revise-json",
        dest="revise_json",
        type=Path,
        required=True,
        help="Path to the revise-input JSON payload from prompts/revise.md.",
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


def _resolve_author_llm(
    *,
    cli_author: str | None,
    payload_author: str | None,
) -> str:
    if cli_author:
        return cli_author
    env_value = os.environ.get(_AUTHOR_ENV)
    if env_value:
        return env_value
    if payload_author:
        return payload_author
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
    return (
        read_text(path=namespace.revise_json)
        .bind(_parse_and_validate_revise_input)
        .bind(lambda payload: _resolve_target_then_process(
            payload=payload,
            namespace=namespace,
            project_root=project_root,
        ))
    )


def _parse_and_validate_revise_input(
    text: str,
) -> IOResult[ReviseInput, LivespecError]:
    parsed = parse_jsonc(text=text)
    match parsed:
        case Failure(err):
            return IOFailure(err)
        case Success(payload):
            return _validate_revise_payload(payload=payload)
        case _:
            assert_never(parsed)


def _validate_revise_payload(
    *,
    payload: dict[str, Any],
) -> IOResult[ReviseInput, LivespecError]:
    return read_text(path=_schema_path(name="revise_input")).bind(
        lambda schema_text: _compile_revise_validator(
            schema_text=schema_text,
            payload=payload,
        ),
    )


def _compile_revise_validator(
    *,
    schema_text: str,
    payload: dict[str, Any],
) -> IOResult[ReviseInput, LivespecError]:
    schema_parsed = parse_jsonc(text=schema_text)
    match schema_parsed:
        case Failure(err):
            return IOFailure(err)
        case Success(schema_dict):
            fast_validator = compile_schema(
                schema_id="revise_input.schema.json",
                schema=schema_dict,
            )
            validator = validate_revise_input.make_validator(
                fast_validator=fast_validator,
            )
            validated = validator(payload)
            match validated:
                case Failure(err):
                    return IOFailure(err)
                case Success(revise_input):
                    return IOSuccess(revise_input)
                case _:
                    assert_never(validated)
        case _:
            assert_never(schema_parsed)


def _resolve_target_then_process(
    *,
    payload: ReviseInput,
    namespace: argparse.Namespace,
    project_root: Path,
) -> IOResult[Path, LivespecError]:
    if namespace.spec_target is not None:
        spec_target_abs = (project_root / namespace.spec_target).resolve()
        return _process_revisions(
            payload=payload,
            namespace=namespace,
            project_root=project_root,
            spec_target=spec_target_abs,
        )
    return _resolve_default_spec_target(project_root=project_root).bind(
        lambda spec_target: _process_revisions(
            payload=payload,
            namespace=namespace,
            project_root=project_root,
            spec_target=spec_target,
        ),
    )


def _resolve_default_spec_target(
    *,
    project_root: Path,
) -> IOResult[Path, LivespecError]:
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
                lambda schema_text: _validate_jsonc(
                    schema_text=schema_text,
                    jsonc_dict=jsonc_dict,
                ),
            )
        case _:
            assert_never(parsed)


def _validate_jsonc(
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
    """Phase 3 minimum-viable mapping (matches seed.py + propose_change.py)."""
    if template == "minimal":
        return project_root
    return project_root / "SPECIFICATION"


def _process_revisions(
    *,
    payload: ReviseInput,
    namespace: argparse.Namespace,
    project_root: Path,
    spec_target: Path,
) -> IOResult[Path, LivespecError]:
    """Discover next vNNN, resolve git_user, then run the file-shaping work."""
    return _next_vnnn(spec_target=spec_target).bind(
        lambda vnnn: _process_with_vnnn(
            payload=payload,
            cli_author=namespace.author,
            project_root=project_root,
            spec_target=spec_target,
            vnnn=vnnn,
        ),
    )


def _next_vnnn(*, spec_target: Path) -> IOResult[str, LivespecError]:
    """List spec_target/history/ → find max vNNN → return vNNN+1 (zero-padded to 3)."""
    history_dir = spec_target / "history"
    return path_exists(path=history_dir).bind(
        lambda exists: _list_or_empty_history(
            history_dir=history_dir,
            exists=exists,
        ),
    ).map(_compute_next_vnnn)


def _list_or_empty_history(
    *,
    history_dir: Path,
    exists: bool,
) -> IOResult[list[Path], LivespecError]:
    if not exists:
        return IOSuccess([])
    return list_dir(path=history_dir)


def _compute_next_vnnn(entries: list[Path]) -> str:
    max_n = 0
    for entry in entries:
        m = _VNNN_RE.match(entry.name)
        if m:
            n = int(m.group(1))
            max_n = max(max_n, n)
    return f"v{max_n + 1:03d}"


def _process_with_vnnn(
    *,
    payload: ReviseInput,
    cli_author: str | None,
    project_root: Path,
    spec_target: Path,
    vnnn: str,
) -> IOResult[Path, LivespecError]:
    author_llm = _resolve_author_llm(
        cli_author=cli_author,
        payload_author=payload.author,
    )
    return get_git_user(project_root=project_root).bind(
        lambda git_user: _shape_history(
            payload=payload,
            project_root=project_root,
            spec_target=spec_target,
            vnnn=vnnn,
            git_user=git_user,
            author_llm=author_llm,
        ),
    ).lash(
        lambda _err: _shape_history(
            payload=payload,
            project_root=project_root,
            spec_target=spec_target,
            vnnn=vnnn,
            git_user=GIT_USER_UNKNOWN,
            author_llm=author_llm,
        ),
    )


def _shape_history(
    *,
    payload: ReviseInput,
    project_root: Path,
    spec_target: Path,
    vnnn: str,
    git_user: str,
    author_llm: str,
) -> IOResult[Path, LivespecError]:
    """Apply resulting_files; mkdir history/vNNN; move proposed-changes; write revisions."""
    any_accept_or_modify = any(
        d.decision in ("accept", "modify") for d in payload.decisions
    )
    history_vnnn = spec_target / "history" / vnnn
    history_pc = history_vnnn / "proposed_changes"
    timestamp = _now_iso()
    ctx = _RevisionContext(
        spec_target=spec_target,
        history_pc=history_pc,
        timestamp=timestamp,
        git_user=git_user,
        author_llm=author_llm,
    )
    return mkdir_p(path=history_pc).bind(
        lambda _: _apply_resulting_files(
            decisions=payload.decisions,
            project_root=project_root,
        ),
    ).bind(
        lambda _: _walk_decisions(
            decisions=payload.decisions,
            index=0,
            ctx=ctx,
        ),
    ).bind(
        lambda _: _maybe_snapshot_spec_files(
            any_accept_or_modify=any_accept_or_modify,
            spec_target=spec_target,
            history_vnnn=history_vnnn,
        ),
    ).map(lambda _: history_vnnn)


def _apply_resulting_files(
    *,
    decisions: list[ProposalDecision],
    project_root: Path,
) -> IOResult[None, LivespecError]:
    """Walk all decisions, write each `resulting_files` entry to its target path.

    Per the prompt convention (prompts/revise.md), `resulting_files[].path`
    values are project-root-relative regardless of `--spec-target` —
    the same convention seed.py's payload uses. Resolve via
    `project_root / rf.path`. Phase 3 minimum-viable: writes flat list
    across all decisions; no conflict detection between decisions
    touching the same file.
    """
    targets: list[tuple[Path, str]] = []
    for decision in decisions:
        if decision.decision in ("accept", "modify"):
            for rf in decision.resulting_files:
                targets.append((project_root / rf.path, rf.content))
    return _walk_writes(targets=targets, index=0)


def _walk_writes(
    *,
    targets: list[tuple[Path, str]],
    index: int,
) -> IOResult[None, LivespecError]:
    if index >= len(targets):
        return IOSuccess(None)
    path, content = targets[index]
    return mkdir_p(path=path.parent).bind(
        lambda _: write_text(path=path, content=content),
    ).bind(
        lambda _: _walk_writes(targets=targets, index=index + 1),
    )


def _walk_decisions(
    *,
    decisions: list[ProposalDecision],
    index: int,
    ctx: _RevisionContext,
) -> IOResult[None, LivespecError]:
    if index >= len(decisions):
        return IOSuccess(None)
    decision = decisions[index]
    return _process_one_decision(
        decision=decision,
        ctx=ctx,
    ).bind(
        lambda _: _walk_decisions(
            decisions=decisions,
            index=index + 1,
            ctx=ctx,
        ),
    )


def _process_one_decision(
    *,
    decision: ProposalDecision,
    ctx: _RevisionContext,
) -> IOResult[None, LivespecError]:
    """Move proposed-change file to history; write paired revision file."""
    src_pc = ctx.spec_target / "proposed_changes" / f"{decision.proposal_topic}.md"
    dst_pc = ctx.history_pc / f"{decision.proposal_topic}.md"
    revision_path = ctx.history_pc / f"{decision.proposal_topic}-revision.md"
    revision_content = _render_revision(
        decision=decision,
        timestamp=ctx.timestamp,
        git_user=ctx.git_user,
        author_llm=ctx.author_llm,
    )
    return _move_file(src=src_pc, dst=dst_pc).bind(
        lambda _: write_text(path=revision_path, content=revision_content),
    )


def _move_file(*, src: Path, dst: Path) -> IOResult[None, LivespecError]:
    """Phase 3 minimum-viable: read + write + remove (same-filesystem assumption)."""
    return read_text(path=src).bind(
        lambda content: write_text(path=dst, content=content),
    ).bind(
        lambda _: remove_file(path=src),
    )


def _render_revision(
    *,
    decision: ProposalDecision,
    timestamp: str,
    git_user: str,
    author_llm: str,
) -> str:
    """Render <topic>-revision.md per PROPOSAL §"Revision file format" lines 3027-3050."""
    body_sections = (
        f"## Decision and Rationale\n"
        f"\n"
        f"{decision.rationale}\n"
    )
    if decision.decision == "modify" and decision.modifications is not None:
        body_sections += (
            f"\n"
            f"## Modifications\n"
            f"\n"
            f"{decision.modifications}\n"
        )
    if decision.decision in ("accept", "modify") and decision.resulting_files:
        files_block = "\n".join(f"- {rf.path}" for rf in decision.resulting_files)
        body_sections += (
            f"\n"
            f"## Resulting Changes\n"
            f"\n"
            f"{files_block}\n"
        )
    return (
        f"---\n"
        f"proposal: {decision.proposal_topic}.md\n"
        f"decision: {decision.decision}\n"
        f"revised_at: {timestamp}\n"
        f"author_human: {git_user}\n"
        f"author_llm: {author_llm}\n"
        f"---\n"
        f"\n"
        f"{body_sections}"
    )


def _maybe_snapshot_spec_files(
    *,
    any_accept_or_modify: bool,
    spec_target: Path,
    history_vnnn: Path,
) -> IOResult[None, LivespecError]:
    """If any accept/modify decision, copy spec_target's working files into history/vNNN/."""
    if not any_accept_or_modify:
        return IOSuccess(None)
    return list_dir(path=spec_target).bind(
        lambda entries: _walk_snapshot(
            entries=cast("list[Path]", entries),
            index=0,
            history_vnnn=history_vnnn,
        ),
    )


def _walk_snapshot(
    *,
    entries: list[Path],
    index: int,
    history_vnnn: Path,
) -> IOResult[None, LivespecError]:
    if index >= len(entries):
        return IOSuccess(None)
    entry = entries[index]
    if not entry.name.endswith(".md"):
        return _walk_snapshot(
            entries=entries,
            index=index + 1,
            history_vnnn=history_vnnn,
        )
    return read_text(path=entry).bind(
        lambda content: write_text(
            path=history_vnnn / entry.name,
            content=content,
        ),
    ).bind(
        lambda _: _walk_snapshot(
            entries=entries,
            index=index + 1,
            history_vnnn=history_vnnn,
        ),
    )


def main(*, argv: Sequence[str] | None = None) -> int:
    log = get_logger(__name__)
    actual_argv: Sequence[str] = list(argv) if argv is not None else sys.argv[1:]
    try:
        return _dispatch(actual_argv=actual_argv)
    except Exception as exc:
        log.exception(
            "revise internal error",
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
                "revise failed",
                error_type=type(err).__name__,
                error_message=str(err),
            )
            return type(err).exit_code
        case _ as unreachable:
            _unreachable(unreachable)


def _unreachable(value: object) -> NoReturn:
    assert_never(value)  # type: ignore[arg-type]


# Keep `Decision` referenced so the import isn't pruned by F401 — used in
# `_render_revision`'s match-on-decision-string-literal indirectly. The
# Literal type is consumed via the dataclass; pyright sees it.
_: type[Decision] = Decision
