---
proposal: codex-distributed-driver.md
decision: accept
revised_at: 2026-06-22T23:49:57Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Maintainer has ratified the underlying decisions: establish a true distributed Codex Driver (livespec-driver-codex) analogous to livespec-driver-claude, distribute core to Codex via a .agents/plugins/marketplace.json + .codex-plugin/plugin.json marketplace over the same prose/ and scripts/, require a Codex pre_tool_use footgun-guard hook before mutating Codex automation, lift the read-only restriction so the Codex Driver exposes all eight operations, and retire the repo-local .agents/skills/livespec-* adapter model. All three findings applied verbatim; no H2/H3/H4 heading added, removed, or renamed, so tests/heading-coverage.json is untouched.

## Resulting Changes

- spec.md
- contracts.md
- non-functional-requirements.md
