# Bootstrap status

**Current phase:** 4
**Current sub-step:** 12
**Last completed exit criterion:** phase 3
**Next action:** Phase 4 sub-step 12 — author `assert_never_exhaustiveness.py`. Per style doc line 1813: every `match` statement in livespec scope MUST end with a `case _ as <bind>:` (or `case _:`) branch that calls `assert_never(<bind>)` (typically via a small `_unreachable(*, value)` helper). Pyright's strict-mode exhaustiveness check requires this for sum-type matches over Result/IOResult and similar discriminated unions. Sub-step 11 closed: authored `dev-tooling/checks/match_keyword_only.py` (every `match` class-pattern destructuring a livespec-authored class uses `kwd_patterns` not positional `patterns`; third-party returns-package types like `Success`/`Failure`/`IOFailure`/`IOSuccess` permitted positionally; livespec-authored = imported from `livespec.*` OR locally-defined ClassDef) + 9 paired tests. 104 dev-tooling tests passing total. Phase 4 progress: 12 of ~22 enforcement scripts done.
**Last updated:** 2026-04-27T23:38:00Z
**Last commit:** ebf10e6
