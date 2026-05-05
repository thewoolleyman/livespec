# tests/prompts/livespec/critique/

Fixture directory for the `livespec` template's `prompts/critique.md`
prompt-QA cases. Each `*.json` file conforms to
`tests/prompts/_fixture.schema.json` and is dispatched by
`tests/prompts/livespec/test_critique.py` through the harness
with the per-template `ASSERTIONS` registry.

The bootstrap-minimum catalogue at
`SPECIFICATION/templates/livespec/contracts.md` §"Per-prompt
semantic-property catalogue → prompts/critique.md" lists two
properties (findings grounded in the spec target's current
state; ambiguity/contradiction prioritization over
wording-style). The catalogue widens via Phase 7 item (c)'s
per-prompt regeneration cycle; fixtures + assertion functions
widen alongside.
