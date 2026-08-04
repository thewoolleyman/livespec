"""Shared resolved spec-governance policy value."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__: list[str] = ["EffectivePolicy", "Source"]

Source = Literal["hard-floor", "invocation", "proposal", "global", "default"]


@dataclass(frozen=True, kw_only=True, slots=True)
class EffectivePolicy:
    """A resolved policy value with its winning source and attention flag."""

    value: str | None
    source: Source
    requires_input: bool
    reason: str
