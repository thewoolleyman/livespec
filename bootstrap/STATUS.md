# Bootstrap status

**Current phase:** 4
**Current sub-step:** 6
**Last completed exit criterion:** phase 3
**Next action:** Phase 4 sub-step 6 — author the next batch. `global_writes.py` (no module-level mutable state writes from functions; with the explicit exemption list per style doc lines 1497-1506: `structlog.configure(...)`, `bind_contextvars(run_id=...)`, and the `_COMPILED` cache mutation in `livespec/io/fastjsonschema_facade.py`); `supervisor_discipline.py` (exactly one catch-all per supervisor; no catch-alls outside supervisors). Sub-step 5 closed: authored `dev-tooling/checks/private_calls.py` (cross-module imports of single-leading-underscore names forbidden; the rule targets imported FUNCTION names, not module names — `from _bootstrap import bootstrap` passes since `bootstrap` is public; bin-wrapper has belt-and-suspenders exemption for that exact form) + 7 paired tests, all passing. Repo passes the check.
**Last updated:** 2026-04-27T22:08:04Z
**Last commit:** dd1c2d0
