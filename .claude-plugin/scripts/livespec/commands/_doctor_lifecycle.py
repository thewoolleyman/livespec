# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none
"""Shared pre- and post-step static-doctor stages for mutating commands."""

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
    "emit_pre_step_skipped_finding",
    "resolve_pre_step_skip",
    "run_post_step_doctor",
    "run_pre_step_doctor",
]


_DOCTOR_STATIC_WRAPPER = Path(__file__).resolve().parents[2] / "bin" / "doctor_static.py"


def emit_pre_step_skipped_finding() -> None:
    """Emit the required structured finding for a skipped pre-step."""
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


def _resolve_skip_from_config_text(*, text: str) -> bool:
    """Return the configured pre-step skip value, defaulting defensively."""
    parsed: dict[str, object] = jsonc.loads(text=text).value_or({})
    return bool(parsed.get("pre_step_skip_static_checks", False))


def resolve_pre_step_skip(
    *,
    namespace: argparse.Namespace,
    project_root: Path,
) -> IOResult[bool, LivespecError]:
    """Apply the wrapper pre-step skip precedence contract."""
    if namespace.skip_pre_check:
        skip: bool = True
        return IOResult.from_value(skip)
    if namespace.run_pre_check:
        run: bool = False
        return IOResult.from_value(run)
    config_path = project_root / ".livespec.jsonc"
    if not config_path.is_file():
        default: bool = False
        return IOResult.from_value(default)
    return fs.read_text(path=config_path).map(
        lambda text: _resolve_skip_from_config_text(text=text),
    )


@safe(exceptions=(ValueError,))
def _safe_json_loads(*, text: str) -> Any:
    """Decode the doctor structured-findings document."""
    return json.loads(text)


def _fold_doctor_result(
    *,
    completed: subprocess.CompletedProcess[str],
    phase: str,
    value: Any,
) -> IOResult[Any, LivespecError]:
    """Convert doctor fail findings into the precondition failure rail."""
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
        return IOResult.from_failure(
            PreconditionError(f"{phase} doctor reported {fail_count} fail-status finding(s)"),
        )
    return IOResult.from_value(value)


def _run_doctor(*, project_root: Path, phase: str, value: Any) -> IOResult[Any, LivespecError]:
    """Run doctor static for one lifecycle phase."""
    return proc.run_subprocess(
        argv=[
            sys.executable,
            str(_DOCTOR_STATIC_WRAPPER),
            "--project-root",
            str(project_root),
        ],
    ).bind(
        lambda completed: _fold_doctor_result(
            completed=completed,
            phase=phase,
            value=value,
        ),
    )


def run_pre_step_doctor(*, project_root: Path) -> IOResult[None, LivespecError]:
    """Run and fold the static doctor before a mutating command writes."""
    return _run_doctor(project_root=project_root, phase="pre-step", value=None).map(
        lambda value: value,
    )


def run_post_step_doctor(*, project_root: Path, value: Any) -> IOResult[Any, LivespecError]:
    """Run and fold the static doctor after a mutating command writes."""
    return _run_doctor(project_root=project_root, phase="post-step", value=value)
