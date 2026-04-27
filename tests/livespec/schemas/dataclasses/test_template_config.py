"""Tests for livespec.schemas.dataclasses.template_config."""

from __future__ import annotations

from pathlib import Path

from livespec.schemas.dataclasses.template_config import TemplateConfig
from livespec.types import SpecRoot

__all__: list[str] = []


def test_default_spec_root_and_check_modules() -> None:
    """`_DEFAULT_SPEC_ROOT` and `_empty_check_modules()` factory cover their lines."""
    cfg = TemplateConfig(template_format_version=1)
    assert str(cfg.spec_root) == "SPECIFICATION/"
    assert cfg.doctor_static_check_modules == []
    assert cfg.doctor_llm_objective_checks_prompt is None
    assert cfg.doctor_llm_subjective_checks_prompt is None


def test_custom_spec_root() -> None:
    cfg = TemplateConfig(
        template_format_version=1,
        spec_root=SpecRoot(Path(".")),
    )
    assert cfg.spec_root == Path(".")


def test_check_modules_factory_returns_fresh_list() -> None:
    """Independent instances each get their own list (no shared-default pitfall)."""
    a = TemplateConfig(template_format_version=1)
    b = TemplateConfig(template_format_version=1)
    assert a.doctor_static_check_modules is not b.doctor_static_check_modules


def test_doctor_prompts_optional() -> None:
    cfg = TemplateConfig(
        template_format_version=2,
        doctor_llm_objective_checks_prompt="prompts/doctor_obj.md",
        doctor_llm_subjective_checks_prompt="prompts/doctor_subj.md",
    )
    assert cfg.doctor_llm_objective_checks_prompt == "prompts/doctor_obj.md"
    assert cfg.doctor_llm_subjective_checks_prompt == "prompts/doctor_subj.md"
