---
proposal: claude-opus-critique.md
decision: accept
revised_at: 2026-05-07T08:02:27Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus
---

## Decision and Rationale

The proposal targets the exact blocker line in contracts.md (§"Pre-commit step ordering" line 93) and replaces it with a concrete prescriptive paragraph plus a follow-up safety-net paragraph. Master-branch and merge-queue runs still execute the full aggregate per the audit-trail invariant. The reference to python-skill-script-style-requirements.md was dropped during application because that file is in archive/ (frozen historical artifacts); the categorization mandate now lives inline in this paragraph, which is the authoritative home.

## Resulting Changes

- contracts.md
