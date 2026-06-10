"""Tests for livespec.validate.livespec_config.

Per style doc §"Skill layout — `validate/`": validator at
`validate/livespec_config.py` exports
`validate_livespec_config(payload, schema)` returning
`Result[LivespecConfig, ValidationError]`. The schema marks
all fields optional with documented defaults; an empty `{}`
payload validates and produces the all-defaults dataclass.

`render_commands` is the extension point introduced alongside
the template-manifest v2 mechanism: when the active template's
spec_files declares any `diagram_source` entry,
`render_commands.diagram_source` MUST be present at the project
level. The cross-config consistency is enforced by a doctor
static check, not by this schema (JSON Schema cannot reach
across .livespec.jsonc and the resolved template's
template.json).
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.livespec_config import LivespecConfig, RenderCommands
from livespec.types import TemplateName
from livespec.validate import livespec_config
from returns.result import Failure, Success

__all__: list[str] = []

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude-plugin"
    / "scripts"
    / "livespec"
    / "schemas"
    / "livespec_config.schema.json"
)

# Module-level schema cache: hypothesis-based @given
# tests run the body ~100 times per invocation; reloading the schema
# from disk on each example pushes individual examples over the
# default 200ms hypothesis deadline under `pytest -n auto` xdist
# worker contention. Loading once at module-import time eliminates
# per-example file I/O and the associated timing nondeterminism.
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_validate_livespec_config_returns_success_with_defaults_for_empty_payload() -> None:
    """An empty `{}` payload validates to Success(LivespecConfig) with all schema defaults."""
    schema = _SCHEMA
    result = livespec_config.validate_livespec_config(payload={}, schema=schema)
    expected = LivespecConfig(
        template=TemplateName("livespec"),
        template_format_version=1,
        post_step_skip_doctor_llm_objective_checks=False,
        post_step_skip_doctor_llm_subjective_checks=False,
        post_step_skip_capture_impl_gaps=False,
        pre_step_skip_static_checks=False,
        pre_step_skip_stale_branch_check=False,
        render_commands=RenderCommands(),
    )
    assert result == Success(expected)


def test_validate_livespec_config_accepts_render_commands_diagram_source() -> None:
    """An explicit render_commands.diagram_source argv flows through to the dataclass."""
    schema = _SCHEMA
    argv = ["plantuml", "-tsvg", "-o", "{output_dir}", "{source}"]
    payload: dict[str, object] = {
        "render_commands": {"diagram_source": argv},
    }
    result = livespec_config.validate_livespec_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.render_commands.diagram_source == argv
        case _:
            msg = f"expected Success(LivespecConfig), got {result}"
            raise AssertionError(msg)


def test_validate_livespec_config_rejects_render_commands_empty_argv() -> None:
    """An empty diagram_source argv returns Failure(ValidationError).

    The schema constrains `diagram_source` to `minItems: 1` — an
    empty argv has no executable to invoke.
    """
    schema = _SCHEMA
    payload: dict[str, object] = {"render_commands": {"diagram_source": []}}
    result = livespec_config.validate_livespec_config(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "livespec_config:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_livespec_config_rejects_render_commands_unknown_kind() -> None:
    """An unknown render_commands kind returns Failure.

    `additionalProperties: false` on the render_commands object
    rejects future-kind names until they're added to the schema.
    """
    schema = _SCHEMA
    payload: dict[str, object] = {"render_commands": {"future_kind": ["echo"]}}
    result = livespec_config.validate_livespec_config(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "livespec_config:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_livespec_config_returns_success_for_explicit_template() -> None:
    """An explicit `template` overrides the default."""
    schema = _SCHEMA
    payload: dict[str, object] = {"template": "minimal"}
    result = livespec_config.validate_livespec_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.template == "minimal"
            assert value.template_format_version == 1  # still default
        case _:
            msg = f"expected Success(LivespecConfig), got {result}"
            raise AssertionError(msg)


def test_validate_livespec_config_returns_failure_on_unknown_field() -> None:
    """A payload with an unknown field returns Failure(ValidationError).

    Drives `additionalProperties: false`: fastjsonschema rejects
    any field not enumerated in the schema's `properties`.
    """
    schema = _SCHEMA
    payload: dict[str, object] = {"unknown_field": "boom"}
    result = livespec_config.validate_livespec_config(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "livespec_config:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


@settings(deadline=None)
@given(
    skip_objective=st.booleans(),
    skip_subjective=st.booleans(),
    skip_capture_impl_gaps=st.booleans(),
    skip_static=st.booleans(),
    skip_stale_branch=st.booleans(),
)
def test_validate_livespec_config_round_trips_skip_flags(
    *,
    skip_objective: bool,
    skip_subjective: bool,
    skip_capture_impl_gaps: bool,
    skip_static: bool,
    skip_stale_branch: bool,
) -> None:
    """For arbitrary skip-flag combinations, the success path preserves them verbatim."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "post_step_skip_doctor_llm_objective_checks": skip_objective,
        "post_step_skip_doctor_llm_subjective_checks": skip_subjective,
        "post_step_skip_capture_impl_gaps": skip_capture_impl_gaps,
        "pre_step_skip_static_checks": skip_static,
        "pre_step_skip_stale_branch_check": skip_stale_branch,
    }
    result = livespec_config.validate_livespec_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.post_step_skip_doctor_llm_objective_checks is skip_objective
            assert value.post_step_skip_doctor_llm_subjective_checks is skip_subjective
            assert value.post_step_skip_capture_impl_gaps is skip_capture_impl_gaps
            assert value.pre_step_skip_static_checks is skip_static
            assert value.pre_step_skip_stale_branch_check is skip_stale_branch
        case _:
            msg = f"expected Success(LivespecConfig), got {result}"
            raise AssertionError(msg)
