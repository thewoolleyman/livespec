# Bootstrap status

**Current phase:** 4
**Current sub-step:** 13
**Last completed exit criterion:** phase 3
**Next action:** Phase 4 sub-step 13 — author `file_lloc.py` (file ≤ 200 logical lines per style doc lines 1457-1472). HALTED: pre-authoring audit (tokenize-based NEWLINE-token count) reveals two existing supervisors over budget — `commands/revise.py` (233 LLOC), `commands/seed.py` (225 LLOC). Spec is strict ("Waivers not permitted; a function/file that can't meet the thresholds MUST be decomposed; the gate has no escape hatch"). Decomposition is a real architectural call with multiple shapes; the `private_calls` rule (no cross-module `_`-prefixed imports) constrains the options. Awaiting user direction on decomposition strategy before authoring file_lloc.py + supervisor refactors. Sub-step 12 closed: authored `dev-tooling/checks/assert_never_exhaustiveness.py` (every `match` MUST terminate with `case _: assert_never(<subject>)` per style doc lines 983-1008) + 10 paired tests; removed the `_unreachable(value=<x>)` wrapper from 7 supervisors (the wrapper's `value: object` typing defeated pyright's exhaustiveness narrowing) and replaced with direct `case _: assert_never(<subject>)` form; dropped `NoReturn` imports no longer needed. 114 dev-tooling tests passing. Phase 4 progress: 13 of ~22 enforcement scripts done (file_lloc.py is sub-step 13's target, blocked on decomposition strategy).
**Last updated:** 2026-04-27T23:55:00Z
**Last commit:** ffca9fb
