# Bootstrap status

**Current phase:** 4
**Current sub-step:** 2
**Last completed exit criterion:** phase 3
**Next action:** Phase 4 sub-step 2 — begin authoring the dev-tooling enforcement scripts. Start with the simpler AST/grep checks: `wrapper_shape.py` (verifies every `bin/*.py` matches the 6-statement shebang-wrapper shape per style doc lines 1664-1668; permits the optional blank line per v016 P5; exempts `_bootstrap.py`); `main_guard.py` (bans `if __name__ == "__main__":` blocks in `livespec/**`); `all_declared.py` (verifies every module under `livespec/`, `bin/`, `dev-tooling/` declares `__all__: list[str]`); `no_inheritance.py` (direct-parent allowlist per v013 M5: `{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict}`); etc. Each script + paired test in `tests/dev-tooling/checks/test_<name>.py` covering pass + fail cases. Sub-step 1 closed: created `dev-tooling/`, `dev-tooling/checks/`, `tests/`, `tests/dev-tooling/`, `tests/dev-tooling/checks/` directories and authored CLAUDE.md in each per the strict DoD-13 rule. Plan-fix landed at sub-step 1 ramp: vendor_manifest.py description (line 1443-1444) had stale "shim: true on typing_extensions" wording — corrected to "shim: true on jsoncomment" per v026 D1 + v027 D1. Phase 4 has ~22 enforcement scripts ahead; expected to span multiple `--ff` invocations.
**Last updated:** 2026-04-26T21:26:32Z
**Last commit:** e7a1cf4
