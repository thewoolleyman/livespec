# Supervisor Handoff - supervisor-skill (ARCHIVED)

This file is intentionally non-executable. The `supervisor-skill` plan is
closed, its directory is archived, and no `supervisor-skill` or
`supervisor-skill-supervisor` tmux session should be started from this prompt.
The former HALT-first checks, driving instructions, and active-path references
remain available in git history.

## What This Archived Supervisor Track Completed

- Preserved the adopted Control-Plane ownership model for
  `plan/<topic>/supervisor-handoff.md`.
- Recorded the merged `livespec-overseer` source implementation
  (`supervise-plan`, PR #49) and its bounded live exercise that produced
  livespec PR #1706.
- Recorded the ratified hosting declarations in livespec core v175
  (PR #1731) and `livespec-orchestrator-beads-fabro` v048 (PR #937).
- Corrected this track's supervisor semantics in livespec PR #1736: an
  ownership conflict blocks only the conflicting action, not all legitimate
  coordination; when every legitimate action is genuinely maintainer-blocked,
  ask the human-facing question immediately and put the recommended answer
  first.
- Filed `overseer-fitvmo` in `livespec-overseer` for the corresponding
  generated-prompt/template regression.

## What This Archive Does Not Prove

A merged source binding and one local exercise do not prove that the plugin was
released, installed, loaded, or discoverable in fresh fleet/adopter sessions.
This archive also does not prove top-of-pyramid shipping coverage, automatic
release, automatic fleet/adopter installation, or automatic release-pin
propagation.

Those outcomes remain in the owning repository's productization and shipping
track. Start any new worker or supervisor sessions from:

`/data/projects/livespec-overseer/plan/cutover-and-shipping/handoff.md`

Do not resume this archived supervisor prompt, and do not use its archived
status as a completion signal for `livespec-overseer`.
