---
topic: codex-driver-spec-wording
author: codex-gpt-5
created_at: 2026-06-19T17:09:51Z
---

## Proposal: Repair core driver and skill wording

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md

### Summary

Update stale core specification text that still describes core as owning Claude Code SKILL.md prompts or an installed core plugin skill tree. The current architecture makes core own harness-neutral prose plus wrapper CLIs, while per-runtime Drivers such as livespec-driver-claude and Codex project skills bind those artifacts.

### Motivation

The Codex family audit found that SPECIFICATION/spec.md still says the core plugin bundle MUST contain skills/<sub-command>/SKILL.md and that slash commands dispatch to matching skill prompts. SPECIFICATION/contracts.md also has a CLI e2e harness section that walks installed core plugin skills. This conflicts with the already-ratified contract-plus-reference-implementations architecture and the proven Codex adapter path.

### Proposed Changes

Revise SPECIFICATION/spec.md so Runtime and packaging says core ships harness-neutral prose under .claude-plugin/prose/, wrapper CLIs under .claude-plugin/scripts/bin/ and .claude-plugin/scripts/livespec/commands/, built-in templates, and vendored libraries, but no core-owned .claude-plugin/skills/ tree. Revise the terminology and Sub-command lifecycle text so authored/transport responsibilities are Driver-binding/prose responsibilities rather than core-owned SKILL.md responsibilities. Keep the slash-command names as Driver surfaces, not core package contents. Revise SPECIFICATION/contracts.md's CLI end-to-end harness contract so the top-of-pyramid harness is explicitly Claude Driver coverage over livespec-driver-claude plus core, and discovery walks the installed Driver plugin's skills instead of an installed core plugin skill tree. Remove obsolete Phase-3 extraction language where it says the reference Driver binding still lives in core.
