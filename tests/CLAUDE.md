# tests/

Mirrors `.claude-plugin/scripts/livespec/`,
`.claude-plugin/scripts/bin/`, and `<repo-root>/dev-tooling/`
one-to-one (per plan §"Phase 5 — Test suite" line 1460-1462).

Test scope at Phase 4 (the current bootstrap phase): only
`tests/dev-tooling/checks/` is populated, holding the paired
test files for each enforcement script in `dev-tooling/checks/`.
The full mirroring (tests/livespec/, tests/bin/, tests/e2e/,
tests/prompts/, tests/fixtures/) lands at Phase 5.

Conventions:

- pytest is the test framework (`uv run pytest tests/` or
  `just check-tests`).
- Every directory under `tests/` (except `fixtures/` subtrees)
  carries a `CLAUDE.md` per the strict DoD-13 rule.
- `tests/heading-coverage.json` and similar data files live at
  `tests/<file>` directly; subdirs cover code under test.
