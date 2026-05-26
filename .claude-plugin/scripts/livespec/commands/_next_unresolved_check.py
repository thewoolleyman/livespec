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
"""Ranker-side `unresolved-spec-commitment` invariant probe for `/livespec:next`.

Per `SPECIFICATION/contracts.md` §"`/livespec:next` spec-side
thin-transport skill" → "Ranker semantics":

  The ranker MUST NOT emit `revise` candidates whose pre-step
  doctor would `fail` on the `unresolved-spec-commitment`
  invariant. A propose-change with unresolved cross-boundary
  commitments is not yet ripe for revise — the user MUST file
  the declared work-items via the active impl-plugin first.
  The ranker surfaces this as a `capture-work-item` candidate
  (action: the impl-plugin's `capture-work-item` skill, not a
  livespec-side action), with narration naming the unresolved
  `id_hint`s and the originating propose-change topic.

Composition mechanism: subprocess-invoke `bin/doctor_static.py`
and inspect findings for `check_id ==
"doctor-unresolved-spec-commitment"` with `status == "fail"`.
Per the layered-architecture import-linter contract,
`livespec.commands` and `livespec.doctor` are independent
siblings that cannot import each other; subprocess is the
canonical cross-layer probe mechanism (mirrors
`_revise_doctor._run_post_step_doctor` and
`_seed_railway_emits._run_post_step_doctor`).

Probe failure (subprocess crash, malformed stdout) gracefully
degrades to "no unresolved-spec-commitment finding" — the
ranker MUST NOT block on its own probe failure. The post-step
doctor at revise-time remains the gating point per
`SPECIFICATION/contracts.md` §"`revise` payload validation".
"""

from __future__ import annotations

import json as _json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from returns.io import IOResult, IOSuccess
from returns.result import Success, safe

from livespec.errors import LivespecError
from livespec.io import proc
from livespec.schemas.dataclasses.next_output import NextOutput

__all__: list[str] = [
    "UNRESOLVED_SPEC_COMMITMENT_CHECK_ID",
    "UnresolvedSpecCommitmentProbe",
    "_apply_probe_to_revise_output",
    "_extract_unresolved_fail_message",
    "_maybe_swap_to_capture_work_item",
    "_probe_unresolved_spec_commitment",
]


_BIN_DIR = Path(__file__).resolve().parents[2] / "bin"
_DOCTOR_STATIC_WRAPPER = _BIN_DIR / "doctor_static.py"

UNRESOLVED_SPEC_COMMITMENT_CHECK_ID: str = "doctor-unresolved-spec-commitment"


@dataclass(frozen=True, kw_only=True, slots=True)
class UnresolvedSpecCommitmentProbe:
    """Probe result: whether the invariant would fail + the fail message.

    `would_fail` is True iff the post-step doctor would emit a
    fail-status Finding with `check_id == "doctor-unresolved-spec-commitment"`.
    `fail_message` is the Finding's `message` text (empty string when
    no fail finding present); the ranker uses it to compose the
    capture-work-item candidate's `reason`.
    """

    would_fail: bool
    fail_message: str


@safe(exceptions=(ValueError,))
def _safe_json_loads(*, text: str) -> object:
    """Decorator-lifted strict-JSON decode for doctor's stdout contract."""
    return _json.loads(text)


def _extract_unresolved_fail_message(
    *,
    completed: subprocess.CompletedProcess[str],
) -> UnresolvedSpecCommitmentProbe:
    """Parse doctor stdout, look for unresolved-spec-commitment fail.

    Per `SPECIFICATION/contracts.md` §"doctor-static-phase output
    contract": findings are `{check_id, status, message, ...}`
    dicts under the top-level `findings` key. The ranker probe
    looks for `check_id == "doctor-unresolved-spec-commitment"`
    AND `status == "fail"`; any other shape (malformed JSON,
    missing key, non-list findings) graceully degrades to
    `would_fail=False` since the post-step doctor at revise-time
    remains the gating point.
    """
    parsed = _safe_json_loads(text=completed.stdout)
    if not isinstance(parsed, Success):
        return UnresolvedSpecCommitmentProbe(would_fail=False, fail_message="")
    payload = parsed.unwrap()
    if not isinstance(payload, dict) or "findings" not in payload:
        return UnresolvedSpecCommitmentProbe(would_fail=False, fail_message="")
    findings_value = payload["findings"]
    if not isinstance(findings_value, list):
        return UnresolvedSpecCommitmentProbe(would_fail=False, fail_message="")
    for finding in findings_value:
        if not isinstance(finding, dict):
            continue
        if finding.get("check_id") != UNRESOLVED_SPEC_COMMITMENT_CHECK_ID:
            continue
        if finding.get("status") != "fail":
            continue
        message_raw = finding.get("message", "")
        message = str(message_raw) if message_raw is not None else ""
        return UnresolvedSpecCommitmentProbe(would_fail=True, fail_message=message)
    return UnresolvedSpecCommitmentProbe(would_fail=False, fail_message="")


def _probe_unresolved_spec_commitment(
    *,
    project_root: Path,
) -> IOResult[UnresolvedSpecCommitmentProbe, LivespecError]:
    """Invoke `bin/doctor_static.py` and probe for unresolved-spec-commitment fail.

    Per `SPECIFICATION/contracts.md` §"Ranker semantics": the
    ranker probes whether the post-step doctor would `fail` on
    the `unresolved-spec-commitment` invariant against the
    current spec state. On probe success, returns a
    `UnresolvedSpecCommitmentProbe` whose `would_fail` flag
    drives the `_rank` dispatch in `next.py`.

    On subprocess failure (e.g., doctor wrapper missing), the
    railway short-circuits with the carried LivespecError per the
    `proc.run_subprocess` contract. The supervisor's pattern-
    match then surfaces the appropriate exit code; the ranker
    MUST NOT swallow the failure silently because that would mask
    a deeper infrastructure-level problem.
    """
    return proc.run_subprocess(
        argv=[
            sys.executable,
            str(_DOCTOR_STATIC_WRAPPER),
            "--project-root",
            str(project_root),
        ],
    ).bind(
        lambda completed: IOSuccess(
            _extract_unresolved_fail_message(completed=completed),
        ),
    )


def _maybe_swap_to_capture_work_item(
    *,
    output: NextOutput,
    project_root: Path,
) -> IOResult[NextOutput, LivespecError]:
    """If the rank is `revise`, probe unresolved-spec-commitment; swap when failing.

    Per `SPECIFICATION/contracts.md` §"Ranker semantics": a
    propose-change with unresolved cross-boundary commitments is
    not yet ripe for revise; the ranker MUST surface a
    `capture-work-item` candidate with narration naming the
    unresolved `id_hint`s and the originating propose-change
    topic. When the probe finds no fail, the output is returned
    unchanged. When the underlying rank is not `revise`, the
    probe is skipped entirely (subprocess-free) since no
    exclusion applies.
    """
    if output.action != "revise":
        return IOResult.from_value(output)
    return _probe_unresolved_spec_commitment(project_root=project_root).map(
        lambda probe: _apply_probe_to_revise_output(output=output, probe=probe),
    )


def _apply_probe_to_revise_output(
    *,
    output: NextOutput,
    probe: UnresolvedSpecCommitmentProbe,
) -> NextOutput:
    """Swap a revise NextOutput to capture-work-item when probe.would_fail.

    Composes the capture-work-item candidate's `reason` from the
    probe's `fail_message` (the doctor Finding text already names
    the unresolved id_hint(s) and originating PC topic per
    `unresolved_spec_commitment._render_fail`). Urgency is lifted
    to `high` regardless of the underlying revise urgency: an
    unresolved cross-boundary commitment IS the blocking issue
    and is more urgent than the original revise's queue-depth
    urgency.
    """
    if not probe.would_fail:
        return output
    fallback = (
        "revise blocked by unresolved spec_commitments.impl_followups[] "
        "id_hint(s); file via the active impl-plugin's capture-work-item skill"
    )
    reason = probe.fail_message or fallback
    return NextOutput(action="capture-work-item", reason=reason, urgency="high")
