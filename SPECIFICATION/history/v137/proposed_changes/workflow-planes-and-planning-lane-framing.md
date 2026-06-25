---
topic: workflow-planes-and-planning-lane-framing
author: claude-opus-4-8
created_at: 2026-06-25T06:42:36Z
---

## Proposal: Workflow planes and Planning Lane architecture framing

### Target specification files

- spec.md

### Summary

Add a high-level architecture framing section, '## Workflow planes and the Planning Lane', immediately before '## Contract + reference implementations architecture', and update the canonical architecture diagram to depict the Control Plane and the plan/<topic>/ planning store. The new section names the three planes (Spec / Orchestrator / Control), carries the planes diagram and the skills diagram, frames the Planning Lane and its two one-directional Spec/Orchestrator seams under the no-shadow-ledger rule, and states the Control-Plane role (with the console as a reference realization that is not yet a required dependency). The existing canonical contract diagram is replaced with the modified version that adds the operator console (Control Plane) and the plan/<topic>/ store while preserving the zero-dependency invariant and the D/O seam labels.

### Motivation

livespec already runs a three-lane workflow (spec lifecycle + tracked implementation) but had no codified frame for the three planes nor for the durable, multi-session planning work that decides what should become spec vs. implementation vs. research. This framing re-adopts livespec's own deferred planning design as a disciplined, codified convention and places each piece on the plane that owns it, per epic livespec-zs22 (increment 1). Source design and the three final diagrams: research/planning-workflow-gap/planning-lane-design.md. Scope is the framing only; the detailed plan skill surface, the plan/<topic>/ layout rules, and the archive-on-epic-close concern are non-functional contributor guidance landed in later increments.

### Proposed Changes

In SPECIFICATION/spec.md, insert a new '## Workflow planes and the Planning Lane' section immediately before '## Contract + reference implementations architecture'. The section: (1) names the Spec Plane (livespec core), the Orchestrator Plane (the producer; reference Beads/Dolt + Fabro), and the Control Plane (the operator console; reference livespec-console-*), each with its owned artifacts and its concern; (2) carries a terminology guard that the console is the Control Plane / operator cockpit and NEVER a 'Driver'; (3) embeds the planes Mermaid diagram; (4) under a '### The Planning Lane' subsection, describes the plan/<topic>/ planning thread (durable reasoning that matures into a propose-change; resumable execution coordination that cites ledger ids), the load-bearing no-shadow-ledger discipline, and the two explicit one-directional Spec/Orchestrator seams (read-only ledger citation; ripe-work routing through capture-work-item), deferring the detailed plan skill/layout/archive rules to non-functional guidance; (5) embeds the skills Mermaid diagram; (6) under a '### The Control-Plane role' subsection, states that the console runs the overall workflow as a general role with the Beads/Dolt + Fabro console as its reference realization, and that the console is not yet a required dependency. Separately, replace the existing fenced canonical architecture diagram inside '## Contract + reference implementations architecture' with the modified diagram that adds the Control Plane (operator console) and the plan/<topic>/ store node plus the plan-writes and matures-to-propose-change arrows, while preserving the load-bearing ZERO-direct-Driver-to-orchestrator-dependency invariant and the D1-D3 / O1-O4 seam labels. Co-edit tests/heading-coverage.json to add the matching TODO entry for the new H2 heading.
