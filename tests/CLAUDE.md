# tests/

Mirrors `.claude-plugin/scripts/livespec/`,
`.claude-plugin/scripts/bin/`, and `<repo-root>/dev-tooling/`
one-to-one (per plan §"Phase 5 — Test suite" line 1460-1462).

Test scope at Phase 5 (the current bootstrap phase): the full
mirror tree is populated. `tests/dev-tooling/checks/` (Phase 4)
holds paired tests for each enforcement script.
`tests/livespec/` mirrors the package one-to-one.
`tests/bin/` covers the shebang wrappers (meta-test for the
6-statement shape, per-wrapper coverage via monkeypatched
`main`, and `_bootstrap.bootstrap()` coverage via
`sys.version_info` monkeypatch). `tests/e2e/` carries the
skeleton + placeholder `fake_claude.py` (real e2e content
lands at Phase 9). `tests/prompts/<template>/` carries
per-template placeholder prompt-QA tests (real content lands
at Phase 7). `tests/fixtures/` is empty (grows through
Phases 6–9).

Conventions:

- pytest is the test framework (`uv run pytest tests/` or
  `just check-coverage`; per v039 D1 the standalone
  `check-tests` target is gone — `check-coverage` is the
  canonical pytest-running aggregate target).
- Every directory under `tests/` (except `fixtures/` subtrees)
  carries a `CLAUDE.md` per the strict DoD-13 rule.
- `tests/heading-coverage.json` and similar data files live at
  `tests/<file>` directly; subdirs cover code under test.
