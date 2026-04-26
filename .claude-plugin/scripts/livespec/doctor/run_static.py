"""Static-phase doctor supervisor.

Per PROPOSAL §"Static-phase structure" lines 2483-2598 + v014 N3
bootstrap lenience + v018 Q1 per-tree iteration (applicability
dispatch finalized in v021 Q1).

The supervisor:

1. Resolves `--project-root` (default cwd).
2. Loads `.livespec.jsonc` with bootstrap lenience: builds
   DoctorContext with sentinel `config_load_status` even when
   the config is absent/malformed/schema-invalid, so
   `livespec_jsonc_valid` can run and emit a fail Finding (per
   K10 fail-Finding discipline).
3. Resolves the active template (with similar lenience for
   `template_load_status`).
4. Enumerates `(spec_root, template_name)` pairs: the main spec
   tree first (template_name="main"), then each sub-spec tree
   under `<main-spec-root>/templates/<sub-name>/` discovered via
   directory listing.
5. For each pair, builds a per-tree DoctorContext and runs the
   applicable check subset per the orchestrator-owned
   applicability table:
   - `template_exists`, `template_files_present`: only when
     `template_name == "main"` (sub-spec trees aren't templates).
   - `gherkin_blank_line_format`: not registered in Phase 3
     (Phase 7 lands the implementation + applicability rule).
   - All other checks: uniform across all trees.
6. Composes all findings into a single DoctorFindings payload.
   Domain failures from check bodies → IOFailure short-circuits
   (a check encountered an unrecoverable I/O error); Findings
   (pass / fail / skipped) flow through as IOSuccess values.
7. Emits `{"findings": [...]}` JSON to stdout (one of three
   places where direct stdout write is permitted per the style
   doc exemption list).
8. Exits 3 if any fail Finding, 0 otherwise; 1 on bug; 127 on
   too-old Python (handled by `_bootstrap.py` upstream).

Phase 3 minimum-viable: hardcoded mapping for the v1 built-in
templates (livespec → SPECIFICATION/, minimal → repo root).
Phase 7 widens to read template_config's spec_root field.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from returns.io import IOResult, IOSuccess
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.context import DoctorContext
from livespec.doctor.static import CHECKS
from livespec.errors import (
    HelpRequested,
    LivespecError,
)
from livespec.io.cli import parse_args
from livespec.io.fastjsonschema_facade import compile_schema
from livespec.io.fs import find_upward, list_dir, path_exists, read_text
from livespec.io.structlog_facade import get_logger
from livespec.parse.jsonc import parse as parse_jsonc
from livespec.schemas.dataclasses.doctor_findings import DoctorFindings
from livespec.schemas.dataclasses.finding import Finding
from livespec.schemas.dataclasses.livespec_config import LivespecConfig
from livespec.types import CheckId, RunId, SpecRoot, TemplateName
from livespec.validate import livespec_config as validate_livespec_config

__all__: list[str] = [
    "build_parser",
    "main",
    "run",
]


_LIVESPEC_JSONC = ".livespec.jsonc"
_VNNN_RE = re.compile(r"^v\d+$")
_BUILT_IN_TEMPLATES = frozenset({"livespec", "minimal"})

LoadStatus = Literal["ok", "absent", "malformed", "schema_invalid"]


@dataclass(frozen=True, kw_only=True, slots=True)
class _ConfigResolution:
    """Result of `.livespec.jsonc` lookup with bootstrap lenience.

    `config` is the parsed LivespecConfig when status=="ok"; for
    other statuses a sentinel default-constructed config carries the
    fallback values. `status` records the actual lookup outcome so
    `livespec_jsonc_valid` can report the correct Finding."""

    config: LivespecConfig
    status: LoadStatus


@dataclass(frozen=True, kw_only=True, slots=True)
class _TemplateResolution:
    """Result of template-path lookup with bootstrap lenience.

    `root` is the resolved template directory when status=="ok"; for
    other statuses a sentinel placeholder carries a path the
    orchestrator can still pass into per-tree DoctorContexts."""

    root: Path
    status: LoadStatus


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="livespec doctor-static",
        description="Run the static-phase doctor checks; emit findings JSON to stdout.",
        exit_on_error=False,
    )
    parser.add_argument(
        "--project-root",
        dest="project_root",
        type=Path,
        default=None,
        help="Project root for .livespec.jsonc lookup (default: cwd).",
    )
    return parser


def _bundle_root() -> Path:
    """Return `.claude-plugin/` per v028 D1."""
    return Path(__file__).resolve().parents[3]


def _schema_path(*, name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "schemas" / f"{name}.schema.json"


def _spec_root_for_template(*, template: str, project_root: Path) -> Path:
    """Phase 3 minimum-viable mapping (matches commands/seed.py and friends)."""
    if template == "minimal":
        return project_root
    return project_root / "SPECIFICATION"


def _template_root_for_value(*, template: str, project_root: Path) -> Path:
    if template in _BUILT_IN_TEMPLATES:
        return _bundle_root() / "specification-templates" / template
    return (project_root / template).resolve()


def run(*, argv: Sequence[str]) -> IOResult[DoctorFindings, LivespecError]:
    """Railway: parse argv → resolve config + template → iterate trees → collect findings."""
    parser = build_parser()
    return parse_args(parser=parser, argv=argv).bind(_orchestrate)


def _orchestrate(
    namespace: argparse.Namespace,
) -> IOResult[DoctorFindings, LivespecError]:
    project_root: Path = (
        namespace.project_root
        if namespace.project_root is not None
        else Path.cwd()
    )
    return _resolve_config(project_root=project_root).bind(
        lambda config_res: _resolve_template_then_iterate(
            project_root=project_root,
            config_res=config_res,
        ),
    )


def _resolve_config(
    *,
    project_root: Path,
) -> IOResult[_ConfigResolution, LivespecError]:
    """Bootstrap lenience: returns a _ConfigResolution even when the file is absent/malformed."""
    return find_upward(start=project_root, name=_LIVESPEC_JSONC).bind(
        lambda jsonc_path: read_text(path=jsonc_path),
    ).bind(_parse_then_validate_config).lash(
        lambda _err: IOSuccess(_default_config_resolution(status="absent")),
    )


def _default_config_resolution(*, status: LoadStatus) -> _ConfigResolution:
    return _ConfigResolution(
        config=LivespecConfig(),
        status=status,
    )


def _parse_then_validate_config(
    text: str,
) -> IOResult[_ConfigResolution, LivespecError]:
    parsed = parse_jsonc(text=text)
    match parsed:
        case Failure(_):
            return IOSuccess(_default_config_resolution(status="malformed"))
        case Success(jsonc_dict):
            return _validate_config_dict(jsonc_dict=jsonc_dict)
        case _:
            assert_never(parsed)


def _validate_config_dict(
    *,
    jsonc_dict: dict[str, Any],
) -> IOResult[_ConfigResolution, LivespecError]:
    return read_text(path=_schema_path(name="livespec_config")).bind(
        lambda schema_text: _run_config_validator(
            schema_text=schema_text,
            jsonc_dict=jsonc_dict,
        ),
    )


def _run_config_validator(
    *,
    schema_text: str,
    jsonc_dict: dict[str, Any],
) -> IOResult[_ConfigResolution, LivespecError]:
    schema_parsed = parse_jsonc(text=schema_text)
    match schema_parsed:
        case Failure(_):
            return IOSuccess(_default_config_resolution(status="schema_invalid"))
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
                case Failure(_):
                    return IOSuccess(_default_config_resolution(status="schema_invalid"))
                case Success(config):
                    return IOSuccess(_ConfigResolution(config=config, status="ok"))
                case _:
                    assert_never(validated)
        case _:
            assert_never(schema_parsed)


def _resolve_template_then_iterate(
    *,
    project_root: Path,
    config_res: _ConfigResolution,
) -> IOResult[DoctorFindings, LivespecError]:
    template_root = _template_root_for_value(
        template=config_res.config.template,
        project_root=project_root,
    )
    return path_exists(path=template_root).bind(
        lambda exists: _check_template_status(
            template_root=template_root,
            exists=exists,
        ),
    ).bind(
        lambda template_res: _iterate_trees(
            project_root=project_root,
            config_res=config_res,
            template_res=template_res,
        ),
    )


def _check_template_status(
    *,
    template_root: Path,
    exists: bool,
) -> IOResult[_TemplateResolution, LivespecError]:
    if not exists:
        return IOSuccess(_TemplateResolution(root=template_root, status="absent"))
    template_json = template_root / "template.json"
    return path_exists(path=template_json).map(
        lambda has_json: _TemplateResolution(
            root=template_root,
            status="ok" if has_json else "malformed",
        ),
    )


def _iterate_trees(
    *,
    project_root: Path,
    config_res: _ConfigResolution,
    template_res: _TemplateResolution,
) -> IOResult[DoctorFindings, LivespecError]:
    main_spec_root = _spec_root_for_template(
        template=config_res.config.template,
        project_root=project_root,
    )
    run_id = RunId(str(uuid.uuid4()))
    main_ctx = _build_doctor_context(
        project_root=project_root,
        spec_root=main_spec_root,
        config_res=config_res,
        template_res=template_res,
        template_name="main",
        run_id=run_id,
    )
    return _list_sub_spec_trees(main_spec_root=main_spec_root).bind(
        lambda sub_specs: _run_all_trees(
            main_ctx=main_ctx,
            sub_specs=sub_specs,
            project_root=project_root,
            config_res=config_res,
            template_res=template_res,
            run_id=run_id,
        ),
    )


def _list_sub_spec_trees(
    *,
    main_spec_root: Path,
) -> IOResult[list[tuple[Path, str]], LivespecError]:
    """Discover sub-spec trees under <main_spec_root>/templates/<name>/."""
    templates_dir = main_spec_root / "templates"
    return path_exists(path=templates_dir).bind(
        lambda exists: _list_or_empty_subspecs(
            templates_dir=templates_dir,
            exists=exists,
        ),
    )


def _list_or_empty_subspecs(
    *,
    templates_dir: Path,
    exists: bool,
) -> IOResult[list[tuple[Path, str]], LivespecError]:
    if not exists:
        return IOSuccess([])
    return list_dir(path=templates_dir).map(_filter_sub_specs)


def _filter_sub_specs(entries: list[Path]) -> list[tuple[Path, str]]:
    """Keep directories only; pair each with its template-name (the directory name)."""
    return [(entry, entry.name) for entry in entries if entry.is_dir()]


@dataclass(frozen=True, kw_only=True, slots=True)
class _OrchestrationContext:
    """Per-invocation state bundle (passed through the per-tree fold)."""

    project_root: Path
    config_res: _ConfigResolution
    template_res: _TemplateResolution
    run_id: RunId


def _run_all_trees(
    *,
    main_ctx: DoctorContext,
    sub_specs: list[tuple[Path, str]],
    project_root: Path,
    config_res: _ConfigResolution,
    template_res: _TemplateResolution,
    run_id: RunId,
) -> IOResult[DoctorFindings, LivespecError]:
    """Run checks for the main tree, then each sub-spec tree; accumulate Findings."""
    orch_ctx = _OrchestrationContext(
        project_root=project_root,
        config_res=config_res,
        template_res=template_res,
        run_id=run_id,
    )
    return _run_checks_for_tree(ctx=main_ctx).bind(
        lambda main_findings: _walk_sub_specs(
            findings_so_far=main_findings,
            sub_specs=sub_specs,
            index=0,
            orch_ctx=orch_ctx,
        ),
    ).map(lambda findings: DoctorFindings(findings=findings))


def _walk_sub_specs(
    *,
    findings_so_far: list[Finding],
    sub_specs: list[tuple[Path, str]],
    index: int,
    orch_ctx: _OrchestrationContext,
) -> IOResult[list[Finding], LivespecError]:
    if index >= len(sub_specs):
        return IOSuccess(findings_so_far)
    sub_root, sub_name = sub_specs[index]
    sub_ctx = _build_doctor_context(
        project_root=orch_ctx.project_root,
        spec_root=sub_root,
        config_res=orch_ctx.config_res,
        template_res=orch_ctx.template_res,
        template_name=sub_name,
        run_id=orch_ctx.run_id,
    )
    return _run_checks_for_tree(ctx=sub_ctx).bind(
        lambda new_findings: _walk_sub_specs(
            findings_so_far=findings_so_far + new_findings,
            sub_specs=sub_specs,
            index=index + 1,
            orch_ctx=orch_ctx,
        ),
    )


def _build_doctor_context(
    *,
    project_root: Path,
    spec_root: Path,
    config_res: _ConfigResolution,
    template_res: _TemplateResolution,
    template_name: str,
    run_id: RunId,
) -> DoctorContext:
    return DoctorContext(
        project_root=project_root,
        spec_root=SpecRoot(spec_root),
        config=config_res.config,
        config_load_status=config_res.status,
        template_root=template_res.root,
        template_load_status=template_res.status,
        template_name=template_name,
        run_id=run_id,
        git_head_available=False,
    )


def _is_check_applicable(*, slug: CheckId, template_name: str) -> bool:
    """Orchestrator-owned applicability table per v021 Q1.

    Phase 3 implemented checks:
    - doctor-template-exists / doctor-template-files-present:
      template_name == "main" only
    - All others: uniform across all trees
    """
    main_only = (
        CheckId("doctor-template-exists"),
        CheckId("doctor-template-files-present"),
    )
    if slug in main_only:
        return template_name == "main"
    return True


def _run_checks_for_tree(
    *,
    ctx: DoctorContext,
) -> IOResult[list[Finding], LivespecError]:
    """Run every applicable check for one (spec_root, template_name) pair."""
    return _walk_checks(
        ctx=ctx,
        index=0,
        accumulated=[],
    )


def _walk_checks(
    *,
    ctx: DoctorContext,
    index: int,
    accumulated: list[Finding],
) -> IOResult[list[Finding], LivespecError]:
    if index >= len(CHECKS):
        return IOSuccess(accumulated)
    slug, run_fn = CHECKS[index]
    if not _is_check_applicable(slug=slug, template_name=ctx.template_name):
        return _walk_checks(
            ctx=ctx,
            index=index + 1,
            accumulated=accumulated,
        )
    return run_fn(ctx=ctx).bind(
        lambda finding: _walk_checks(
            ctx=ctx,
            index=index + 1,
            accumulated=[*accumulated, cast("Finding", finding)],
        ),
    )


def _findings_to_json(*, doctor_findings: DoctorFindings) -> str:
    """Render the {findings: [...]} stdout payload."""
    payload = {
        "findings": [
            {
                "check_id": str(finding.check_id),
                "status": finding.status,
                "message": finding.message,
                "path": finding.path,
                "line": finding.line,
                "spec_root": finding.spec_root,
            }
            for finding in doctor_findings.findings
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def _has_fail_finding(*, doctor_findings: DoctorFindings) -> bool:
    return any(f.status == "fail" for f in doctor_findings.findings)


def main(*, argv: Sequence[str] | None = None) -> int:
    """Supervisor: bug-catcher + railway dispatch inline (sys.stdout.write
    exemption per style doc lines 1474-1481 is per-`main()`, NOT per-helper)."""
    log = get_logger(name=__name__)
    actual_argv: Sequence[str] = list(argv) if argv is not None else sys.argv[1:]
    try:
        result = run(argv=actual_argv)
        inner = unsafe_perform_io(result)
        match inner:
            case Success(doctor_findings):
                sys.stdout.write(_findings_to_json(doctor_findings=doctor_findings))
                return 3 if _has_fail_finding(doctor_findings=doctor_findings) else 0
            case Failure(HelpRequested(text=text)):
                sys.stdout.write(text)
                return 0
            case Failure(err):
                log.error(
                    "doctor-static failed",
                    error_type=type(err).__name__,
                    error_message=str(err),
                )
                return type(err).exit_code
            case _:
                assert_never(inner)
    except Exception as exc:
        log.exception(
            "doctor-static internal error",
            exception_type=type(exc).__name__,
            exception_repr=repr(exc),
        )
        return 1



# `_VNNN_RE` is exported for downstream use by the few callers that need
# to enumerate version directories the same way the orchestrator does.
_ = _VNNN_RE
# `TemplateName` is referenced indirectly via the LivespecConfig.template
# field type; this marker keeps the import live for future widening.
_2 = TemplateName
