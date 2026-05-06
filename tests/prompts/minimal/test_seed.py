"""Prompt-QA tests for the `minimal` template's `prompts/seed.md`.

Parametrizes over every `*.json` fixture under
`tests/prompts/minimal/seed/`, dispatches each fixture through
the harness with the per-template `ASSERTIONS` registry, and
asserts the fixture's declared properties hold for its
`replayed_response`.

Per SPECIFICATION/templates/minimal/contracts.md §"Per-prompt
semantic-property catalogue → prompts/seed.md", the
bootstrap-minimum catalogue is two properties (`sub_specs: []`
regardless of input per the v020 Q2 opt-out; single `files[]`
entry at path `SPECIFICATION.md`). Phase 7 item (d)'s per-prompt
regeneration cycle widens the catalogue and adds matching
assertion functions; until then, fixtures may declare empty
`expected_semantic_properties` lists.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from _harness import assert_fixture

__all__: list[str] = []


_FIXTURE_DIR = Path(__file__).resolve().parent / "seed"


@pytest.mark.parametrize(
    "fixture_path",
    sorted(_FIXTURE_DIR.glob("*.json")),
    ids=lambda p: p.name,
)
def test_seed_prompt_qa(
    *,
    fixture_path: Path,
    assertions: dict[str, Callable[..., None]],
) -> None:
    assert_fixture(fixture_path=fixture_path, assertions=assertions)
