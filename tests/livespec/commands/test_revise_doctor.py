"""Tests for livespec.commands._revise_doctor.

Per `SPECIFICATION/contracts.md` §"Sub-command wire contracts"
→ "`revise` payload validation": "Revise's post-step doctor
MUST run the `unresolved-spec-commitment` invariant against
the freshly-cut `vNNN/` snapshot." When any fail-status
finding is reported, the supervisor lifts to exit 3 — the
gating mechanism is `_fold_post_step_doctor_completed_process`
folding fail-status findings to `IOFailure(PreconditionError)`.

Per the work-item description (li-f2dk3t): "the snapshot is
already cut by the time post-step runs; the exit 3 surfaces
the gap and the user's corrective action is to file the
declared work-items then re-run doctor to verify resolution."
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from livespec.commands._revise_doctor import (
    _fold_post_step_doctor_completed_process,
    _run_post_step_doctor,
)
from livespec.errors import PreconditionError
from livespec.schemas.dataclasses.revise_input import RevisionInput
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def _build_revise_input() -> RevisionInput:
    """Helper: build a minimal RevisionInput for the fold-helper input slot."""
    return RevisionInput(author=None, decisions=[{"proposal_topic": "x", "decision": "reject"}])


def test_fold_post_step_doctor_returns_failure_on_malformed_json_stdout(
    *,
    tmp_path: Path,
) -> None:
    """Malformed-JSON stdout from the doctor subprocess -> Failure(PreconditionError).

    Per `_fold_post_step_doctor_completed_process` guard: the
    doctor wrapper's documented stdout contract is a single
    `{"findings": [...]}` JSON object. If stdout cannot be decoded
    by `json.loads`, the doctor's contract was violated and the
    revise wrapper cannot proceed — the helper lifts the
    json.ValueError catch into a Failure(PreconditionError) so
    the supervisor pattern-matches it onto exit 3 via err.exit_code.

    Mirrors the parallel test for seed's
    `_fold_doctor_completed_process` (see test_seed.py).
    """
    _ = tmp_path  # symmetry; helper does not touch the disk
    revise_input = _build_revise_input()
    completed = subprocess.CompletedProcess[str](
        args=["doctor"],
        returncode=0,
        stdout="not json {",
        stderr="",
    )
    result = _fold_post_step_doctor_completed_process(
        revise_input=revise_input,
        completed=completed,
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            msg = f"expected Failure(PreconditionError), got {unwrapped!r}"
            raise AssertionError(msg)


def test_fold_post_step_doctor_returns_failure_on_missing_findings_key(
    *,
    tmp_path: Path,
) -> None:
    """Doctor stdout JSON without a `findings` key -> Failure(PreconditionError).

    Per `_fold_post_step_doctor_completed_process` guard: the
    payload must be a dict carrying a `findings` key. A non-dict
    payload (e.g., a JSON array at the root) or a dict missing
    the `findings` key both signal a contract violation.
    """
    _ = tmp_path
    revise_input = _build_revise_input()
    completed = subprocess.CompletedProcess[str](
        args=["doctor"],
        returncode=0,
        stdout="{}",
        stderr="",
    )
    result = _fold_post_step_doctor_completed_process(
        revise_input=revise_input,
        completed=completed,
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            msg = f"expected Failure(PreconditionError), got {unwrapped!r}"
            raise AssertionError(msg)


def test_fold_post_step_doctor_returns_failure_on_non_list_findings(
    *,
    tmp_path: Path,
) -> None:
    """`findings` not a list -> Failure(PreconditionError)."""
    _ = tmp_path
    revise_input = _build_revise_input()
    completed = subprocess.CompletedProcess[str](
        args=["doctor"],
        returncode=0,
        stdout='{"findings": "not-a-list"}',
        stderr="",
    )
    result = _fold_post_step_doctor_completed_process(
        revise_input=revise_input,
        completed=completed,
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            msg = f"expected Failure(PreconditionError), got {unwrapped!r}"
            raise AssertionError(msg)


def test_fold_post_step_doctor_returns_failure_on_unresolved_spec_commitment_fail(
    *,
    tmp_path: Path,
    capsys: object,
) -> None:
    """Post-step fail on unresolved-spec-commitment lifts to Failure(PreconditionError).

    Per `SPECIFICATION/contracts.md` §"Sub-command wire contracts"
    → "`revise` payload validation": when the `unresolved-spec-
    commitment` invariant fires `fail`, the revise wrapper exits
    3 — the post-step is the gating point.

    This is the SCENARIO 1 test from the brief: "Post-step fail
    path (revise cuts vNNN, post-step fails on unresolved
    id_hint, exit 3 surfaced)." Tested at the fold-helper layer
    so we don't need a full doctor subprocess invocation; the
    supervisor exit-code derivation is covered by the pattern-
    match in revise.py's _pattern_match_io_result.
    """
    import pytest

    assert isinstance(capsys, pytest.CaptureFixture)
    _ = tmp_path
    revise_input = _build_revise_input()
    findings_payload = {
        "findings": [
            {
                "check_id": "doctor-unresolved-spec-commitment",
                "status": "fail",
                "message": (
                    "unresolved-spec-commitment: 1 declared "
                    "spec_commitments.impl_followups[] id_hint(s) have no "
                    "matching work-item with spec_commitment_hint: "
                    "alpha-hint (from v005/commitments.md)"
                ),
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
    result = _fold_post_step_doctor_completed_process(
        revise_input=revise_input,
        completed=completed,
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError() as err):
            # Message names the fail count for the supervisor
            # narration layer (SKILL.md prose surfaces findings).
            assert "1 fail-status finding" in str(
                err
            ), f"expected message to name fail-status count, got: {err}"
        case _:
            msg = f"expected Failure(PreconditionError), got {unwrapped!r}"
            raise AssertionError(msg)
    # The doctor stdout is forwarded verbatim so the SKILL.md
    # prose can narrate the findings to the user.
    captured = capsys.readouterr()
    assert (
        "doctor-unresolved-spec-commitment" in captured.out
    ), "expected doctor stdout to be forwarded for SKILL.md narration"


def test_fold_post_step_doctor_returns_success_on_no_fail_findings(
    *,
    tmp_path: Path,
) -> None:
    """Post-step with no fail-status findings -> Success(RevisionInput) — green path."""
    _ = tmp_path
    revise_input = _build_revise_input()
    findings_payload = {
        "findings": [
            {
                "check_id": "doctor-unresolved-spec-commitment",
                "status": "pass",
                "message": "unresolved-spec-commitment: every declared id_hint resolves",
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
    result = _fold_post_step_doctor_completed_process(
        revise_input=revise_input,
        completed=completed,
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(returned):
            assert returned == revise_input
        case _:
            msg = f"expected Success(RevisionInput), got {unwrapped!r}"
            raise AssertionError(msg)


def test_fold_post_step_doctor_returns_success_when_supersession_exempts_id_hint(
    *,
    tmp_path: Path,
) -> None:
    """Supersession exemption: post-step pass when later PC supersedes earlier id_hint.

    This is SCENARIO 2 from the brief: "Supersession exemption
    (later vNNN with `supersedes[]` exempts previously-failing
    id_hint)." Mirrors the unresolved-spec-commitment unit test
    `test_passes_when_id_hint_is_superseded_in_a_later_version`
    — at the doctor static layer that produces the pass finding,
    the post-step fold returns Success.

    The fixture simulates the doctor's stdout under the
    supersession scenario: only a `pass` finding for
    unresolved-spec-commitment. The post-step fold treats this
    identically to any pass-status finding.
    """
    _ = tmp_path
    revise_input = _build_revise_input()
    findings_payload = {
        "findings": [
            {
                "check_id": "doctor-unresolved-spec-commitment",
                "status": "pass",
                "message": (
                    "unresolved-spec-commitment: every declared spec_commitments."
                    "impl_followups[] id_hint resolves to a work-item with matching "
                    "spec_commitment_hint or has been superseded "
                    "(2 obligation(s) scanned)"
                ),
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
    result = _fold_post_step_doctor_completed_process(
        revise_input=revise_input,
        completed=completed,
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(returned):
            assert returned == revise_input
        case _:
            msg = f"expected Success(RevisionInput) on supersession exemption, got {unwrapped!r}"
            raise AssertionError(msg)


def test_run_post_step_doctor_invokes_doctor_static_wrapper_via_subprocess(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """`_run_post_step_doctor` invokes `bin/doctor_static.py` via subprocess.

    Verifies the composition mechanism: subprocess invocation
    (per the layered-architecture import-linter contract that
    forbids `livespec.commands` from importing `livespec.doctor`).
    Mirrors the parallel coverage for seed's `_run_post_step_doctor`.
    """
    import pytest
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
    revise_input = _build_revise_input()
    result = _run_post_step_doctor(
        revise_input=revise_input,
        project_root=tmp_path,
    )
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Success), f"expected Success, got {unwrapped!r}"
    assert captured_argv, "expected subprocess to be invoked"
    cmd = captured_argv[0]
    # The argv carries doctor_static.py and forwards --project-root.
    assert any(
        "doctor_static.py" in part for part in cmd
    ), f"expected doctor_static.py in argv, got: {cmd}"
    assert "--project-root" in cmd, f"expected --project-root in argv, got: {cmd}"
    assert str(tmp_path) in cmd, f"expected tmp_path in argv, got: {cmd}"
