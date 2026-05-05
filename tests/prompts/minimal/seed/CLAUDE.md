# tests/prompts/minimal/seed/

Fixture directory for the `minimal` template's `prompts/seed.md`
prompt-QA cases. Each `*.json` file conforms to
`tests/prompts/_fixture.schema.json` and is dispatched by
`tests/prompts/minimal/test_seed.py` through the harness with
the per-template `ASSERTIONS` registry.

The bootstrap-minimum catalogue at
`SPECIFICATION/templates/minimal/contracts.md` §"Per-prompt
semantic-property catalogue → prompts/seed.md" lists two
properties (`sub_specs: []` regardless of input — v020 Q2
opt-out — and a single `files[]` entry at path
`SPECIFICATION.md`). Phase 7 item (d)'s per-prompt regeneration
cycle widens the catalogue; fixtures + assertion functions
widen alongside.
