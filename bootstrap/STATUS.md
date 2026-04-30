# Bootstrap status

**Current phase:** 5
**Current sub-step:** Phase 5 §"Retroactive TDD redo of Phase 3 + Phase 4 work — second attempt (v033 D5b)" — coverage-cleanup batch complete; per-file 100% line+branch is now mechanically gated commit-by-commit
**Last completed exit criterion:** phase 4
**Next action:** Coverage-cleanup batch landed at HEAD `ac55b6a`. Total coverage is **100.00%** (1204 statements + 108 branches; zero missing on either axis). Test inventory: **70 passing** (was 49 at batch start; +21 new). The `just check` aggregate is now `(check-imports-architecture, check-tests, check-coverage)`. The user directive "every commit stays at 100%" is mechanically enforced from `ac55b6a` forward — any file slipping below 100% on either line or branch coverage blocks the commit at lefthook pre-commit.

**Coverage-cleanup batch (cycles 103-117 + 2 config commits):**

- `3252c88` (config): pyproject.toml `[tool.coverage.run]` switched from `source = [...]` allowlist to `omit = ["*/_vendor/*", "*/.venv/*", "*/site-packages/*", "*/__pycache__/*"]` blocklist; justfile `check-coverage` recipe gains `--cov-config=pyproject.toml` flag.
- Cycle 103 (`cf303f1`): `livespec/doctor/static/__init__.py` stubbed down to canonical preamble (was importing `livespec.context` which doesn't exist + 8 unauthored Phase-3 check modules; 0% wasn't lack-of-test, it was can't-be-imported).
- Cycle 104 (`7f245e0`): `propose_change.py` cwd-default `spec_target` branch.
- Cycle 105 (`776c813`): `seed.py` cwd-default `project_root` branch.
- Cycle 106 (`1914000`): `seed.py` history+seed-md skip single-component paths.
- Cycle 107 (`28b54fc`): `seed.py` skips seed-md emission when `files[]` is empty.
- Cycles 108-112 (`f7f4a0b`/`6eaf0e3`/`beb39dd`/`bf91525`/`578c2ca`): defensive isinstance-guards in `_write_sub_spec_files` + `_write_sub_spec_history_v001` (private helpers carry runtime `isinstance(...)` guards needed for pyright strict-mode; covered by tests calling underscore-prefixed helpers directly with malformed-typed data).
- Cycles 113-117 (`f045882`/`5fb2a0f`/`1cc134f`/`6bad461`/`65117e9`): the four v033 D5a guardrail scripts brought to 100% — pass-case + importable-without-main + edge-case branches (no-data, git-failure, non-redo-skip, empty-sha).
- `ac55b6a` (config): re-add `check-coverage` to `just check` aggregate's `targets=` list. Last commit of the batch; subsequent commits gate on per-file 100%.

**Two configuration bugs surfaced + fixed:**

1. **pytest-cov silently bypasses pyproject.toml** — `pytest --cov` defaults `--cov-config` to `.coveragerc` (doesn't exist in this repo). Without explicit `--cov-config=pyproject.toml`, the parent-process Coverage instance had no source filter and no omit, AND it forwarded an empty `COV_CORE_CONFIG` to subprocess children. This caused 19 vendored structlog files to inflate the report and the dev-tooling check files to be ad-hoc-instrumented through subprocess auto-discovery.
2. **`source` allowlist was load-bearing-broken under subprocess coverage** — tests that subprocess into `cwd=tmp_path` resolved `dev-tooling` relative to the empty tmp_path, silently dropping `<repo>/dev-tooling/checks/<name>.py` from measurement. Switched to omit-only configuration that works regardless of cwd.

**Test patterns established for future cycles:**

- **Importable-without-main test**: every `dev-tooling/checks/<name>.py` ships a sibling test that imports the module via `importlib.util.spec_from_file_location` + `exec_module` and asserts `module.main` is callable. Closes the `if __name__ == "__main__":` else-arm + the `if str(_VENDOR_DIR) not in sys.path:` already-present branch in one test. Future check-script cycles should follow this pattern.
- **Pass-case + rejection-case as separate tests**: every check ships both arms (rejects bad fixture; accepts good fixture). Closes the success-arm branches that single-rejection cycles miss.
- **Defensive-guard tests calling private helpers**: when an isinstance-guard branch is unreachable post-schema-validation but needed for pyright strict-mode, test it by calling the underscore-prefixed helper directly with malformed-typed data. SLF (flake8-self) only catches cross-class instance/class member access, not module-level private function calls.

**Next sub-step:** resume v033 D5b Phase-3-parity work from cycle 118. Phase-3 work still ahead: critique/revise/prune-history body widening (currently stub-returning-1); doctor static minimum subset (8 checks per Plan Phase 3 detail); post-step doctor wiring in seed.main. Estimated ~30-40 more cycles for Phase-3-exit-criterion parity. Then Phase-4-parity (re-author 25 deleted dev-tooling/checks/*.py scripts + re-add each target to `just check` aggregate).

Open issues: zero unresolved.
**Last updated:** 2026-04-30T04:00:00Z
**Last commit:** ac55b6a
