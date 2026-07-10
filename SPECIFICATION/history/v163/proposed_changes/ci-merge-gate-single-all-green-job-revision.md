---
proposal: ci-merge-gate-single-all-green-job.md
decision: accept
revised_at: 2026-07-10T23:34:16Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Slice 6 of fleet-ci-aggregate-coverage (epic livespec-cf4bcu): codify the single all-green gate-job CI merge-gate model the fleet has already shipped, replacing the superseded 'required-check set MUST cover the full CI matrix' rule and realigning the branch_protection_alignment companion description to the shipped v0.37.3 behavior. Independent Fable adversarial review returned NO-BLOCKERS across two rounds. Maintainer-approved ratification.

## Resulting Changes

- non-functional-requirements.md
