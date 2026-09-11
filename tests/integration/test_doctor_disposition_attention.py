"""Integration-tier coverage for `SPECIFICATION/scenarios.md`.

Covers the H2 section "Error path — doctor disposition requires
attention" end-to-end over the shipped `effective_doctor_disposition`
resolver and the shipped `.livespec.jsonc` parser, so each scenario is
driven through real config text and the production resolution path:

- Unmapped or failed disposition reaches a human — an unmapped check,
  an invalid check id, an invalid mapped verb, and a mapped verb whose
  execution fails each set `requires_doctor_disposition_input` true.
- Missing consent or journal failure prevents automatic disposition —
  absent downstream consent and a failed journal append each escalate.
- Empty defaults arm no doctor action — an absent `doctor_dispositions`
  map yields an empty effective map, so a non-pass finding escalates.

The POSITIVE CONTROL is a mapped, valid, executable disposition that
returns `requires_input=False`, proving the escalation pins are not
vacuously always-true.
"""

from __future__ import annotations

import pytest
from livespec.spec_governance.config import parse_config_text
from livespec.spec_governance.effective import (
    DoctorContext,
    effective_doctor_disposition,
    requires_doctor_disposition_input,
)

__all__: list[str] = []

pytestmark = pytest.mark.integration

_CHECK = "doctor-spec-tree-manifested"
_MAPPED = f'{{"spec_governance": {{"doctor_dispositions": {{"{_CHECK}": "dismiss"}}}}}}'


def test_mapped_executable_disposition_owns_the_finding() -> None:
    """POSITIVE CONTROL: one valid executable disposition needs no human."""
    config = parse_config_text(text=_MAPPED).effective

    policy = effective_doctor_disposition(
        config=config,
        check_id=_CHECK,
        context=DoctorContext(),
    )

    assert not requires_doctor_disposition_input(policy=policy)
    assert policy.value == "dismiss"
    assert policy.source == "global"


def test_unmapped_invalid_or_failed_disposition_reaches_a_human() -> None:
    """Unmapped check, invalid id, invalid verb, and failed action escalate."""
    mapped = parse_config_text(text=_MAPPED).effective
    empty = parse_config_text(text="{}").effective

    unmapped = effective_doctor_disposition(config=empty, check_id=_CHECK, context=DoctorContext())
    invalid_id = effective_doctor_disposition(
        config=mapped, check_id="Not A Check Id", context=DoctorContext()
    )
    invalid_verb = effective_doctor_disposition(
        config=mapped,
        check_id=_CHECK,
        context=DoctorContext(invocation_disposition="not-a-verb"),
    )
    execution_failed = effective_doctor_disposition(
        config=mapped, check_id=_CHECK, context=DoctorContext(execution_ok=False)
    )

    for policy in (unmapped, invalid_id, invalid_verb, execution_failed):
        assert requires_doctor_disposition_input(policy=policy)
        assert policy.value is None


def test_missing_consent_or_journal_failure_prevents_disposition() -> None:
    """Absent downstream consent and a failed journal append both escalate."""
    config = parse_config_text(text=_MAPPED).effective

    no_consent = effective_doctor_disposition(
        config=config, check_id=_CHECK, context=DoctorContext(downstream_consent=False)
    )
    journal_failed = effective_doctor_disposition(
        config=config, check_id=_CHECK, context=DoctorContext(journal_ok=False)
    )

    assert requires_doctor_disposition_input(policy=no_consent)
    assert requires_doctor_disposition_input(policy=journal_failed)


def test_empty_defaults_arm_no_doctor_action() -> None:
    """An absent map leaves an empty effective map, so a finding escalates."""
    empty = parse_config_text(text="{}").effective

    assert empty.doctor_dispositions == {}
    policy = effective_doctor_disposition(config=empty, check_id=_CHECK, context=DoctorContext())
    assert requires_doctor_disposition_input(policy=policy)
    assert policy.source == "default"
