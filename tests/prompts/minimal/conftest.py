"""Shared fixtures for tests/prompts/minimal/.

Provides the `assertions` pytest fixture loading
`tests/prompts/minimal/_assertions.py` via importlib with a
unique sys.modules name. Mirrors `tests/prompts/livespec/
conftest.py`; both templates ship a same-named registry, so the
fixture-based loading avoids Python's `import _assertions`
sys.modules collision.
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
        "_minimal_template_assertions",
        _ASSERTIONS_PATH,
    )
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"could not load {_ASSERTIONS_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ASSERTIONS
