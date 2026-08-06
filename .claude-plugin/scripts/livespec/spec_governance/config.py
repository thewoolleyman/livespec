"""Type-strict safe-default parsing for spec-governance config."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, cast

from livespec.parse import jsonc
from livespec.spec_governance.registry import CONFIG_KEYS

__all__: list[str] = [
    "DOCTOR_CHECK_ID_PATTERN",
    "MODEL_PATTERN",
    "PROPOSAL_STEM_PATTERN",
    "DeclaredConfig",
    "SpecGovernanceConfig",
    "parse_config_text",
]

DOCTOR_CHECK_ID_PATTERN = re.compile(r"^doctor-[a-z0-9]+(?:-[a-z0-9]+)*$")
PROPOSAL_STEM_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:-[0-9]+)?$")
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")

_ENUM_DEFAULTS = {
    row.key: row.safe_default
    for row in CONFIG_KEYS
    if row.value_type == "enum" and isinstance(row.safe_default, str)
}
_ALLOWED = {row.key: frozenset(row.allowed_values) for row in CONFIG_KEYS}
_DIAG_MISSING_BLOCK = "missing spec_governance block; safe defaults applied"


@dataclass(frozen=True, kw_only=True, slots=True)
class SpecGovernanceConfig:
    """Effective safe-defaulted spec-governance config."""

    propose_change_mode: str = "interactive"
    critique_mode: str = "interactive"
    in_flight_alignment: str = "prompt"
    doctor_dispositions: dict[str, str] = field(default_factory=dict)
    revise_decision_mode: str = "manual"
    drift_acceptance_mode: str = "human"
    ratification_review: str = "manual-spawn"
    ratification_reviewer_model: str | None = None
    ratification_min_review_age_seconds: int = 1


@dataclass(frozen=True, kw_only=True, slots=True)
class DeclaredConfig:
    """Declared block plus parsed safe-defaulted values and diagnostics."""

    raw: dict[str, Any]
    effective: SpecGovernanceConfig
    diagnostics: list[str]


def parse_config_text(*, text: str) -> DeclaredConfig:
    """Parse `.livespec.jsonc` text without raising on malformed input."""
    parsed_result = jsonc.loads(text=text)
    parsed = cast(object, parsed_result.value_or(None))
    if not isinstance(parsed, dict):
        return DeclaredConfig(
            raw={},
            effective=SpecGovernanceConfig(),
            diagnostics=["malformed .livespec.jsonc; safe defaults applied"],
        )
    root = cast(dict[str, Any], parsed)
    block = root.get("spec_governance")
    if not isinstance(block, dict):
        return DeclaredConfig(
            raw={},
            effective=SpecGovernanceConfig(),
            diagnostics=[_DIAG_MISSING_BLOCK],
        )
    return _parse_block(block=cast(dict[str, Any], block))


def _parse_block(*, block: dict[str, Any]) -> DeclaredConfig:
    diagnostics: list[str] = []
    return DeclaredConfig(
        raw=dict(block),
        effective=SpecGovernanceConfig(
            propose_change_mode=_enum_value(
                block=block,
                key="propose_change_mode",
                diagnostics=diagnostics,
            ),
            critique_mode=_enum_value(
                block=block,
                key="critique_mode",
                diagnostics=diagnostics,
            ),
            in_flight_alignment=_enum_value(
                block=block,
                key="in_flight_alignment",
                diagnostics=diagnostics,
            ),
            doctor_dispositions=_doctor_map(block=block, diagnostics=diagnostics),
            revise_decision_mode=_enum_value(
                block=block,
                key="revise_decision_mode",
                diagnostics=diagnostics,
            ),
            drift_acceptance_mode=_enum_value(
                block=block,
                key="drift_acceptance_mode",
                diagnostics=diagnostics,
            ),
            ratification_review=_enum_value(
                block=block,
                key="ratification_review",
                diagnostics=diagnostics,
            ),
            ratification_reviewer_model=_model_value(block=block, diagnostics=diagnostics),
            ratification_min_review_age_seconds=_positive_int_value(
                block=block,
                key="ratification_min_review_age_seconds",
                diagnostics=diagnostics,
            ),
        ),
        diagnostics=diagnostics,
    )


def _enum_value(
    *,
    block: dict[str, Any],
    key: str,
    diagnostics: list[str],
) -> str:
    value = block.get(key)
    default = _ENUM_DEFAULTS[key]
    if value is None:
        return str(default)
    if isinstance(value, str) and value in _ALLOWED[key]:
        return value
    diagnostics.append(f"{key}: invalid value ignored; safe default {default!r} applied")
    return str(default)


def _doctor_map(
    *,
    block: dict[str, Any],
    diagnostics: list[str],
) -> dict[str, str]:
    value = block.get("doctor_dispositions")
    if value is None:
        return {}
    if not isinstance(value, dict):
        diagnostics.append("doctor_dispositions: invalid map ignored; safe default {} applied")
        return {}
    valid: dict[str, str] = {}
    mapping = cast(dict[object, object], value)
    for check_id, disposition in sorted(mapping.items()):
        if not isinstance(check_id, str) or not DOCTOR_CHECK_ID_PATTERN.fullmatch(check_id):
            diagnostics.append("doctor_dispositions: invalid check id ignored")
            continue
        if not isinstance(disposition, str) or disposition not in _ALLOWED["doctor_dispositions"]:
            diagnostics.append(f"doctor_dispositions[{check_id}]: invalid disposition ignored")
            continue
        valid[check_id] = disposition
    return valid


def _model_value(
    *,
    block: dict[str, Any],
    diagnostics: list[str],
) -> str | None:
    value = block.get("ratification_reviewer_model")
    if value is None:
        return None
    if isinstance(value, str) and MODEL_PATTERN.fullmatch(value):
        return value
    diagnostics.append("ratification_reviewer_model: invalid model ignored")
    return None


def _positive_int_value(
    *,
    block: dict[str, Any],
    key: str,
    diagnostics: list[str],
) -> int:
    value = block.get(key)
    if value is None:
        return 1
    if isinstance(value, int) and not isinstance(value, bool) and value >= 1:
        return value
    diagnostics.append(f"{key}: invalid value ignored; safe default 1 applied")
    return 1
