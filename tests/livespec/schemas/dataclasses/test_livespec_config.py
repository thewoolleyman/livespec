"""Tests for livespec.schemas.dataclasses.livespec_config."""

from __future__ import annotations

import dataclasses

import pytest
from livespec.schemas.dataclasses.livespec_config import LivespecConfig
from livespec.types import TemplateName

__all__: list[str] = []


_FORMAT_VERSION_OVERRIDE = 2


def test_default_construction() -> None:
    """No-kwargs construction yields the as-if-missing-file state."""
    cfg = LivespecConfig()
    assert cfg.template == "livespec"
    assert cfg.template_format_version == 1
    assert cfg.post_step_skip_doctor_llm_objective_checks is False
    assert cfg.post_step_skip_doctor_llm_subjective_checks is False
    assert cfg.pre_step_skip_static_checks is False


def test_custom_template() -> None:
    cfg = LivespecConfig(template=TemplateName("minimal"))
    assert cfg.template == "minimal"


def test_skip_flags_override() -> None:
    cfg = LivespecConfig(
        post_step_skip_doctor_llm_objective_checks=True,
        post_step_skip_doctor_llm_subjective_checks=True,
        pre_step_skip_static_checks=True,
    )
    assert cfg.post_step_skip_doctor_llm_objective_checks is True
    assert cfg.post_step_skip_doctor_llm_subjective_checks is True
    assert cfg.pre_step_skip_static_checks is True


def test_template_format_version_override() -> None:
    cfg = LivespecConfig(template_format_version=_FORMAT_VERSION_OVERRIDE)
    assert cfg.template_format_version == _FORMAT_VERSION_OVERRIDE


def test_livespec_config_is_frozen() -> None:
    cfg = LivespecConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.template_format_version = 99  # type: ignore[misc]
