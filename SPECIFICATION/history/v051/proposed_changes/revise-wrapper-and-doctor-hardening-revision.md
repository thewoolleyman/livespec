---
proposal: revise-wrapper-and-doctor-hardening.md
decision: accept
revised_at: 2026-05-07T08:52:25Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus
---

## Decision and Rationale

All 4 findings address the v050 silent-data-loss incident's distinct error modes and layer as defense-in-depth: Finding 1 (path-relativity guard in revise wrapper) catches the known error class at validation time. Finding 2 (snapshot-consistency doctor check) catches any future write-silent-failure regardless of root cause at post-step. Finding 3 (schema path-relativity descriptions in contracts.md) prevents the LLM from authoring the bad path in the first place. Finding 4 (require-existing-target rule on resulting_files[]) catches any other path-resolution error at write time. Findings 1, 2, and 4 land in spec.md §"Sub-command lifecycle"; finding 3 lands in contracts.md §"Skill ↔ template JSON contracts".

## Resulting Changes

- spec.md
- contracts.md
