"""Tests for livespec.schemas.dataclasses.livespec_config.

Per `tests/livespec/schemas/dataclasses/CLAUDE.md`: field
invariants (the strict-dataclass triple) hold, and the
dataclass-side defaults mirror the schema's `default` keywords
byte-for-byte so direct construction (without going through the
validator) yields the same configured state as an empty `{}`
payload run through `validate_livespec_config`.

The per-operation core-default argvs in `SpecClis` are the
load-bearing surface of `contracts.md` (pre-populated with core's reference defaults); the
schema-mirror test below pins the schema/dataclass equality so
the two co-authoritative declarations cannot drift silently.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from livespec.schemas.dataclasses.livespec_config import (
    LivespecConfig,
    OrchestratorConfig,
    SpecClis,
)

__all__: list[str] = []

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[4]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "livespec_config.schema.json"
)


def test_spec_clis_defaults_mirror_schema_default_arrays() -> None:
    """Every SpecClis field default equals the schema's per-key `default` array.

    The schema and the dataclass are co-authoritative; this
    equality pins the byte-for-byte mirror so an edit to either
    side without the other surfaces immediately.
    """
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_defaults = {
        key: subschema["default"]
        for key, subschema in schema["properties"]["spec_clis"]["properties"].items()
    }
    dataclass_defaults = dataclasses.asdict(SpecClis())
    assert dataclass_defaults == schema_defaults


def test_livespec_config_defaults_carry_spec_tier_facts() -> None:
    """Direct construction defaults match the schema's documented defaults."""
    config = LivespecConfig()
    assert config.template == "livespec"
    assert config.spec_root == "SPECIFICATION"
    assert config.spec_clis == SpecClis()
    assert config.orchestrator is None


def test_livespec_config_dataclasses_are_frozen_kw_only_slotted() -> None:
    """The strict-dataclass triple holds for every wire dataclass in the module."""
    for cls in (LivespecConfig, SpecClis, OrchestratorConfig):
        params = cls.__dataclass_params__  # pyright: ignore[reportAttributeAccessIssue]
        assert params.frozen, f"{cls.__name__} must be frozen"
        assert all(
            field.kw_only for field in dataclasses.fields(cls)
        ), f"{cls.__name__} fields must be kw_only"
        assert hasattr(cls, "__slots__"), f"{cls.__name__} must declare slots"


def test_orchestrator_config_round_trips_field_values() -> None:
    """OrchestratorConfig carries its four required fields verbatim."""
    orchestrator = OrchestratorConfig(
        name="livespec-orchestrator-beads-fabro",
        spec_reader=["impl-beads", "spec-reader"],
        gap_capture=["impl-beads", "gap-capture"],
        drift_capture=["impl-beads", "drift-capture"],
    )
    assert orchestrator.name == "livespec-orchestrator-beads-fabro"
    assert orchestrator.spec_reader == ["impl-beads", "spec-reader"]
    assert orchestrator.gap_capture == ["impl-beads", "gap-capture"]
    assert orchestrator.drift_capture == ["impl-beads", "drift-capture"]
