"""Tests for livespec.context.

Each context dataclass is `frozen=True, kw_only=True, slots=True`.
Tests cover construction (all required fields), the slots invariant
(no `__dict__`), the frozen invariant (FrozenInstanceError on
field reassignment), and the kw-only invariant (positional args
raise TypeError).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from livespec.context import (
    CritiqueContext,
    DoctorContext,
    ProposeChangeContext,
    PruneHistoryContext,
    ReviseContext,
    SeedContext,
)
from livespec.schemas.dataclasses.livespec_config import LivespecConfig
from livespec.schemas.dataclasses.proposal_findings import ProposalFindings
from livespec.schemas.dataclasses.revise_input import ReviseInput
from livespec.schemas.dataclasses.seed_input import SeedInput
from livespec.types import Author, RunId, SpecRoot, TopicSlug

__all__: list[str] = []


def _make_doctor_context(*, project_root: Path) -> DoctorContext:
    return DoctorContext(
        project_root=project_root,
        spec_root=SpecRoot(project_root / "SPECIFICATION"),
        config=LivespecConfig(),
        config_load_status="ok",
        template_root=project_root / ".claude-plugin" / "specification-templates" / "livespec",
        template_load_status="ok",
        template_name="livespec",
        run_id=RunId("test-run-id"),
        git_head_available=True,
    )


def test_doctor_context_construct(*, tmp_path: Path) -> None:
    ctx = _make_doctor_context(project_root=tmp_path)
    assert ctx.project_root == tmp_path
    assert ctx.template_name == "livespec"
    assert ctx.run_id == "test-run-id"


def test_doctor_context_is_frozen(*, tmp_path: Path) -> None:
    ctx = _make_doctor_context(project_root=tmp_path)
    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.project_root = tmp_path / "other"  # type: ignore[misc]


def test_doctor_context_uses_slots(*, tmp_path: Path) -> None:
    """slots=True omits __dict__ and exposes __slots__ instead."""
    ctx = _make_doctor_context(project_root=tmp_path)
    assert not hasattr(ctx, "__dict__")
    assert hasattr(DoctorContext, "__slots__")


def test_doctor_context_kw_only(*, tmp_path: Path) -> None:
    """Positional args raise TypeError per kw_only=True."""
    with pytest.raises(TypeError):
        DoctorContext(tmp_path)  # type: ignore[misc]  # missing kw args + positional


def test_seed_context_embeds_doctor(*, tmp_path: Path) -> None:
    doctor = _make_doctor_context(project_root=tmp_path)
    seed_input = SeedInput(template="livespec", intent="bootstrap", files=[], sub_specs=[])  # type: ignore[arg-type]
    ctx = SeedContext(doctor=doctor, seed_input=seed_input)
    assert ctx.doctor is doctor
    assert ctx.seed_input is seed_input


def test_propose_change_context_carries_topic(*, tmp_path: Path) -> None:
    doctor = _make_doctor_context(project_root=tmp_path)
    findings = ProposalFindings(findings=[])
    ctx = ProposeChangeContext(
        doctor=doctor,
        findings=findings,
        topic=TopicSlug("my-topic"),
    )
    assert ctx.topic == "my-topic"


def test_critique_context_carries_author(*, tmp_path: Path) -> None:
    doctor = _make_doctor_context(project_root=tmp_path)
    findings = ProposalFindings(findings=[])
    ctx = CritiqueContext(
        doctor=doctor,
        findings=findings,
        author=Author("you@example.com"),
    )
    assert ctx.author == "you@example.com"


def test_revise_context_optional_steering(*, tmp_path: Path) -> None:
    doctor = _make_doctor_context(project_root=tmp_path)
    revise_input = ReviseInput(decisions=[])
    ctx = ReviseContext(
        doctor=doctor,
        revise_input=revise_input,
        steering_intent=None,
    )
    assert ctx.steering_intent is None

    ctx_with_steering = ReviseContext(
        doctor=doctor,
        revise_input=revise_input,
        steering_intent="add new check",
    )
    assert ctx_with_steering.steering_intent == "add new check"


def test_prune_history_context_only_doctor(*, tmp_path: Path) -> None:
    doctor = _make_doctor_context(project_root=tmp_path)
    ctx = PruneHistoryContext(doctor=doctor)
    assert ctx.doctor is doctor
