---
proposal: fleet-merged-branch-cleanup.md
decision: accept
revised_at: 2026-07-04T23:28:54Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accepted per maintainer directive (2026-07-05) after the mandatory independent Fable-model adversarial review returned NO-BLOCKERS across all five dimensions (replacement-target fidelity, design-record fidelity vs plan/archive/fleet-merged-branch-cleanup + epic livespec-ixap, drift-sweep completeness, ratification mechanics [topic/stem match; no ## H2 change so no heading-coverage co-edit owed], cross-repo consistency [openbrain constraints.md section verified locally]). Inserts the durable fleet-membership obligation that every fleet-array repo keep delete_branch_on_merge enabled, enforced by a manifest-driven fleet-conformance Verifier with a warn-vs-fail token lever and wire-fleet-member reconcile parity; adopters deliberately out of scope. Ride-along co-edit: an openbrain external_references allowlist entry in .livespec.jsonc so the paragraph's cross-repo section citation clears the doctor-no-cross-spec-reference gate via the check's own blessed path (parallels the existing livespec-dev-tooling entry; no cross_repo_targets clone dependency added).

## Resulting Changes

- non-functional-requirements.md
- ../.livespec.jsonc
