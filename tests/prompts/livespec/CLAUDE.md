# tests/prompts/livespec/

Prompt-QA tests for the `livespec` built-in template's REQUIRED
prompts (`prompts/seed.md`, `prompts/propose-change.md`,
`prompts/revise.md`, `prompts/critique.md`).

## Layout

- `_assertions.py` — per-template `ASSERTIONS: dict[str,
  Callable[..., None]]` registry, populated via explicit
  imports per the static-enumeration discipline. Property
  names mirror the entries codified in
  `SPECIFICATION/templates/livespec/contracts.md` §"Per-prompt
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

The per-prompt semantic-property catalogue starts at
bootstrap-minimum and widens via the in-line per-prompt
regeneration cycles in Phase 7 item (c). When a regeneration
cycle adds a property to the catalogue, it ALSO adds the
matching assertion function to `_assertions.py` and
`expected_semantic_properties` entry to the relevant fixture(s).
