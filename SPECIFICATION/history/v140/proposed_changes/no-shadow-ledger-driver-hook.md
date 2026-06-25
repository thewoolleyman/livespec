---
topic: no-shadow-ledger-driver-hook
author: claude-opus-4-8
created_at: 2026-06-25T13:51:14Z
---

## Proposal: Add the no-shadow-ledger Stop hook as a required cross-Driver bundle surface

### Target specification files

- contracts.md

### Summary

Add a third required Driver-shipped hook — a WARN-only Stop hook (no_shadow_ledger.py) that warns when a planning artifact (a handoff, or any markdown under plan/ or prompts/) is persisted carrying an embedded markdown checkbox task queue ([ ]/[x]) instead of deriving status from the work-item ledger. Unlike block-auto-memory and warn-plan-persistence (Claude bundle only), this hook is REQUIRED in BOTH Drivers' bundles, single-sourced as a byte-identical neutral body with each hooks.json Stop registration as the thin per-runtime adapter.

### Motivation

contracts.md §"Driver-shipped hooks" mandates a propose-change cycle to ADD a hook to a Driver bundle. This hook is the agent-runtime realization of non-functional-requirements.md §"Planning Lane guidance" → "No shadow ledger" (the load-bearing rule that a planning artifact never embeds a [ ]/[x] task queue), exactly as warn-plan-persistence realizes §"Completion includes persistence and workspace cleanup". Codex was verified to support a turn-scoped Stop event, so one neutral body serves both runtimes. This is increment 3b of epic livespec-zs22 (the Planning Lane formalization) and discharges the first slice of the Conformance Pattern's Plugin-resolution concern; the mechanical Verifier that keeps the two copies byte-identical is deferred to increment 5 (the Conformance Pattern itself), so this section requires the single-sourced-and-identical disposition without pinning a sync mechanism.

### Proposed Changes

In SPECIFICATION/contracts.md §"Driver-shipped hooks":

1. Change the bundle-intro sentence "The bundle carries two hooks:" to "The bundle carries three hooks:".

2. After the warn-plan-persistence bullet, add a new bullet:
   - **Stop no-shadow-ledger WARN** (no_shadow_ledger.py). Registered on the Stop event; scans the agent's last turn (the same last-real-user-message window as the plan-persistence hook) for a file-persisting tool call (Write / Edit / MultiEdit) that wrote a PLANNING ARTIFACT — a handoff, or any markdown file under a plan/ or prompts/ directory — whose written content carries markdown checkbox task-list items ([ ] / [x]) at or above a mechanical threshold. When found, it emits a systemMessage warning that the artifact embeds a parallel work queue and directs the agent to the no-shadow-ledger rule (non-functional-requirements.md §"Planning Lane guidance" → "No shadow ledger"): a planning artifact derives its status from the work-item ledger as its first action, so each checklist item is a session-local step OR a pointer to a real ledger id, never an embedded [ ]/[x] task queue. Like the plan-persistence hook it is WARN-ONLY (never a decision key, never non-zero) and never auto-edits. Unlike block-auto-memory and warn-plan-persistence, which the Claude bundle carries alone, the no-shadow-ledger hook is REQUIRED in BOTH Drivers' bundles.

3. Change "Fail-open discipline (both hooks)." to "Fail-open discipline (every hook).".

4. Add a new paragraph (after the Fail-open discipline paragraph) titled **Cross-Driver single-sourcing (no-shadow-ledger).** stating: the hook's detection body MUST be single-sourced and ship byte-identically in BOTH Driver bundles (livespec-driver-claude .claude-plugin/hooks/ and livespec-driver-codex livespec/hooks/), with each bundle's hooks.json Stop registration the thin per-runtime adapter; Codex consumes the Claude Stop hook I/O format so one neutral body serves both runtimes; this section requires the single-sourced-and-byte-identical disposition while the mechanical no-drift guarantee is a cross-repo Conformance concern (the Plugin-resolution concern) realized separately; and the detection internals (path predicate, checkbox threshold, persisting-tool set) remain Driver implementation detail tunable without a core spec cycle, provided the WARN-only Stop posture and fail-open discipline hold.

No "## " (H2) heading changes, so tests/heading-coverage.json is unaffected. Consistent with the existing hook surfaces, no scenarios.md scenario is added.
