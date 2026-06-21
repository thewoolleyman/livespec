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

Per `SPECIFICATION/contracts.md` §"Spec-side CLI contract" +
§"Orchestrator CLI contract — the three named CLIs" +
§"Plugin distribution": core's config schema carries the
spec-tier facts (`template`, `spec_root`), the seven spec-side
CLI names (pre-populated with core's reference defaults,
individually overridable), and the optional orchestrator
selection naming its three CLIs. The schema root is
`additionalProperties: true` — each plugin or sibling consumer
owns a top-level section named for itself, and core MUST
tolerate unknown sections.
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


def test_validate_livespec_config_tolerates_unknown_top_level_sections() -> None:
    """Unknown top-level sections validate (root is `additionalProperties: true`).

    Per `SPECIFICATION/contracts.md` §"Plugin distribution":
    "`.livespec.jsonc`'s schema root is `additionalProperties:
    true`; each plugin or sibling consumer owns a top-level
    section named for itself and MUST validate its own section
    on read and MUST tolerate unknown sections." The payload
    here mirrors this repo's own dogfood `.livespec.jsonc`
    shape (implementation selection, an impl-plugin-owned
    section, external_references, cross_repo_targets).
    """
    schema = _SCHEMA
    payload: dict[str, object] = {
        "template": "livespec",
        "spec_root": "SPECIFICATION",
        "implementation": {"plugin": "livespec-orchestrator-beads-fabro"},
        "livespec-orchestrator-beads-fabro": {"format": "beads"},
        "external_references": {"livespec-dev-tooling": []},
        "cross_repo_targets": {},
    }
    result = livespec_config.validate_livespec_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.template == "livespec"
        case _:
            msg = f"expected Success(LivespecConfig), got {result}"
            raise AssertionError(msg)


def test_validate_livespec_config_spec_root_defaults_to_specification() -> None:
    """`spec_root` defaults to "SPECIFICATION" and is overridable.

    Per `SPECIFICATION/contracts.md` §"Spec-side CLI contract":
    "Core's config schema carries spec-tier facts (`template`,
    `spec_root`), the orchestrator selection, and the named
    CLIs."
    """
    schema = _SCHEMA
    default_result = livespec_config.validate_livespec_config(payload={}, schema=schema)
    match default_result:
        case Success(value):
            assert value.spec_root == "SPECIFICATION"
        case _:
            msg = f"expected Success(LivespecConfig), got {default_result}"
            raise AssertionError(msg)
    override_result = livespec_config.validate_livespec_config(
        payload={"spec_root": "docs/SPEC"},
        schema=schema,
    )
    match override_result:
        case Success(value):
            assert value.spec_root == "docs/SPEC"
        case _:
            msg = f"expected Success(LivespecConfig), got {override_result}"
            raise AssertionError(msg)


def test_validate_livespec_config_spec_clis_default_to_core_reference_wrappers() -> None:
    """All seven spec-side CLI names pre-populate with core's reference defaults.

    Per `SPECIFICATION/contracts.md` §"Spec-side CLI contract":
    the spec-side lifecycle operations — seed, propose-change,
    revise, critique, doctor, prune-history, next — are each
    named in `.livespec.jsonc` and pre-populated with core's
    reference defaults. Each default is an argv-form array
    whose `${CLAUDE_PLUGIN_ROOT}` placeholder is expanded at
    dispatch time.
    """
    schema = _SCHEMA
    result = livespec_config.validate_livespec_config(payload={}, schema=schema)
    match result:
        case Success(value):
            clis = value.spec_clis
            assert clis.seed == ["python3", "${CLAUDE_PLUGIN_ROOT}/scripts/bin/seed.py"]
            assert clis.propose_change == [
                "python3",
                "${CLAUDE_PLUGIN_ROOT}/scripts/bin/propose_change.py",
            ]
            assert clis.revise == ["python3", "${CLAUDE_PLUGIN_ROOT}/scripts/bin/revise.py"]
            assert clis.critique == [
                "python3",
                "${CLAUDE_PLUGIN_ROOT}/scripts/bin/critique.py",
            ]
            assert clis.doctor == [
                "python3",
                "${CLAUDE_PLUGIN_ROOT}/scripts/bin/doctor_static.py",
            ]
            assert clis.prune_history == [
                "python3",
                "${CLAUDE_PLUGIN_ROOT}/scripts/bin/prune_history.py",
            ]
            assert clis.next == ["python3", "${CLAUDE_PLUGIN_ROOT}/scripts/bin/next.py"]
        case _:
            msg = f"expected Success(LivespecConfig), got {result}"
            raise AssertionError(msg)


def test_validate_livespec_config_spec_clis_individually_overridable() -> None:
    """Overriding one spec-side CLI leaves every sibling at its core default.

    Per `SPECIFICATION/contracts.md` §"Spec-side CLI contract":
    "an alternate implementation of any one operation is
    selected by overriding its name in config. `doctor` is NOT
    privileged: it is config-named and overridable like any
    other spec-side CLI."
    """
    schema = _SCHEMA
    payload: dict[str, object] = {
        "spec_clis": {"doctor": ["my-custom-doctor", "--json"]},
    }
    result = livespec_config.validate_livespec_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.spec_clis.doctor == ["my-custom-doctor", "--json"]
            assert value.spec_clis.seed == [
                "python3",
                "${CLAUDE_PLUGIN_ROOT}/scripts/bin/seed.py",
            ]
        case _:
            msg = f"expected Success(LivespecConfig), got {result}"
            raise AssertionError(msg)


def test_validate_livespec_config_rejects_spec_clis_empty_argv() -> None:
    """An empty argv for a spec-side CLI returns Failure (minItems: 1)."""
    schema = _SCHEMA
    payload: dict[str, object] = {"spec_clis": {"seed": []}}
    result = livespec_config.validate_livespec_config(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "livespec_config:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_livespec_config_orchestrator_absent_yields_none() -> None:
    """When no orchestrator section is configured, the dataclass carries None.

    Per `SPECIFICATION/contracts.md` §"Orchestrator CLI contract
    — the three named CLIs" the orchestrator selection is wired
    by `.livespec.jsonc`; a project without one simply has no
    orchestrator-side CLIs for doctor to verify.
    """
    schema = _SCHEMA
    result = livespec_config.validate_livespec_config(payload={}, schema=schema)
    match result:
        case Success(value):
            assert value.orchestrator is None
        case _:
            msg = f"expected Success(LivespecConfig), got {result}"
            raise AssertionError(msg)


def test_validate_livespec_config_orchestrator_round_trips_three_clis() -> None:
    """A complete orchestrator section round-trips its name + three argv-form CLIs."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "orchestrator": {
            "name": "livespec-orchestrator-beads-fabro",
            "spec_reader": ["impl-beads", "spec-reader"],
            "gap_capture": ["impl-beads", "gap-capture"],
            "drift_capture": ["impl-beads", "drift-capture"],
        },
    }
    result = livespec_config.validate_livespec_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            orchestrator = value.orchestrator
            assert orchestrator is not None
            assert orchestrator.name == "livespec-orchestrator-beads-fabro"
            assert orchestrator.spec_reader == ["impl-beads", "spec-reader"]
            assert orchestrator.gap_capture == ["impl-beads", "gap-capture"]
            assert orchestrator.drift_capture == ["impl-beads", "drift-capture"]
        case _:
            msg = f"expected Success(LivespecConfig), got {result}"
            raise AssertionError(msg)


def test_validate_livespec_config_orchestrator_missing_cli_is_rejected() -> None:
    """An orchestrator section missing any of the three CLIs returns Failure.

    The three orchestrator-side CLIs are the WHOLE cross-boundary
    contract (per §"Orchestrator CLI contract — the three named
    CLIs"); a partial section is a wiring error, not a default.
    """
    schema = _SCHEMA
    payload: dict[str, object] = {
        "orchestrator": {
            "name": "livespec-orchestrator-beads-fabro",
            "spec_reader": ["impl-beads", "spec-reader"],
        },
    }
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
