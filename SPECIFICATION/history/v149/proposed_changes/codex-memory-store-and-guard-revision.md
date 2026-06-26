---
proposal: codex-memory-store-and-guard.md
decision: accept
revised_at: 2026-06-26T06:35:37Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accept ENFORCE-codex Option C contract change (epic livespec-hso8 / co9h). Three edits to SPECIFICATION/contracts.md within existing sections (no new H2, no scenario, no heading-coverage churn): generalize the memory-store language to cover Codex's ~/.codex/memories/; note the per-runtime auto-memory-write-guard pair; and require the Codex Driver to ship a pre_tool_use guard for the hookable manual-write path, with the stated limitation that background-generated memories are outside the hook lifecycle. Mirrors the existing 'Codex footgun guard' required-Driver-surface precedent. Implements the maintainer's 2026-06-26 Option C decision.

## Resulting Changes

- contracts.md
