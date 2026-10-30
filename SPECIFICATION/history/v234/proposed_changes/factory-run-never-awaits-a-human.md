---
topic: factory-run-never-awaits-a-human
author: claude-fable-5 (session fix-fabro-blockages)
created_at: 2026-08-30T17:02:05Z
---

## Proposal: Dispatcher guidance: a factory run never awaits a human — the ledger is the only human gate

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add one guidance bullet to the non-normative "Orchestrator-internal Dispatcher guidance" list so every orchestrator family member inherits the rule livespec-orchestrator-beads-fabro ratified in its own v093 (contracts section "A factory run never awaits a human"): a Dispatcher SHOULD never let a factory run wait on a human; a needs-human outcome terminates the run, preserves the work by reference, and rests the work-item in the ledger's human-gated state, and the Dispatcher reconciles every factory's non-terminal run inventory against the ledger so a run that outlives its work-item is released without a human. Measured motivation in that repo: 17 of 336 dispatches over nine days parked at an in-loop human gate and 16 of the 17 items were later closed by another route, each parked run holding a factory scheduler slot for a question nobody could answer. Placement follows the Boundary litmus: this is contributor-facing orchestrator guidance, and the section is already explicitly non-normative on core's contract, so no core skill, CLI, doctor invariant, or scenario is added.

### Motivation

Make the invariant fleet-wide rather than a single orchestrator's discovery: no factory run may wait for a human; human gates are ledger states; orphaned runs are reconciled mechanically. Realization stays in each orchestrator's own SPECIFICATION (livespec-orchestrator-beads-fabro v093 is the reference).

### Proposed Changes

```diff
@@ SPECIFICATION/non-functional-requirements.md — "#### Orchestrator-internal Dispatcher guidance", the "A Dispatcher SHOULD support:" list, append one bullet after the structured-iteration-journal bullet @@
+- a **ledger-held human gate** — a factory run SHOULD never wait on a
+  human. When a dispatched run reaches an outcome the loop cannot
+  auto-resolve, the run terminates non-green, preserves its work by
+  reference (a pushed ref and/or a durable pointer to its checkpointed
+  artifacts), and the Dispatcher rests the work-item in the ledger's
+  human-gated state; the human's answer is a ledger action, never an
+  attach-and-resume of a parked run. The Dispatcher SHOULD reconcile every
+  configured factory's non-terminal run inventory against the ledger and
+  release any run whose work-item is no longer active under that run —
+  exporting its record before terminating it, and never changing the
+  item's human-gated state — so a run overtaken by a re-dispatch or a hand
+  landing cannot hold factory capacity waiting for a question nobody can
+  answer. Reference realization: livespec-orchestrator-beads-fabro,
+  contracts section "A factory run never awaits a human" (its v093).
```
