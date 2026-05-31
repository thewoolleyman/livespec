# tests/e2e-cli/

The top-of-pyramid, user-surface CLI end-to-end tier for livespec, per
`SPECIFICATION/contracts.md` §"CLI end-to-end harness contract". This is a
SIBLING to `tests/e2e/` (the wrapper-chain tier), not a superset: it adds a
higher tier whose sole interaction surface is the `claude` CLI binary, and
both coexist in CI.

The harness itself is the single canonical implementation that ships from
`livespec-dev-tooling` (`livespec_dev_tooling.testing.cli_e2e`); this repo
is a CONSUMER of it via the pin-bump dependency flow (contract requirement
6). The imported `test_workflow_full_round_trip` entry point is wired into
the collection by `test_cli_e2e.py`, parametrized over the known impl
plugin(s).

## Tier selection — `LIVESPEC_E2E_HARNESS=mock|real`

- `mock` (default) — runs in `just check`/CI. Real plugin discovery
  (`discover_skills` walks `.claude-plugin/skills/*/SKILL.md` + reads the
  prefix from `plugin.json`'s `name`), real fixture loading, and the real
  fail-closed coverage gate all execute; only the `claude -p` subprocess is
  replaced by an injected deterministic runner. This catches install-shape
  and discovery bugs deterministically without an API key.
- `real` — drives the real `claude` binary (requires `ANTHROPIC_API_KEY`).
  NOT part of `just check`; runs via the dedicated CI job / on demand.

## Files

- `test_cli_e2e.py` — the consumer wiring. Imports the harness entry point
  under a non-`test_`-prefixed alias (so pytest does not try to collect the
  library function directly), supplies a `HarnessConfig` pointing discovery
  at the in-repo `.claude-plugin/` source, injects a deterministic fake
  `claude -p` runner that materializes each fixture's expected files, and
  asserts the full round-trip passes. Also carries the red-baseline test
  that proves the time-bomb coverage gate fails closed when a discovered
  skill lacks a fixture (contract requirement 5).
- `conftest.py` — adds `tests/e2e-cli/` to `sys.path`; scrubs inherited
  `GIT_*` env vars; auto-skips `mock_only` items when
  `LIVESPEC_E2E_HARNESS=real` (mirrors `tests/e2e/conftest.py`).
- `fixtures/<skill>/` — one directory per discovered `/livespec:*` skill
  (seed, propose-change, critique, revise, doctor, prune-history, next,
  help), each holding a `prompt.md` (text piped to `claude -p`) and an
  `expected_files.txt` (paths that MUST exist afterward). Directory present
  == fixture exists (contract requirement 4). The `fixtures/` subtree is a
  data tree, exempt from the per-directory CLAUDE.md rule.

## Conventions

- The impl-plugin id is a `HarnessConfig` parameter (contract requirement
  2). livespec-core's consumer tests discover the FIXED spec-side `livespec`
  plugin; the impl-plugin repos own their own `tests/e2e-cli/` consumer
  obligation (contract requirement 7) and discover their own skills paired
  with livespec.
- Coverage measurement does NOT apply to `tests/e2e-cli/` (the source list
  for `[tool.coverage.run]` is anchored at `livespec/`, `bin/`,
  `dev-tooling/`; this is test infrastructure).
