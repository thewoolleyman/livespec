---
topic: restore-spec-pr-merge-durable-evidence
author: claude-spec-side-autonomy
created_at: 2026-08-11T05:14:01Z
---

## Proposal: Restore the dropped durable-evidence leg to the spec_pr_merge journal clause

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Restore one accidentally-dropped sentence to the spec_pr_merge journal-event clause in contracts.md: the GitHub pull-request timeline MAY serve as the durable final-evidence leg, so the journal itself is a decision gate (it names the governing setting and refuses registration when it cannot be written) rather than the durable archive. This is a restoration of text present in the v190 design record and silently dropped during the v200 redesign, not a new policy and not a reversal of anything v200 ratified.

### Motivation

The v190 proposal that first introduced this journal event (SPECIFICATION/history/v190/proposed_changes/spec-governance-pr-merge.md) stated: "The GitHub pull-request timeline MAY be the durable final-evidence leg, but the policy journal MUST name the governing setting; journal failure requires human input and prevents registration." I verified that sentence against the live v190 file myself before citing it (grep confirms it verbatim, one match). I then verified it is absent from every live SPECIFICATION/*.md file (grep found zero matches), with a positive control confirming the same grep finds it in v190. I then checked whether v200 dropped it deliberately by reading the ratified v200 proposal file (SPECIFICATION/history/v200/proposed_changes/spec-governance-pr-merge-redesign.md): it mentions spec_pr_merge 27 times and mentions "timeline" or "durab" zero times, again with a positive control confirming both terms appear in the v190 proposal file using the same grep. The v200 redesign's motivation and blockers (the PR merge-base diff derivation, the conservative fold, the dual-source hardening) never discuss durability or evidence retention at all -- the sentence was not superseded by anything in v200, it was simply never carried forward. Restoring it resolves a real implementation blocker: without it, an implementer has no ratified basis for treating the ephemeral tmp/ journal path (inside a GitHub Actions runner's discarded $GITHUB_WORKSPACE) as an intentional design choice rather than a bug, because nothing in the live spec says where the durable record is supposed to live.

### Proposed Changes

In SPECIFICATION/contracts.md, under the existing `### Spec-governance control wrapper` heading (no heading is added, changed, or removed -- this edit lands inside the existing journal paragraph, so no tests/heading-coverage.json co-edit is owed), locate the live sentence: "An `auto-on-green` merge-registration attempt MUST append an event naming `spec_pr_merge`, the pull-request identity, the derived proposal-stem set, the resolved pull-request effective policy and its effective source, the registration result, the required-gate state, and the final merge evidence when available; it MUST NOT carry raw proposal or resulting-file content, following the same digest-only discipline as every other event." Immediately after that sentence (and before the existing following sentence "Every automated `revise_decision` event MUST append before mutation. Journal failure requires human input and prevents the governed mutation, disposition, or merge registration.", which is UNCHANGED and MUST NOT be weakened -- journal failure still prevents registration exactly as today), insert one new sentence: "The GitHub pull-request timeline MAY serve as the durable final-evidence leg for this event; the journal itself is the decision gate -- it records which setting governed the registration attempt and refuses to proceed when it cannot be written -- not the durable archive." This restores, verbatim in substance, the missing half of the v190 design record's journal clause (SPECIFICATION/history/v190/proposed_changes/spec-governance-pr-merge.md), clarifying that an ephemeral CI-local journal location is consistent with the ratified design rather than an oversight, while leaving every existing MUST/MUST NOT in the paragraph completely intact.
