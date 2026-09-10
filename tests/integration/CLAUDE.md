# tests/integration/

Integration-tier scenario tests. Each module here exercises a
`SPECIFICATION/scenarios.md` H2 section end-to-end across the
real seams the scenario names — real git repositories under
`tmp_path`, the committed schema, the shipped validator, and the
shipped check module — rather than a single unit in isolation.

`tests.integration` is one of the integration-tier node-id
prefixes declared in `pyproject.toml`'s `scenario_tiers`, so a
`tests/heading-coverage.json` entry for a `scenarios.md` heading
MAY map here. Every module additionally declares
`pytestmark = pytest.mark.integration`, so the tier holds whether
the reader resolves it by prefix or by marker.

Conventions:

- Drive real `git` subprocesses for author/commit behavior; never
  spawn a Python subprocess (the in-process `main()` /
  `run(ctx=...)` call is the pattern, per
  `check-tests-no-subprocess-spawn`).
- Assert on the shipped surface's own output (a `Finding`'s
  status and message, a railway carrier), not on internals.
