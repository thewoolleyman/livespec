# tests/prompts/livespec/revise/

Fixture directory for the `livespec` template's `prompts/revise.md`
prompt-QA cases. Each `*.json` file conforms to
`tests/prompts/_fixture.schema.json` and is dispatched by
`tests/prompts/livespec/test_revise.py` through the harness with
the per-template `ASSERTIONS` registry.

The bootstrap-minimum catalogue at
`SPECIFICATION/templates/livespec/contracts.md` §"Per-prompt
semantic-property catalogue → prompts/revise.md" lists two
properties (walk every pending proposed-change file before
composing revise-input; emit a per-proposal disposition with a
one-line rationale). The catalogue widens via Phase 7 item (c)'s
per-prompt regeneration cycle; fixtures + assertion functions
widen alongside.
