# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Post-step doctor invocation railway stages for the `revise` sub-command.

Per `SPECIFICATION/contracts.md` §"Sub-command wire contracts" →
"`revise` payload validation": "Revise's post-step doctor MUST
run the `unresolved-spec-commitment` invariant against the
freshly-cut `vNNN/` snapshot." The full static-phase doctor
registry is exercised; the new `unresolved-spec-commitment`
invariant lands in the registry per the PR #281 sibling
(li-7jniti) landing.

On any fail-status finding from post-step → IOFailure(
PreconditionError), which the supervisor pattern-match in
`revise.py` lifts to exit 3 per the existing exit-code table.
Per the work-item description (li-f2dk3t): "the snapshot is
already cut by the time post-step runs; the exit 3 surfaces the
gap and the user's corrective action is to file the declared
work-items then re-run doctor to verify resolution."

Extracted from `revise.py` so the parent file's LLOC stays
under the 250-LLOC hard ceiling enforced by
`livespec_dev_tooling.checks.file_lloc`. Mirrors the
sibling-module composition mechanism used in
`_seed_railway_emits._run_post_step_doctor`.
"""

from __future__ import annotations

import json as _json
import subprocess
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult
from returns.result import Success, safe

from livespec.errors import LivespecError, PreconditionError
from livespec.io import proc
from livespec.schemas.dataclasses.revise_input import RevisionInput

__all__: list[str] = [
    "_fold_post_step_doctor_completed_process",
    "_run_post_step_doctor",
]


_BIN_DIR = Path(__file__).resolve().parents[2] / "bin"
_DOCTOR_STATIC_WRAPPER = _BIN_DIR / "doctor_static.py"


@safe(exceptions=(ValueError,))
def _safe_json_loads(*, text: str) -> Any:
    """Decorator-lifted strict-JSON decode for doctor's stdout contract."""
    return _json.loads(text)


def _fold_post_step_doctor_completed_process(
    *,
    revise_input: RevisionInput,
    completed: subprocess.CompletedProcess[str],
) -> IOResult[RevisionInput, LivespecError]:
    """Parse the post-step doctor subprocess's stdout JSON; fold fail findings -> Failure.

    Mirror of `_seed_railway_emits._fold_doctor_completed_process`
    specialized to revise's RevisionInput threading. Per
    `SPECIFICATION/contracts.md` §"`revise` payload validation":
    when one or more findings carry `status == "fail"`, the
    supervisor MUST short-circuit with `IOFailure(
    PreconditionError)` so the supervisor pattern-match lifts to
    exit 3.

    The freshly-cut `vNNN/` snapshot is already on disk by the
    time post-step runs; exit 3 is INFORMATIONAL — the user's
    corrective action is to file the declared work-items via
    the active impl-plugin's `capture-work-item` skill, then
    re-invoke doctor to verify resolution.
    """
    parsed = _safe_json_loads(text=completed.stdout)
    if not isinstance(parsed, Success):
        return IOResult.from_failure(
            PreconditionError(
                f"post-step doctor stdout malformed JSON: {parsed.failure()}",
            ),
        )
    payload = parsed.unwrap()
    if not isinstance(payload, dict) or "findings" not in payload:
        return IOResult.from_failure(
            PreconditionError("post-step doctor stdout missing 'findings' key"),
        )
    findings_value = payload["findings"]
    if not isinstance(findings_value, list):
        return IOResult.from_failure(
            PreconditionError("post-step doctor 'findings' is not a list"),
        )
    fail_count = sum(
        1
        for finding in findings_value
        if isinstance(finding, dict) and finding.get("status") == "fail"
    )
    if fail_count > 0:
        _ = sys.stdout.write(completed.stdout)
        return IOResult.from_failure(
            PreconditionError(
                f"post-step doctor reported {fail_count} fail-status finding(s)",
            ),
        )
    return IOResult.from_value(revise_input)


def _run_post_step_doctor(
    *,
    revise_input: RevisionInput,
    project_root: Path,
) -> IOResult[RevisionInput, LivespecError]:
    """Invoke `bin/doctor_static.py` as a subprocess; fold fail findings -> Failure.

    Per `SPECIFICATION/spec.md` §"Sub-command lifecycle":
    `revise` MUST run a post-step doctor static check after its
    action. Per `SPECIFICATION/contracts.md` §"Sub-command wire
    contracts" → "`revise` payload validation": "Revise's
    post-step doctor MUST run the `unresolved-spec-commitment`
    invariant against the freshly-cut `vNNN/` snapshot."

    Composition mechanism mirrors the post-step doctor invocation
    in `_seed_railway_emits._run_post_step_doctor` — `subprocess`
    is chosen over direct in-process import because the layered-
    architecture import-linter contract treats `livespec.commands`
    and `livespec.doctor` as independent siblings that cannot
    import each other.

    Forwards `--project-root <path>` to the subprocess so the
    doctor resolves the spec root from the same project root the
    revise wrapper resolved.
    """
    return proc.run_subprocess(
        argv=[
            sys.executable,
            str(_DOCTOR_STATIC_WRAPPER),
            "--project-root",
            str(project_root),
        ],
    ).bind(
        lambda completed: _fold_post_step_doctor_completed_process(
            revise_input=revise_input,
            completed=completed,
        ),
    )
