---
proposal: spec-governance-pr-merge-redesign.md
decision: accept
revised_at: 2026-08-10T05:39:29Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accept the spec-governance PR-merge redesign. Four rounds of independent adversarial review of the PROPOSAL closed all seven blockers it raised. Two further independent read-only Fable reviews then examined the exact final resulting_files[] BYTES, which are a different artifact: the first returned one blocker (constraints.md stated 'four further rails' over a paragraph carrying five normative statements — a clause-lockstep defect, fixed by DROPPING the count rather than correcting it, so it cannot rot again), plus a non-blocking Gherkin defect (`Or` used as a step keyword, which is not valid Gherkin and has no precedent in the file, recast as a Scenario Outline); the bytes were rebuilt from freshly fetched origin/master with both fixed, and the second review returned NO BLOCKERS on the rebuilt digest that this record cites. The amendment adds spec_pr_merge with a safe manual default, specifies the caller-supplied per-pull-request conservative fold the rejected v190 draft left unspecified, keeps an explicitly-empty stem set and every derivation failure on the manual floor, and separates the ratified spec requirement from the out-of-scope workflow-file implementation. Payload built from freshly fetched origin/master bytes.

## Resulting Changes

- spec.md
- contracts.md
- constraints.md
- non-functional-requirements.md
- scenarios.md
- ../tests/heading-coverage.json

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-10T05:38:00Z
verdict: NO BLOCKERS
proposal_stem: spec-governance-pr-merge-redesign
content_digest: e3c823dd6767e4b6338657845611b4f07d3524845e3601e7298959863570778a
