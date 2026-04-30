# Bootstrap status

**Current phase:** 5
**Current sub-step:** Phase 5 §"Retroactive TDD redo of Phase 3 + Phase 4 work — second attempt (v033 D5b)" — about to start cycle 1 of the second redo
**Last completed exit criterion:** phase 4
**Next action:** v033 D5a steps 1-5 + D5b steps 1-2 complete. Lefthook installed at e89deff → `just bootstrap` (e89deff is the LAST ungated commit). From the next commit onward, every commit is mechanically gated by lefthook pre-commit:

1. `just check-commit-pairs-source-and-test` (cheap; staged-file inspection) — every feature/bugfix commit touching `livespec/**`/`bin/**`/`dev-tooling/checks/**` MUST also touch `tests/**`.
2. `just check-red-output-in-commit` (cheap; `git log` walk) — every redo commit (`phase-5: cycle <N> — ...`) MUST contain `## Red output` block in body.
3. `just check` (thinned aggregate per Path 2) — currently `check-imports-architecture` + `check-tests`. Each second-redo cycle restoring a check brings its target back into the aggregate in the same commit.

D5b step-1 stash + step-2 deletion landed at 609db8e (82 .py files archived to `bootstrap/scratch/pre-second-redo.zip`, deleted from tree). Working tree state: clean second-redo baseline — all v033-D5a guardrails (4 dev-tooling scripts + 4 paired tests) plus preserved files (_bootstrap.py, tests/bin/test_bootstrap.py, conftest.py, vendored libs, all CLAUDE.md, all `__init__.py` files). 8 tests passing. `just check` (thinned) passes.

Cycles 1-56 + Phase-4-scaffold preserved in linear history (per Case-B direct-fix at 4f63f0b which switched D5b mechanism from `git reset --hard + cherry-pick` to `stash + git rm` — see `bootstrap/decisions.md`).

**Next sub-step (D5b cycle 1):** start the second retroactive redo. First Red→Green pair is the v033 D5b plan's "outermost rail": author the Phase-3-exit-criterion seed-round-trip integration test as the outermost test, then drop into a unit test at the layer where the integration test's failure is too coarse to drive design. Each cycle commit:
- modifies source under livespec/**/bin/**/dev-tooling/checks/** AND its paired test under tests/**
- carries a `## Red output` fenced block in commit body
- per-file 100% coverage on the just-authored source (when the cycle re-adds `check-coverage` to the aggregate)

Per v033 D1 mirror-pairing exemption (which the second redo will progressively bring into the aggregate): `_vendor/**`, `bin/_bootstrap.py`, and empty-init `__init__.py` files are exempt. Cycle 66 (or wherever appropriate) will re-add `check-tests-mirror-pairing` to the aggregate after broadening the cycle-1 exemption logic to handle the docstring-+-`__all__` shape of the existing `__init__.py` files.

Open issues: zero unresolved.
**Last updated:** 2026-04-30T02:05:00Z
**Last commit:** e89deff
