---
topic: codex-contract-binding-wording
author: codex-gpt-5
created_at: 2026-06-19T17:13:39Z
---

## Proposal: Repair remaining contract skill wording

### Target specification files

- SPECIFICATION/contracts.md
- tests/heading-coverage.json

### Summary

Update remaining core contract text that still names SKILL.md or core-owned skills where the current architecture is operation prose plus per-runtime Driver bindings.

### Motivation

After the first Codex driver wording repair, contracts.md still described core reference interfaces as skill prompts, treated prose+CLI decomposition as future Phase-2 work, named retry handling as a SKILL.md contract, and titled next as a thin-transport skill. These terms should align with the Driver/prose/wrapper architecture before family-wide Codex support work builds on them.

### Proposed Changes

Revise contracts.md to describe core's reference implementation as harness-neutral operation prose, wrapper CLIs, schemas, and templates; state that prose+CLI decomposition has landed; replace SKILL.md retry/narration wording with operation-prose or Driver-bound prose wording; reinterpret orchestrator interactive front-ends as runtime-specific interfaces rather than universal SKILL.md files; rename the Skill/template JSON and next thin-transport headings to operation-prose/Driver-binding language. Update tests/heading-coverage.json for the renamed H2 headings.
