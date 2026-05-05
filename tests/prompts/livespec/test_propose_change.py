"""Prompt-QA tests for the `livespec` template's `prompts/propose-change.md`.

Parametrizes over every `*.json` fixture under
`tests/prompts/livespec/propose-change/`, dispatches each
fixture through the harness with the per-template `ASSERTIONS`
registry, and asserts the fixture's declared properties hold
for its `replayed_response`.

Per SPECIFICATION/templates/livespec/contracts.md §"Per-prompt
semantic-property catalogue → prompts/propose-change.md", the
bootstrap-minimum catalogue is two properties (per-finding
`target_spec_files` referencing the spec-target tree; BCP14
normative language in `proposed_changes`). Phase 7 item (c)'s
per-prompt regeneration cycle widens the catalogue and adds
matching assertion functions; until then, fixtures may declare
empty `expected_semantic_properties` lists to assert
schema-conformance only.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from _assertions import ASSERTIONS
from _harness import assert_fixture

__all__: list[str] = []


_FIXTURE_DIR = Path(__file__).resolve().parent / "propose-change"


@pytest.mark.parametrize(
    "fixture_path",
    sorted(_FIXTURE_DIR.glob("*.json")),
    ids=lambda p: p.name,
)
def test_propose_change_prompt_qa(*, fixture_path: Path) -> None:
    assert_fixture(fixture_path=fixture_path, assertions=ASSERTIONS)
