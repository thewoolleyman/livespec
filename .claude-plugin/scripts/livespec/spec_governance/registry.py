"""Declarative spec-governance config-key registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

__all__: list[str] = [
    "CONFIG_KEYS",
    "ConfigKey",
    "ConfigValueType",
    "ManifestRow",
    "manifest_rows",
]

ConfigValueType = Literal["enum", "map", "string"]


@dataclass(frozen=True, kw_only=True, slots=True)
class ConfigKey:
    """One declarative spec-governance policy key."""

    key: str
    value_type: ConfigValueType
    safe_default: str | dict[str, str] | None
    per_proposal_override: str | None
    allowed_values: list[str] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True, slots=True)
class ManifestRow:
    """Wire projection of one registry row."""

    key: str
    value_type: str
    safe_default: str | dict[str, str] | None
    per_proposal_override: str | None
    allowed_values: list[str]


CONFIG_KEYS: tuple[ConfigKey, ...] = (
    ConfigKey(
        key="propose_change_mode",
        value_type="enum",
        safe_default="interactive",
        per_proposal_override=None,
        allowed_values=["interactive", "batch"],
    ),
    ConfigKey(
        key="critique_mode",
        value_type="enum",
        safe_default="interactive",
        per_proposal_override=None,
        allowed_values=["interactive", "batch"],
    ),
    ConfigKey(
        key="in_flight_alignment",
        value_type="enum",
        safe_default="prompt",
        per_proposal_override=None,
        allowed_values=["prompt", "default-align"],
    ),
    ConfigKey(
        key="doctor_dispositions",
        value_type="map",
        safe_default={},
        per_proposal_override=None,
        allowed_values=[
            "fix-now",
            "capture-as-work-item",
            "propose-change",
            "defer",
            "dismiss",
        ],
    ),
    ConfigKey(
        key="ratification_review",
        value_type="enum",
        safe_default="manual-spawn",
        per_proposal_override="ratification_review_policy",
        allowed_values=["manual-spawn", "auto-spawn"],
    ),
    ConfigKey(
        key="ratification_reviewer_model",
        value_type="string",
        safe_default=None,
        per_proposal_override=None,
        allowed_values=[],
    ),
)


def manifest_rows() -> list[ManifestRow]:
    """Project the registry to the committed API-key manifest shape."""
    return [
        ManifestRow(
            key=row.key,
            value_type=row.value_type,
            safe_default=row.safe_default,
            per_proposal_override=row.per_proposal_override,
            allowed_values=list(row.allowed_values),
        )
        for row in CONFIG_KEYS
    ]
