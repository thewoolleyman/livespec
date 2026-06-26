---
topic: codex-memory-store-and-guard
author: claude-opus-4-8
created_at: 2026-06-26T06:35:22Z
---

## Proposal: Generalize the memory-store contract to cover Codex and require the Codex auto-memory-write guard

### Target specification files

- SPECIFICATION/contracts.md

### Summary

ENFORCE-codex (Option C) of epic livespec-hso8 / co9h. Now that Codex's own ephemeral local-memory store (~/.codex/memories/) is in scope, contracts.md must (1) stop describing the no-home-for-durable-guidance memory store as Claude-specific and name it per-runtime (Claude ~/.claude/.../memory/*.md OR Codex ~/.codex/memories/), and (2) require the Codex Driver to ship a per-runtime sibling of block-auto-memory.sh: a pre_tool_use guard that denies a MANUAL write into ~/.codex/memories/ and intent-routes it to AGENTS.md/.ai/, with the stated limitation that Codex's background-generated memories are outside the hook lifecycle and are governed by Codex config + the runtime-agnostic convention.

### Motivation

Maintainer decision 2026-06-26 (Option C). My earlier 'codex not-applicable' call was wrong: the OpenAI Codex docs confirm Codex has an auto-memory store (~/.codex/memories/, off-by-default) and state this track's exact thesis ('Keep required team guidance in AGENTS.md ... Treat memories as a helpful local recall layer'). Codex memories are background-generated (a pre_tool_use hook cannot intercept them) but a manual apply_patch/Write into that dir IS hookable, and Codex PreToolUse can deny. So the convention already covers Codex runtime-agnostically (CAPTURE slot); this change generalizes the contract language and requires the hookable manual-write guard, restoring cross-runtime symmetry. Completing this + a follow-up auto-memory investigation work-item closes co9h and the hso8 track.

### Proposed Changes

Three edits in `SPECIFICATION/contracts.md`, all within existing sections (no new `## ` H2 heading, no Gherkin scenario — the Codex guard is a required Driver surface tested in the Driver repo, exactly like the existing 'Codex footgun guard' paragraph, which carries no core scenario).

(1) §"Fleet agent-instruction core" — GENERALIZE the memory-store sentence. REPLACE:

"The harness-private per-session local-memory store (the Claude Code auto-memory layout `~/.claude/projects/<slug>/memory/*.md`) is NEVER the home for durable guidance in a livespec-governed member: it is ephemeral, per-user, per-machine, and invisible to other agents and runtimes, so anything durable written there is lost to the project."

WITH:

"The harness-private per-session local-memory store — the per-runtime ephemeral memory layout, whether the Claude Code auto-memory layout (`~/.claude/projects/<slug>/memory/*.md`) or the Codex local-memory store (`~/.codex/memories/`) — is NEVER the home for durable guidance in a livespec-governed member: it is ephemeral, per-user, per-machine, and invisible to other agents and runtimes, so anything durable written there is lost to the project."

(2) §"Driver-shipped hooks", the **Stop no-shadow-ledger WARN** bullet — UPDATE the 'carries alone' clause. REPLACE:

"Unlike `block-auto-memory` and `warn-plan-persistence`, which the Claude bundle carries alone, the no-shadow-ledger hook is REQUIRED in BOTH Drivers' bundles (see the cross-Driver single-sourcing paragraph below)."

WITH:

"Unlike `warn-plan-persistence`, which the Claude bundle carries alone, the no-shadow-ledger hook is REQUIRED in BOTH Drivers' bundles (see the cross-Driver single-sourcing paragraph below); the auto-memory-write guard is likewise present in BOTH bundles, but as a PER-RUNTIME pair rather than a single shared body — `block-auto-memory.sh` targets the Claude layout (`~/.claude/.../memory/*.md`), and the Codex Driver ships its own guard targeting the Codex local-memory store (`~/.codex/memories/`), per the Codex auto-memory-write-guard paragraph below."

(3) §"Driver-shipped hooks" — INSERT a new bold-lead paragraph immediately AFTER the 'Codex footgun guard (required for mutating Codex automation)' paragraph (which ends '... in particular `prune-history` remains explicit-user-invocation only and MUST NOT be auto-activated.'):

"**Codex auto-memory-write guard (required).** The Codex Driver (`livespec-driver-codex`) MUST ship a Codex `pre_tool_use` hook that is the per-runtime sibling of the Claude `block-auto-memory.sh`: in a livespec-governed project it MUST intercept a tool call that would write a file into the Codex local-memory store (`~/.codex/memories/`) — a manual `apply_patch` / `Edit` / `Write` whose target path is under that store — and emit `permissionDecision: deny` with a reason that INTENT-ROUTES the would-be write by what it IS, identically to the Claude hook: an in-flight trackable observation to the active orchestrator plugin's `/<plugin>:capture-work-item` skill (resolved from `implementation.plugin`); a spec-level rule to `/livespec:propose-change`; durable non-work-item agent guidance to the member's `AGENTS.md` or a referenced progressively-disclosed `.ai/<topic>.md` file; and only genuinely session-ephemeral scratch may be dropped. The reason MUST NOT silently drop durable guidance. KNOWN LIMITATION (stated by contract, not a defect): Codex's PRIMARY memories are GENERATED IN THE BACKGROUND by Codex itself and are OUTSIDE the `pre_tool_use` hook lifecycle, so this guard CANNOT intercept them — it covers the manual-write path only. Codex's background-generated memories are governed instead by Codex's own memory configuration (off-by-default; the `[features] memories` flag and `memories.*` settings) together with the runtime-agnostic `AGENTS.md` / `.ai/<topic>.md` convention §\"Fleet agent-instruction core\" establishes, which Codex loads. Like the footgun guard, the script implementation and its tests live in the Driver repo; this section states only the required surface and its behavioral discipline. The fail-open discipline above applies: a hook failure MUST be a silent pass-through, and the guard acts only when it POSITIVELY identifies a write into the Codex local-memory store."

The background-generation governance (whether a deeper guard or config setting is warranted) is filed as a separate follow-up work-item, not resolved here.
