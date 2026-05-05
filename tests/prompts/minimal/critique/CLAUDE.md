# tests/prompts/minimal/critique/

Fixture directory for the `minimal` template's `prompts/critique.md`
prompt-QA cases. Each `*.json` file conforms to
`tests/prompts/_fixture.schema.json` and is dispatched by
`tests/prompts/minimal/test_critique.py` through the harness
with the per-template `ASSERTIONS` registry.

Per `SPECIFICATION/templates/minimal/contracts.md` §"Per-prompt
semantic-property catalogue → prompts/critique.md", the
bootstrap-minimum catalogue is a single placeholder property;
Phase 7 item (d)'s per-prompt regeneration cycle widens the
catalogue and adds matching assertion functions + fixture
`expected_semantic_properties` lists.
