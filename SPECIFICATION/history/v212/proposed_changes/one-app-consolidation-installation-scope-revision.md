---
proposal: one-app-consolidation-installation-scope.md
decision: accept
revised_at: 2026-08-19T02:33:52Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fabro-on-hp
---

## Decision and Rationale

Maintainer ruling 2026-08-18 (one automation App for all owned repos, installed account-wide so the shared factory servers can clone any governed repo) made the fleet-repos-only installation restriction contradict decided reality. The amendment moves installation breadth to the resource owner's decision while keeping tenant-scoped credential resolution, no-silent-fallback, and least-privilege permissions intact. Independent ratification review returned NO BLOCKERS for the exact resulting bytes.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-19T02:33:20Z
verdict: NO BLOCKERS
proposal_stem: one-app-consolidation-installation-scope
content_digest: 21f4153b63e967b501770c6f7169e4b21373f65301d2a3131a9083bfc80769b9
