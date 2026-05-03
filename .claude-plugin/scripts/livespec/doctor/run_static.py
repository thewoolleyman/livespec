"""Doctor static-phase orchestrator.

Per PROPOSAL.md §"`doctor`" (line ~2468) and Plan Phase 3 (lines
1554-1616): the orchestrator enumerates (spec_root,
template_name) pairs at startup; per pair it builds a per-tree
DoctorContext and runs the applicable check subset decided by
the orchestrator-owned applicability table
(`APPLICABILITY_BY_TREE_KIND` in `static/__init__.py` per v022
D7).

Phase-3 minimum subset registers 8 implemented checks per Plan
line 1596-1602 (livespec_jsonc_valid, template_exists,
template_files_present, proposed_changes_and_history_dirs,
version_directories_complete, version_contiguity,
revision_to_proposed_change_pairing,
proposed_change_topic_format). Cycle 142 lands the
single-tree dispatch pathway; the v037-era cycle (iii) Phase-6
gap-fix widens the orchestrator to multi-tree per the Phase 6
exit-criterion ("one wrapper invocation, exit 0 overall, with
per-tree findings emitted"): the main spec at
`<project_root>/SPECIFICATION` runs the `main` applicability
subset (all 8 checks); each sub-spec tree at
`<main_spec_root>/templates/<name>/` runs the `sub_spec`
applicability subset (6 checks; project-root-only checks
`livespec_jsonc_valid` + `template_exists` are skipped). The
canonical `{"findings": [...]}` JSON payload is emitted once
with the union of per-tree findings; exit code is derived from
the union of statuses (0 = all pass, 3 = at least one fail).
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
from livespec.doctor.static import APPLICABILITY_BY_TREE_KIND, TreeKind
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


def _enumerate_sub_spec_roots(*, main_spec_root: Path) -> list[Path]:
    """Enumerate sub-spec tree roots under `<main_spec_root>/templates/<name>/`.

    Per Plan §"Phase 6" (sub-spec trees materialized at
    `SPECIFICATION/templates/<name>/`) + v018 Q1 + v020 Q1
    (uniform livespec-internal multi-file layout), each
    immediate subdirectory of `<main_spec_root>/templates/`
    is treated as a sub-spec tree. Missing templates/ directory
    yields an empty list (the project doesn't ship sub-specs).
    Sorted-by-name for deterministic finding order.
    """
    templates_path = main_spec_root / "templates"
    if not templates_path.is_dir():
        return []
    return sorted(child for child in templates_path.iterdir() if child.is_dir())


def _run_tree(*, ctx: DoctorContext, tree_kind: TreeKind) -> list[Finding]:
    """Run the APPLICABILITY_BY_TREE_KIND[tree_kind] subset against `ctx`.

    Returns the per-tree Findings list. Each Finding carries
    the spec_root field via `_run_one_check` -> per-check
    `_pass_finding(ctx=ctx)` already populating `spec_root=
    str(ctx.spec_root)`, so per-tree provenance is intrinsic to
    the Finding payload.
    """
    modules = APPLICABILITY_BY_TREE_KIND[tree_kind]
    return [_run_one_check(ctx=ctx, module=module) for module in modules]


def _orchestrate(*, namespace: argparse.Namespace) -> int:
    """Run the per-tree, per-check dispatch pathway against every spec tree.

    Derive project_root from --project-root; build the main
    DoctorContext at `<project_root>/SPECIFICATION` and run the
    `main` applicability subset (all 8 Phase-3-minimum checks).
    Then enumerate sub-spec trees under
    `<main_spec_root>/templates/<name>/` and run the `sub_spec`
    applicability subset (6 checks; project-root-only checks
    `livespec_jsonc_valid` + `template_exists` are skipped) per
    the v022 D7 narrowed-registry policy. Emit one aggregated
    `{"findings": [...]}` JSON payload; derive exit code from
    the union of statuses.
    """
    project_root = _resolve_project_root(namespace=namespace)
    main_spec_root = project_root / "SPECIFICATION"
    main_ctx = DoctorContext(project_root=project_root, spec_root=main_spec_root)
    findings = _run_tree(ctx=main_ctx, tree_kind="main")
    for sub_spec_root in _enumerate_sub_spec_roots(main_spec_root=main_spec_root):
        sub_ctx = DoctorContext(project_root=project_root, spec_root=sub_spec_root)
        findings.extend(_run_tree(ctx=sub_ctx, tree_kind="sub_spec"))
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
