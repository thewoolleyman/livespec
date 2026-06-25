---
topic: planning-lane-non-functional-guidance
author: claude-opus-4-8
created_at: 2026-06-25T08:57:12Z
---

## Proposal: Planning Lane non-functional guidance

### Target specification files

- non-functional-requirements.md

### Summary

Add a NON-normative '#### Planning Lane guidance' block under '### Orchestrator plugin ecosystem' in non-functional-requirements.md, sibling to the existing '#### Orchestrator-internal Dispatcher guidance' and '#### Orchestrator-internal grooming guidance' blocks. It records the durable multi-session planning discipline for orchestrator authors as a repo-agnostic PATTERN: the plan/<topic>/ thread (durable reasoning that matures into a propose-change; at most one resumable handoff.md), the load-bearing no-shadow-ledger rule (status derived from the ledger first, never stored; handoff items are session-local steps or ledger-id pointers, never a parallel queue; refresh at context budget; closing summary names the next-session command; per-repo prompts/AGENTS.md defines the convention), the two one-directional Spec/Orchestrator seams (read-only ledger citation; ripe-work routing through capture-work-item), and the archive-on-epic-close lifecycle. Core gets the guidance only: no new core skill/CLI/doctor invariant; the plan-skill realization belongs to the reference orchestrator's spec. The just boundary is restated for the Planning Lane's realization.

### Motivation

Increment 2 of epic livespec-zs22. Increment 1 framed the three planes and the Planning Lane in spec.md; this lands the contributor discipline where it belongs per the §Boundary litmus — non-functional fleet infrastructure, not a contract a governed consumer inherits. It is placed and framed exactly like the existing NON-normative Dispatcher and grooming guidance (core records the pattern, the orchestrator repo owns the realization), honoring locked decision 1 (handoff/coordination skill orchestrator-side) and locked decision 3 (just mandated non-functionally only, never in core's functional surface). Source design: research/planning-workflow-gap/planning-lane-design.md.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md, insert a new '#### Planning Lane guidance' subsection under '### Orchestrator plugin ecosystem', immediately after '#### Orchestrator-internal grooming guidance' and before '### Codex dogfooding compatibility'. The block opens with the same NON-normative framing as the Dispatcher and grooming blocks ('core neither names nor verifies any of it'; 'what core records here is the repo-agnostic PATTERN, not the realization'; 'NO new core skill, NO new core CLI, and NO new core doctor invariant'; realization belongs to the reference orchestrator's spec), references spec.md §"Workflow planes and the Planning Lane" for the architectural frame, and carries five bold-led paragraphs: (1) The planning thread — plan/<topic>/ with its two facets (durable reasoning maturing to propose-change; at most one handoff.md), research/ subdir, research-only young threads allowed; (2) No shadow ledger (the load-bearing rule) — status derived from the ledger first and never stored, handoff items are session-local steps OR ledger-id pointers never a parallel queue, refresh at budget, closing summary names the next command, per-repo prompts/AGENTS.md; re-adopting the openbrain discipline; (3) The two seams — read-only prompt→ledger citation; plan→work routing through capture-work-item; (4) Archive on epic close — plan/<topic>/ active iff epic open, archived to plan/archive/<topic>/ iff epic closed, bidirectional, nothing lost, mechanical backstops are conformance concerns realized separately; (5) The just boundary — just MAY be mandated for the realization's tooling but MUST NEVER appear in core's functional spec, the /livespec:* plugin skills, or the core↔orchestrator CLI contract. No new H2/H3 heading is introduced (the block is an H4 under an existing H3), so tests/heading-coverage.json needs no change.
