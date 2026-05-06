"""Shared fixtures for tests/prompts/livespec/.

Provides the `assertions` pytest fixture loading
`tests/prompts/livespec/_assertions.py` via importlib with a
unique sys.modules name, avoiding the collision Python's bare
`import _assertions` would otherwise hit when both built-in
templates ship a same-named registry. Per
SPECIFICATION/contracts.md §"Prompt-QA harness contract" (v014)
the per-template `_assertions.py` filename is pinned; the
fixture-based loading is the test-infrastructure mechanism that
preserves the contract.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path

import pytest

__all__: list[str] = []


_ASSERTIONS_PATH = Path(__file__).resolve().parent / "_assertions.py"


@pytest.fixture
def assertions() -> dict[str, Callable[..., None]]:
    spec = importlib.util.spec_from_file_location(
        "_livespec_template_assertions",
        _ASSERTIONS_PATH,
    )
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"could not load {_ASSERTIONS_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ASSERTIONS
