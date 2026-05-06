"""Seed sub-command supervisor.

Per PROPOSAL.md §"`seed`" + briefing "outside-in walking
direction": this is the wrapper entry-point importing
`livespec.commands.seed.main`. Drives the seed flow:
load+validate `--seed-json` payload, write `.livespec.jsonc`,
materialize the main + sub-spec trees, auto-capture the seed
proposed-change, run post-step doctor.

`build_parser()` is the pure argparse factory per style doc
§"CLI argument parsing seam"; `main()` is the supervisor that
threads argv through the railway and pattern-matches the final
IOResult to derive the exit code.

Cycle 4e (2026-05-02) split the heavy file-writing and
emission stages into sibling private modules
(`_seed_railway_writes.py`, `_seed_railway_emits.py`) so this
file stays under the 200-LLOC ceiling enforced by
`check-complexity`.
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

from livespec.commands._seed_railway_emits import (
    _emit_seed_proposed_change,
    _emit_seed_revision,
    _emit_skill_owned_history_readme,
    _emit_skill_owned_proposed_changes_readme,
    _emit_skill_owned_sub_spec_history_readmes,
    _emit_skill_owned_sub_spec_history_v001_gitkeeps,
    _emit_skill_owned_sub_spec_proposed_changes_readmes,
    _run_post_step_doctor,
)
from livespec.commands._seed_railway_writes import (
    _write_main_spec_files,
    _write_main_spec_history_v001,
    _write_sub_spec_files,
    _write_sub_spec_history_v001,
)
from livespec.errors import LivespecError
from livespec.io import cli, fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.seed_input import SeedInput
from livespec.validate import seed_input as validate_seed_input_module

__all__: list[str] = ["build_parser", "main"]


_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
_SEED_INPUT_SCHEMA_PATH = _SCHEMAS_DIR / "seed_input.schema.json"


def build_parser() -> argparse.ArgumentParser:
    """Construct the seed argparse parser without parsing.

    Pure: returns the configured parser; the caller (the io/cli
    facade) drives `parse_args()`. Per style doc §"CLI argument
    parsing seam", `exit_on_error=False` lets argparse signal
    errors via `argparse.ArgumentError` rather than `SystemExit`.
    """
    parser = argparse.ArgumentParser(prog="seed", exit_on_error=False)
    _ = parser.add_argument("--seed-json", required=True)
    _ = parser.add_argument("--project-root", default=None)
    return parser


def _load_seed_json(*, namespace: argparse.Namespace) -> IOResult[str, LivespecError]:
    """Read the --seed-json payload from disk; railway-stage 2."""
    return fs.read_text(path=Path(namespace.seed_json))


def _parse_payload(*, text: str) -> IOResult[Any, LivespecError]:
    """Lift the pure JSONC parser onto the IOResult track."""
    return IOResult.from_result(jsonc.loads(text=text))


def _validate_payload(*, payload: dict[str, Any]) -> IOResult[SeedInput, LivespecError]:
    """Read the seed-input schema and validate the payload against it."""
    return (
        fs.read_text(path=_SEED_INPUT_SCHEMA_PATH)
        .bind(lambda schema_text: IOResult.from_result(jsonc.loads(text=schema_text)))
        .bind(
            lambda schema_dict: IOResult.from_result(
                validate_seed_input_module.validate_seed_input(
                    payload=payload,
                    schema=schema_dict,
                ),
            ),
        )
    )


def _write_livespec_config(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Write `<project-root>/.livespec.jsonc` from the validated seed input."""
    skeleton = '{\n  "template": "' + seed_input.template + '"\n}\n'
    config_path = project_root / ".livespec.jsonc"
    return fs.write_text(path=config_path, text=skeleton).map(lambda _: seed_input)


def _pattern_match_io_result(
    *,
    io_result: IOResult[Any, LivespecError],
) -> int:
    """Pattern-match the final railway IOResult onto an exit code."""
    unwrapped = unsafe_perform_io(io_result)
    match unwrapped:
        case Success(_):
            return 0
        case Failure(LivespecError() as err):
            return err.exit_code
        case _:
            assert_never(unwrapped)


def _resolve_project_root(*, namespace: argparse.Namespace) -> Path:
    """Resolve --project-root to a Path, defaulting to Path.cwd()."""
    if namespace.project_root is None:
        return Path.cwd()
    return Path(namespace.project_root)


def main(*, argv: list[str] | None = None) -> int:
    """Seed supervisor entry point. Returns the process exit code.

    Threads argv through the railway:
      parse_argv -> read --seed-json -> jsonc.loads ->
      validate_seed_input -> write .livespec.jsonc ->
      write main-spec files -> write sub-spec files ->
      write main-spec history/v001/ -> write sub-spec
      history/v001/ -> emit seed.md proposed-change ->
      emit seed-revision.md -> emit skill-owned README ->
      run post-step doctor.

    Exit codes: 0 success, 2 UsageError (parse), 3
    PreconditionError (missing file), 4 ValidationError
    (malformed payload or schema violation).
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
    railway: IOResult[Any, LivespecError] = parse_result.bind(
        lambda namespace: (
            _load_seed_json(namespace=namespace)
            .bind(lambda text: _parse_payload(text=text))
            .bind(lambda payload: _validate_payload(payload=payload))
            .bind(
                lambda si: _write_livespec_config(
                    seed_input=si,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda si: _write_main_spec_files(
                    seed_input=si,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda si: _write_sub_spec_files(
                    seed_input=si,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda si: _write_main_spec_history_v001(
                    seed_input=si,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda si: _write_sub_spec_history_v001(
                    seed_input=si,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda si: _emit_seed_proposed_change(
                    seed_input=si,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda si: _emit_seed_revision(
                    seed_input=si,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda si: _emit_skill_owned_proposed_changes_readme(
                    seed_input=si,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda si: _emit_skill_owned_sub_spec_proposed_changes_readmes(
                    seed_input=si,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda si: _emit_skill_owned_history_readme(
                    seed_input=si,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda si: _emit_skill_owned_sub_spec_history_readmes(
                    seed_input=si,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda si: _emit_skill_owned_sub_spec_history_v001_gitkeeps(
                    seed_input=si,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda si: _run_post_step_doctor(
                    seed_input=si,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
        ),
    )
    return _pattern_match_io_result(io_result=railway)
