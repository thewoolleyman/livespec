"""Tests for livespec/__init__.py.

The module-level structlog configuration runs once at first
import; covering the body requires re-importing the module under
each environment variable variant via importlib.reload.
"""

from __future__ import annotations

import importlib
import logging
import sys
from collections.abc import Iterator
from typing import Any

import pytest

import livespec

__all__: list[str] = []


@pytest.fixture
def reset_livespec_module() -> Iterator[None]:
    """Restore the cached `livespec` module after each reload-based test."""
    saved = sys.modules.get("livespec")
    yield
    if saved is not None:
        sys.modules["livespec"] = saved
    else:
        sys.modules.pop("livespec", None)


def _reload_with_env(*, env: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> Any:
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return importlib.reload(livespec)


def test_default_log_level_is_warning(
    *, monkeypatch: pytest.MonkeyPatch, reset_livespec_module: None
) -> None:
    """Without LIVESPEC_LOG_LEVEL set, the default is WARNING."""
    monkeypatch.delenv("LIVESPEC_LOG_LEVEL", raising=False)
    reloaded = importlib.reload(livespec)
    assert reloaded._resolve_log_level() == logging.WARNING


def test_explicit_log_level_recognized(
    *, monkeypatch: pytest.MonkeyPatch, reset_livespec_module: None
) -> None:
    """LIVESPEC_LOG_LEVEL=DEBUG resolves to logging.DEBUG."""
    reloaded = _reload_with_env(env={"LIVESPEC_LOG_LEVEL": "DEBUG"}, monkeypatch=monkeypatch)
    assert reloaded._resolve_log_level() == logging.DEBUG


def test_invalid_log_level_falls_back_to_warning(
    *, monkeypatch: pytest.MonkeyPatch, reset_livespec_module: None
) -> None:
    """An unknown LIVESPEC_LOG_LEVEL falls back to WARNING via getattr default."""
    reloaded = _reload_with_env(env={"LIVESPEC_LOG_LEVEL": "BOGUS"}, monkeypatch=monkeypatch)
    assert reloaded._resolve_log_level() == logging.WARNING
