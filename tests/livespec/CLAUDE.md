# tests/livespec/

Tests for the `livespec` package under
`.claude-plugin/scripts/livespec/`. Mirrors the package's
directory shape one-to-one. Top-level files
(`context.py`, `errors.py`, `types.py`) are covered by
`test_<name>.py` directly under this directory; subpackages
get their own subdirectory with paired tests.

Layered-architecture coverage targets (per
`python-skill-script-style-requirements.md` §"Skill layout"):

- `commands/`, `doctor/` — supervisor + railway tests; assert
  the railway composition produces the expected `IOResult` and
  the supervisor pattern-match emits the right exit code +
  stdout.
- `io/` — impure-layer tests; use real filesystem fixtures
  (`tmp_path`) and the typed facades; exercise the
  `@impure_safe` carriers.
- `parse/`, `validate/` — pure-layer tests; property-based
  tests via Hypothesis are required where applicable
  (`check-pbt-coverage-pure-modules`).
- `schemas/dataclasses/` — wire-dataclass tests cover
  serialization round-trips and field invariants.
