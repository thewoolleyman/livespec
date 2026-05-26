"""Tests for livespec.commands._next_unresolved_check.

Per `SPECIFICATION/contracts.md` §"`/livespec:next` spec-side
thin-transport skill" → "Ranker semantics":

  The ranker MUST NOT emit `revise` candidates whose pre-step
  doctor would `fail` on the `unresolved-spec-commitment`
  invariant. The ranker surfaces this as a `capture-work-item`
  candidate.

This module's tests cover the `_extract_unresolved_fail_message`
extraction-from-doctor-stdout helper and the
`_probe_unresolved_spec_commitment` subprocess-composition
helper. The supervisor-level ranker swap is covered separately
in `test_next.py`.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from livespec.commands._next_unresolved_check import (
    UNRESOLVED_SPEC_COMMITMENT_CHECK_ID,
    UnresolvedSpecCommitmentProbe,
    _apply_probe_to_revise_output,
    _extract_unresolved_fail_message,
    _maybe_swap_to_capture_work_item,
    _probe_unresolved_spec_commitment,
)
from livespec.schemas.dataclasses.next_output import NextOutput
from returns.result import Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def test_extract_unresolved_fail_message_returns_no_fail_on_pass_only(
    *,
    tmp_path: Path,
) -> None:
    """Findings carrying only pass-status -> `would_fail=False`."""
    _ = tmp_path
    findings_payload = {
        "findings": [
            {
                "check_id": UNRESOLVED_SPEC_COMMITMENT_CHECK_ID,
                "status": "pass",
                "message": "every id_hint resolves",
                "path": None,
                "line": None,
                "spec_root": "/tmp/SPECIFICATION",
            },
        ],
    }
    completed = subprocess.CompletedProcess[str](
        args=["doctor"],
        returncode=0,
        stdout=json.dumps(findings_payload),
        stderr="",
    )
    probe = _extract_unresolved_fail_message(completed=completed)
    assert probe == UnresolvedSpecCommitmentProbe(would_fail=False, fail_message="")


def test_extract_unresolved_fail_message_returns_would_fail_on_fail_finding(
    *,
    tmp_path: Path,
) -> None:
    """Findings carrying fail-status for unresolved-spec-commitment -> `would_fail=True`."""
    _ = tmp_path
    fail_message = (
        "unresolved-spec-commitment: 1 declared "
        "spec_commitments.impl_followups[] id_hint(s) have no matching "
        "work-item with spec_commitment_hint: alpha-hint (from v005/commitments.md)"
    )
    findings_payload = {
        "findings": [
            {
                "check_id": UNRESOLVED_SPEC_COMMITMENT_CHECK_ID,
                "status": "fail",
                "message": fail_message,
                "path": "/tmp/work-items.jsonl",
                "line": None,
                "spec_root": "/tmp/SPECIFICATION",
            },
        ],
    }
    completed = subprocess.CompletedProcess[str](
        args=["doctor"],
        returncode=1,
        stdout=json.dumps(findings_payload),
        stderr="",
    )
    probe = _extract_unresolved_fail_message(completed=completed)
    assert probe.would_fail is True
    assert probe.fail_message == fail_message


def test_extract_unresolved_fail_message_ignores_other_checks_failing(
    *,
    tmp_path: Path,
) -> None:
    """Fail on OTHER checks (not unresolved-spec-commitment) -> `would_fail=False`.

    The probe is narrowly scoped to the
    `doctor-unresolved-spec-commitment` finding. Other doctor
    failures (BCP14 keyword, version contiguity, etc.) are not
    the ranker's concern — they're surfaced by doctor's own
    invocation path.
    """
    _ = tmp_path
    findings_payload = {
        "findings": [
            {
                "check_id": "doctor-bcp14-keyword-wellformedness",
                "status": "fail",
                "message": "constraints.md:298 mixed-case BCP 14 keyword 'Shall'",
                "path": "/tmp/SPECIFICATION/constraints.md",
                "line": 298,
                "spec_root": "/tmp/SPECIFICATION",
            },
        ],
    }
    completed = subprocess.CompletedProcess[str](
        args=["doctor"],
        returncode=1,
        stdout=json.dumps(findings_payload),
        stderr="",
    )
    probe = _extract_unresolved_fail_message(completed=completed)
    assert probe.would_fail is False
    assert probe.fail_message == ""


def test_extract_unresolved_fail_message_degrades_gracefully_on_malformed_json(
    *,
    tmp_path: Path,
) -> None:
    """Malformed-JSON stdout from doctor -> `would_fail=False` (graceful degrade).

    The ranker MUST NOT block on its own probe failure — the
    post-step doctor at revise-time remains the gating point.
    """
    _ = tmp_path
    completed = subprocess.CompletedProcess[str](
        args=["doctor"],
        returncode=0,
        stdout="not json {",
        stderr="",
    )
    probe = _extract_unresolved_fail_message(completed=completed)
    assert probe.would_fail is False
    assert probe.fail_message == ""


def test_extract_unresolved_fail_message_degrades_gracefully_on_missing_findings_key(
    *,
    tmp_path: Path,
) -> None:
    """Doctor stdout missing `findings` key -> `would_fail=False` (graceful degrade)."""
    _ = tmp_path
    completed = subprocess.CompletedProcess[str](
        args=["doctor"],
        returncode=0,
        stdout="{}",
        stderr="",
    )
    probe = _extract_unresolved_fail_message(completed=completed)
    assert probe.would_fail is False
    assert probe.fail_message == ""


def test_extract_unresolved_fail_message_handles_mixed_findings(
    *,
    tmp_path: Path,
) -> None:
    """Mixed pass + fail across multiple checks: only the unresolved-spec-commitment fail matters."""
    _ = tmp_path
    fail_message = "unresolved-spec-commitment: 1 declared id_hint(s) have no matching work-item"
    findings_payload = {
        "findings": [
            {
                "check_id": "doctor-template-exists",
                "status": "pass",
                "message": "template resolves",
                "path": None,
                "line": None,
                "spec_root": "/tmp/SPECIFICATION",
            },
            {
                "check_id": UNRESOLVED_SPEC_COMMITMENT_CHECK_ID,
                "status": "fail",
                "message": fail_message,
                "path": "/tmp/work-items.jsonl",
                "line": None,
                "spec_root": "/tmp/SPECIFICATION",
            },
            {
                "check_id": "doctor-no-stale-merged-branch",
                "status": "warn",
                "message": "stale branch X",
                "path": None,
                "line": None,
                "spec_root": "/tmp/SPECIFICATION",
            },
        ],
    }
    completed = subprocess.CompletedProcess[str](
        args=["doctor"],
        returncode=1,
        stdout=json.dumps(findings_payload),
        stderr="",
    )
    probe = _extract_unresolved_fail_message(completed=completed)
    assert probe.would_fail is True
    assert probe.fail_message == fail_message


def test_probe_unresolved_spec_commitment_invokes_doctor_static_via_subprocess(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """`_probe_unresolved_spec_commitment` invokes `bin/doctor_static.py` via subprocess.

    Verifies the composition mechanism: subprocess invocation
    (per the layered-architecture import-linter contract that
    forbids `livespec.commands` from importing `livespec.doctor`).
    """
    import pytest
    from livespec.errors import PreconditionError
    from livespec.io import proc
    from returns.io import IOResult

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    captured_argv: list[list[str]] = []

    def fake_run_subprocess(
        *,
        argv: list[str],
        cwd: Path | None = None,
    ) -> IOResult[subprocess.CompletedProcess[str], PreconditionError]:
        _ = cwd
        captured_argv.append(list(argv))
        completed = subprocess.CompletedProcess[str](
            args=argv,
            returncode=0,
            stdout='{"findings": []}',
            stderr="",
        )
        return IOResult.from_value(completed)

    monkeypatch.setattr(proc, "run_subprocess", fake_run_subprocess)
    result = _probe_unresolved_spec_commitment(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(probe):
            assert probe.would_fail is False
        case _:
            msg = f"expected Success(UnresolvedSpecCommitmentProbe), got {unwrapped!r}"
            raise AssertionError(msg)
    assert captured_argv, "expected subprocess to be invoked"
    cmd = captured_argv[0]
    assert any(
        "doctor_static.py" in part for part in cmd
    ), f"expected doctor_static.py in argv, got: {cmd}"
    assert "--project-root" in cmd, f"expected --project-root in argv, got: {cmd}"


def test_extract_unresolved_fail_message_handles_non_list_findings(
    *,
    tmp_path: Path,
) -> None:
    """`findings` value not a list -> `would_fail=False` (graceful degrade)."""
    _ = tmp_path
    completed = subprocess.CompletedProcess[str](
        args=["doctor"],
        returncode=0,
        stdout='{"findings": "not-a-list"}',
        stderr="",
    )
    probe = _extract_unresolved_fail_message(completed=completed)
    assert probe.would_fail is False


def test_extract_unresolved_fail_message_skips_non_dict_finding_entry(
    *,
    tmp_path: Path,
) -> None:
    """Non-dict entries within `findings` list are skipped, not crash."""
    _ = tmp_path
    findings_payload = {
        "findings": [
            "not-a-dict",
            {
                "check_id": UNRESOLVED_SPEC_COMMITMENT_CHECK_ID,
                "status": "fail",
                "message": "x",
                "path": None,
                "line": None,
                "spec_root": "/tmp/SPECIFICATION",
            },
        ],
    }
    completed = subprocess.CompletedProcess[str](
        args=["doctor"],
        returncode=1,
        stdout=json.dumps(findings_payload),
        stderr="",
    )
    probe = _extract_unresolved_fail_message(completed=completed)
    assert probe.would_fail is True
    assert probe.fail_message == "x"


def test_maybe_swap_to_capture_work_item_skips_non_revise_action(
    *,
    tmp_path: Path,
) -> None:
    """When action != 'revise', the swap helper short-circuits without invoking the probe."""
    output = NextOutput(action="none", reason="nothing pressing", urgency="low")
    result = _maybe_swap_to_capture_work_item(output=output, project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(returned):
            assert returned == output
        case _:
            msg = f"expected Success(output) on non-revise short-circuit, got {unwrapped!r}"
            raise AssertionError(msg)


def test_maybe_swap_to_capture_work_item_invokes_probe_when_action_is_revise(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """When action == 'revise', the swap helper invokes the probe and applies the result.

    Exercises the revise-action branch of the dispatch in
    `_maybe_swap_to_capture_work_item`: the probe is invoked,
    and the swap is applied based on the probe's `would_fail`
    flag.
    """
    import pytest
    from livespec.errors import PreconditionError
    from livespec.io import proc
    from returns.io import IOResult

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    output = NextOutput(action="revise", reason="r", urgency="low")
    findings_payload = {
        "findings": [
            {
                "check_id": UNRESOLVED_SPEC_COMMITMENT_CHECK_ID,
                "status": "fail",
                "message": "unresolved-spec-commitment: 1 declared id_hint(s) have no match",
                "path": "/tmp/work-items.jsonl",
                "line": None,
                "spec_root": str(tmp_path),
            },
        ],
    }

    def fake_run_subprocess(
        *,
        argv: list[str],
        cwd: Path | None = None,
    ) -> IOResult[object, PreconditionError]:
        _ = cwd
        completed = subprocess.CompletedProcess[str](
            args=argv,
            returncode=1,
            stdout=json.dumps(findings_payload),
            stderr="",
        )
        return IOResult.from_value(completed)

    monkeypatch.setattr(proc, "run_subprocess", fake_run_subprocess)
    result = _maybe_swap_to_capture_work_item(output=output, project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(returned):
            assert returned.action == "capture-work-item"
            assert returned.urgency == "high"
        case _:
            msg = f"expected Success with capture-work-item swap, got {unwrapped!r}"
            raise AssertionError(msg)


def test_apply_probe_to_revise_output_returns_unchanged_on_no_fail() -> None:
    """When `probe.would_fail=False`, the output is returned unchanged."""
    output = NextOutput(action="revise", reason="r", urgency="low")
    probe = UnresolvedSpecCommitmentProbe(would_fail=False, fail_message="")
    result = _apply_probe_to_revise_output(output=output, probe=probe)
    assert result == output


def test_apply_probe_to_revise_output_swaps_to_capture_work_item_on_fail() -> None:
    """When `probe.would_fail=True`, swap action to capture-work-item with high urgency."""
    output = NextOutput(action="revise", reason="r", urgency="low")
    probe = UnresolvedSpecCommitmentProbe(would_fail=True, fail_message="fail-text")
    result = _apply_probe_to_revise_output(output=output, probe=probe)
    assert result.action == "capture-work-item"
    assert result.reason == "fail-text"
    assert result.urgency == "high"


def test_apply_probe_to_revise_output_uses_fallback_reason_when_message_empty() -> None:
    """When `probe.fail_message` is empty, the fallback reason text is composed."""
    output = NextOutput(action="revise", reason="r", urgency="low")
    probe = UnresolvedSpecCommitmentProbe(would_fail=True, fail_message="")
    result = _apply_probe_to_revise_output(output=output, probe=probe)
    assert result.action == "capture-work-item"
    assert "revise blocked by unresolved spec_commitments" in result.reason
