---
proposal: comment-discipline-why-not-what.md
decision: accept
revised_at: 2026-05-07T08:02:27Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus
---

## Decision and Rationale

The proposal codifies WHY-not-WHAT and forbids historical-bookkeeping citations in source comments. Inserted as a new top-level section §"Comment discipline" between §"Linter and formatter" and §"Complexity thresholds". The mention of python-skill-script-style-requirements.md was dropped during application because that file is in archive/; the new check `check-comment-no-historical-refs` is categorized as a python-code check per §"Pre-commit step ordering" via an inline note in the new section.

## Resulting Changes

- constraints.md
