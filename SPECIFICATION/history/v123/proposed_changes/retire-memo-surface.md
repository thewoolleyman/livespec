---
topic: retire-memo-surface
author: claude-opus-4-8
created_at: 2026-06-20T16:24:02Z
---

## Proposal: Retire memo as a named core surface; retarget the auto-memory redirect to capture-work-item

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md

### Summary

Memo is retired as a named surface across the orchestrator reference implementations; the work-item ledger absorbs its function (actionable captures via capture-work-item, spec input via propose-change, durable lessons via the orchestrator's lessons.md). The v103 re-steering already dropped the memo skills from core's contract catalogue, but two live spots still name memo: the block-auto-memory PreToolUse redirect target in contracts.md §"Driver-shipped hooks", and the Terminology "Transient (queue/archive item)" entry's canonical instance in spec.md §"Terminology". This proposal (1) retargets the redirect from the active impl-plugin's capture-memo skill to its capture-work-item skill and rewords the trailing parenthetical so it no longer asserts a memo substrate, and (2) rewords the Terminology entry to keep the load-bearing transient-vs-durable-pending principle while no longer presenting memo as a live shipped instance. The doctor-boundary example list in contracts.md §"Doctor cross-boundary invariants" ("…work-items, memos, …") is intentionally retained: it illustrates a class of orchestrator-private state doctor must not inspect, not a recommended surface, and a contract test pins its text.

### Motivation

W7 orchestrator convergence (livespec-zkmn.1, step 3 — work-item livespec-gjn4): the two reference orchestrators converge by removing duplicated memo machinery the ledger already absorbs. This spec change is the keystone because retargeting the Driver-shipped block-auto-memory hook's redirect target is a contract change against contracts.md §"Driver-shipped hooks", whose final paragraph requires a propose-change cycle to change a hook's redirect surface. Downstream impl removals are tracked as beads work-items: livespec-kfiz (impl-beads), livespec-d4j3 (impl-git-jsonl), and a Driver-repo block-auto-memory.sh retarget (to be filed). User-confirmed 2026-06-20: actionable captures → work-item ledger; persistent-knowledge → the orchestrator's lessons.md. Safe cross-repo order: this core contract change → Driver retarget (point the hook at capture-work-item, which already exists) → impl memo removals.

### Proposed Changes

Two edits, both confined to existing sections (no `## ` heading added, removed, or renamed — so no tests/heading-coverage.json co-edit is required).

**Edit 1 — `SPECIFICATION/contracts.md`, §"Driver-shipped hooks", the "PreToolUse auto-memory redirect (`block-auto-memory.sh`)" bullet.** The hook KEEPS its name and its `Write(**/memory/*.md)` matcher (it guards the Claude Code auto-memory layout, which is unrelated to the memo concept). Only the redirect TARGET and the trailing parenthetical change:

```diff
-When such a write occurs AND the governed project (resolved via `CLAUDE_PROJECT_DIR`) carries a `.livespec.jsonc` whose `implementation.plugin` key names an active impl-plugin, the hook emits a block decision (PreToolUse `permissionDecision: deny`) whose reason redirects the agent to the active impl-plugin's `/<plugin>:capture-memo` skill, so in-flight observations land in the durable memo store instead of harness-private auto-memory files. The redirect target MUST be resolved from `implementation.plugin` — never hardcoded to any one impl-plugin. The presence of a non-empty `implementation.plugin` value is the SOLE config gate (the `memos_path` gate named in the originating work-item predates the orchestrator-substrate migration and is retired; the memo substrate is orchestrator-private).
+When such a write occurs AND the governed project (resolved via `CLAUDE_PROJECT_DIR`) carries a `.livespec.jsonc` whose `implementation.plugin` key names an active impl-plugin, the hook emits a block decision (PreToolUse `permissionDecision: deny`) whose reason redirects the agent to the active impl-plugin's `/<plugin>:capture-work-item` skill, so in-flight observations land in the orchestrator's work-item ledger instead of harness-private auto-memory files. The redirect target MUST be resolved from `implementation.plugin` — never hardcoded to any one impl-plugin. The presence of a non-empty `implementation.plugin` value is the SOLE config gate (the `memos_path` gate named in the originating work-item predates the orchestrator-substrate migration and is retired; the work-item ledger is orchestrator-private).
```

**Edit 2 — `SPECIFICATION/spec.md`, §"Terminology", the "Transient (queue/archive item)" entry.** Keep the category definition and the load-bearing doctor-catalogue scoping principle verbatim; replace only the middle sentences that present memos as the live canonical instance:

```diff
-**Transient (queue/archive item)** — An item category in which the item type is defined by needing disposition: the item's value is exhausted on routing to one of its terminal dispositions, and pile-up of transient items violates the type. The canonical instance — memos — is now orchestrator-private machinery: an orchestrator that keeps a memo queue owns its own drain discipline, and core's doctor enforces nothing against it. The category principle remains load-bearing for doctor-catalogue scoping. Contrasts with **Durable-pending (queue/archive item)**. The transient-vs-durable-pending principle MUST be load-bearing for proposals that expand doctor's invariant catalog: structural invariants on either category are in scope; productivity-heuristic invariants (staleness, pile-up) on durable-pending items are out of scope and belong to `/livespec:next` instead.
+**Transient (queue/archive item)** — An item category in which the item type is defined by needing disposition: the item's value is exhausted on routing to one of its terminal dispositions, and pile-up of transient items violates the type. The category was historically instantiated by memos; the reference orchestrators have since retired that surface (in-flight captures now flow to the work-item ledger, spec input to `/livespec:propose-change`, and durable lessons to the orchestrator's own knowledge home), so core ships no transient instance and its doctor enforces nothing against any orchestrator that chooses to keep a transient queue privately. The category principle remains load-bearing for doctor-catalogue scoping. Contrasts with **Durable-pending (queue/archive item)**. The transient-vs-durable-pending principle MUST be load-bearing for proposals that expand doctor's invariant catalog: structural invariants on either category are in scope; productivity-heuristic invariants (staleness, pile-up) on durable-pending items are out of scope and belong to `/livespec:next` instead.
```
