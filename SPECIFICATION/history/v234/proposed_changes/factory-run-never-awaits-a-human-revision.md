---
proposal: factory-run-never-awaits-a-human.md
decision: modify
revised_at: 2026-10-30T21:11:27Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

MODIFY (punctuation only). Adds the non-normative Dispatcher guidance bullet that a factory run never waits on a human: a needs-human outcome terminates the run, preserves its work by reference, and rests the work-item in the ledger's human-gated state, and the Dispatcher reconciles non-terminal runs against the ledger. It matches its reference realization, livespec-orchestrator-beads-fabro contracts section 'A factory run never awaits a human' (v093), softened to SHOULD as fits the section. Delegated decision; the independent reviewer returned NO BLOCKERS on these exact bytes. Reviewer: separately spawned read-only Sonnet 5.5 agent adc62c3a0b6c45299.

## Modifications

The proposal's bullet is appended verbatim. The previously-last bullet (structured iteration journal) now ends with ';' instead of '.', so the list's punctuation stays consistent.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-30T21:09:51Z
verdict: NO BLOCKERS
proposal_stem: factory-run-never-awaits-a-human
content_digest: 735a3fbfea484b8f1309255bb5efe3067c8f004806b28baabbf6c833d9bfe5ff
