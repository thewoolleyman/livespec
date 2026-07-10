# Fable fresh-review round 2 — autonomous-mode MVP plans

**Reviewer:** a FRESH Fable-model session (no prior involvement in authoring
or revising these plans; resumed the thread via the `plan` operation and ran
`research/fable-review-brief.md` end-to-end). **Date:** 2026-07-10.

Scope: all three plans at `origin/master` as revised by round 1 —
`livespec/plan/autonomous-mode/{handoff,design}.md`,
`livespec-console-beads-fabro/plan/autonomous-mode/{handoff,design}.md`,
`livespec-orchestrator-beads-fabro/plan/autonomous-mode/{handoff,design}.md`.
Every factual claim re-verified against the live spec trees (`git show
origin/master:…`), the crate/script sources, the three Beads tenants (`bd
show … --json` via the credential wrapper, from inside each repo), and
master CI (`gh run list --workflow CI` — green on all three repos at review
time). Prior-round documents were read only AFTER forming an independent
view; all nine round-1 observations and all four currency corrections
verify as baked into the current plan texts — nothing was lost.

## Round 2 fresh review: FIXES LANDED

Nothing found makes any plan unsound, unexecutable, or MVP-missing — the
dependency graph is consistent across all three documents, every step has an
owner/gate/checkable done, the three seam pins are coherent with both live
specs, and executing the steps in order still reaches the MVP and passes I2
under its full gate. But real defects WERE found and fixed (below), so per
the loop rule this round does NOT clear the gate; round 3 runs next with
another fresh session.

### Per-plan
- **livespec (overall):** solid; two defects fixed (stale `orchestrate run`
  in its own C2 step text; C2-gate ambiguity) + one currency update
  (fabro-token-refresh) + the missing thread epic anchor recorded.
- **console operator surface (`livespec-console-beads-fabro`):** solid; one
  defect fixed (same C2-gate ambiguity) + one factual nit (`mb64bv` is a
  `chore`, not a task) + round-agnostic loop-status wording.
- **orchestrator engine (`livespec-orchestrator-beads-fabro`):** solid; one
  currency update (fabro-token-refresh) + one done-check precision fix (O2's
  "done" no longer hard-codes `drive --mode autonomous` ahead of O1's
  surface pin) + round-agnostic loop-status wording.

### Fixed this round (finding → fix → merged PR)
1. **Core design §7 C2 cited the stale `orchestrate run` surface** — the
   very citation the plans themselves declare CONFIRMED DRIFT (§6.3 d; the
   published surface is `drive`). Fixed to `drive`. → repo
   `thewoolleyman/livespec` PR #1014.
2. **C2's gate was ambiguous after round 1 made C1 two-phase.** Round 1
   split C1 into a main ratification + an I1-gated persistence-seam
   amendment, but C2 stayed gated on bare "C1" — read literally, C2
   serializes behind orchestrator O1 (via I1), contradicting the
   load-bearing "C2 ∥ O1→O2" parallelism claim that round 1's own verdict
   affirmed. Clarified in all three places (core design §7 C2 gate + core
   handoff step 5; console design §4 C2 gate + console handoff gates line):
   C2 gates on C1's MAIN ratification; the persistence-seam amendment gates
   C3 only. → `thewoolleyman/livespec` PR #1014,
   `thewoolleyman/livespec-console-beads-fabro` PR #141.
3. **fabro-token-refresh state moved after round 1** (round-1 revisions
   merged 03:37–03:51Z; the thread's validation landed 04:55Z). The 60-min
   App-token TTL fix is now VALIDATED LIVE (gh-free publish via GitHub
   REST/GraphQL proven on `livespec-console-beads-fabro` PR #136; a genuine
   >60-min run pushed green past the TTL); the landing sequence (upstream
   fabro PR, production pin, PR #136 cleanup) awaits maintainer decisions in
   that thread's handoff. Plans no longer describe the TTL as an active
   killer; it remains an I2 precondition until production fabro carries the
   fix. → `thewoolleyman/livespec` PR #1014,
   `thewoolleyman/livespec-orchestrator-beads-fabro` PR #404.
4. **`mb64bv` is a `chore`, not "task"** in the console design §6 (verified
   against the live console tenant). →
   `thewoolleyman/livespec-console-beads-fabro` PR #141.
5. **O2's "Done" hard-coded `drive --mode autonomous`** while O1 pin (c)
   may pin the mode flag to the dispatcher `loop` subcommand — a later
   "done" dispute waiting to happen. The done-check now names whichever
   mode-bearing surface O1's contract pins. →
   `thewoolleyman/livespec-orchestrator-beads-fabro` PR #404.
6. **Sibling handoffs' loop-status lines were per-round snapshots** that
   would go stale every round. Reworded round-agnostically, pointing at the
   authoritative loop state in this repo's handoff. → PRs #141 and #404.

### Non-blocking observations
1. **This thread has NO ledger epic anchor in the core tenant** — every
   other active core plan thread has one, and the Planning-Lane realization
   expects the handoff to cite it. A review round is barred from ledger
   writes, so the DRIVER must file it via the `capture-work-item` operation
   at next touch (now recorded in the handoff's Ledger-items section).
2. **fabro-token-refresh carries four pending maintainer decisions**
   (upstream fabro PR, production-fabro sequencing, PR #136 cleanup,
   fleet-wide gh-removal scope) that gate its landing sequence — I2 timing
   depends on them; they live in that thread's handoff, not here.
3. `pke3y3`'s in-ledger description still carries the stale pre-v014
   command list — already handled by C2's planned regroom-and-split; no
   plan change needed.
4. `drive` hardcodes `--mode shadow` when delegating to the dispatcher
   `loop` subcommand (`build_dispatcher_argv`, `commands/drive.py`) —
   further confirmation that O1 pin (c) (which surface carries
   `--mode autonomous`) is a REAL decision, not a wording nit.

### Currency findings
1. **fabro-token-refresh moved** (fixed — see Fixed #3). Genuinely
   post-round-1 state, not a round-1 miss.
2. **`mb64bv` type** (fixed — see Fixed #4).
3. **Everything else verified TRUE today**, including: console spec v016 /
   orchestrator v032 current with zero pending proposals; master CI green
   ×3; every quoted spec clause verbatim-present (orchestrator spec.md:145
   §"Full autonomous mode", contracts.md:1331 incl. the persistent
   `…dispatcher.autonomous_mode` key + "MUST NOT persist beyond the current
   invocation" tension, contracts.md:781 `manual` = "first-class realization
   of the prior `human-gated` spec-change marker", the Terminology
   three-pronged truly-unresolvable test, Scenarios 33-37 with the
   Scenario-36 `human-only` carve-out; console contracts.md:395 stale
   "`orchestrate run`" citation and :490 lane-ownership mis-attribution —
   both still awaiting C1 as planned; core spec.md:387 drift-acceptance
   normative quote; the non-normative grooming-guidance attributions);
   every implementation-absence claim (console `CommandType` =
   `FactoryDrainRequested` only, zero `autonomous` hits, no
   `.livespec.jsonc` reading, read-side `AcceptancePolicy` = `AiThenHuman`
   only, real `DispatcherFactoryDrainPort` with honest `NotWired`;
   orchestrator `--mode autonomous` = queue-scope only, valves hold/park,
   blocked never auto-resumes, cost gate fail-closed, no
   `dispatcher.autonomous_mode` key in code, `loop` at dispatcher.py:2594);
   all ledger statuses (`rt4` backlog + stale v013 pointer, `pke3y3` epic
   backlog, `ipi` backlog, `mb64bv` active with gate `iblkzp` closed, the
   fully-closed impl-dispatch chain, `bd-ib-82a` backlog no-slices no-deps
   + stale v025 pointer, open `bd-ib-18r`/`bd-ib-6vu`, core `livespec-nrdk`
   epic + `livespec-0jxs` task both backlog, closed `livespec-35s3zo` /
   `livespec-zs22.6`); "backlog-bounce" absent from orchestrator spec+code
   with journal field `bounced_to_regroom`; the `drive` action-id grammar
   matching the console's five commands exactly; and round-1's PRs (#395,
   #134, #1000) all merged.

## Loop consequence

FIXES LANDED → round 3 runs next, with ANOTHER fresh Fable session (this
session cannot clear the gate on its own fixes). The handoff's Loop state
and Next actions are updated accordingly in the same PR as this record.
