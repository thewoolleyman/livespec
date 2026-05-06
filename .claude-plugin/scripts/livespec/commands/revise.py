"""Revise sub-command supervisor.

Per and Plan Phase 3
: revise is minimum-viable per v019 Q1 —
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
IOResult to derive the exit code. The file-shaping railway
helpers live in the sibling private module
`_revise_railway_emits.py` (extracted at cycle 5.c.4 to keep
this file under the 250-LLOC hard ceiling).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.commands._revise_helpers import (
    _compose_resulting_changes_section,  # re-exported for the paired test surface  # noqa: F401
    _now_utc_iso8601,
    _resolve_author,
)
from livespec.commands._revise_railway_emits import (
    _bind_resulting_files,  # re-exported for the paired test surface  # noqa: F401
    _format_next_version_name,  # re-exported for the paired test surface  # noqa: F401
    _process_decisions,
)
from livespec.errors import LivespecError
from livespec.io import cli, fs
from livespec.io import git as io_git
from livespec.parse import jsonc
from livespec.validate import revise_input as validate_revise_input_module

__all__: list[str] = ["build_parser", "main"]


_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
_REVISE_INPUT_SCHEMA_PATH = _SCHEMAS_DIR / "revise_input.schema.json"


def build_parser() -> argparse.ArgumentParser:
    """Construct the revise argparse parser without parsing.

     Per style doc §"CLI argument parsing seam":
     `exit_on_error=False` lets argparse signal errors via
     `argparse.ArgumentError` rather than `SystemExit`. The
     parser exposes `--revise-json <path>` (required), and the
     optional `--author`, `--spec-target`, `--project-root` flags
    .
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

    Threads argv through `parse_argv` -> `fs.read_text` ->
    `jsonc.loads` -> `validate_payload` -> `io_git.get_git_user`
    -> `_process_decisions` (in `_revise_railway_emits`), then
    pattern-matches the final IOResult onto an exit code per
    style doc §"Exit code contract".
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
    revised_at = _now_utc_iso8601()
    railway: IOResult[Any, LivespecError] = parse_result.bind(
        lambda namespace: (
            fs.read_text(path=Path(namespace.revise_json))
            .bind(lambda text: IOResult.from_result(jsonc.loads(text=text)))
            .bind(lambda payload: _validate_payload(payload=payload))
            .bind(
                lambda revise_input: io_git.get_git_user().bind(
                    lambda author_human: _process_decisions(
                        revise_input=revise_input,
                        spec_target=_resolve_spec_target(namespace=namespace),
                        author_human=author_human,
                        author_llm=_resolve_author(
                            namespace=namespace,
                            payload=revise_input,
                            env_lookup=os.environ.get,
                        ),
                        revised_at=revised_at,
                    ),
                ),
            )
        ),
    )
    return _pattern_match_io_result(io_result=railway)


def _validate_payload(*, payload: dict[str, Any]) -> IOResult[Any, LivespecError]:
    """Read revise_input.schema.json and validate the payload.

    Composes fs.read_text(schema) -> jsonc.loads(schema-text) ->
    validate_revise_input(payload, schema-dict). Mirrors
    propose_change/critique's same stage; failures bubble via the
    IOResult track (schema-file missing -> PreconditionError;
    schema malformed -> ValidationError; payload schema-violation
    -> ValidationError).
    """
    return (
        fs.read_text(path=_REVISE_INPUT_SCHEMA_PATH)
        .bind(lambda schema_text: IOResult.from_result(jsonc.loads(text=schema_text)))
        .bind(
            lambda schema_dict: IOResult.from_result(
                validate_revise_input_module.validate_revise_input(
                    payload=payload,
                    schema=schema_dict,
                ),
            ),
        )
    )


def _resolve_spec_target(*, namespace: argparse.Namespace) -> Path:
    """Resolve --spec-target to a Path, defaulting to <project-root>/SPECIFICATION.

    Per Plan Phase 3 +:
    `<spec-target>` is selected via --spec-target, defaulting to
    the project's main spec root (`<project-root>/SPECIFICATION/`
    under the built-in livespec template).
    """
    if namespace.spec_target is not None:
        return Path(namespace.spec_target)
    project_root = Path.cwd() if namespace.project_root is None else Path(namespace.project_root)
    return project_root / "SPECIFICATION"
