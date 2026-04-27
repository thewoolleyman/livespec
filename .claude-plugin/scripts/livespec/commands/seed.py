"""seed sub-command: bootstraps a fresh livespec specification tree.

Per PROPOSAL.md §"`seed`" lines ~1865-2080. The wrapper is invoked
as `bin/seed.py --seed-json <path>` after the LLM (driven by the
active template's `prompts/seed.md`) writes a JSON payload
conforming to `seed_input.schema.json` to a temp file.

Wrapper file-shaping work (in order, all BEFORE post-step
doctor-static):

1. Read + parse + schema-validate the seed-json payload (exit 4 on
   schema invalidity — retryable).
2. Pre-seed `.livespec.jsonc` handling (v016 P2 + v017 Q5/Q6) —
   absent: continue; present + valid + matching template: continue;
   present + valid + mismatching template: exit 3; present +
   malformed: exit 3.
3. Idempotency check — if any payload-target file already exists,
   exit 3 listing the existing files.
4. Write `.livespec.jsonc` at project root using the payload's
   `template` value.
5. Write each main-spec `files[]` entry.
6. Write each sub-spec entry's `files[]` entries (v018 Q1).
7. Materialize `<spec-root>/history/v001/` for the main spec and
   each sub-spec tree (v020 Q1 uniform README), including
   `proposed_changes/` subdir.
8. Auto-capture `seed.md` proposed-change + `seed-revision.md`
   under the main spec's `history/v001/proposed_changes/`
   (delegated to `commands/_seed_helpers.py`).

The pipeline is structured as `@rop_pipeline class SeedPipeline`
with a single public `run(*, argv)` entry per Phase 4 sub-step
14a. Per-invocation state (`_project_root`, `_payload`) is set
inside `_orchestrate` and the chain steps read from `self`,
avoiding lambda closure plumbing across the bind chain.

Phase 7 widens the pipeline with deeper validation, atomic-rollback
on partial-write failure, and richer auto-capture content (the
helpers in `_seed_helpers.py` are the natural extension point).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from returns.io import IOFailure, IOResult, IOSuccess
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.commands._seed_helpers import (
    now_iso,
    write_seed_pair,
)
from livespec.errors import (
    HelpRequested,
    LivespecError,
    PreconditionError,
)
from livespec.io.cli import parse_args
from livespec.io.fastjsonschema_facade import compile_schema
from livespec.io.fs import (
    mkdir_p,
    path_exists,
    read_text,
    write_text,
)
from livespec.io.git import GIT_USER_UNKNOWN, get_git_user
from livespec.io.structlog_facade import get_logger
from livespec.parse.jsonc import parse as parse_jsonc
from livespec.schemas.dataclasses.seed_input import SeedInput
from livespec.types import rop_pipeline
from livespec.validate import livespec_config as validate_livespec_config
from livespec.validate import seed_input as validate_seed_input

__all__: list[str] = [
    "SeedPipeline",
    "build_parser",
    "main",
    "run",
]


_LIVESPEC_JSONC = ".livespec.jsonc"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="livespec seed",
        description="Bootstrap a fresh livespec specification tree from a seed-input payload.",
        exit_on_error=False,
    )
    parser.add_argument(
        "--seed-json",
        dest="seed_json",
        type=Path,
        required=True,
        help="Path to the seed-input JSON payload produced by prompts/seed.md.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root for file-shaping work (default: cwd).",
    )
    return parser


def _schema_path(*, name: str) -> Path:
    """Path to a livespec/schemas/<name>.schema.json file inside the bundle."""
    return Path(__file__).resolve().parent.parent / "schemas" / f"{name}.schema.json"


@rop_pipeline
class SeedPipeline:
    """Railway-oriented file-shaping pipeline for `livespec seed`.

    Single public method `run`. `_payload` is initialized to a
    typed-`SeedInput` placeholder in `__init__` and overwritten in
    `_stash_then_check_jsonc`; chain steps downstream of that
    bind read `self._payload` directly without per-method
    `assert is not None` narrowing. The placeholder is never
    observed externally — `_orchestrate` is the only entry into
    the chain and it sets the real payload before any downstream
    step runs.
    """

    def __init__(self) -> None:
        self._project_root: Path = Path.cwd()
        self._payload: SeedInput = cast("SeedInput", None)

    def run(self, *, argv: Sequence[str]) -> IOResult[Path, LivespecError]:
        """Parse argv → run the file-shaping chain → return project_root."""
        return parse_args(parser=build_parser(), argv=argv).bind(self._orchestrate)

    def _orchestrate(self, namespace: argparse.Namespace) -> IOResult[Path, LivespecError]:
        self._project_root = (
            namespace.project_root if namespace.project_root is not None else Path.cwd()
        )
        return (
            read_text(path=namespace.seed_json)
            .bind(
                self._parse_and_validate_seed,
            )
            .bind(self._stash_then_check_jsonc)
        )

    def _parse_and_validate_seed(self, text: str) -> IOResult[SeedInput, LivespecError]:
        parsed = parse_jsonc(text=text)
        match parsed:
            case Failure(err):
                return IOFailure(err)
            case Success(payload):
                return self._validate_seed_payload(payload=payload)
            case _:
                assert_never(parsed)

    def _validate_seed_payload(
        self, *, payload: dict[str, Any]
    ) -> IOResult[SeedInput, LivespecError]:
        return read_text(path=_schema_path(name="seed_input")).bind(
            lambda schema_text: self._compile_seed_validator_and_run(
                schema_text=schema_text,
                payload=payload,
            ),
        )

    def _compile_seed_validator_and_run(
        self,
        *,
        schema_text: str,
        payload: dict[str, Any],
    ) -> IOResult[SeedInput, LivespecError]:
        schema_parsed = parse_jsonc(text=schema_text)
        match schema_parsed:
            case Failure(err):
                return IOFailure(err)
            case Success(schema_dict):
                fast_validator = compile_schema(
                    schema_id="seed_input.schema.json",
                    schema=schema_dict,
                )
                validator = validate_seed_input.make_validator(fast_validator=fast_validator)
                validated = validator(payload=payload)
                match validated:
                    case Failure(err):
                        return IOFailure(err)
                    case Success(seed_input):
                        return IOSuccess(seed_input)
                    case _:
                        assert_never(validated)
            case _:
                assert_never(schema_parsed)

    def _stash_then_check_jsonc(self, payload: SeedInput) -> IOResult[Path, LivespecError]:
        self._payload = payload
        jsonc_path = self._project_root / _LIVESPEC_JSONC
        return path_exists(path=jsonc_path).bind(
            lambda exists: self._resolve_jsonc_branch(jsonc_present=exists),
        )

    def _resolve_jsonc_branch(self, *, jsonc_present: bool) -> IOResult[Path, LivespecError]:
        if not jsonc_present:
            return self._idempotency_check_then_shape()
        return read_text(path=self._project_root / _LIVESPEC_JSONC).bind(
            self._verify_existing_jsonc,
        )

    def _verify_existing_jsonc(self, jsonc_text: str) -> IOResult[Path, LivespecError]:
        parsed = parse_jsonc(text=jsonc_text)
        match parsed:
            case Failure(err):
                return IOFailure(err)
            case Success(jsonc_dict):
                return read_text(path=_schema_path(name="livespec_config")).bind(
                    lambda schema_text: self._validate_existing_jsonc(
                        jsonc_dict=jsonc_dict,
                        schema_text=schema_text,
                    ),
                )
            case _:
                assert_never(parsed)

    def _validate_existing_jsonc(
        self,
        *,
        jsonc_dict: dict[str, Any],
        schema_text: str,
    ) -> IOResult[Path, LivespecError]:
        schema_parsed = parse_jsonc(text=schema_text)
        match schema_parsed:
            case Failure(err):
                return IOFailure(err)
            case Success(schema_dict):
                fast_validator = compile_schema(
                    schema_id="livespec_config.schema.json",
                    schema=schema_dict,
                )
                validator = validate_livespec_config.make_validator(fast_validator=fast_validator)
                validated = validator(payload=jsonc_dict)
                match validated:
                    case Failure(err):
                        return IOFailure(err)
                    case Success(config):
                        existing_t = config.template
                        payload_t = self._payload.template
                        if existing_t != payload_t:
                            return IOFailure(
                                PreconditionError(
                                    f"existing .livespec.jsonc template={existing_t!r} "
                                    f"does not match seed payload template={payload_t!r}",
                                )
                            )
                        return self._idempotency_check_then_shape()
                    case _:
                        assert_never(validated)
            case _:
                assert_never(schema_parsed)

    def _idempotency_check_then_shape(self) -> IOResult[Path, LivespecError]:
        targets = [self._project_root / e.path for e in self._payload.files]
        for sub in self._payload.sub_specs:
            targets.extend(self._project_root / e.path for e in sub.files)
        return self._walk_target_existence(targets=targets, index=0).bind(
            lambda _: self._shape_files(),
        )

    def _walk_target_existence(
        self,
        *,
        targets: list[Path],
        index: int,
    ) -> IOResult[None, LivespecError]:
        if index >= len(targets):
            return IOSuccess(None)
        candidate = targets[index]
        return path_exists(path=candidate).bind(
            lambda exists: IOFailure(
                PreconditionError(
                    f"seed target file already exists: {candidate}; "
                    f"refusing to overwrite. Run `livespec doctor` to diagnose.",
                )
            )
            if exists
            else self._walk_target_existence(targets=targets, index=index + 1),
        )

    def _shape_files(self) -> IOResult[Path, LivespecError]:
        return (
            self._write_livespec_jsonc()
            .bind(lambda _: self._write_main_files())
            .bind(lambda _: self._write_sub_spec_files())
            .bind(lambda _: self._write_history_v001())
            .bind(lambda _: self._write_seed_auto_capture())
            .map(lambda _: self._project_root)
        )

    def _write_livespec_jsonc(self) -> IOResult[None, LivespecError]:
        content = (
            "{\n"
            "  // Active template (built-in name or path).\n"
            '  // Default: "livespec"\n'
            f'  "template": "{self._payload.template}",\n'
            "\n"
            "  // Expected template format version.\n"
            "  // Default: 1\n"
            '  "template_format_version": 1,\n'
            "\n"
            "  // Skip post-step LLM-driven objective checks. Default: false\n"
            '  "post_step_skip_doctor_llm_objective_checks": false,\n'
            "\n"
            "  // Skip post-step LLM-driven subjective checks. Default: false\n"
            '  "post_step_skip_doctor_llm_subjective_checks": false,\n'
            "\n"
            "  // Skip pre-step static checks (emergency-recovery only). Default: false\n"
            '  "pre_step_skip_static_checks": false\n'
            "}\n"
        )
        return write_text(path=self._project_root / _LIVESPEC_JSONC, content=content)

    def _write_main_files(self) -> IOResult[None, LivespecError]:
        return self._walk_writes(
            entries=[(e.path, e.content) for e in self._payload.files],
            index=0,
        )

    def _write_sub_spec_files(self) -> IOResult[None, LivespecError]:
        entries: list[tuple[str, str]] = []
        for sub in self._payload.sub_specs:
            entries.extend((e.path, e.content) for e in sub.files)
        return self._walk_writes(entries=entries, index=0)

    def _walk_writes(
        self,
        *,
        entries: list[tuple[str, str]],
        index: int,
    ) -> IOResult[None, LivespecError]:
        if index >= len(entries):
            return IOSuccess(None)
        rel_path, content = entries[index]
        target = self._project_root / rel_path
        return (
            mkdir_p(path=target.parent)
            .bind(
                lambda _: write_text(path=target, content=content),
            )
            .bind(lambda _: self._walk_writes(entries=entries, index=index + 1))
        )

    def _write_history_v001(self) -> IOResult[None, LivespecError]:
        return self._walk_history_writes(spec_roots=self._enumerate_spec_roots(), index=0)

    def _enumerate_spec_roots(self) -> list[tuple[Path, list[tuple[str, str]]]]:
        main_files = [(e.path, e.content) for e in self._payload.files]
        result: list[tuple[Path, list[tuple[str, str]]]] = [(self._derive_spec_root(), main_files)]
        for sub in self._payload.sub_specs:
            sub_root = self._project_root / "SPECIFICATION" / "templates" / sub.template_name
            result.append((sub_root, [(e.path, e.content) for e in sub.files]))
        return result

    def _derive_spec_root(self) -> Path:
        """Phase 3 minimum-viable per-template hard-coding (Phase 7 widens via template_config)."""
        if self._payload.template == "minimal":
            return self._project_root
        return self._project_root / "SPECIFICATION"

    def _walk_history_writes(
        self,
        *,
        spec_roots: list[tuple[Path, list[tuple[str, str]]]],
        index: int,
    ) -> IOResult[None, LivespecError]:
        if index >= len(spec_roots):
            return IOSuccess(None)
        spec_root_abs, files = spec_roots[index]
        return self._materialize_one_history(spec_root_abs=spec_root_abs, files=files).bind(
            lambda _: self._walk_history_writes(spec_roots=spec_roots, index=index + 1),
        )

    def _materialize_one_history(
        self,
        *,
        spec_root_abs: Path,
        files: list[tuple[str, str]],
    ) -> IOResult[None, LivespecError]:
        history_v001 = spec_root_abs / "history" / "v001"
        return (
            mkdir_p(path=history_v001 / "proposed_changes")
            .bind(
                lambda _: mkdir_p(path=spec_root_abs / "proposed_changes"),
            )
            .bind(
                lambda _: self._walk_history_file_writes(
                    files=files,
                    index=0,
                    history_v001=history_v001,
                ),
            )
        )

    def _walk_history_file_writes(
        self,
        *,
        files: list[tuple[str, str]],
        index: int,
        history_v001: Path,
    ) -> IOResult[None, LivespecError]:
        if index >= len(files):
            return IOSuccess(None)
        rel_path, content = files[index]
        target = history_v001 / Path(rel_path).name
        return write_text(path=target, content=content).bind(
            lambda _: self._walk_history_file_writes(
                files=files,
                index=index + 1,
                history_v001=history_v001,
            ),
        )

    def _write_seed_auto_capture(self) -> IOResult[None, LivespecError]:
        payload = self._payload
        pc_dir = self._derive_spec_root() / "history" / "v001" / "proposed_changes"
        timestamp = now_iso()
        return (
            get_git_user(project_root=self._project_root)
            .bind(
                lambda git_user: write_seed_pair(
                    payload=payload,
                    pc_dir=pc_dir,
                    timestamp=timestamp,
                    git_user=git_user,
                ),
            )
            .lash(
                lambda _err: write_seed_pair(
                    payload=payload,
                    pc_dir=pc_dir,
                    timestamp=timestamp,
                    git_user=GIT_USER_UNKNOWN,
                ),
            )
        )


def run(*, argv: Sequence[str]) -> IOResult[Path, LivespecError]:
    """Module-level entry: instantiate SeedPipeline and dispatch."""
    return SeedPipeline().run(argv=argv)


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
                    "seed failed",
                    error_type=type(err).__name__,
                    error_message=str(err),
                )
                return type(err).exit_code
            case _:
                assert_never(inner)
    except Exception as exc:
        log.exception(
            "seed internal error",
            exception_type=type(exc).__name__,
            exception_repr=repr(exc),
        )
        return 1
