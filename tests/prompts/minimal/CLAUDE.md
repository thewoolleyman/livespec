# tests/prompts/minimal/

Prompt-QA tests for the `minimal` built-in template's REQUIRED
prompts (`prompts/seed.md`, `prompts/propose-change.md`,
`prompts/revise.md`, `prompts/critique.md`).

## Layout

- `_assertions.py` — per-template `ASSERTIONS: dict[str,
  Callable[..., None]]` registry, populated via explicit
  imports per the static-enumeration discipline. Property names
  mirror the entries codified in
  `SPECIFICATION/templates/minimal/contracts.md` §"Per-prompt
  semantic-property catalogue".
- `conftest.py` — adds this directory to `sys.path` so test
  modules can `import _assertions` at top level.
- `<prompt-name>/<case>.json` — fixture files (one
  subdirectory per REQUIRED prompt; one or more `*.json` cases
  per subdirectory). Each fixture conforms to
  `tests/prompts/_fixture.schema.json`.
- `test_<prompt>.py` — pytest test module that parametrizes
  over `<prompt-name>/*.json` and dispatches each fixture to
  the harness via `_assertions.ASSERTIONS`.

## Catalogue widening

The bootstrap-minimum catalogue at Phase 6 carries 1-2 properties
per prompt; Phase 7 item (d)'s per-prompt regeneration cycle
widens the catalogue and the matching `_assertions.py` entries
+ fixture `expected_semantic_properties` lists land alongside.
The minimal template's seed-prompt catalogue specifically pins
the v020 Q2 sub-spec opt-out (`sub_specs: []` regardless of input)
plus the single-file `files[]` entry at path `SPECIFICATION.md`.
