---
proposal: spec-pr-merge-durable-evidence-locus.md
decision: accept
revised_at: 2026-08-11T06:40:52Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted. The proposal adds one normative sentence to the existing `spec_pr_merge` journal-event clause in contracts.md, naming the GitHub pull-request timeline as a permitted durable final-evidence leg and characterizing the journal as the decision gate for that event rather than its durable archive. It resolves a real, already-paid ambiguity: the contract requires appending the event to a journal at a gitignored, runner-ephemeral path while giving no basis for judging whether that location is intentional, which halted an implementer. The clause is additive and permissive (MAY); every existing MUST and MUST NOT in the paragraph is left byte-identical, including the requirement that journal failure prevents merge registration, so no obligation is weakened. It is scoped to this event by the phrases "for this event" and "its durable archive", making no claim about the authoring, doctor, ratification, or revise_decision events the same journal carries. The proposal's Lineage section states its own provenance correctly and self-corrects an earlier false restoration claim: the v190 proposal it once cited was rejected, and this is a new normative clause judged on its merits rather than a restoration or a reversal of anything v200 ratified. The edit adds, changes, and removes no `## ` heading -- the 22-heading H2 set of contracts.md is identical before and after, verified by diff -- so no tests/heading-coverage.json co-edit is owed. Review history: two independent adversarial reviews cleared the proposal file's bytes (sha256 d8db5d979d284e6281d14039bef3cd18f3ae6aae1b1a0f0f010b0283ced47866) before this pass; because ratification evidence binds to a canonical digest over the proposal bytes plus the final resulting_files bytes rather than to the proposal alone, a third separately-spawned read-only Fable reviewer additionally verified the exact final bytes recorded in the Ratification Review section below and returned NO BLOCKERS. The effective ratification_review mode is manual-spawn (the safe default; neither .livespec.jsonc nor this proposal's front matter overrides it), and the driver initiated that review as the prose permits.

## Resulting Changes

- contracts.md

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-11T06:36:50Z
verdict: NO BLOCKERS
proposal_stem: spec-pr-merge-durable-evidence-locus
content_digest: 526079e1e67608cc5843b235caa72a62e9ad8e1f52b058f84dd8c59bc5b91132
