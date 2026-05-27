---
topic: rename-loop-skill-directory-to-livespec-orchestrate
author: claude-opus-4-7
created_at: 2026-05-27T15:13:04Z
---

## Proposal: rename-loop-skill-directory-to-livespec-orchestrate-to-avoid-harness-collision

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/contracts.md

### Summary

Rename the project-local Layer 3 driver's directory from `.claude/skills/loop/` to `.claude/skills/livespec-orchestrate/` to avoid the slash-command name collision with Claude Code's built-in `/loop` harness skill (recurring-task scheduler). The new directory name autocompletes alongside the other `livespec-*` skills and is semantically distinct from any harness skill. The Layer 3 architectural role, contract, and SKILL.md content are unchanged — only the path is updated.

### Motivation

Claude Code's harness ships a built-in `/loop` skill for recurring-task scheduling. Project-local skills at `.claude/skills/<name>/SKILL.md` resolve as `/<name>` in the flat (un-namespaced) skill namespace and shadow harness skills with the same name. Authoring the Layer 3 driver at `.claude/skills/loop/` therefore takes over the `/loop` slash command in any context where livespec is the working directory, hiding the harness's recurring-task primitive from the user. Renaming to `.claude/skills/livespec-orchestrate/` removes the collision (no harness skill named `livespec-orchestrate`) and gives the new skill an autocomplete-friendly `livespec-*` prefix consistent with the rest of the livespec family's user-facing skill surface (livespec:revise, livespec:critique, etc.). The hyphen-prefix is a manual visual scoping convention — project-local skills have no real namespace mechanism, and `:` in the SKILL.md frontmatter `name:` field is reserved for plugin-namespace lookup. The conceptual term `Layer 3 loop driver` MAY remain in spec prose where the driver's behavior is described (the driver loops over iterations until budget exhausted — that is accurate); only the literal `.claude/skills/loop/SKILL.md` path references MUST update.

### Proposed Changes

Across the three spec files, every literal occurrence of `.claude/skills/loop/SKILL.md` MUST be replaced with `.claude/skills/livespec-orchestrate/SKILL.md`, AND every literal occurrence of `.claude/skills/loop/` (the directory path, without the `SKILL.md` suffix) MUST be replaced with `.claude/skills/livespec-orchestrate/`. The five known occurrences (audited 2026-05-27 against master at 37d9ddf): (1) spec.md §"Three-layer orchestration architecture" → "Layer 3 — Cross-repo orchestration (livespec-resident)" bullet — path in MUST-carry mandate; (2) spec.md §"Three-layer orchestration architecture" → "Cross-side composition belongs at Layer 3" paragraph — path in the discoverability-nudge cross-reference; (3) contracts.md §"Layer 3 discoverability nudge" — path in the user-facing nudge prose; (4) non-functional-requirements.md §"Cross-repo orchestration layer (livespec-resident)" — path in the livespec-MUST-carry mandate AND in the MUST-NOT-carry exclusion for impl-plugin repos AND in the template-MUST-NOT-include constraint; (5) non-functional-requirements.md §"Layer 3 loop driver — required shape and discipline" — path in the MUST-be-implemented-at constraint. The conceptual phrase `Layer 3 loop driver` in prose MAY remain unchanged — it describes the driver's loop behavior, not its file path. No new sections; no heading renames; pure path substitution.
