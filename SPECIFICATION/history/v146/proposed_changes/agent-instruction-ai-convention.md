---
topic: agent-instruction-ai-convention
author: claude-opus-4-8
created_at: 2026-06-26T03:22:33Z
---

## Proposal: Codify the .ai/<topic>.md agent-instruction convention

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Extend contracts.md §"Fleet agent-instruction core" to codify the agent-instruction `.ai/<topic>.md` progressive-disclosure convention: durable, non-ephemeral agent guidance routes to AGENTS.md and its referenced sibling `.ai/<topic>.md` files (supported at ANY directory level, additive across nesting), never to the harness-private per-session local-memory store; and every AGENTS.md-declared `.ai/<topic>.md` reference MUST resolve, enforced fleet-wide by the existing shared fleet-membership obligation suite and propagated to adopters by the copier template.

### Motivation

Maintainer decisions 2026-06-26 (design at research/agent-instruction-dot-ai-convention/design.md; epic livespec-hso8, keystone livespec-a244). Durable agent guidance currently has no reliable home in a livespec-governed repo: the Claude Code per-session auto-memory store (~/.claude/projects/<slug>/memory/*.md) is ephemeral, per-user, per-machine, and invisible to other agents and runtimes, so anything durable written there is lost to the project. This is the SPECIFY slot of the five-slot Conformance Pattern (livespec-zs22.7) applied to the agent-instruction concern. The convention reuses the .ai/<topic>.md form already sketched in research/workflow-processes/tool-agnostic-workflow.md ("Persistent Agent Knowledge").

### Proposed Changes

Two edits in `SPECIFICATION/contracts.md`, within the existing `## Fleet agent-instruction core` section. No new `## ` heading is introduced and no Gherkin scenario is required: these are contract obligations enforced by the already-named fleet-membership obligation suite, exactly like the section's existing AGENTS.md/symlink and beads-access-guard obligations.

(1) INSERT two new paragraphs immediately AFTER the existing AGENTS.md / `.claude/CLAUDE.md` symlink paragraph ("A member's agent instructions MUST live in a canonical `AGENTS.md` at the repo root, and `.claude/CLAUDE.md` MUST be a symlink to `../AGENTS.md` — a single source of truth, never a hand-maintained divergent duplicate."):

> A member's `AGENTS.md` MAY progressively disclose detailed agent guidance into sibling **`.ai/<topic>.md`** files that it references, so the always-loaded `AGENTS.md` stays small and topic detail loads only when the agent is working on that topic. A `.ai/` directory is supported at ANY directory level: it sits beside that level's `AGENTS.md` (and its symlinked `.claude/CLAUDE.md`) and is scoped to it, mirroring the nested-`AGENTS.md` pattern Claude Code and Codex already honor. Nested `.ai/` topics are ADDITIVE — a deeper-level `.ai/<topic>.md` augments, never silently overrides, an ancestor-level topic of the same name, exactly as nested `AGENTS.md` composes additively.
>
> Durable, non-ephemeral agent guidance — a learned maintainer preference, a convention, or a cross-cutting discipline — routes to `AGENTS.md` and its referenced `.ai/<topic>.md` files. The harness-private per-session local-memory store (the Claude Code auto-memory layout `~/.claude/projects/<slug>/memory/*.md`) is NEVER the home for durable guidance in a livespec-governed member: it is ephemeral, per-user, per-machine, and invisible to other agents and runtimes, so anything durable written there is lost to the project. `AGENTS.md` is the guaranteed durable-guidance home in every member; the `.ai/<topic>.md` files are OPTIONAL progressive-disclosure overflow. Every `.ai/<topic>.md` path an `AGENTS.md` references MUST resolve to an existing file, at every directory level that declares one — so the destination the auto-memory redirect (§"Driver-shipped hooks") points to actually exists.

(2) UPDATE the closing fleet-wide-enforcement paragraph. REPLACE:

"Presence of the core, the `AGENTS.md` / `.claude/CLAUDE.md` symlink shape, the beads-runtime section in beads-backed members, and the beads-access guard MUST be enforced fleet-wide by the shared fleet-membership obligation suite per `non-functional-requirements.md` §\"Shared code sync — livespec-dev-tooling\", so that drift in any member is un-mergeable — mirroring the suite's existing beads tenant-connection consistency obligation."

WITH:

"Presence of the core, the `AGENTS.md` / `.claude/CLAUDE.md` symlink shape, the resolvability of every `AGENTS.md`-declared `.ai/<topic>.md` reference at each directory level, the beads-runtime section in beads-backed members, and the beads-access guard MUST be enforced fleet-wide by the shared fleet-membership obligation suite per `non-functional-requirements.md` §\"Shared code sync — livespec-dev-tooling\", so that drift in any member is un-mergeable — mirroring the suite's existing beads tenant-connection consistency obligation. The `AGENTS.md` convention block and a seed `.ai/<topic>.md` scaffold ship from the copier template per `non-functional-requirements.md` §\"Shared content sync — copier template\", so every adopter repo inherits the convention with a concrete example."

DESIGN INTENT (records the maintainer decision so a later revise/critique does not re-litigate it): the load-bearing, drift-proof invariant the conformance check asserts is REFERENTIAL INTEGRITY — every referenced `.ai/<topic>.md` resolves — NOT that a specifically-named universal topic file exists in every repo. This keeps the contract architecture-level per `non-functional-requirements.md` §"Boundary" and the specify-architecture-not-mechanism discipline, and avoids making a member with a clean `AGENTS.md` and no overflow topics un-mergeable.

## Proposal: Intent-route the block-auto-memory redirect

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Reword the auto-memory redirect contract in contracts.md §"Driver-shipped hooks" so a blocked Write(**/memory/*.md) is INTENT-ROUTED by the kind of content rather than always redirected to capture-work-item or silently dropped: trackable work -> the orchestrator ledger; a durable spec rule -> /livespec:propose-change; durable non-work-item guidance -> AGENTS.md / a referenced .ai/<topic>.md; only genuinely session-ephemeral scratch is dropped. The reason MUST NOT silently drop durable guidance.

### Motivation

Provenance (design.md §Provenance; bug livespec-co9h): an agent tried to persist a durable maintainer preference, hit the block-auto-memory hook whose reason offered ONLY capture-work-item, judged it over-broad for non-work-item guidance, and bypassed the guard — the exact misroute-or-drop failure. The hook must point at the durable-guidance home this proposal establishes (AGENTS.md / .ai/<topic>.md) so the ENFORCE slot has a real, non-dropping destination. This is the spec/contract half of co9h; the Driver hook scripts (claude + codex) are the impl half.

### Proposed Changes

One edit in `SPECIFICATION/contracts.md`, in the `### Driver-shipped hooks` H3 (under the existing `## Plugin distribution` H2 — no new heading, no scenario). In the **PreToolUse auto-memory redirect (`block-auto-memory.sh`)** bullet, REPLACE the sentence:

"When such a write occurs AND the governed project (resolved via `CLAUDE_PROJECT_DIR`) carries a `.livespec.jsonc` whose `implementation.plugin` key names an active orchestrator plugin, the hook emits a block decision (PreToolUse `permissionDecision: deny`) whose reason redirects the agent to the active orchestrator plugin's `/<plugin>:capture-work-item` skill, so in-flight observations land in the orchestrator's work-item ledger instead of harness-private auto-memory files."

WITH:

"When such a write occurs AND the governed project (resolved via `CLAUDE_PROJECT_DIR`) carries a `.livespec.jsonc` whose `implementation.plugin` key names an active orchestrator plugin, the hook emits a block decision (PreToolUse `permissionDecision: deny`) whose reason INTENT-ROUTES the blocked content by its kind — rather than assuming it is always trackable work or silently dropping it: an in-flight trackable observation -> the active orchestrator plugin's `/<plugin>:capture-work-item` skill (the work-item ledger); a durable specification rule -> `/livespec:propose-change`; durable non-work-item agent guidance (a learned preference, convention, or discipline) -> the member's `AGENTS.md` or a referenced progressively-disclosed `.ai/<topic>.md` file per §\"Fleet agent-instruction core\"; and only genuinely session-ephemeral scratch is dropped. The reason MUST NOT silently drop durable guidance and MUST NOT present `capture-work-item` as the sole destination."

Then in the FOLLOWING sentence, scope the `implementation.plugin` resolution to the ledger route. REPLACE:

"The redirect target MUST be resolved from `implementation.plugin` — never hardcoded to any one orchestrator plugin."

WITH:

"The orchestrator-ledger redirect target (the `capture-work-item` route) MUST be resolved from `implementation.plugin` — never hardcoded to any one orchestrator plugin; the `/livespec:propose-change` and `AGENTS.md` / `.ai/<topic>.md` routes are runtime-static destinations that do not depend on the orchestrator plugin's identity."

The final sentence of the bullet ("The presence of a non-empty `implementation.plugin` value is the SOLE config gate ...") is UNCHANGED: a non-empty `implementation.plugin` remains the sole gate on whether the hook fires at all.
