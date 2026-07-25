# supervisor-skill - archived completion record

**Ledger anchor:** epic `overseer-3wt` (`livespec-overseer` tenant).
**Opened:** 2026-07-25. **Archived:** 2026-07-25.

This thread is closed and is not an active resume point. It preserves the
core-side coordination record for the durable `supervisor-handoff.md` design,
its bounded source-level proof, the upstream hosting declarations, and the
supervisor prompt correction. It does not claim that the `livespec-overseer`
plugin completed release, installation, or fleet/adopter rollout.

## Completed Work

- The maintainer adopted the Control-Plane `supervise-plan` shape: the
  `livespec-overseer` plugin owns creation of
  `plan/<topic>/supervisor-handoff.md` through the target repository's normal
  worktree -> PR -> merge discipline. The full reasoning remains in
  `plan/archive/plan-skill-supervisor-handoff/design.md`.
- The source implementation of the `supervise-plan` binding, prose, and tests
  merged in `livespec-overseer` PR #49 as work item `overseer-myjovi`.
- A bounded live exercise ran that source operation against the live
  `rop-sweep-fleet-policy` track and created its reviewed artifact through
  livespec PR #1706. That proves the operation in the exercise environment; it
  is not proof that a released plugin is installed or discoverable in a fresh
  fleet or adopter session.
- The hosted-artifact declarations were ratified in livespec core v175
  (PR #1731) and `livespec-orchestrator-beads-fabro` v048 (PR #937). Those
  declarations let a plan directory host one opaque Control-Plane supervisor
  artifact without making the Spec or Orchestrator plane create or consume it.
- The no-idle/no-silent-block correction landed in livespec PR #1736,
  commit `90cef6a18dfc78ba18c712596d36dc138ec262d6`. The archived supervisor
  prompt now records that a conflicting ownership lane is not a thread-wide
  blocked state: continue legitimate non-conflicting work, or immediately ask
  the maintainer the genuinely blocking question with the recommended answer.
- Follow-up work item `overseer-fitvmo` was filed in `livespec-overseer` to
  carry that correction into the generated `supervise-plan` prompt/template
  and its regression tests.

## Explicit Scope Boundary

This archive is not evidence that any of the following are complete:

- published-release availability of the `livespec-overseer` plugin;
- discovery and invocation of `/livespec-overseer:supervise-plan` from a fresh,
  correctly installed Claude/tmux session, including
  `worktree-location-enforcement`;
- top-of-pyramid end-to-end coverage for the shipping and installation
  scenarios;
- automatic plugin release;
- automatic installation for fleet and adopter repositories; or
- automatic propagation of the released plugin pin.

Those productization, cutover, shipping, and rollout outcomes belong to the
active plan in the owning repository:

`/data/projects/livespec-overseer/plan/cutover-and-shipping/handoff.md`

Do not reopen this livespec-core archive to perform that work, and do not cite
this archive's closed state as proof that the owning plan's acceptance gates
have passed. Start follow-up sessions in `livespec-overseer` from the path
above.

## Historical Supervisor Prompt

The companion
`plan/archive/supervisor-skill/supervisor-handoff.md` is an archived,
non-executable completion record. The former live-session prompt and restart
instructions remain available in git history, but are intentionally absent
from current tracked state so a fresh reader cannot restart this closed track
by mistake.
