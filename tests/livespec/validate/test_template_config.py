"""Tests for livespec.validate.template_config.

Per style doc §"Skill layout — `validate/`": validator at
`validate/template_config.py` exports
`validate_template_config(payload, schema)` returning
`Result[TemplateConfig, ValidationError]`.

Per v011 K5: a template's `template.json` declares its format
version, spec_root location, optional doctor extensibility
hooks, and optional LLM-prompt paths.

Per the v2 manifest mechanism (SPECIFICATION/spec.md §"Template
manifest" + contracts.md §"Template manifest wire contract"):
v2 templates additionally declare a `spec_files` manifest with
per-file `kind` discriminators (markdown | diagram_source |
diagram_rendered); diagram_rendered entries also carry a
`derived_from` pointing at a diagram_source entry in the same
manifest.
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from livespec.errors import ValidationError
from livespec.schemas.dataclasses.template_config import SpecFileDecl, TemplateConfig
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


def test_validate_template_config_returns_success_for_minimal_v1_payload() -> None:
    """A minimal v1 payload validates with defaults and spec_files=None."""
    schema = _SCHEMA
    payload: dict[str, object] = {"template_format_version": 1}
    result = template_config.validate_template_config(payload=payload, schema=schema)
    expected = TemplateConfig(
        template_format_version=1,
        spec_root=SpecRoot("SPECIFICATION/"),
        spec_files=None,
        doctor_static_check_modules=[],
        doctor_llm_objective_checks_prompt=None,
        doctor_llm_subjective_checks_prompt=None,
    )
    assert result == Success(expected)


def test_validate_template_config_returns_failure_on_unsupported_version() -> None:
    """A template_format_version outside {1, 2} returns Failure."""
    schema = _SCHEMA
    payload: dict[str, object] = {"template_format_version": 3}
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


def test_validate_template_config_accepts_v2_with_spec_files() -> None:
    """A v2 payload with a well-formed spec_files manifest validates."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "template_format_version": 2,
        "spec_files": {
            "spec.md": {"kind": "markdown"},
            "diagrams/example.plantuml": {"kind": "diagram_source"},
            "diagrams/example.svg": {
                "kind": "diagram_rendered",
                "derived_from": "diagrams/example.plantuml",
            },
        },
    }
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.template_format_version == 2
            assert value.spec_files is not None
            assert value.spec_files["spec.md"] == SpecFileDecl(kind="markdown")
            assert value.spec_files["diagrams/example.plantuml"] == SpecFileDecl(
                kind="diagram_source",
            )
            assert value.spec_files["diagrams/example.svg"] == SpecFileDecl(
                kind="diagram_rendered",
                derived_from="diagrams/example.plantuml",
            )
        case _:
            msg = f"expected Success(TemplateConfig), got {result}"
            raise AssertionError(msg)


def test_validate_template_config_rejects_v2_without_spec_files() -> None:
    """A v2 payload missing spec_files returns Failure."""
    schema = _SCHEMA
    payload: dict[str, object] = {"template_format_version": 2}
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "template_config:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_template_config_rejects_v1_with_spec_files() -> None:
    """A v1 payload declaring spec_files returns Failure.

    Drives the schema's `else` branch: v1 templates synthesize
    their manifest implicitly from the seed prompt's well-known
    file set; declaring spec_files on a v1 template is forbidden.
    """
    schema = _SCHEMA
    payload: dict[str, object] = {
        "template_format_version": 1,
        "spec_files": {"spec.md": {"kind": "markdown"}},
    }
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "template_config:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_template_config_rejects_diagram_rendered_without_derived_from() -> None:
    """A diagram_rendered entry missing derived_from returns Failure."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "template_format_version": 2,
        "spec_files": {
            "spec.md": {"kind": "markdown"},
            "diagrams/example.svg": {"kind": "diagram_rendered"},
        },
    }
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "template_config:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_template_config_rejects_markdown_with_derived_from() -> None:
    """A markdown entry carrying derived_from returns Failure.

    Drives the per-entry if/then/else: derived_from is REQUIRED
    for diagram_rendered and FORBIDDEN otherwise.
    """
    schema = _SCHEMA
    payload: dict[str, object] = {
        "template_format_version": 2,
        "spec_files": {
            "spec.md": {"kind": "markdown", "derived_from": "anywhere"},
        },
    }
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "template_config:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_template_config_rejects_orphan_derived_from() -> None:
    """A diagram_rendered whose derived_from doesn't resolve to a source returns Failure.

    Drives the post-schema cross-property check in
    `validate_template_config`: every diagram_rendered's
    derived_from MUST point at a path that exists in spec_files
    as a kind: diagram_source entry. JSON Schema can't express
    this (refs across instance fields), so the validator runs
    the check after schema validation.
    """
    schema = _SCHEMA
    payload: dict[str, object] = {
        "template_format_version": 2,
        "spec_files": {
            "spec.md": {"kind": "markdown"},
            "diagrams/orphan.svg": {
                "kind": "diagram_rendered",
                "derived_from": "diagrams/nonexistent.plantuml",
            },
        },
    }
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "derived_from" in str(err)
            assert "diagrams/nonexistent.plantuml" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_template_config_rejects_derived_from_pointing_at_markdown() -> None:
    """A diagram_rendered whose derived_from points at a non-diagram_source returns Failure.

    The post-schema cross-property check rejects derived_from
    references that resolve to entries of a different kind.
    """
    schema = _SCHEMA
    payload: dict[str, object] = {
        "template_format_version": 2,
        "spec_files": {
            "spec.md": {"kind": "markdown"},
            "diagrams/wrong.svg": {
                "kind": "diagram_rendered",
                "derived_from": "spec.md",
            },
        },
    }
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "derived_from" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


_SPECIFICATION_TEMPLATES_DIR = (
    Path(__file__).resolve().parents[3] / ".claude-plugin" / "specification-templates"
)


def test_shipped_livespec_template_json_validates() -> None:
    """The shipped built-in `livespec` template.json validates as v1 unchanged.

    Regression check: the v2 manifest mechanism MUST NOT break
    the existing v1 built-in template.
    """
    schema = _SCHEMA
    template_json_path = _SPECIFICATION_TEMPLATES_DIR / "livespec" / "template.json"
    payload = json.loads(template_json_path.read_text(encoding="utf-8"))
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.template_format_version == 1
            assert value.spec_files is None
        case _:
            msg = f"expected Success(TemplateConfig), got {result}"
            raise AssertionError(msg)


def test_shipped_minimal_template_json_validates() -> None:
    """The shipped built-in `minimal` template.json validates as v1 unchanged."""
    schema = _SCHEMA
    template_json_path = _SPECIFICATION_TEMPLATES_DIR / "minimal" / "template.json"
    payload = json.loads(template_json_path.read_text(encoding="utf-8"))
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.template_format_version == 1
        case _:
            msg = f"expected Success(TemplateConfig), got {result}"
            raise AssertionError(msg)


def test_shipped_livespec_with_diagrams_template_json_validates() -> None:
    """The new `livespec-with-diagrams` template.json validates as v2.

    Asserts the shipped template.json is structurally well-formed,
    declares the six NLSpec markdown files plus the starter
    diagram_source / diagram_rendered pair, and that the
    derived_from cross-property invariant holds (the post-schema
    check would fail the validator otherwise).
    """
    schema = _SCHEMA
    template_json_path = _SPECIFICATION_TEMPLATES_DIR / "livespec-with-diagrams" / "template.json"
    payload = json.loads(template_json_path.read_text(encoding="utf-8"))
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.template_format_version == 2
            assert value.spec_files is not None
            assert "spec.md" in value.spec_files
            assert value.spec_files["spec.md"].kind == "markdown"
            assert "diagrams/example.plantuml" in value.spec_files
            assert value.spec_files["diagrams/example.plantuml"].kind == "diagram_source"
            assert "diagrams/example.svg" in value.spec_files
            rendered = value.spec_files["diagrams/example.svg"]
            assert rendered.kind == "diagram_rendered"
            assert rendered.derived_from == "diagrams/example.plantuml"
        case _:
            msg = f"expected Success(TemplateConfig), got {result}"
            raise AssertionError(msg)


def test_shipped_livespec_with_diagrams_specification_template_files_present() -> None:
    """The new template's specification-template/SPECIFICATION/ tree ships every manifest entry.

    Reads the template.json's spec_files manifest and asserts every
    declared path exists as a file on disk under the template's
    `specification-template/` seed root. Catches manifest-vs-shipped
    drift at test time rather than at first-seed time.
    """
    schema = _SCHEMA
    template_dir = _SPECIFICATION_TEMPLATES_DIR / "livespec-with-diagrams"
    template_json_path = template_dir / "template.json"
    payload = json.loads(template_json_path.read_text(encoding="utf-8"))
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.spec_files is not None
            spec_template_root = (
                template_dir / "specification-template" / value.spec_root.rstrip("/")
            )
            for rel_path in value.spec_files:
                assert (spec_template_root / rel_path).is_file(), (
                    f"manifest entry {rel_path!r} missing from " f"{spec_template_root}",
                )
        case _:
            msg = f"expected Success(TemplateConfig), got {result}"
            raise AssertionError(msg)


def test_validate_template_config_accepts_multiple_renders_per_source() -> None:
    """Multiple diagram_rendered entries MAY share the same derived_from.

    Per contracts.md §"Template manifest wire contract": a single
    diagram_source file may produce multiple diagram_rendered
    outputs (e.g., one .puml file with multiple @startuml blocks).
    """
    schema = _SCHEMA
    payload: dict[str, object] = {
        "template_format_version": 2,
        "spec_files": {
            "diagrams/many.plantuml": {"kind": "diagram_source"},
            "diagrams/many-a.svg": {
                "kind": "diagram_rendered",
                "derived_from": "diagrams/many.plantuml",
            },
            "diagrams/many-b.svg": {
                "kind": "diagram_rendered",
                "derived_from": "diagrams/many.plantuml",
            },
        },
    }
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.spec_files is not None
            assert len(value.spec_files) == 3
        case _:
            msg = f"expected Success(TemplateConfig), got {result}"
            raise AssertionError(msg)
