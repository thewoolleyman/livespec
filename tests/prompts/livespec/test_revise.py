"""Prompt-QA tests for the `livespec` template's `prompts/revise.md`.

Parametrizes over every `*.json` fixture under
`tests/prompts/livespec/revise/`, dispatches each fixture
through the harness with the per-template `ASSERTIONS` registry,
and asserts the fixture's declared properties hold for its
`replayed_response`.

Per SPECIFICATION/templates/livespec/contracts.md §"Per-prompt
semantic-property catalogue → prompts/revise.md", the
bootstrap-minimum catalogue is two properties (walk every
pending proposed-change file; emit per-proposal disposition).
Phase 7 item (c)'s per-prompt regeneration cycle widens the
catalogue and adds matching assertion functions; until then,
fixtures may declare empty `expected_semantic_properties` lists.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from _harness import assert_fixture

__all__: list[str] = []


_FIXTURE_DIR = Path(__file__).resolve().parent / "revise"


@pytest.mark.parametrize(
    "fixture_path",
    sorted(_FIXTURE_DIR.glob("*.json")),
    ids=lambda p: p.name,
)
def test_revise_prompt_qa(
    *,
    fixture_path: Path,
    assertions: dict[str, Callable[..., None]],
) -> None:
    assert_fixture(fixture_path=fixture_path, assertions=assertions)
