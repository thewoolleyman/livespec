# Bootstrap status

**Current phase:** 5
**Current sub-step:** Phase 5 §"Aggregate-restoration drain (v034 D7)" — drain sub-cycle 3f in flight: Red commit at sha 2210e11 (full Red trailers, sub_spec_payload test); Green amend pending stages dataclass + validator + STATUS update. Drain cycle 3 progress: 3a-3e done. 1 sub-cycle remains: 3g for `template_config` + binding `check-schema-dataclass-pairing` to the aggregate.
**Last completed exit criterion:** phase 4
**Next action:** Drain sub-cycle 3b — author `schemas/dataclasses/doctor_findings.py` + `validate/doctor_findings.py` + paired tests (per cycle 3a pattern: test-only Red commit → impl Green amend; aggregate-bind for `check-schema-dataclass-pairing` deferred until the LAST sub-cycle since the target only passes once all 6 missing triples are complete).

**Drain rhythm (per 2026-05-02T09:55:00Z `bootstrap/decisions.md` entry):** drain cycles use the Conventional Commit type that honestly describes the work — `test:` for test-coverage strengthening (cycle 1), `chore:` for residual config-tier cleanup AND for the cycle 2.7 commit-pairs amend-skip fix (atomic test+impl form is required to break the catch-22 of fixing commit-pairs while under commit-pairs enforcement), `feat:`/`fix:` for genuine behavior change with full v034 D2 trailer schema via the replay hook + Red→Green amend pattern (per v036 D1 the Red commit's failing test is allowed by `just check-pre-commit`'s Red-mode classifier; per cycle 2.7 the Green amend's source-only staged tree is allowed when HEAD carries unpaired Red trailers), `refactor:` for pure restructuring.

**v034 scope (eight decisions):** D1 Conventional Commits + semantic-release adoption; D2 TDD-Red/Green trailer schema; D3 replay-based enforcement contract via `dev-tooling/checks/red_green_replay.py`; D4 `refs/notes/commits` as advisory operational cache; D5 plan-text + dev-tooling enumeration housekeeping; D6 baseline mechanism via `phase-5-deferred-violations.toml` (deferred indefinitely per v035 D1); D7 Phase 5 §"Aggregate-restoration drain" sub-section (in progress); D8 branch protection on master with deferred end-of-Phase-5 activation.

**Triggered by three concurrent issues:** (1) broken pushes to master because `just check` aggregate is thinned during the v033 D5b drain; CI matrix runs the full canonical-target list while the local hook runs only the thinned aggregate; (2) v033 D4's `## Red output` rule is honor-system content (cannot mechanically prove temporal Red→Green order); (3) PROPOSAL.md §"Versioning" describes spec versioning but does not describe livespec-the-software's version cadence — the Phase 10 v1.0.0 tag goal needs a machine-parseable commit-format path.

**Pre-v034 cycle history preserved as-is:** the v033 D5b second-redo cycles 1-172 used the v033 discipline (`## Red output` honor system; `phase-N: cycle N — ...` commit prefix). They are grandfathered: commitlint will exclude pre-v034-codification ancestor SHAs, and the replay-hook will skip commits without `feat:`/`fix:` subjects.

Open issues: zero unresolved.
**Last updated:** 2026-05-02T20:42:00Z
**Last commit:** drain-sub-cycle-3f pending (feat: sub_spec_payload; Red commit pre-amend at sha 2210e11 with full Red trailers). Prior: 7f9ee8e (3e feat: revision_front_matter), 9d291e8 (3d feat: proposed_change_front_matter + TopicSlug), 5d5116b (3c livespec_config), ecee4af (3b doctor_findings), 611e0d8 (3a finding), a9810b4 (2.8), 2435814 (2.7), db73c11 (2), 70b0752 (v036 impl), 1754534 (v036 codification).
