"""Hand-authored dataclass paired with `finding.schema.json`.

Per `livespec/schemas/dataclasses/CLAUDE.md`, fields match the
schema one-to-one in name and Python type. Status is the
three-value Literal per `finding.schema.json` lines 23-26.

v032 TDD redo cycle 21: minimal authoring under outside-in
consumer pressure — the cycle-21 test needs only that the
orchestrator emits a Finding with `check_id`/`status` set; later
cycles drive the NewType discipline (`CheckId` over `str` per
`livespec/types.py` and `check-newtype-domain-primitives`) into
existence when the corresponding Phase-4 enforcement check is
authored. Plain `str` for `check_id` and `spec_root` here is
field-shape-equivalent at the JSON wire level — `NewType` is a
type-checker affordance only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__: list[str] = ["Finding"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Finding:
    """One static-check Finding (v014 N2 standalone) per spec tree."""

    check_id: str
    status: Literal["pass", "fail", "skipped"]
    message: str
    path: str | None
    line: int | None
    spec_root: str
