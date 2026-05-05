# tests/prompts/minimal/propose-change/

Fixture directory for the `minimal` template's
`prompts/propose-change.md` prompt-QA cases. Each `*.json` file
conforms to `tests/prompts/_fixture.schema.json` and is
dispatched by `tests/prompts/minimal/test_propose_change.py`
through the harness with the per-template `ASSERTIONS` registry.

Per `SPECIFICATION/templates/minimal/contracts.md` §"Per-prompt
semantic-property catalogue → prompts/propose-change.md", the
bootstrap-minimum catalogue is a single placeholder property
documenting the Phase 7 item (d) widening intent. Phase 7 widens
the catalogue to the full assertion surface; fixtures + assertion
functions widen alongside.
