# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. This module's
# railway composition means most lines are bind targets, so file-level
# silencing keeps the source readable, matching the sibling command
# modules that carry the same pragma.
"""Shared pre-step / post-step doctor-static lifecycle for mutating wrappers.

Per `SPECIFICATION/contracts.md` (pre-step skip control) and `SPECIFICATION/spec.md`
(sub-command lifecycle): the `propose-change`, `critique`, and
`revise` wrappers each accept the mutually exclusive
`--skip-pre-check` / `--run-pre-check` pair, resolve the effective
skip value in the order (1) skip flag, (2) run flag overriding
config, (3) the `.livespec.jsonc` key `pre_step_skip_static_checks`
(default false), and either emit the single `pre-step-skipped`
finding or run the pre-step doctor static phase before their write.
Each runs the post-step doctor static phase after its write. Passing
both flags is rejected by argparse, which `io/cli.parse_argv` lifts
to `UsageError` (exit 2).

A fail-status finding from either phase folds to
`IOFailure(PreconditionError)` (exit 3), and the doctor's own
structured-findings document is propagated to stdout so the
operation prose can surface it. The doctor runs as a subprocess
because the import-linter layering keeps `livespec.commands` and
`livespec.doctor` independent siblings; the mechanism mirrors
`_prune_history_railway._invoke_pre_step_doctor` and
`_revise_doctor._run_post_step_doctor`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult
from returns.result import Success, safe

from livespec.errors import LivespecError, PreconditionError
from livespec.io import fs, proc, streams
from livespec.parse import jsonc

__all__: list[str] = [
    "add_pre_check_flags",
    "emit_pre_step_skipped_finding",
    "resolve_pre_step_skip",
    "run_post_step_doctor",
    "run_pre_step",
]


_DOCTOR_STATIC_WRAPPER = Path(__file__).resolve().parents[2] / "bin" / "doctor_static.py"


def add_pre_check_flags(*, parser: argparse.ArgumentParser) -> None:
    """Register the mutually exclusive `--skip-pre-check` / `--run-pre-check` pair."""
    pre_check_group = parser.add_mutually_exclusive_group()
    _ = pre_check_group.add_argument("--skip-pre-check", action="store_true")
    _ = pre_check_group.add_argument("--run-pre-check", action="store_true")


def emit_pre_step_skipped_finding() -> None:
    """Write the canonical single-finding `pre-step-skipped` document to stdout."""
    payload = {
        "findings": [
            {
                "check_id": "pre-step-skipped",
                "status": "skipped",
                "message": "pre-step checks skipped by user config or --skip-pre-check",
            },
        ],
    }
    _ = streams.write_stdout(text=json.dumps(payload) + "\n")


def _skip_from_config_text(*, text: str) -> bool:
    """Extract `pre_step_skip_static_checks`; malformed or non-bool reads as false."""
    parsed = jsonc.loads(text=text).value_or({})
    if not isinstance(parsed, dict):
        return False
    return parsed.get("pre_step_skip_static_checks", False) is True


def resolve_pre_step_skip(
    *,
    namespace: argparse.Namespace,
    project_root: Path,
) -> IOResult[bool, LivespecError]:
    """Resolve the effective pre-step skip value in the spec's precedence order."""
    if namespace.skip_pre_check:
        skip: bool = True
        return IOResult.from_value(skip)
    run: bool = False
    if namespace.run_pre_check:
        return IOResult.from_value(run)
    config_path = project_root / ".livespec.jsonc"
    if not config_path.is_file():
        return IOResult.from_value(run)
    return fs.read_text(path=config_path).map(
        lambda text: _skip_from_config_text(text=text),
    )


@safe(exceptions=(ValueError,))
def _safe_json_loads(*, text: str) -> Any:
    """Decorator-lifted strict-JSON decode for the doctor stdout contract."""
    return json.loads(text)


def _fold_doctor_result(
    *,
    completed: subprocess.CompletedProcess[str],
    phase: str,
    value: Any,
) -> IOResult[Any, LivespecError]:
    """Fold the doctor's findings document: any fail-status finding -> PreconditionError."""
    parsed = _safe_json_loads(text=completed.stdout)
    if not isinstance(parsed, Success):
        return IOResult.from_failure(
            PreconditionError(f"{phase} doctor stdout malformed JSON: {parsed.failure()}"),
        )
    payload = parsed.unwrap()
    if not isinstance(payload, dict) or "findings" not in payload:
        return IOResult.from_failure(
            PreconditionError(f"{phase} doctor stdout missing 'findings' key"),
        )
    findings = payload["findings"]
    if not isinstance(findings, list):
        return IOResult.from_failure(
            PreconditionError(f"{phase} doctor 'findings' is not a list"),
        )
    fail_count = sum(
        1 for finding in findings if isinstance(finding, dict) and finding.get("status") == "fail"
    )
    if fail_count:
        _ = streams.write_stdout(text=completed.stdout)
        return IOResult.from_failure(
            PreconditionError(f"{phase} doctor reported {fail_count} fail-status finding(s)"),
        )
    return IOResult.from_value(value)


def _run_doctor(*, project_root: Path, phase: str, value: Any) -> IOResult[Any, LivespecError]:
    """Run `bin/doctor_static.py` against the project root for one lifecycle phase."""
    return proc.run_subprocess(
        argv=[
            sys.executable,
            str(_DOCTOR_STATIC_WRAPPER),
            "--project-root",
            str(project_root),
        ],
    ).bind(
        lambda completed: _fold_doctor_result(completed=completed, phase=phase, value=value),
    )


def _dispatch_pre_step(*, skip: bool, project_root: Path) -> IOResult[None, LivespecError]:
    """Emit the skip finding, or run the pre-step doctor static phase."""
    if skip:
        emit_pre_step_skipped_finding()
        return IOResult.from_value(None)
    return _run_doctor(project_root=project_root, phase="pre-step", value=None)


def run_pre_step(
    *,
    namespace: argparse.Namespace,
    project_root: Path,
) -> IOResult[None, LivespecError]:
    """Resolve the skip value, then skip (with its finding) or run the pre-step doctor."""
    return resolve_pre_step_skip(namespace=namespace, project_root=project_root).bind(
        lambda skip: _dispatch_pre_step(skip=skip, project_root=project_root),
    )


def run_post_step_doctor(*, project_root: Path, value: Any) -> IOResult[Any, LivespecError]:
    """Run the post-step doctor static phase after the write, threading `value` through."""
    return _run_doctor(project_root=project_root, phase="post-step", value=value)
