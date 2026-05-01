# Bootstrap status

**Current phase:** 5
**Current sub-step:** Phase 5 §"v034 transition — replay-hook activation + drain authorization (v034 D3 / D5 / D6)" — v034 codification commit pending. Next per the v034 D5 transition: (a) author `dev-tooling/checks/red_green_replay.py` + paired test under v033 discipline (~5-10 cycles); (b) replay-hook activation commit (renames `check-red-output-in-commit` → `check-red-green-replay`, removes the v033 hook + paired test, authors initial `phase-5-deferred-violations.toml`, replaces thinned aggregate, adds notes refspec to bootstrap recipe, updates lefthook.yml); (c) v034 D7 drain (~11-15 cycles fixing the 4 unbound aggregate targets + config-tier `check-lint`/`check-format`); (d) v034 D5c quality-comparison report; (e) Phase 5 exit gates (5a/5b/5c); (f) v034 D8 branch protection activation as final Phase 5 sub-step.
**Last completed exit criterion:** phase 4
**Next action:** Stage + commit + push the v034 codification commit. Files: `PROPOSAL.md`, `PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`, `history/v034/PROPOSAL.md` (snapshot), `history/v034/proposed_changes/critique-fix-v033-revision.md` (revision file), `bootstrap/STATUS.md`. Subject: `chore!: codify v034 — TDD-replay, conventional-commits, drain authorization` (the first conventional commit per v034 D1; pre-v034 commits grandfathered).

**v034 scope (eight decisions):** D1 Conventional Commits + semantic-release adoption; D2 TDD-Red/Green trailer schema; D3 replay-based enforcement contract via new `dev-tooling/checks/red_green_replay.py`; D4 `refs/notes/commits` as advisory operational cache; D5 plan-text + dev-tooling enumeration housekeeping; D6 baseline mechanism via `phase-5-deferred-violations.toml` (replaces v033 thinned aggregate); D7 Phase 5 §"Aggregate-restoration drain" sub-section; D8 branch protection on master with deferred end-of-Phase-5 activation.

**Triggered by three concurrent issues:** (1) broken pushes to master because `just check` aggregate is thinned during the v033 D5b drain; CI matrix runs the full canonical-target list while the local hook runs only the thinned aggregate; (2) v033 D4's `## Red output` rule is honor-system content (cannot mechanically prove temporal Red→Green order); (3) PROPOSAL.md §"Versioning" describes spec versioning but does not describe livespec-the-software's version cadence — the Phase 10 v1.0.0 tag goal needs a machine-parseable commit-format path.

**Pre-v034 cycle history preserved as-is:** the v033 D5b second-redo cycles 1-172 used the v033 discipline (`## Red output` honor system; `phase-N: cycle N — ...` commit prefix). They are grandfathered: commitlint will exclude pre-v034-codification ancestor SHAs, and the replay-hook will skip commits without `feat:`/`fix:` subjects.

Open issues: zero unresolved.
**Last updated:** 2026-05-01T08:38:31Z
**Last commit:** 54684d5 (v034 codification commit pending; STATUS will be updated to that SHA post-commit)
