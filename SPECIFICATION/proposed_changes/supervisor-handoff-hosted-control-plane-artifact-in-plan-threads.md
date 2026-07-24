---
topic: supervisor-handoff-hosted-control-plane-artifact-in-plan-threads
author: claude-fable-5
created_at: 2026-07-24T12:11:23Z
---

## Proposal: Planning threads MAY host one Control-Plane supervision artifact

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/spec.md

### Summary

Both core enumerations of a planning thread's contents (non-functional-requirements.md §"Planning Lane guidance" → "The planning thread.", and spec.md §"Workflow planes and the Planning Lane") describe `plan/<topic>/` as carrying exactly two facets, and are now contradicted by live tracked state: `plan/rop-sweep-fleet-policy/supervisor-handoff.md` (merged in livespec PR #1706) is a third file, authored by the Control Plane's `supervise-plan` operation (shipped in livespec-overseer PR #49 per the adopted design in `plan/plan-skill-supervisor-handoff/design.md` §11). This amendment admits the hosted artifact in both places while keeping the two-facet model and the one-resumption-point rule literally true: the artifact is declared NOT a facet, it resumes a different actor (the supervisor, never the thread's own work), the Spec and Orchestrator Planes treat it as opaque, and core stays realization-agnostic — no tool, skill, CLI, or doctor invariant is named or added.

### Motivation

Adopted design record `plan/plan-skill-supervisor-handoff/design.md` §11.3 (maintainer-adopted 2026-07-23): both upstream specs enumerate the planning thread's contents, so a third file contradicts them no matter who wrote it; the correct amendments are realization-agnostic declarations of non-ownership — the opposite of coupling. The design deliberately sequenced these one-line amendments AFTER the `supervise-plan` skill existed and had produced a real artifact, so the spec describes something that exists (slice 4 of §11.6; the skill shipped as livespec-overseer PR #49, was accepted done as work-item overseer-myjovi with live-exercise evidence, and its first generated artifact merged as livespec PR #1706). Leaving the enumerations unamended is precisely the unstated-drift failure the fleet's doctor checks exist to catch.

### Proposed Changes

Two edits, both verified against origin/master at filing time; each anchor string occurs exactly once in the live spec tree.

EDIT 1 — SPECIFICATION/non-functional-requirements.md, §"Planning Lane guidance": insert a new paragraph immediately AFTER the single paragraph that begins with this byte-exact anchor (one occurrence in the file):

**The planning thread.** A planning thread is a directory `plan/<topic>/` carrying two facets: The inserted paragraph reads:

**The hosted supervision artifact.** A planning-thread directory MAY additionally host at most one Control-Plane-authored artifact, at the reserved filename `plan/<topic>/supervisor-handoff.md`: the durable prompt for the actor SUPERVISING the thread's sessions (the coordinate-the-human charter in `spec.md` §"Workflow planes and the Planning Lane"). It is NOT a third facet — it carries neither the thread's reasoning nor the thread's execution coordination, and it resumes the SUPERVISING actor rather than the thread's own work, so the one-resumption-point rule above is unaffected. Plane ownership stays clean: a Control-Plane realization authors and maintains the file through the repository's normal reviewed commit path, and no Spec-Plane or Orchestrator-Plane operation creates it, consumes it as input, or validates its content — the Planning Lane treats the file as opaque, and repo-generic hygiene (commit gates, the no-shadow-ledger WARN) applies to it as to any markdown file without making any plane a consumer of it. The artifact archives and unarchives with its thread. As with the rest of this guidance, core names no tool and adds no skill, CLI, or doctor invariant for it.

EDIT 2 — SPECIFICATION/spec.md, §"Workflow planes and the Planning Lane": append one sentence to the end of the single paragraph containing this byte-exact anchor (one occurrence in the file; the paragraph currently ends with "so it sits at the Spec/Orchestrator seam."):

A planning thread lives in `plan/<topic>/` and carries two facets: The appended sentence reads:

The thread directory MAY additionally host one Control-Plane-authored supervision prompt at the reserved `plan/<topic>/supervisor-handoff.md` — a hosted artifact of the Control Plane's coordinate-the-human charter, not a third facet; the Spec and Orchestrator Planes MUST treat it as opaque (detail: `non-functional-requirements.md` §"Planning Lane guidance").

Neither edit adds, removes, or renames any `## ` heading, so no `tests/heading-coverage.json` co-edit is required. No scenario is added: this lands inside guidance that is explicitly NON-normative on core's contract ("core neither names nor verifies any of it") and the design's constraint is exactly that core gains no new skill, CLI, or doctor invariant.
