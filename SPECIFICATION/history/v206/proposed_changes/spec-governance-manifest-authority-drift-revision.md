---
proposal: spec-governance-manifest-authority-drift.md
decision: accept
revised_at: 2026-08-14T21:32:49Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5-spec-side-autonomy
---

## Decision and Rationale

Accepted. contracts.md's spec-governance control-wrapper paragraph was wrong in two independent ways -- it named the ConfigKey manifest at a path that resolves to nothing, and it asserted that a declarative registry and that manifest are co-authoritative, which stopped being true in the same relocation (d2ab3cbf, 2026-08-09): registry.py is now a compatibility projection DERIVED from the manifest, so there is one authority, not two in maintained agreement. Correcting only the path would have been worse than correcting neither, because a freshly-accurate path makes the stale architecture claim beside it read as reviewed. The ratified change therefore carries five edits across two spec files: the closing sentence, the --check-default-block clause (which also misstated what the check compares -- it compares the documented block's key set AND values against the manifest rows), the --show-effective clause, spec.md's sentence asserting the INVERTED derivation direction, and spec.md's policy-key table intro. Direction and wording were chosen by the maintainer on 2026-08-14; two declined alternatives are recorded in the proposal. TWO independent adversarial reviews by separately-spawned read-only Fable reviewers ran over six rounds, raising ten blockers, none waived. They repeatedly found disjoint sets and graded three findings differently; the stricter grade was taken each time. Both returned NO BLOCKERS bound to proposal commit a10f8078 and to the exact resulting bytes. The vendoring-enumeration collision the reviews surfaced is deliberately excluded by maintainer direction and recorded as owed.

## Resulting Changes

- contracts.md
- spec.md

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-14T21:21:47Z
verdict: NO BLOCKERS
proposal_stem: spec-governance-manifest-authority-drift
content_digest: 94563ae894bfe8deb544a80bb5be44f276e04aa228b1b014cc826291387c74d9
