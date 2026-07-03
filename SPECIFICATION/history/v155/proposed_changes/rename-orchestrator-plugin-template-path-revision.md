---
proposal: rename-orchestrator-plugin-template-path.md
decision: accept
revised_at: 2026-07-02T23:58:23Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accept the copier-template path/name rename as filed. The three exact-string renames (templates/impl-plugin/ -> templates/orchestrator-plugin/; 'impl-plugin copier template' -> 'orchestrator-plugin copier template'; 'impl-plugin scaffold' -> 'orchestrator-plugin scaffold') land in contracts.md and non-functional-requirements.md only. The impl-plugin repo-class / role term is deliberately preserved (every impl-plugin repo; each impl-plugin's .github/workflows/; the repo-class enumeration). No ## heading changes, so tests/heading-coverage.json is untouched.

## Resulting Changes

- contracts.md
- non-functional-requirements.md
