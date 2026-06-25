---
proposal: workflow-planes-and-planning-lane-framing.md
decision: accept
revised_at: 2026-06-25T06:43:37Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Increment-1 architecture framing for epic livespec-zs22. The proposal adds the high-level three-planes frame (Spec/Orchestrator/Control), the Planning Lane and its two one-directional seams under the no-shadow-ledger rule, and the Control-Plane role, carrying the planes and skills diagrams; and it replaces the canonical contract diagram with the modified version that adds the Control Plane and the plan/<topic>/ store while preserving the zero-Driver-to-orchestrator-dependency invariant and the D/O seam labels. The three diagrams are the final set agreed in the 2026-06-25 design session (research/planning-workflow-gap/planning-lane-design.md). Scope is framing only; detailed plan skill/layout/archive rules are deferred to later increments. tests/heading-coverage.json is co-edited to add the matching TODO entry for the new H2 per the self-application co-edit discipline.

## Resulting Changes

- spec.md
- ../tests/heading-coverage.json
