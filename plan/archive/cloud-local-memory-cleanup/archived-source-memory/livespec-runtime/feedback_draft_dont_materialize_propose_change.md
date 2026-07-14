---
name: feedback_draft_dont_materialize_propose_change
description: "When drafting a spec change for a maintainer-owned revise gate, surface a validated findings draft — do NOT run propose-change to materialize the on-disk proposed_changes file."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: db4fe3bd-c210-4624-b143-857675bb0685
---

When a livespec spec change is headed for the maintainer-owned `revise`
ratification gate, **draft the propose-change PAYLOAD** (a schema-valid
`proposal_findings.schema.json` findings JSON + a human-readable
spec-delta doc in the plan thread) and surface it — do NOT run
`/livespec:propose-change` yourself to materialize
`SPECIFICATION/proposed_changes/<topic>.md`.

**Why:** the maintainer owns `revise`; authoring the on-disk
proposed-change file (which runs doctor pre/post static + the in-flight
survey) belongs with that gate. Materializing it early risks partial
state and splits authoring from ratification. Keep them together under
the maintainer's gate.

**How to apply:** ship the findings JSON + deltas doc in the plan
thread; the handoff's next action is "maintainer authors from the
findings JSON, then `/livespec:revise`." Confirmed for the L0
work-item-state-machine track (epic livespec-runtime-l4yojx). See
[[feedback_worktree_discipline]].
