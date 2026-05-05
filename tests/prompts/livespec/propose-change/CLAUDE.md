# tests/prompts/livespec/propose-change/

Fixture directory for the `livespec` template's
`prompts/propose-change.md` prompt-QA cases. Each `*.json` file
conforms to `tests/prompts/_fixture.schema.json` and is
dispatched by `tests/prompts/livespec/test_propose_change.py`
through the harness with the per-template `ASSERTIONS` registry.

The bootstrap-minimum catalogue at
`SPECIFICATION/templates/livespec/contracts.md` §"Per-prompt
semantic-property catalogue → prompts/propose-change.md" lists
two properties (per-finding `target_spec_files` referencing the
spec target's tree; BCP14 normative language in
`proposed_changes`). The catalogue widens via Phase 7 item (c)'s
per-prompt regeneration cycle; fixtures + assertion functions
widen alongside.
