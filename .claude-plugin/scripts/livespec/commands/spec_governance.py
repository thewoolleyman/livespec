# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
"""Spec-governance control CLI supervisor."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult, IOSuccess
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.errors import LivespecError, UsageError
from livespec.io import cli, streams
from livespec.spec_governance.config import parse_config_text
from livespec.spec_governance.editing import EditResult, apply_action
from livespec.spec_governance.journal import JournalAppend, append_journal_event
from livespec.spec_governance.registry import manifest_rows

__all__: list[str] = ["build_parser", "dispatch", "main"]


def build_parser() -> argparse.ArgumentParser:
    """Construct the spec-governance argparse parser without parsing."""
    parser = argparse.ArgumentParser(prog="spec-governance", exit_on_error=False)
    _ = parser.add_argument("--project-root", default=None)
    group = parser.add_mutually_exclusive_group(required=True)
    _ = group.add_argument("--show-effective", action="store_true")
    _ = group.add_argument("--action")
    _ = group.add_argument("--journal-event-json")
    return parser


def main(*, argv: list[str] | None = None) -> int:
    """Spec-governance supervisor entry point."""
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    railway: IOResult[Any, LivespecError] = cli.parse_argv(
        parser=parser,
        argv=resolved_argv,
    ).bind(lambda namespace: dispatch(namespace=namespace))  # pyright: ignore[reportArgumentType]
    unwrapped = unsafe_perform_io(railway)  # pyright: ignore[reportArgumentType]
    match unwrapped:
        case Success(_):
            return 0
        case Failure(LivespecError() as err):
            return cli.emit_livespec_failure(command="spec-governance", err=err)
        case _:
            assert_never(unwrapped)


def dispatch(*, namespace: argparse.Namespace) -> IOResult[Any, LivespecError]:
    project_root = _project_root(namespace=namespace)
    if namespace.show_effective:
        return _emit_effective(project_root=project_root)
    if namespace.action is not None:
        return _apply_action(project_root=project_root, action=str(namespace.action))
    if namespace.journal_event_json is not None:
        return _append_journal(
            project_root=project_root,
            event_path=Path(str(namespace.journal_event_json)),
        )
    return IOResult.from_failure(UsageError("spec-governance: one operation is required"))


def _project_root(*, namespace: argparse.Namespace) -> Path:
    if namespace.project_root is None:
        return Path.cwd()
    return Path(str(namespace.project_root))


def _emit_effective(*, project_root: Path) -> IOResult[str, LivespecError]:
    config_path = project_root / ".livespec.jsonc"
    text = config_path.read_text(encoding="utf-8") if config_path.exists() else "{}"
    declared = parse_config_text(text=text)
    payload = {
        "manifest": [dataclasses.asdict(row) for row in manifest_rows()],
        "declared": declared.raw,
        "effective": dataclasses.asdict(declared.effective),
        "diagnostics": declared.diagnostics,
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    _ = streams.write_stdout(text=f"{rendered}\n")
    return IOSuccess(rendered)


def _apply_action(*, project_root: Path, action: str) -> IOResult[EditResult, LivespecError]:
    result = apply_action(project_root=project_root, action=action)
    if isinstance(result, str):
        return IOResult.from_failure(UsageError(result))
    _ = streams.write_stdout(
        text=json.dumps(
            {"changed_path": str(result.changed_path), "message": result.message},
            sort_keys=True,
        )
        + "\n",
    )
    return IOSuccess(result)


def _append_journal(
    *,
    project_root: Path,
    event_path: Path,
) -> IOResult[JournalAppend, LivespecError]:
    result = append_journal_event(project_root=project_root, event_path=event_path)
    if isinstance(result, str):
        return IOResult.from_failure(UsageError(result))
    _ = streams.write_stdout(
        text=json.dumps(
            {"journal_path": str(result.path), "event_digest": result.digest},
            sort_keys=True,
        )
        + "\n",
    )
    return IOSuccess(result)
