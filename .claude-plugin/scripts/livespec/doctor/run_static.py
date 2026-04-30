"""Doctor static-phase orchestrator.

Per PROPOSAL.md §"`doctor`" (line ~2468) and Plan Phase 3 (lines
1554-1616): the orchestrator enumerates (spec_root,
template_name) pairs at startup; per pair it builds a per-tree
DoctorContext and runs the applicable check subset decided by
the orchestrator-owned applicability table.

Phase-3 minimum subset registers 8 implemented checks per Plan
line 1596-1602 (livespec_jsonc_valid, template_exists,
template_files_present, proposed_changes_and_history_dirs,
version_directories_complete, version_contiguity,
revision_to_proposed_change_pairing,
proposed_change_topic_format). Cycle 142 lands the
single-tree dispatch pathway: parse --project-root, build one
DoctorContext (spec_root defaults to <project_root>/SPECIFICATION),
iterate every member of STATIC_CHECKS, collect Findings, emit
the canonical {"findings": [...]} JSON payload to stdout, and
derive exit code from the aggregated statuses (0 = all pass,
3 = at least one fail).

Multi-tree enumeration (sub-spec trees + applicability table)
lands in subsequent cycles under outside-in pressure.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.context import DoctorContext
from livespec.doctor.static import STATIC_CHECKS
from livespec.errors import LivespecError
from livespec.io import cli
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    """Construct the doctor-static argparse parser without parsing.

    Phase-3 minimum: accepts only --project-root. The
    `exit_on_error=False` mirrors the rest of the project's
    parsers per style doc §"CLI argument parsing seam".
    """
    parser = argparse.ArgumentParser(prog="doctor-static", exit_on_error=False)
    _ = parser.add_argument("--project-root", default=None)
    return parser


def _resolve_project_root(*, namespace: argparse.Namespace) -> Path:
    """Resolve --project-root to a Path, defaulting to Path.cwd()."""
    if namespace.project_root is None:
        return Path.cwd()
    return Path(namespace.project_root)


def _run_one_check(*, ctx: DoctorContext, module: Any) -> Finding:
    """Invoke a single registered check module's run(ctx) and unwrap to Finding.

    Per static/CLAUDE.md the per-check railway is
    `IOResult[Finding, LivespecError]`. The orchestrator
    consumes the IOResult by pattern-matching: Success wraps
    the Finding directly; Failure wraps a LivespecError that
    represents a check-process bug (cycle 142 maps that to a
    fail-status Finding so the JSON output remains uniform).
    """
    io_result: IOResult[Finding, LivespecError] = module.run(ctx=ctx)
    unwrapped = unsafe_perform_io(io_result)
    match unwrapped:
        case Success(finding):
            return finding
        case Failure(LivespecError() as err):
            return Finding(
                check_id=module.SLUG,
                status="fail",
                message=f"check process error: {err}",
                path=None,
                line=None,
                spec_root=str(ctx.spec_root),
            )
        case _:
            assert_never(unwrapped)


def _emit_findings_json(*, findings: list[Finding]) -> None:
    """Write the canonical `{"findings": [...]}` JSON payload to stdout.

    One of three places in the codebase where `sys.stdout.write`
    is permitted (per python-skill-script-style-requirements.md
    §"Logging" exemption list — the supervisor's documented
    stdout contract). Each Finding is serialized as a dict via
    dataclasses.asdict.
    """
    payload = {"findings": [dataclasses.asdict(finding) for finding in findings]}
    _ = sys.stdout.write(json.dumps(payload) + "\n")


def _derive_exit_code(*, findings: list[Finding]) -> int:
    """Derive the supervisor exit code from aggregated finding statuses.

    Per PROPOSAL.md §"`doctor` → Static-phase output contract":
    no findings or every finding pass => exit 0; at least one
    fail => exit 3. The skipped status is treated as pass for
    exit-code derivation.
    """
    if any(finding.status == "fail" for finding in findings):
        return 3
    return 0


def _orchestrate(*, namespace: argparse.Namespace) -> int:
    """Run the per-check dispatch pathway against the resolved spec_root.

    Cycle 142 lands the single-tree pathway: derive
    project_root from --project-root, default spec_root to
    <project_root>/SPECIFICATION, iterate STATIC_CHECKS, emit
    the JSON payload, and derive the exit code.
    """
    project_root = _resolve_project_root(namespace=namespace)
    spec_root = project_root / "SPECIFICATION"
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    findings = [_run_one_check(ctx=ctx, module=module) for module in STATIC_CHECKS]
    _emit_findings_json(findings=findings)
    return _derive_exit_code(findings=findings)


def main(*, argv: list[str] | None = None) -> int:
    """Doctor static-phase supervisor entry point. Returns the process exit code.

    Threads argv through the parser, then dispatches the
    per-check pathway. UsageError (parse) -> exit 2 via
    err.exit_code; success path -> 0 if all checks pass, 3 if
    any fail.
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
    unwrapped = unsafe_perform_io(parse_result)
    match unwrapped:
        case Success(namespace):
            return _orchestrate(namespace=namespace)
        case Failure(LivespecError() as err):
            return err.exit_code
        case _:
            assert_never(unwrapped)
