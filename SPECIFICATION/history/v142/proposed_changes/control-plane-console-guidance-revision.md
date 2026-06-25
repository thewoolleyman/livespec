---
proposal: control-plane-console-guidance.md
decision: accept
revised_at: 2026-06-25T16:28:14Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Increment 4 of epic livespec-zs22. Lands the Control-Plane discipline as NON-normative guidance in non-functional-requirements.md, framed exactly like the existing Dispatcher / grooming / Planning Lane blocks (core records the repo-agnostic PATTERN; the reference console's own spec owns the realization; no new core skill / CLI / doctor invariant). It is a NEW top-level '### Control-Plane console guidance' section — a PEER of '### Orchestrator plugin ecosystem', not an H4 nested inside it — because the console is the Control Plane, a plane distinct from the Orchestrator Plane; nesting it under the orchestrator section would contradict the plane separation this track codifies. Records what the console reads / composes / coordinates / never owns, that it is not a required dependency and not a Driver, and the just boundary. Honors locked decision 4 (console is the Control Plane / runner, distinct from a Driver, not yet a required dependency) and locked decision 3 (just non-functional-only). H3 addition, so heading-coverage (which tracks H2 only) is unaffected. Source design: research/planning-workflow-gap/planning-lane-design.md.

## Resulting Changes

- non-functional-requirements.md
