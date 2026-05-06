# tests/prompts/

Prompt-QA tier and SPECIFICATION/contracts.md
§"Prompt-QA harness contract" (v014). Each per-template
subdirectory exercises that template's REQUIRED prompts via
deterministic replay-and-assert against canonical fixtures.

## Layout

- `_harness.py` — the harness framework (load fixture,
  validate fixture-format, validate `replayed_response` against
  the named wire schema, dispatch per-name assertions).
- `_fixture.schema.json` — the fixture-format schema; every
  fixture file MUST validate against this at load time.
- `conftest.py` — adds this directory to `sys.path` so
  per-template test modules can `import _harness` directly.
- `<template>/` — per-template subdirectory containing
  `_assertions.py` (per-template `ASSERTIONS` dict + functions),
  `<prompt>/<case>.json` fixture files, `test_<prompt>.py` test
  modules, and a per-template `conftest.py` mirroring this one.

## Distinction from `tests/e2e/`

The prompt-QA harness performs no LLM round-trip and no wrapper
invocation; it deterministically replays fixture-canned
responses and asserts schema + semantic-property properties.
The end-to-end harness at `tests/e2e/` (per v014 N9 + Phase 9)
exercises wrappers via the Claude Agent SDK surface. The two
harnesses are scope-distinct.

## Coverage scope

`tests/prompts/` is OUT of the unit-tier coverage source list
(`pyproject.toml [tool.coverage.run].source` enumerates only
`livespec/`, `bin/`, `dev-tooling/`). The prompt-QA tier
provides additional confidence but does NOT contribute to the
100% per-file line+branch gate.

## Just target

`just check-prompts` runs `pytest tests/prompts/`; included in
`just check`.
