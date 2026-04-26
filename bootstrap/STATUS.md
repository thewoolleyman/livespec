# Bootstrap status

**Current phase:** 4
**Current sub-step:** 4
**Last completed exit criterion:** phase 3
**Next action:** Phase 4 sub-step 4 — refactor the 5 `livespec/commands/*.py` supervisors + `livespec/doctor/run_static.py` to inline their `_dispatch` helper into `main()` directly; then re-author `no_write_direct.py` (the script that surfaced the issue). The style doc's `sys.stdout.write` exemption (lines 1474-1481) is per-supervisor "the function named `main` at module top-level", NOT per-helper. My Phase 3 supervisor pattern split the bug-catcher (in `main()`) from the dispatch logic (in `_dispatch()`), placing the `sys.stdout.write` calls in a helper. The refactor folds them back into `main()`. Phase 3 implementation drift surfaced by Phase 4 enforcement-script work — same precedent as decisions.md 2026-04-26T20:25:13Z (revise.py path-resolution bug surfaced by Phase 3 exit-criterion smoke). Sub-step 3 closed: authored 3 dev-tooling enforcement scripts (`main_guard.py` — bans top-level `if __name__ == "__main__":` in livespec/**; `all_declared.py` — verifies module-top `__all__: list[str]` declaration with every name resolving to a module binding; `no_inheritance.py` — direct-parent allowlist `{Exception, BaseException, LivespecError, NamedTuple, Protocol, TypedDict}` per v013 M5) + 3 paired tests (4+6+8 = 18 tests, all passing, both pass and fail cases covered for each). Each script + test follows the established pattern from sub-step 2 (wrapper_shape).
**Last updated:** 2026-04-26T21:52:10Z
**Last commit:** 8d9671e
