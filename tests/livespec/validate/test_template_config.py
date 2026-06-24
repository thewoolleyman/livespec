"""Tests for livespec.validate.template_config.

Per style doc §"Skill layout — `validate/`": validator at
`validate/template_config.py` exports
`validate_template_config(payload, schema)` returning
`Result[TemplateConfig, ValidationError]`.

A template's `template.json` declares its format version,
spec_root location, optional doctor extensibility hooks, and
optional LLM-prompt paths.

Per the v2 manifest mechanism (SPECIFICATION/spec.md §"Template
manifest" + contracts.md §"Template manifest wire contract"):
v2 templates additionally declare a `spec_files` manifest whose
every entry carries `{kind: markdown}`. livespec manages no
diagram file kinds; an alternate tool's image is an opaque
committed asset, not a manifest-declared file kind.
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

# Module-level schema cache: hypothesis-based @given
# tests run the body ~100 times per invocation; reloading the schema
# from disk on each example pushes individual examples over the
# default 200ms hypothesis deadline under `pytest -n auto` xdist
# worker contention. Loading once at module-import time eliminates
# per-example file I/O and the associated timing nondeterminism.
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))

_SPECIFICATION_TEMPLATES_DIR = (
    Path(__file__).resolve().parents[3] / ".claude-plugin" / "specification-templates"
)


def test_validate_template_config_returns_success_for_minimal_v1_payload() -> None:
    """A minimal v1 payload (just template_format_version) validates with defaults."""
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
    """A v2 payload with a well-formed markdown-only spec_files manifest validates."""
    schema = _SCHEMA
    payload: dict[str, object] = {
        "template_format_version": 2,
        "spec_files": {
            "spec.md": {"kind": "markdown"},
            "contracts.md": {"kind": "markdown"},
        },
    }
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.template_format_version == 2
            assert value.spec_files is not None
            assert value.spec_files["spec.md"] == SpecFileDecl(kind="markdown")
            assert value.spec_files["contracts.md"] == SpecFileDecl(kind="markdown")
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


def test_validate_template_config_rejects_non_markdown_kind() -> None:
    """A spec_files entry whose kind is not `markdown` returns Failure.

    `markdown` is the sole legal manifest kind: livespec manages
    no diagram file kinds, so the schema enum rejects the
    former `diagram_source` / `diagram_rendered` values. This is
    the Red→Green hinge for the rendering-machinery removal — the
    pre-removal validator accepted `diagram_source`; the
    collapsed-enum validator rejects it.
    """
    schema = _SCHEMA
    payload: dict[str, object] = {
        "template_format_version": 2,
        "spec_files": {
            "spec.md": {"kind": "markdown"},
            "diagrams/example.svg": {"kind": "diagram_source"},
        },
    }
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Failure(ValidationError() as err):
            assert "template_config:" in str(err)
        case _:
            msg = f"expected Failure(ValidationError), got {result}"
            raise AssertionError(msg)


def test_validate_template_config_rejects_unknown_per_entry_property() -> None:
    """A spec_files entry carrying an unknown property (e.g. derived_from) returns Failure.

    The per-entry `additionalProperties: false` rejects any key
    beyond `kind`. `derived_from` was the diagram-rendered
    back-reference; it no longer exists in the schema, so a
    payload carrying it is rejected.
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
    """The `livespec-with-diagrams` template.json validates as a markdown-only v2.

    Asserts the shipped template.json is structurally
    well-formed and declares exactly the six NLSpec markdown
    files (no diagram entries — the variant is Mermaid-first, and
    fenced Mermaid blocks live inside the markdown spec files
    themselves, not as separate manifest-declared file kinds).
    """
    schema = _SCHEMA
    template_json_path = _SPECIFICATION_TEMPLATES_DIR / "livespec-with-diagrams" / "template.json"
    payload = json.loads(template_json_path.read_text(encoding="utf-8"))
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.template_format_version == 2
            assert value.spec_files is not None
            assert {path for path, decl in value.spec_files.items() if decl.kind == "markdown"} == {
                "spec.md",
                "contracts.md",
                "constraints.md",
                "non-functional-requirements.md",
                "scenarios.md",
                "README.md",
            }
            assert all(decl.kind == "markdown" for decl in value.spec_files.values())
        case _:
            msg = f"expected Success(TemplateConfig), got {result}"
            raise AssertionError(msg)


def test_shipped_livespec_with_diagrams_template_files_present() -> None:
    """Every spec_files manifest entry ships in the template's seed tree.

    Reads the template.json's spec_files manifest and asserts
    every declared path exists as a file on disk under the
    template's `specification-template/<spec_root>` seed root.
    Catches manifest-vs-shipped drift at test time rather than at
    first-seed time.
    """
    schema = _SCHEMA
    template_dir = _SPECIFICATION_TEMPLATES_DIR / "livespec-with-diagrams"
    payload = json.loads((template_dir / "template.json").read_text(encoding="utf-8"))
    result = template_config.validate_template_config(payload=payload, schema=schema)
    match result:
        case Success(value):
            assert value.spec_files is not None
            seed_root = template_dir / "specification-template" / value.spec_root.rstrip("/")
            for rel_path in value.spec_files:
                assert (
                    seed_root / rel_path
                ).is_file(), f"manifest entry {rel_path!r} missing from {seed_root}"
        case _:
            msg = f"expected Success(TemplateConfig), got {result}"
            raise AssertionError(msg)


def test_shipped_livespec_with_diagrams_seed_spec_carries_mermaid_block() -> None:
    """The variant's seeded spec.md carries a fenced mermaid example block.

    Per SPECIFICATION/spec.md §"Template manifest": the
    `livespec-with-diagrams` variant is Mermaid-first — it seeds
    diagram conventions and example fenced blocks into the
    template's spec files. The fenced block is plain markdown
    content (kind: markdown), so its presence in the seed tree is
    the whole mechanism; this test pins it against accidental
    removal.
    """
    seed_spec = (
        _SPECIFICATION_TEMPLATES_DIR
        / "livespec-with-diagrams"
        / "specification-template"
        / "SPECIFICATION"
        / "spec.md"
    )
    assert "```mermaid" in seed_spec.read_text(encoding="utf-8")
