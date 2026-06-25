"""Prompt-QA tests for the `minimal` template's `prompts/propose-change.md`.

Parametrizes over every `*.json` fixture under
`tests/prompts/minimal/propose-change/`, dispatches each fixture
through the harness with the per-template `ASSERTIONS` registry,
and asserts the fixture's declared properties hold for its
`replayed_response`.

Per SPECIFICATION/templates/minimal/contracts.md, the
catalogue starts at a single placeholder property; per-prompt
regeneration cycles widen the catalogue and add matching
assertion functions.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from _harness import assert_fixture

__all__: list[str] = []


_FIXTURE_DIR = Path(__file__).resolve().parent / "propose-change"


@pytest.mark.parametrize(
    "fixture_path",
    sorted(_FIXTURE_DIR.glob("*.json")),
    ids=lambda p: p.name,
)
def test_propose_change_prompt_qa(
    *,
    fixture_path: Path,
    assertions: dict[str, Callable[..., None]],
) -> None:
    assert_fixture(fixture_path=fixture_path, assertions=assertions)
