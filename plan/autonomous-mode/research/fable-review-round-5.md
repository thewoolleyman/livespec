# Fable fresh-review round 5 — autonomous-mode MVP plans

**Reviewer:** a FRESH Fable-model session (no prior involvement in authoring
or revising these plans; spawned by the driver session with
`research/fable-review-brief.md` and ran it end-to-end). **Date:** 2026-07-10.

Scope: all three plans at `origin/master` as revised by rounds 1-4 —
`livespec/plan/autonomous-mode/{handoff,design}.md`,
`livespec-console-beads-fabro/plan/autonomous-mode/{handoff,design}.md`,
`livespec-orchestrator-beads-fabro/plan/autonomous-mode/{handoff,design}.md`.
Every load-bearing claim verified first-hand against live state this
session: the spec trees via `git show origin/master:<path>`, the
crate/script sources, all three Beads tenants (`bd show … --json` via the
credential wrapper, from inside each repo), and master CI (`gh run list
--workflow CI` — green on all three repos at review time). Prior-round
records were read only after forming an independent view; all nine round-1
step-0 observations remain folded in — nothing lost.

## Round 5 fresh review: FIXES LANDED

One real defect found — a currency/completeness citation in the overall
plan's own Loop state — fixed and merged this session. Both sibling plans
passed clean again (the console plan's third consecutive clean round; the
orchestrator plan's second). Because a fix landed, this round does NOT
clear the gate; round 6 runs next with another fresh session.

### Per-plan
- **livespec (overall):** solid; ONE currency fix landed (the round-4
  Loop-state bullet omitted the record-carrying PR #1023). Structure
  sound — the dependency graph is acyclic and agrees across all three
  documents (`Step0→C1→C2→C3→I2`; `Step0→O1→O2→I2`; `O1/I1→C3 and C1's
  persistence-seam portion`), every step has an owner, a gate, and a
  checkable "done", the three seam pins (single persistent permission key
  = the orchestrator's `dispatcher.autonomous_mode`;
  engine-owns-all-gate-resolution + Scenario-10 re-scope; the two vocab
  fixes) are coherent with both live specs, and executing the steps in
  order reaches the MVP under I2's full gate.
- **console operator surface (`livespec-console-beads-fabro`):** solid;
  NO fixes needed — third consecutive clean round. Spec v016 / zero
  pending proposals; both C1 citation drifts still present as planned
  (`contracts.md:395` "orchestrate run", `:490` "owned by livespec
  core"); `CommandType` = `FactoryDrainRequested` only, zero `autonomous`
  hits in `crates/`, `AcceptancePolicy` = `AiThenHuman` only; ledger
  `rt4` (feature/backlog/v013), `pke3y3` (epic/backlog), `ipi`
  (task/backlog), `mb64bv` (chore/active), gate `iblkzp` (closed) all
  exact.
- **orchestrator engine (`livespec-orchestrator-beads-fabro`):** solid;
  NO fixes needed — second consecutive clean round. Spec v032 / zero
  pending proposals; no `dispatcher.autonomous_mode` config key in code
  (only the cost-label constant `_AUTONOMOUS_MODE` at
  `_dispatcher_cost.py:109/211`); `loop` carries `--mode` at
  `dispatcher.py:2594` while `drive` does not; the O1 hazard is verbatim
  real (`contracts.md:1345` collapse auto-approves even stored-`manual`
  items vs `:781` naming `manual` the spec-change-marker realization) +
  Scenario 36's `human-only` carve-out present; `bounced_to_regroom`
  real (6 files) / `backlog-bounce` absent; `bd-ib-82a`
  (feature/backlog/no deps/v025 pointer), bugs `bd-ib-18r`/`bd-ib-6vu`
  open.

### Fixed this round (finding → fix → merged PR)
1. **Round-4 Loop-state bullet omitted the record-carrying PR.** The core
   handoff's round-4 bullet cited only "core PR #1022" for the round-4
   "verdict + fixes", but the round-4 record
   (`research/fable-review-round-4.md`) + the handoff Loop-state advance
   actually landed in PR #1023 — #1022 carried only the two plan fixes.
   Rounds 2 and 3 both name their record-carrying PR; round 4's omission
   left the durable loop-state audit trail missing the PR that advanced
   it (the same currency/completeness class prior rounds fixed). →
   Reworded the bullet to "fixes in core PR #1022, record + loop state in
   core PR #1023". → `thewoolleyman/livespec` PR #1024 (merged, master
   `9f7236e`): <https://github.com/thewoolleyman/livespec/pull/1024>

### Non-blocking observations
1. **`rt4` naming nuance:** the core handoff's Ledger bullet calls `rt4`
   an "epic-shaped feature" while its `issue_type` is `feature` (console
   design §6 says "feature, backlog"). Not a contradiction —
   "epic-shaped" is a size descriptor, not the type — so no fix.
2. **Carried from prior rounds, still no plan change needed:** console
   `plan/impl-dispatch/` remains unarchived (separate housekeeping, not a
   dependency); the fabro-token-refresh thread's OWN handoff still lists
   the moot "PR #136 cleanup" question (out of this loop's scope — the
   autonomous-mode plans no longer repeat it); orchestrator
   `plan/codex-factory-telemetry/` corroborates the "NO telemetry
   shipping" operability claim behind `livespec-0jxs`.
3. **Repo states at handoff:** both sibling repos left exactly as found
   (read-only): console on master/clean/behind origin by 2; orchestrator
   behind origin by 1 with the pre-existing maintainer-owned dirty
   `orchestrator-image/real-work-dispatch.sh` + untracked
   `plan/fabro-token-refresh/design-notes.md` untouched. Core primary
   refreshed to `9f7236e`, clean on master, worktree removed, branch
   deleted.

### Currency findings
Everything re-verified TRUE today except the one fixed citation (core,
above). Confirmed current: console spec v016 / orchestrator spec v032,
both zero pending proposals (console `proposed_changes/` = README only;
orchestrator = `.gitkeep` only); master CI green ×3; core PRs
#1020/#1022/#1023 merged, console PR #136 merged 2026-07-10; core epic
anchor `livespec-bvuy4w` (epic/backlog; `livespec-nrdk` [epic] blocks /
`livespec-0jxs` [task] related), closed `livespec-35s3zo` [epic] +
`livespec-zs22.6` [task]; core `spec.md:387` drift-acceptance normative
quote under §"Contract + reference implementations architecture",
non-functional-requirements.md:149 spec-change human-gated + :162 regroom
"one human-in-the-loop step" both explicitly NON-normative; and core
SPECIFICATION defines no work-item lane vocabulary and no `attention_item`
schema (the shipped `attention_item.py` runtime is the diff target).

## Loop consequence

FIXES LANDED → round 6 runs next, with ANOTHER fresh Fable session (the
round-5 session cannot clear the gate on its own fix). Convergence signal:
round 1 = 9 observations + 4 corrections; round 2 = 6 fixes; round 3 = 2;
round 4 = 2 with both siblings clean; round 5 = 1 currency fix with BOTH
siblings clean again. The handoff's Loop state and Next actions are
updated in the same PR as this record.
