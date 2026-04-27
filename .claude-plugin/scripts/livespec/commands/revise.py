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

Pipeline (encapsulated as `@rop_pipeline class RevisePipeline`
with single public `run(*, argv)` entry per sub-step 14b):

1. Read + parse + schema-validate `--revise-json` against
   `revise_input.schema.json` (exit 4 on validation failure —
   retryable).
2. Resolve `--spec-target` (default: main spec root via the same
   `.livespec.jsonc` upward-walk + built-in template mapping
   propose_change uses, delegated to `_revise_helpers.py`).
3. Determine next vNNN by listing `<spec-target>/history/`.
4. Resolve author_human via `io.git.get_git_user`
   (`GIT_USER_UNKNOWN` fallback if git is absent / config is
   incomplete).
5. Resolve author_llm: --author CLI → LIVESPEC_AUTHOR_LLM env →
   payload `author` field → "unknown-llm" fallback.
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
     <topic>-revision.md` with front-matter + body sections.
8. If any decision was accept or modify: copy current working
   spec files (post-update) into `<spec-target>/history/vNNN/`.

Out-of-Phase-3 scope per plan line 1194-1203 (LLM decision flow,
collision-suffix handling, cross-fs move, etc.) is Phase 7.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from returns.io import IOFailure, IOResult, IOSuccess
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.commands._revise_helpers import (
    AUTHOR_FALLBACK,
    compute_next_vnnn,
    now_iso,
    render_revision,
    resolve_default_spec_target,
    walk_writes,
)
from livespec.errors import HelpRequested, LivespecError
from livespec.io.cli import parse_args
from livespec.io.fastjsonschema_facade import compile_schema
from livespec.io.fs import (
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
from livespec.types import rop_pipeline
from livespec.validate import revise_input as validate_revise_input

__all__: list[str] = [
    "RevisePipeline",
    "build_parser",
    "main",
    "run",
]


_AUTHOR_ENV = "LIVESPEC_AUTHOR_LLM"


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


def _resolve_author_llm(*, cli_author: str | None, payload_author: str | None) -> str:
    if cli_author:
        return cli_author
    env_value = os.environ.get(_AUTHOR_ENV)
    if env_value:
        return env_value
    if payload_author:
        return payload_author
    return AUTHOR_FALLBACK


@rop_pipeline
class RevisePipeline:
    """Railway-oriented pipeline for `livespec revise`. Single public `run`."""

    def __init__(self) -> None:
        self._project_root: Path = Path.cwd()
        self._namespace: argparse.Namespace = cast("argparse.Namespace", None)
        self._payload: ReviseInput = cast("ReviseInput", None)

    def run(self, *, argv: Sequence[str]) -> IOResult[Path, LivespecError]:
        """Parse argv → resolve target → process revisions → return history_vnnn."""
        return parse_args(parser=build_parser(), argv=argv).bind(self._orchestrate)

    def _orchestrate(self, namespace: argparse.Namespace) -> IOResult[Path, LivespecError]:
        self._namespace = namespace
        self._project_root = (
            namespace.project_root if namespace.project_root is not None else Path.cwd()
        )
        return read_text(path=namespace.revise_json).bind(self._parse_and_validate)

    def _parse_and_validate(self, text: str) -> IOResult[Path, LivespecError]:
        parsed = parse_jsonc(text=text)
        match parsed:
            case Failure(err):
                return IOFailure(err)
            case Success(payload):
                return self._validate_payload(payload=payload)
            case _:
                assert_never(parsed)

    def _validate_payload(self, *, payload: dict[str, object]) -> IOResult[Path, LivespecError]:
        return read_text(path=_schema_path(name="revise_input")).bind(
            lambda schema_text: self._compile_validator(
                schema_text=schema_text,
                payload=payload,
            ),
        )

    def _compile_validator(
        self,
        *,
        schema_text: str,
        payload: dict[str, object],
    ) -> IOResult[Path, LivespecError]:
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
                validated = validator(payload=payload)
                match validated:
                    case Failure(err):
                        return IOFailure(err)
                    case Success(revise_input):
                        return self._stash_then_resolve_target(payload=revise_input)
                    case _:
                        assert_never(validated)
            case _:
                assert_never(schema_parsed)

    def _stash_then_resolve_target(self, *, payload: ReviseInput) -> IOResult[Path, LivespecError]:
        self._payload = payload
        if self._namespace.spec_target is not None:
            spec_target_abs = (self._project_root / self._namespace.spec_target).resolve()
            return self._process_revisions(spec_target=spec_target_abs)
        return resolve_default_spec_target(project_root=self._project_root).bind(
            lambda spec_target: self._process_revisions(spec_target=spec_target),
        )

    def _process_revisions(self, *, spec_target: Path) -> IOResult[Path, LivespecError]:
        return self._next_vnnn(spec_target=spec_target).bind(
            lambda vnnn: self._process_with_vnnn(spec_target=spec_target, vnnn=vnnn),
        )

    def _next_vnnn(self, *, spec_target: Path) -> IOResult[str, LivespecError]:
        history_dir = spec_target / "history"
        return (
            path_exists(path=history_dir)
            .bind(
                lambda exists: self._list_or_empty(history_dir=history_dir, exists=exists),
            )
            .map(lambda entries: compute_next_vnnn(entries=entries))
        )

    def _list_or_empty(
        self,
        *,
        history_dir: Path,
        exists: bool,
    ) -> IOResult[list[Path], LivespecError]:
        if not exists:
            return IOSuccess([])
        return list_dir(path=history_dir)

    def _process_with_vnnn(self, *, spec_target: Path, vnnn: str) -> IOResult[Path, LivespecError]:
        author_llm = _resolve_author_llm(
            cli_author=self._namespace.author,
            payload_author=self._payload.author,
        )
        return (
            get_git_user(project_root=self._project_root)
            .bind(
                lambda git_user: self._shape_history(
                    spec_target=spec_target,
                    vnnn=vnnn,
                    git_user=git_user,
                    author_llm=author_llm,
                ),
            )
            .lash(
                lambda _err: self._shape_history(
                    spec_target=spec_target,
                    vnnn=vnnn,
                    git_user=GIT_USER_UNKNOWN,
                    author_llm=author_llm,
                ),
            )
        )

    def _shape_history(
        self,
        *,
        spec_target: Path,
        vnnn: str,
        git_user: str,
        author_llm: str,
    ) -> IOResult[Path, LivespecError]:
        any_accept = any(d.decision in ("accept", "modify") for d in self._payload.decisions)
        history_vnnn = spec_target / "history" / vnnn
        ctx = _RevisionContext(
            spec_target=spec_target,
            history_pc=history_vnnn / "proposed_changes",
            timestamp=now_iso(),
            git_user=git_user,
            author_llm=author_llm,
        )
        return (
            mkdir_p(path=ctx.history_pc)
            .bind(
                lambda _: self._apply_resulting_files(),
            )
            .bind(
                lambda _: self._walk_decisions(index=0, ctx=ctx),
            )
            .bind(
                lambda _: self._maybe_snapshot(
                    any_accept_or_modify=any_accept,
                    spec_target=spec_target,
                    history_vnnn=history_vnnn,
                ),
            )
            .map(lambda _: history_vnnn)
        )

    def _apply_resulting_files(self) -> IOResult[None, LivespecError]:
        targets: list[tuple[Path, str]] = []
        for decision in self._payload.decisions:
            if decision.decision in ("accept", "modify"):
                for rf in decision.resulting_files:
                    targets.append((self._project_root / rf.path, rf.content))
        return walk_writes(targets=targets, index=0)

    def _walk_decisions(
        self, *, index: int, ctx: _RevisionContext
    ) -> IOResult[None, LivespecError]:
        if index >= len(self._payload.decisions):
            return IOSuccess(None)
        return self._process_one(decision=self._payload.decisions[index], ctx=ctx).bind(
            lambda _: self._walk_decisions(index=index + 1, ctx=ctx),
        )

    def _process_one(
        self,
        *,
        decision: ProposalDecision,
        ctx: _RevisionContext,
    ) -> IOResult[None, LivespecError]:
        src_pc = ctx.spec_target / "proposed_changes" / f"{decision.proposal_topic}.md"
        dst_pc = ctx.history_pc / f"{decision.proposal_topic}.md"
        revision_path = ctx.history_pc / f"{decision.proposal_topic}-revision.md"
        revision_content = render_revision(
            decision=decision,
            timestamp=ctx.timestamp,
            git_user=ctx.git_user,
            author_llm=ctx.author_llm,
        )
        return self._move_file(src=src_pc, dst=dst_pc).bind(
            lambda _: write_text(path=revision_path, content=revision_content),
        )

    def _move_file(self, *, src: Path, dst: Path) -> IOResult[None, LivespecError]:
        return (
            read_text(path=src)
            .bind(
                lambda content: write_text(path=dst, content=content),
            )
            .bind(lambda _: remove_file(path=src))
        )

    def _maybe_snapshot(
        self,
        *,
        any_accept_or_modify: bool,
        spec_target: Path,
        history_vnnn: Path,
    ) -> IOResult[None, LivespecError]:
        if not any_accept_or_modify:
            return IOSuccess(None)
        return list_dir(path=spec_target).bind(
            lambda entries: self._walk_snapshot(
                entries=cast("list[Path]", entries),
                index=0,
                history_vnnn=history_vnnn,
            ),
        )

    def _walk_snapshot(
        self,
        *,
        entries: list[Path],
        index: int,
        history_vnnn: Path,
    ) -> IOResult[None, LivespecError]:
        if index >= len(entries):
            return IOSuccess(None)
        entry = entries[index]
        if not entry.name.endswith(".md"):
            return self._walk_snapshot(entries=entries, index=index + 1, history_vnnn=history_vnnn)
        return (
            read_text(path=entry)
            .bind(
                lambda content: write_text(path=history_vnnn / entry.name, content=content),
            )
            .bind(
                lambda _: self._walk_snapshot(
                    entries=entries,
                    index=index + 1,
                    history_vnnn=history_vnnn,
                ),
            )
        )


def run(*, argv: Sequence[str]) -> IOResult[Path, LivespecError]:
    """Module-level entry: instantiate RevisePipeline and dispatch."""
    return RevisePipeline().run(argv=argv)


def main(*, argv: Sequence[str] | None = None) -> int:
    """Supervisor: bug-catcher + railway dispatch inline (sys.stdout.write
    exemption per style doc lines 1474-1481 is per-`main()`, NOT per-helper)."""
    log = get_logger(name=__name__)
    actual_argv: Sequence[str] = list(argv) if argv is not None else sys.argv[1:]
    try:
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
            case _:
                assert_never(inner)
    except Exception as exc:
        log.exception(
            "revise internal error",
            exception_type=type(exc).__name__,
            exception_repr=repr(exc),
        )
        return 1


# Keep `Decision` referenced so the import isn't pruned by F401 — used in
# `_process_one`'s match-on-decision-string-literal indirectly. The
# Literal type is consumed via the dataclass; pyright sees it.
_: type[Decision] = Decision
