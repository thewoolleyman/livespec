# research/architecture/

Architectural sketches and multi-repo / multi-component design
explorations. Distinct from `research/workflow-processes/` (which
captures HOW livespec is built and how contributors collaborate)
and `research/beads/` (which catalogues beads-specific upstream
issues).

## What lives here

Long-form design discussions that consider the *shape* of the
livespec system at the repo / artifact / contract level — how
components decompose, where contracts live, what dependencies
flow which way, and what tradeoffs each topology implies.

Files here are pre-formal: the load-bearing answers, when they
mature, get codified into `SPECIFICATION/` via
`/livespec:propose-change` → `/livespec:revise`. The research
doc itself stays here as the audit trail of how the answer was
reached, or gets deleted if it's wholly superseded.

## What does NOT belong here

- Implementation-level intent (refactors, helpers, cleanups) —
  file as a freeform beads issue instead.
- Workflow-process discussions (agent / contributor patterns,
  issue-tracker scope, observation routing) — those go in
  `research/workflow-processes/`.
- Beads upstream issues — `research/beads/`.
- Frozen historical artifacts — `archive/`.
