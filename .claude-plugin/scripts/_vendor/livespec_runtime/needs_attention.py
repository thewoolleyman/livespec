"""Pure needs-attention composition shared by orchestrators."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypeVar

from livespec_runtime.attention_item import (
    AttentionItem,
    AttentionUrgency,
    Handoff,
    SourceRef,
    validate_attention_item_id,
)

__all__: list[str] = [
    "HygieneScanFinding",
    "ImplNextOutput",
    "PlanThreadOutput",
    "SpecNextOutput",
    "WorkItemHumanValveLane",
    "compose_needs_attention",
]

_ValueT = TypeVar("_ValueT")


@dataclass(frozen=True, slots=True, kw_only=True)
class SpecNextOutput:
    """Injected `spec-next` primitive output."""

    op: str
    spec_target: str
    summary: str
    command: str
    urgency: AttentionUrgency = "medium"


@dataclass(frozen=True, slots=True, kw_only=True)
class ImplNextOutput:
    """Injected `impl-next` primitive output."""

    work_item: str
    summary: str
    command: str
    urgency: AttentionUrgency = "high"


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkItemHumanValveLane:
    """Injected human-valve lane from `list-work-items`."""

    verb: str
    work_item: str
    summary: str
    action_id: str
    command: str
    urgency: AttentionUrgency = "high"


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanThreadOutput:
    """Injected `list-plan-threads` primitive output."""

    topic: str
    path: str
    summary: str
    command: str
    urgency: AttentionUrgency = "medium"


@dataclass(frozen=True, slots=True, kw_only=True)
class HygieneScanFinding:
    """Injected `hygiene-scan` primitive output."""

    type: str
    resource: str
    path: str
    summary: str
    command: str
    urgency: AttentionUrgency = "low"


def compose_needs_attention(
    *,
    repo: str,
    spec_next: SpecNextOutput | None = None,
    impl_next: ImplNextOutput | None = None,
    human_valve_lanes: Iterable[WorkItemHumanValveLane] = (),
    plan_threads: Iterable[PlanThreadOutput] = (),
    hygiene_scan: Iterable[HygieneScanFinding] = (),
) -> list[AttentionItem]:
    """Normalize injected primitive outputs into a flat attention list."""
    attention: list[AttentionItem] = []
    for lane in human_valve_lanes:
        _append_if_valid(
            attention=attention,
            item=AttentionItem(
                id=f"valve:{lane.verb}:{lane.work_item}",
                kind="human-valve",
                urgency=lane.urgency,
                summary=lane.summary,
                source_ref=SourceRef(repo=repo, work_item=lane.work_item),
                handoff=Handoff(kind="drive", action_id=lane.action_id, command=lane.command),
            ),
        )
    for current_impl in _present(value=impl_next):
        _append_if_valid(
            attention=attention,
            item=AttentionItem(
                id=f"impl:{current_impl.work_item}",
                kind="impl",
                urgency=current_impl.urgency,
                summary=current_impl.summary,
                source_ref=SourceRef(repo=repo, work_item=current_impl.work_item),
                handoff=Handoff(kind="drive", command=current_impl.command),
            ),
        )
    for current_spec in _present(value=spec_next):
        _append_if_valid(
            attention=attention,
            item=AttentionItem(
                id=f"spec:{current_spec.op}:{current_spec.spec_target}",
                kind="spec",
                urgency=current_spec.urgency,
                summary=current_spec.summary,
                source_ref=SourceRef(repo=repo, path=current_spec.spec_target),
                handoff=Handoff(kind="livespec-op", command=current_spec.command),
            ),
        )
    for thread in plan_threads:
        _append_if_valid(
            attention=attention,
            item=AttentionItem(
                id=f"plan:{thread.topic}",
                kind="plan",
                urgency=thread.urgency,
                summary=thread.summary,
                source_ref=SourceRef(repo=repo, path=thread.path),
                handoff=Handoff(kind="plan", command=thread.command),
            ),
        )
    for finding in hygiene_scan:
        _append_if_valid(
            attention=attention,
            item=AttentionItem(
                id=f"hygiene:{finding.type}:{finding.resource}",
                kind="hygiene",
                urgency=finding.urgency,
                summary=finding.summary,
                source_ref=SourceRef(repo=repo, path=finding.path),
                handoff=Handoff(kind="shell", command=finding.command),
            ),
        )
    return attention


def _present(*, value: _ValueT | None) -> tuple[_ValueT, ...]:
    if value is None:
        return ()
    return (value,)


def _append_if_valid(*, attention: list[AttentionItem], item: AttentionItem) -> None:
    if validate_attention_item_id(id=item.id):
        attention.append(item)
