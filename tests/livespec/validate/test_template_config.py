"""Tests for livespec.validate.template_config.

Per style doc §"Skill layout — `validate/`": validator at
`validate/template_config.py` exports
`validate_template_config(payload, schema)` returning
`Result[TemplateConfig, ValidationError]`.

Per v011 K5: a template's `template.json` declares its format
version, spec_root location, optional doctor extensibility
hooks, and optional LLM-prompt paths. v1 livespec supports only
`template_format_version: 1`.
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.template_config import TemplateConfig
from livespec.types import SpecRoot
from livespec.validate import template_config
from returns.result import Failure, Success

__all__: list[str] = []

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "template_config.schema.json"
)

# Module-level schema cache (v040 D1): hypothesis-based @given
# tests run the body ~100 times per invocation; reloading the schema
# from disk on each example pushes individual examples over the
# default 200ms hypothesis deadline under `pytest -n auto` xdist
# worker contention. Loading once at module-import time eliminates
# per-example file I/O and the associated timing nondeterminism.
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_validate_template_config_returns_success_for_minimal_payload() -> None:
    """The minimum-required payload (just template_format_version) validates with defaults."""
    schema = _SCHEMA
    payload: dict[str, object] = {"template_format_version": 1}
    result = template_config.validate_template_config(payload=payload, schema=schema)
    expected = TemplateConfig(
        template_format_version=1,
        spec_root=SpecRoot("SPECIFICATION/"),
        doctor_static_check_modules=[],
        doctor_llm_objective_checks_prompt=None,
        doctor_llm_subjective_checks_prompt=None,
    )
    assert result == Success(expected)


def test_validate_template_config_returns_failure_on_unsupported_version() -> None:
    """A template_format_version other than 1 returns Failure."""
    schema = _SCHEMA
    payload: dict[str, object] = {"template_format_version": 2}
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "template_config:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_template_config_carries_doctor_check_modules() -> None:
    """Populated doctor_static_check_modules flows through to the dataclass."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "template_format_version": 1,
        "doctor_static_check_modules": ["checks/foo.py", "checks/bar.py"],
    }
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.doctor_static_check_modules == ["checks/foo.py", "checks/bar.py"]
        case _:
            msg = f"expected Success(TemplateConfig), got {result}"
            raise AssertionError(msg)


@settings(deadline=None)
@given(spec_root=st.text(min_size=1, max_size=80))
def test_validate_template_config_round_trips_spec_root(*, spec_root: str) -> None:
    """For arbitrary spec_root text, the success path preserves it verbatim."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "template_format_version": 1,
        "spec_root": spec_root,
    }
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.spec_root == spec_root
        case _:
            msg = f"expected Success(TemplateConfig), got {result}"
            raise AssertionError(msg)
