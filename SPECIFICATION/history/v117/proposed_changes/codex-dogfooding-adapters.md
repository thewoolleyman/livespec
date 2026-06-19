---
topic: codex-dogfooding-adapters
author: codex-gpt-5
created_at: 2026-06-19T07:48:41Z
---

## Proposal: Codex project adapters over core prose and wrappers

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Repair the Codex dogfooding specification so it matches the proven project-local Codex adapter architecture instead of the obsolete symlink-to-.claude-plugin/skills model.

### Motivation

The Codex support audit and adapter proof show that core intentionally ships no .claude-plugin/skills tree, Claude runtime bindings live in livespec-driver-claude, and Codex CLI 0.141.0 loads committed project-local .agents/skills/livespec-* adapters. The spec still says Codex skills symlink to .claude-plugin/skills/* and that Codex reads those SKILL.md files, which is stale and conflicts with the landed read-only adapters.

### Proposed Changes

Update SPECIFICATION/non-functional-requirements.md so Codex dogfooding MUST use thin project-local .agents/skills/livespec-* adapters over shared core prose in .claude-plugin/prose/<operation>.md and wrapper CLIs in .claude-plugin/scripts/bin/. The spec MUST NOT require or describe symlinks into .claude-plugin/skills/*, because core intentionally has no such tree. The spec MUST state that the currently verified Codex project-skill surface is limited to the read-only help, next, and doctor adapters until mutating operations are separately specified and proven. The spec MUST keep Codex marketplace support explicitly unclaimed until marketplace registration creates an installed LiveSpec plugin entry and a separate codex exec invocation can use that registered plugin without relying on .agents/skills/* or AGENTS.md. The verification scenarios SHOULD name .agents/skills/livespec-help, .agents/skills/livespec-next, .agents/skills/livespec-doctor, .claude-plugin/prose/help.md, .claude-plugin/prose/next.md, .claude-plugin/prose/doctor.md, .claude-plugin/scripts/bin/next.py, and .claude-plugin/scripts/bin/doctor_static.py as the proven artifacts.
