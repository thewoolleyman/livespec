# Bootstrap status

**Current phase:** 5
**Current sub-step:** 1
**Last completed exit criterion:** phase 4
**Next action:** Begin Phase 5 (Test suite). Per plan §"Phase 5 — Test suite": build out the test tree mirroring `.claude-plugin/scripts/livespec/`, `.claude-plugin/scripts/bin/`, and `<repo-root>/dev-tooling/` one-to-one; author `tests/bin/test_wrappers.py` (meta-test for 6-statement wrapper shape), per-wrapper coverage tests, `tests/bin/test_bootstrap.py` (covers `_bootstrap.bootstrap()` via `sys.version_info` monkeypatch), `tests/e2e/` skeleton + CLAUDE.md + placeholder `fake_claude.py`, `tests/prompts/<template>/` skeletons + per-template CLAUDE.md + placeholder per-prompt test files, `tests/fixtures/` empty, `tests/heading-coverage.json` empty array, `tests/test_meta_section_drift_prevention.py`. Phase 5 ALSO promotes `just bootstrap` from its Phase-1 placeholder to the real recipe (`lefthook install && ln -sfn ../.claude-plugin/skills .claude/skills`). Phase 5 exit criterion adds these targets to the passing set: check-tests, check-coverage, check-pbt-coverage-pure-modules, check-claude-md-coverage, check-heading-coverage (against empty-array baseline), check-vendor-manifest, check-prompts (against placeholder test files that pass trivially); plus `just bootstrap` run + lefthook installed. The Phase 4 sub-step 26 cleanup commit (67ca34f) and the Case-B plan-fix commit (62e5ab5) leave the codebase ready for Phase 5 work.
**Last updated:** 2026-04-27T06:48:48Z
**Last commit:** 8af9266
