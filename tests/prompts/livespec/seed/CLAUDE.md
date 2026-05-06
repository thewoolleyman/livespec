# tests/prompts/livespec/seed/

Fixture directory for the `livespec` template's `prompts/seed.md`
prompt-QA cases. Each `*.json` file conforms to
`tests/prompts/_fixture.schema.json` (validated at load time)
and is dispatched by `tests/prompts/livespec/test_seed.py`
through the harness with the per-template `ASSERTIONS` registry.

Cases ship with `expected_semantic_properties` listing the
property names from `SPECIFICATION/templates/livespec/contracts.md`
§"Per-prompt semantic-property catalogue → prompts/seed.md" that
the canonical `replayed_response` MUST satisfy. The catalogue
widens via Phase 7 item (c)'s per-prompt regeneration cycle;
fixtures + assertion functions widen alongside.
