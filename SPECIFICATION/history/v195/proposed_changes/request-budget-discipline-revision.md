---
proposal: request-budget-discipline.md
decision: accept
revised_at: 2026-08-05T04:05:21Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Reviewers: two separately-spawned Fable-model agents, named spec-reviewer and spec-reviewer-2 in the driving session. Both were strictly read-only. spec-reviewer-2 verified at 2026-08-05T04:02:17Z and spec-reviewer at 2026-08-05T04:03:08Z, each returning NO BLOCKERS bound to commit 27b90144. Accepted after TWO independently-spawned Fable-model reviewers each returned NO BLOCKERS bound to these exact bytes (commit 27b90144). Both reviewers, without seeing each other's report, independently found the SAME three blockers in the first draft, which is the corroboration this gate exists to produce. All five blockers raised were real and were fixed before acceptance: (1) the replace-target began after a sentence-final period and would have spliced a lowercase conjunction into the spec, so it was widened to cover the whole list item and now yields exactly one resulting text; (2) the Verifier slot forbade any upstream check reading downstream while mandating the fleet-conformance sweep, which is one, so the design record's 'new bespoke' precision was restored; (3) the Mechanism slot claimed a plugin-vendored consumption surface contradicting the one-surface model in the Shared runtime section, so the claim was dropped rather than amending an unrelated section; (4) adopter scope was ambiguous about whether the Verifier inspects an adopter's own code, now explicit that it asserts wiring presence only; (5) two normative MUSTs had no design-record support - the reserved floor is now recorded in the design record with its rationale, and the concurrency clause was softened from an absolute ban to the published ceiling it rests on. Two further wording defects were caught and fixed in review: proposal-time voice ('the existing fleet-conformance sweep') that would have ratified into permanent spec text as a claim expiring at ratification, and an undefined term ('governed consumer') doing load-bearing disambiguation. This registers Request-budget-discipline as a baseline Conformance-Pattern concern and fills its five slots, single-sourcing the existing GitHub App request budget paragraph rather than restating it. Anchored to ledger epic livespec-httc and plan thread plan/github-request-budget-discipline/.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-05T04:02:17Z
verdict: NO BLOCKERS
proposal_stem: request-budget-discipline
content_digest: 90f9d398ddc6152a919f04ad13e44d339581916669dab4611de5ad73783f91b4
