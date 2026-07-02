---
proposal: coverage-omit-only-not-source-allowlist.md
decision: accept
revised_at: 2026-07-02T05:38:25Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accept: reconciles the coverage-config prose (non-functional-requirements.md §"Code coverage thresholds" + contracts.md §"Python-rule compliance") with the shipped omit-only blocklist (no source allowlist; a relative source list resolves against the dev-tooling/checks subprocess cwd and silently drops those modules). Verified drift; contributor-only/non-functional, no scenario needed; no heading changes. contracts.md content here is identical to the callability proposal's (cumulative), so the shared-file end state is order-independent.

## Resulting Changes

- non-functional-requirements.md
- contracts.md
