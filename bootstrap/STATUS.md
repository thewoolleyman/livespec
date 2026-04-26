# Bootstrap status

**Current phase:** 4
**Current sub-step:** 5
**Last completed exit criterion:** phase 3
**Next action:** Phase 4 sub-step 5 — author the next batch of dev-tooling enforcement scripts. Candidates: `private_calls.py` (bans cross-class _-prefixed access per SLF rule); `global_writes.py` (no module-level mutable state writes; with explicit exemption list per style doc lines 1497-1506); `supervisor_discipline.py` (exactly one catch-all per supervisor); `no_raise_outside_io.py` + `no_except_outside_io.py` (raise/except discipline per livespec/io/** scope); `keyword_only_args.py` (def uses *, dataclass triple frozen+kw_only+slots); etc. Sub-step 4 closed: refactored 5 commands/*.py + doctor/run_static.py supervisors to inline `_dispatch` into `main()` directly (per style doc lines 1474-1481 sys.stdout.write exemption is per-`main()`, NOT per-helper); authored `dev-tooling/checks/no_write_direct.py` + paired test_no_write_direct.py (8 tests passing, both pass and fail cases covered, including bin/_bootstrap exemption + nested-closure-inside-main exemption). Phase 3 round-trip re-verified post-refactor: seed/propose-change/revise/sub-spec all exit 0 with correct shaping. no_write_direct uses recursive _walk function (no ast.NodeVisitor inheritance — would violate v013 M5 direct-parent allowlist).
**Last updated:** 2026-04-27T22:04:27Z
**Last commit:** ed96afd
