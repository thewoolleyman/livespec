# supervisor-skill — active handoff

**Ledger anchor:** epic `overseer-3wt` (livespec-overseer tenant).
**Opened:** 2026-07-25. **Status:** ACTIVE coordination thread.

This thread supersedes the archived research-only topic
`plan/archive/plan-skill-supervisor-handoff/`. Read that archived design note
for historical context only; do not resume from it.

## Current Objective

Keep the durable supervisor prompt feature moving without colliding with the
active `cutover-and-shipping` track.

The feature has already shipped its core shape:

- `supervise-plan` exists in `livespec-overseer` and can create
  `plan/<topic>/supervisor-handoff.md` through the target repo's own
  worktree -> PR -> merge discipline.
- `livespec` core and `livespec-orchestrator-beads-fabro` have ratified the
  upstream one-line declarations that let a plan directory host one
  Control-Plane supervisor artifact while the Spec and Orchestrator planes
  ignore it.
- The remaining `livespec-overseer` spec repair/ratification lane is active
  elsewhere, under `cutover-and-shipping`.

## Hard Conflict Boundary

Do not touch the `livespec-overseer` PR #44 proposed-change lane from this
thread unless the maintainer explicitly transfers ownership here.

That lane includes:

- `SPECIFICATION/proposed_changes/non-interference-attended-skill-carveout.md`
  in `livespec-overseer`.
- The review blockers found by `plan-skill-supervisor-handoff`: missed
  `constraints.md` drift and missing discovery scenario coverage.
- The advisory to split the already-shipped attended `supervise-plan` carve-out
  from the unbuilt Surface A/B existence-probe allowance.
- Any `/livespec:revise` ratification or follow-up dispatch of
  `overseer-6uobos`.

`cutover-and-shipping` is already surfacing and driving that maintainer decision.
This thread may pass review findings to that track, but must not repair, split,
ratify, dispatch, or close the same work.

## What This Thread Owns

- Preserve the durable design record by keeping the old topic archived and this
  topic as the active resume point.
- Keep future supervisor-skill sessions conflict-aware.
- Verify that any new supervisor prompt artifacts created in `livespec` do not
  duplicate active work owned by another plan thread.
- Resume work only on supervisor-skill coordination that is not already owned by
  `cutover-and-shipping` or another named track.

## Immediate Resume Checklist

1. Re-check the live tmux sessions for `cutover-and-shipping` and
   `supervisor-skill`; do not infer state from this file.
2. Re-read `cutover-and-shipping`'s visible pane or handoff before touching any
   `livespec-overseer` proposal.
3. If `cutover-and-shipping` still owns PR #44/proposal repair, stand down only
   on that conflicting lane, offer review findings as input, and continue any
   non-conflicting supervisor-skill coordination work.
4. If ownership has been explicitly transferred, record the transfer in this
   handoff before acting.

## Blocked-State Rule

A conflicting lane is not a thread-wide blocked state. Never declare blocked or
leave this lane idle merely because PR #44/proposal repair remains owned by
`cutover-and-shipping`.

When a conflict is found, preserve the boundary and keep moving on legitimate
non-conflicting work: update the supervisor prompt, refresh this handoff,
prepare safe tmux nudges, or pass findings to the owning track without taking
over its proposal lane.

Declare `blocked:` only when every legitimate non-conflicting action is blocked
by a genuinely human-facing maintainer-only decision. When that happens, ask the
blocking question immediately and state the recommended answer first.

## Next Action

After this rotation lands, restart fresh sessions named exactly:

- supervised: `supervisor-skill`
- supervisor: `supervisor-skill-supervisor`

The fresh supervisor should read `plan/supervisor-skill/supervisor-handoff.md`
first. The fresh supervised session should read this file first.

## Standing Safety

- Never pass `--no-verify`; halt and report on hook failure.
- Never touch another session's worktrees, branches, or active proposal lane.
- Treat plan prose as stale until re-verified from git, GitHub, ledger, and tmux
  live state.
- If a remaining action is owned by `cutover-and-shipping`, stand down only on
  that action and continue non-conflicting coordination work. If nothing
  legitimate remains, ask the maintainer a blocking question with the
  recommended answer first.
