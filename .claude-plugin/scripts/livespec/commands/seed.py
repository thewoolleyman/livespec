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
   under the main spec's `history/v001/proposed_changes/`.

Seed is exempt from pre-step doctor-static; post-step runs after
the wrapper exits (orchestrated by `seed/SKILL.md` prose).

Phase 3 minimum-viable scope: implements the contract above
faithfully, with `--project-root` defaulting to `Path.cwd()`. Spec
root is derived from `.livespec.jsonc`'s template field via the
same `resolve_template` logic; for the v1 built-ins, spec root is
`SPECIFICATION/` (livespec) or the repo root (minimal). Phase 7
widens with deeper validation, atomic-rollback on partial-write
failure, and richer auto-capture content.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from returns.io import IOFailure, IOResult, IOSuccess
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

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
from livespec.validate import livespec_config as validate_livespec_config
from livespec.validate import seed_input as validate_seed_input

__all__: list[str] = [
    "build_parser",
    "main",
    "run",
]


_LIVESPEC_JSONC = ".livespec.jsonc"
_SEED_AUTHOR = "livespec-seed"
_SEED_TOPIC = "seed"


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


def _now_iso() -> str:
    """UTC ISO-8601 to seconds (no microseconds), with Z suffix."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(*, argv: Sequence[str]) -> IOResult[Path, LivespecError]:
    """Railway entry: parse argv → run the file-shaping chain → return project_root."""
    parser = build_parser()
    return parse_args(parser=parser, argv=argv).bind(_orchestrate)


def _orchestrate(namespace: argparse.Namespace) -> IOResult[Path, LivespecError]:
    """Top-level composition for the seed file-shaping pipeline."""
    project_root: Path = (
        namespace.project_root
        if namespace.project_root is not None
        else Path.cwd()
    )
    seed_json_path: Path = namespace.seed_json
    return (
        read_text(path=seed_json_path)
        .bind(_parse_and_validate_seed)
        .bind(lambda payload: _check_jsonc_state_then_write(
            payload=payload,
            project_root=project_root,
        ))
    )


def _parse_and_validate_seed(text: str) -> IOResult[SeedInput, LivespecError]:
    """Parse seed-json text → validate against seed_input.schema.json → SeedInput."""
    parsed = parse_jsonc(text=text)
    match parsed:
        case Failure(err):
            return IOFailure(err)
        case Success(payload):
            return _validate_seed_payload(payload=payload)
        case _:
            assert_never(parsed)


def _validate_seed_payload(
    *,
    payload: dict[str, Any],
) -> IOResult[SeedInput, LivespecError]:
    return read_text(path=_schema_path(name="seed_input")).bind(
        lambda schema_text: _compile_seed_validator_and_run(
            schema_text=schema_text,
            payload=payload,
        ),
    )


def _compile_seed_validator_and_run(
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
            validator = validate_seed_input.make_validator(
                fast_validator=fast_validator,
            )
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


def _check_jsonc_state_then_write(
    *,
    payload: SeedInput,
    project_root: Path,
) -> IOResult[Path, LivespecError]:
    """Pre-seed `.livespec.jsonc` state (v016 P2 + v017 Q5/Q6) → idempotency → shape."""
    jsonc_path = project_root / _LIVESPEC_JSONC
    return path_exists(path=jsonc_path).bind(
        lambda exists: _resolve_jsonc_branch(
            jsonc_present=exists,
            jsonc_path=jsonc_path,
            payload=payload,
            project_root=project_root,
        ),
    )


def _resolve_jsonc_branch(
    *,
    jsonc_present: bool,
    jsonc_path: Path,
    payload: SeedInput,
    project_root: Path,
) -> IOResult[Path, LivespecError]:
    if not jsonc_present:
        return _idempotency_check_then_shape(
            payload=payload,
            project_root=project_root,
        )
    return read_text(path=jsonc_path).bind(
        lambda jsonc_text: _verify_existing_jsonc(
            jsonc_text=jsonc_text,
            payload=payload,
            project_root=project_root,
        ),
    )


def _verify_existing_jsonc(
    *,
    jsonc_text: str,
    payload: SeedInput,
    project_root: Path,
) -> IOResult[Path, LivespecError]:
    """Present-and-valid branch (v017 Q5/Q6): parse + schema-validate; fail on mismatch."""
    parsed = parse_jsonc(text=jsonc_text)
    match parsed:
        case Failure(err):
            return IOFailure(err)
        case Success(jsonc_dict):
            return read_text(path=_schema_path(name="livespec_config")).bind(
                lambda schema_text: _validate_existing_jsonc(
                    jsonc_dict=jsonc_dict,
                    schema_text=schema_text,
                    payload=payload,
                    project_root=project_root,
                ),
            )
        case _:
            assert_never(parsed)


def _validate_existing_jsonc(
    *,
    jsonc_dict: dict[str, Any],
    schema_text: str,
    payload: SeedInput,
    project_root: Path,
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
            validator = validate_livespec_config.make_validator(
                fast_validator=fast_validator,
            )
            validated = validator(payload=jsonc_dict)
            match validated:
                case Failure(err):
                    return IOFailure(err)
                case Success(config):
                    if config.template != payload.template:
                        return IOFailure(
                            PreconditionError(
                                f"existing .livespec.jsonc template={config.template!r} "
                                f"does not match seed payload template={payload.template!r}",
                            ),
                        )
                    return _idempotency_check_then_shape(
                        payload=payload,
                        project_root=project_root,
                    )
                case _:
                    assert_never(validated)
        case _:
            assert_never(schema_parsed)


def _idempotency_check_then_shape(
    *,
    payload: SeedInput,
    project_root: Path,
) -> IOResult[Path, LivespecError]:
    """Verify no payload-target file already exists, then run file-shaping."""
    return _check_no_targets_exist(
        payload=payload,
        project_root=project_root,
    ).bind(
        lambda _: _shape_files(
            payload=payload,
            project_root=project_root,
        ),
    )


def _check_no_targets_exist(
    *,
    payload: SeedInput,
    project_root: Path,
) -> IOResult[None, LivespecError]:
    """Sequentially check each target path; fail at first existing one.

    Phase 3 minimum-viable: stops at the first existing file rather
    than gathering and reporting the full list. PROPOSAL line
    2065-2069 prescribes the full-list reporting; Phase 7 widens
    this to the multi-finding form.
    """
    targets = [project_root / entry.path for entry in payload.files]
    for sub in payload.sub_specs:
        targets.extend(project_root / entry.path for entry in sub.files)
    return _walk_target_existence(targets=targets, index=0)


def _walk_target_existence(
    *,
    targets: list[Path],
    index: int,
) -> IOResult[None, LivespecError]:
    if index >= len(targets):
        return IOSuccess(None)
    candidate = targets[index]
    return path_exists(path=candidate).bind(
        lambda exists: (
            IOFailure(
                PreconditionError(
                    f"seed target file already exists: {candidate}; "
                    f"refusing to overwrite. Run `livespec doctor` to diagnose.",
                ),
            )
            if exists
            else _walk_target_existence(targets=targets, index=index + 1)
        ),
    )


def _shape_files(
    *,
    payload: SeedInput,
    project_root: Path,
) -> IOResult[Path, LivespecError]:
    """Write `.livespec.jsonc` + main files + sub-spec files + history/v001/ + auto-capture."""
    return (
        _write_livespec_jsonc(payload=payload, project_root=project_root)
        .bind(lambda _: _write_main_files(payload=payload, project_root=project_root))
        .bind(lambda _: _write_sub_spec_files(payload=payload, project_root=project_root))
        .bind(lambda _: _write_history_v001(payload=payload, project_root=project_root))
        .bind(lambda _: _write_seed_auto_capture(payload=payload, project_root=project_root))
        .map(lambda _: project_root)
    )


def _write_livespec_jsonc(
    *,
    payload: SeedInput,
    project_root: Path,
) -> IOResult[None, LivespecError]:
    """Write `.livespec.jsonc` with the payload's template field, all defaults inline."""
    content = (
        '{\n'
        '  // Active template (built-in name or path).\n'
        '  // Default: "livespec"\n'
        f'  "template": "{payload.template}",\n'
        '\n'
        '  // Expected template format version.\n'
        '  // Default: 1\n'
        '  "template_format_version": 1,\n'
        '\n'
        '  // Skip post-step LLM-driven objective checks. Default: false\n'
        '  "post_step_skip_doctor_llm_objective_checks": false,\n'
        '\n'
        '  // Skip post-step LLM-driven subjective checks. Default: false\n'
        '  "post_step_skip_doctor_llm_subjective_checks": false,\n'
        '\n'
        '  // Skip pre-step static checks (emergency-recovery only). Default: false\n'
        '  "pre_step_skip_static_checks": false\n'
        '}\n'
    )
    return write_text(path=project_root / _LIVESPEC_JSONC, content=content)


def _write_main_files(
    *,
    payload: SeedInput,
    project_root: Path,
) -> IOResult[None, LivespecError]:
    """Write each main-spec files[] entry. Creates parent dirs as needed."""
    return _write_file_list(entries_with_path_content=[
        (entry.path, entry.content) for entry in payload.files
    ], project_root=project_root)


def _write_sub_spec_files(
    *,
    payload: SeedInput,
    project_root: Path,
) -> IOResult[None, LivespecError]:
    entries: list[tuple[str, str]] = []
    for sub in payload.sub_specs:
        entries.extend((entry.path, entry.content) for entry in sub.files)
    return _write_file_list(
        entries_with_path_content=entries,
        project_root=project_root,
    )


def _write_file_list(
    *,
    entries_with_path_content: list[tuple[str, str]],
    project_root: Path,
) -> IOResult[None, LivespecError]:
    return _walk_writes(
        entries=entries_with_path_content,
        index=0,
        project_root=project_root,
    )


def _walk_writes(
    *,
    entries: list[tuple[str, str]],
    index: int,
    project_root: Path,
) -> IOResult[None, LivespecError]:
    if index >= len(entries):
        return IOSuccess(None)
    rel_path, content = entries[index]
    target = project_root / rel_path
    return mkdir_p(path=target.parent).bind(
        lambda _: write_text(path=target, content=content),
    ).bind(
        lambda _: _walk_writes(
            entries=entries,
            index=index + 1,
            project_root=project_root,
        ),
    )


def _write_history_v001(
    *,
    payload: SeedInput,
    project_root: Path,
) -> IOResult[None, LivespecError]:
    """Materialize history/v001/ for main spec + each sub-spec tree.

    Phase 3 minimum-viable: copies the just-written spec-file content
    into history/v001/ at the same relative path under each tree's
    history/v001/ subdir, plus creates an empty proposed_changes/
    subdir on each tree. Per-version README is omitted in this
    minimum-viable scope; the seed auto-capture covers the v001
    audit trail through seed.md / seed-revision.md (next step).
    """
    spec_roots = _enumerate_spec_roots(payload=payload, project_root=project_root)
    return _walk_history_writes(
        payload=payload,
        spec_roots=spec_roots,
        index=0,
        project_root=project_root,
    )


def _enumerate_spec_roots(
    *,
    payload: SeedInput,
    project_root: Path,
) -> list[tuple[Path, list[tuple[str, str]]]]:
    """Return [(spec_root_abs, [(rel_path, content), ...]), ...] for main + each sub-spec."""
    main_files: list[tuple[str, str]] = [
        (entry.path, entry.content) for entry in payload.files
    ]
    main_root = _derive_spec_root(payload=payload, project_root=project_root)
    result: list[tuple[Path, list[tuple[str, str]]]] = [(main_root, main_files)]
    for sub in payload.sub_specs:
        sub_root = project_root / "SPECIFICATION" / "templates" / sub.template_name
        sub_files = [(entry.path, entry.content) for entry in sub.files]
        result.append((sub_root, sub_files))
    return result


def _derive_spec_root(
    *,
    payload: SeedInput,
    project_root: Path,
) -> Path:
    """Phase 3 minimum-viable: hard-coded per built-in template.

    livespec → project_root / SPECIFICATION/
    minimal → project_root (single SPECIFICATION.md at repo root)
    other → project_root / SPECIFICATION/ (best-guess fallback)

    Phase 7 widens this to read template.json's `spec_root` field
    via resolve_template + parse + template_config validation.
    """
    if payload.template == "minimal":
        return project_root
    return project_root / "SPECIFICATION"


def _walk_history_writes(
    *,
    payload: SeedInput,
    spec_roots: list[tuple[Path, list[tuple[str, str]]]],
    index: int,
    project_root: Path,
) -> IOResult[None, LivespecError]:
    if index >= len(spec_roots):
        return IOSuccess(None)
    spec_root_abs, files = spec_roots[index]
    return _materialize_one_history(
        spec_root_abs=spec_root_abs,
        files=files,
        project_root=project_root,
    ).bind(
        lambda _: _walk_history_writes(
            payload=payload,
            spec_roots=spec_roots,
            index=index + 1,
            project_root=project_root,
        ),
    )


def _materialize_one_history(
    *,
    spec_root_abs: Path,
    files: list[tuple[str, str]],
    project_root: Path,
) -> IOResult[None, LivespecError]:
    """Create <spec_root>/history/v001/ + <spec_root>/proposed_changes/."""
    history_v001 = spec_root_abs / "history" / "v001"
    proposed_changes = spec_root_abs / "proposed_changes"
    return mkdir_p(path=history_v001 / "proposed_changes").bind(
        lambda _: mkdir_p(path=proposed_changes),
    ).bind(
        lambda _: _copy_files_to_history(
            files=files,
            history_v001=history_v001,
            project_root=project_root,
        ),
    )


def _copy_files_to_history(
    *,
    files: list[tuple[str, str]],
    history_v001: Path,
    project_root: Path,
) -> IOResult[None, LivespecError]:
    """Copy each file's content into history/v001/ at the same relative path-stem."""
    return _walk_history_file_writes(
        files=files,
        index=0,
        history_v001=history_v001,
        project_root=project_root,
    )


def _walk_history_file_writes(
    *,
    files: list[tuple[str, str]],
    index: int,
    history_v001: Path,
    project_root: Path,
) -> IOResult[None, LivespecError]:
    if index >= len(files):
        return IOSuccess(None)
    rel_path, content = files[index]
    file_name = Path(rel_path).name
    target = history_v001 / file_name
    return write_text(path=target, content=content).bind(
        lambda _: _walk_history_file_writes(
            files=files,
            index=index + 1,
            history_v001=history_v001,
            project_root=project_root,
        ),
    )


def _write_seed_auto_capture(
    *,
    payload: SeedInput,
    project_root: Path,
) -> IOResult[None, LivespecError]:
    """Write seed.md + seed-revision.md under history/v001/proposed_changes/."""
    main_root = _derive_spec_root(payload=payload, project_root=project_root)
    pc_dir = main_root / "history" / "v001" / "proposed_changes"
    seed_md = pc_dir / "seed.md"
    seed_revision_md = pc_dir / "seed-revision.md"
    timestamp = _now_iso()
    targets_block = "\n".join(f"- {entry.path}" for entry in payload.files)
    seed_md_content = (
        f"---\n"
        f"topic: {_SEED_TOPIC}\n"
        f"author: {_SEED_AUTHOR}\n"
        f"created_at: {timestamp}\n"
        f"---\n"
        f"\n"
        f"## Proposal: seed\n"
        f"\n"
        f"### Target specification files\n"
        f"\n"
        f"{targets_block}\n"
        f"\n"
        f"### Summary\n"
        f"\n"
        f"Initial seed of the specification from user-provided intent.\n"
        f"\n"
        f"### Motivation\n"
        f"\n"
        f"{payload.intent}\n"
        f"\n"
        f"### Proposed Changes\n"
        f"\n"
        f"{payload.intent}\n"
    )
    return get_git_user(project_root=project_root).bind(
        lambda git_user: _write_seed_files(
            seed_md=seed_md,
            seed_md_content=seed_md_content,
            seed_revision_md=seed_revision_md,
            timestamp=timestamp,
            git_user=git_user,
            payload=payload,
        ),
    ).lash(
        lambda _err: _write_seed_files(
            seed_md=seed_md,
            seed_md_content=seed_md_content,
            seed_revision_md=seed_revision_md,
            timestamp=timestamp,
            git_user=GIT_USER_UNKNOWN,
            payload=payload,
        ),
    )


def _write_seed_files(
    *,
    seed_md: Path,
    seed_md_content: str,
    seed_revision_md: Path,
    timestamp: str,
    git_user: str,
    payload: SeedInput,
) -> IOResult[None, LivespecError]:
    resulting_files_block = "\n".join(f"- {entry.path}" for entry in payload.files)
    seed_revision_content = (
        f"---\n"
        f"proposal: seed.md\n"
        f"decision: accept\n"
        f"revised_at: {timestamp}\n"
        f"author_human: {git_user}\n"
        f"author_llm: {_SEED_AUTHOR}\n"
        f"---\n"
        f"\n"
        f"## Decision and Rationale\n"
        f"\n"
        f"Auto-accepted during seed.\n"
        f"\n"
        f"## Resulting Changes\n"
        f"\n"
        f"{resulting_files_block}\n"
    )
    return write_text(path=seed_md, content=seed_md_content).bind(
        lambda _: write_text(path=seed_revision_md, content=seed_revision_content),
    )


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

