# spec-side-autonomy — handoff

Design thread for automating the remaining spec-side human gates
(revise delegation, drift acceptance, the groom cut, doctor
dispositions, ratification-review codification) via a core-owned
`spec_governance` config lever family, composing with the
livespec-overseer foreman (repo `livespec-overseer`, thread
`plan/foreman/`).

**Ledger anchor:** epic `livespec-jvdvx4` (livespec tenant). Status is
READ from the ledger (`list-work-items` / `next`), never stored here.

## Read first

1. `plan/spec-side-autonomy/research/brainstorm.md` — the complete
   grounded design: the two already-armed impl-side levers, the
   three-class gate inventory, the `spec_governance` lever family with
   its unconditional floors, the three increments with their per-repo
   landing map, the `dispatcher.*` pattern checklist to mirror, and
   the three values calls with their 2026-08-03 resolutions.

## Next action

Two independent lanes; neither waits on the other:

**Lane A — CLOSED 2026-08-03.** All three values calls are resolved;
the decisions are recorded in `research/brainstorm.md` §"Values calls —
ALL THREE RESOLVED 2026-08-03" and are ratified inputs to Increments 2
and 3, not re-openable without a fresh maintainer decision:

1. the drift-doctrine sentence IS amendable, to the consensus tier only,
   via a DEDICATED `spec_governance.drift_acceptance_mode` key
   (`human | consensus`, default `human`, opt-in, Increment 3);
   `delegated` is never legal for drift, and the key must not ship
   armed-able before the consensus panel exists;
2. the groom cut MAY leave the maintainer's hands, but automated last,
   consensus-gated, with slice-size ceilings and a regroom cap as
   required rails;
3. the consensus-tier definition lives in livespec core;
   `livespec-orchestrator-beads-fabro` and `livespec-overseer`
   implement it.

**Lane B — Increment 1 (no doctrine change; proceed without Lane A).**
Draft Increment 1 (the no-doctrine-change levers) as
`/livespec:propose-change` proposals against this repo's
`SPECIFICATION/`, one topic file per independently-acceptable piece,
each ratified only after the independent adversarial review
(`AGENTS.md` §"Independent Fable review before every ratification";
`.ai/spec-proposal-review.md`) returns NO BLOCKERS. File matured
implementation slices as children of epic `livespec-jvdvx4` via the
`capture-work-item` operation; ready, factory-safe slices are built
factory-side — the `drive` operation (action `impl:<id>`) or the
Dispatcher drain — never inline in a planning session.

## Mechanics

- Ledger operations are the `livespec-orchestrator-beads-fabro`
  plugin surface (e.g. `/livespec-orchestrator-beads-fabro:list-work-items --json`
  to read epic status; `/livespec-orchestrator-beads-fabro:capture-work-item`
  to file children). "Dispatcher drain" means the same plugin's
  Dispatcher polling and dispatching `ready` items unattended — the
  sanctioned alternative to per-item `drive --action impl:<id>`.
- All repo edits (this thread's files included) follow `AGENTS.md`
  §"Repository mutation protocol": dedicated worktree under
  `~/.worktrees/livespec/<branch>` → PR → rebase-merge → cleanup;
  never commits on the primary checkout.

## Standing constraints for this thread

- Class (c) gates (drift acceptance, the groom cut, the
  truly-unresolvable set) are doctrine floors: no config key may touch
  them without a ratified spec amendment, and any such amendment is
  Increment 3. The values calls that gated those amendments are now
  RESOLVED (see "Lane A — CLOSED" above), so Increment 3 is unblocked
  in principle — but it remains blocked in practice until the consensus
  panel exists, and the `drift_acceptance_mode` key must not ship
  armed-able before it does.
- Increment 3's truly-unresolvable-set amendment in
  `livespec-orchestrator-beads-fabro` is PARTIAL, not wholesale: the
  groom cut may move behind the consensus tier, and drift acceptance
  moves only to `consensus` — never to a single delegated model.
- The orchestrator `drive` contract's refusal of spec-side action-ids
  is deliberately preserved; the foreman is the spec-side executor.
- Cross-repo pieces land as one epic with per-repo child work-items
  and cross-repo links — never "follow-up PRs in another session".
