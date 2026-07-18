"""Dedicated schema for stateless needs-attention items."""

from dataclasses import dataclass
from typing import Literal

__all__: list[str] = [
    "AttentionItem",
    "AttentionKind",
    "AttentionUrgency",
    "Handoff",
    "HandoffKind",
    "SourceRef",
    "validate_attention_item_id",
]

AttentionKind = Literal[
    "human-valve",
    "impl",
    "spec",
    "plan",
    "hygiene",
    "internal",
    "host-only",
]
AttentionUrgency = Literal["high", "medium", "low"]
HandoffKind = Literal["drive", "livespec-op", "plan", "shell"]

_TWO_PART_COUNT = 2
_THREE_PART_COUNT = 3
_TWO_PART_PREFIXES = frozenset(("impl", "plan"))
_THREE_PART_PREFIXES = frozenset(("host-only", "valve", "hygiene", "spec"))


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceRef:
    """Primitive source pointer carried by an attention item."""

    repo: str
    work_item: str | None = None
    path: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Handoff:
    """Action payload a caller can render without backend knowledge."""

    kind: HandoffKind
    command: str
    action_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class AttentionItem:
    """Flat point-in-time attention record shared by orchestrators."""

    id: str
    kind: AttentionKind
    urgency: AttentionUrgency
    summary: str
    source_ref: SourceRef
    handoff: Handoff


def validate_attention_item_id(*, id: str) -> bool:
    """Return whether `id` follows the stable needs-attention key grammar."""
    parts = id.split(":", maxsplit=_TWO_PART_COUNT)
    prefix = parts[0]
    is_valid = False
    if prefix in _TWO_PART_PREFIXES:
        is_valid = len(parts) == _TWO_PART_COUNT and _is_stable_component(value=parts[1])
    elif prefix in _THREE_PART_PREFIXES:
        is_valid = _valid_three_part_key(parts=parts)
    return is_valid


def _valid_three_part_key(*, parts: list[str]) -> bool:
    return (
        len(parts) == _THREE_PART_COUNT
        and _is_stable_component(value=parts[1])
        and _is_stable_component(value=parts[2])
    )


def _is_stable_component(*, value: str) -> bool:
    return value != "" and not value.isdecimal()
