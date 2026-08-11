---
topic: spec-pr-merge-durable-evidence-locus
author: claude-spec-side-autonomy
created_at: 2026-08-11T05:14:01Z
---

## Proposal: Name the durable-evidence locus for the spec_pr_merge journal event

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add one sentence to the spec_pr_merge journal-event clause in contracts.md naming where the durable final-evidence record lives: the GitHub pull-request timeline MAY serve as that leg, so the journal itself is a decision gate — it records which setting governed the registration attempt and refuses to proceed when it cannot be written — rather than its durable archive. This is a NEW normative clause, judged on its merits. It is not a restoration and does not reverse anything v200 ratified.

### Lineage — stated precisely, because an earlier filing of this proposal got it wrong

An earlier revision of this proposal claimed to "restore accidentally-dropped" text and cited SPECIFICATION/history/v190/proposed_changes/spec-governance-pr-merge.md as a design record. That framing was FALSE and an independent adversarial review caught it.

That v190 proposal was REJECTED. Its paired disposition record SPECIFICATION/history/v190/proposed_changes/spec-governance-pr-merge-revision.md carries `decision: reject` with the rationale "Dropped from Increment 1 after three consecutive BLOCKERS passes ... it must be redesigned and refiled separately before ratification." Corroborating: v190's own ratified SPECIFICATION/history/v190/contracts.md contains ZERO occurrences of `spec_pr_merge` on every counting method, with a positive control confirming the same query does find the term in v200's contracts.md. The evidentiary point is zero-versus-present; no magnitude is quoted here deliberately, because a count in an archived design record is a derived value that rots, and re-deriving it is one command. The sentence therefore never appeared in any ratified spec file, nothing was dropped, and the v200 redesign WAS the mandated refile.

The general trap, recorded so the next author avoids it: a history cut archives accepted and rejected proposals side by side under the same `proposed_changes/` directory, and only the paired `<stem>-revision.md` front matter distinguishes them. A file's presence in a history cut is not evidence it was ratified.

### Motivation

The v200-ratified text is silent on where the durable final-evidence record for a merge-registration attempt lives. That silence has a concrete cost, already paid: an implementer working the workflow half halted, because the contract requires appending to a journal at `<project-root>/tmp/livespec-spec-governance-journal.jsonl` while giving no basis for judging whether that ephemeral location — inside a GitHub Actions runner's discarded `$GITHUB_WORKSPACE`, under a gitignored path — is an intentional design choice or a defect to be worked around. Nothing in the live spec answers it, so the honest options were to invent a persistence mechanism the contract never names or to stop. Naming the locus resolves that without weakening any existing obligation.

The clause is also the least-surprising reading of the surrounding contract, which already requires the event to carry the resolved pull-request effective policy and its effective source — that is a decision record, not an archive — and already requires journal failure to prevent registration, which is gate behavior.

### Proposed Changes

In SPECIFICATION/contracts.md, under the existing `### Spec-governance control wrapper` heading (no heading is added, changed, or removed — this edit lands inside the existing journal paragraph, so no tests/heading-coverage.json co-edit is owed), locate the live sentence: "An `auto-on-green` merge-registration attempt MUST append an event naming `spec_pr_merge`, the pull-request identity, the derived proposal-stem set, the resolved pull-request effective policy and its effective source, the registration result, the required-gate state, and the final merge evidence when available; it MUST NOT carry raw proposal or resulting-file content, following the same digest-only discipline as every other event." Immediately after that sentence, and before the existing sentences "Every automated `revise_decision` event MUST append before mutation. Journal failure requires human input and prevents the governed mutation, disposition, or merge registration." (both UNCHANGED and NOT weakened — journal failure still prevents registration exactly as today), insert one new sentence: "The GitHub pull-request timeline MAY serve as the durable final-evidence leg for this event; the journal is the decision gate — it records which setting governed the registration attempt and refuses to proceed when it cannot be written — rather than its durable archive."

The inserted sentence is scoped to this event by "for this event" and by "its durable archive", so it makes no claim about the durability of the authoring, doctor, ratification, or revise_decision events the same journal also carries. Every existing MUST and MUST NOT in the paragraph is left intact.
