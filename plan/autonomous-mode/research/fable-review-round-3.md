# Fable fresh-review round 3 — autonomous-mode MVP plans

**Reviewer:** a FRESH Fable-model session (no prior involvement in authoring
or revising these plans; resumed the thread via the `plan` operation and ran
`research/fable-review-brief.md` end-to-end). **Date:** 2026-07-10.

Scope: all three plans at `origin/master` as revised by rounds 1-2 —
`livespec/plan/autonomous-mode/{handoff,design}.md`,
`livespec-console-beads-fabro/plan/autonomous-mode/{handoff,design}.md`,
`livespec-orchestrator-beads-fabro/plan/autonomous-mode/{handoff,design}.md`.
Every factual claim re-verified against the live spec trees, the
crate/script sources, the three Beads tenants (`bd show … --json` via the
credential wrapper, from inside each repo), and master CI (`gh run list
--workflow CI` — green on all three repos at review time). Prior-round
documents were read only AFTER forming an independent view; every round-1
observation/correction and every round-2 fix verifies as present in the
current plan texts — nothing was lost. (Mid-round, the orchestrator's
master advanced by two routine `chore(deps)` pin bumps to v0.36.3; a diff
confirmed the plan documents were untouched.)

## Round 3 fresh review: FIXES LANDED

No structural defect anywhere: the dependency graph is consistent across
all four documents that state it (core design §7 + core handoff step 5 +
console design §4 + console handoff gates line), every step has an
owner/gate/checkable done, the three seam pins are coherent with BOTH live
specs (persistent key + invocation-mode tension verified verbatim at
orchestrator contracts.md §"Arming full autonomous mode"; `loop` — not
`drive` — verified as the shipped mode-bearing entry point at
`dispatcher.py:2594`; Scenario 10's console-records-the-command first case
verified verbatim), and executing the steps in order still reaches the MVP
and passes I2 under its full gate. But two small state claims failed the
"true TODAY" bar and were fixed per the loop rule, so this round does NOT
clear the gate; round 4 runs next with another fresh session.

### Per-plan
- **livespec (overall):** solid; two precision/currency fixes landed
  (design §2 `livespec-zs22.6` is a closed *task*, not an epic; design §9
  stale "PR #136 cleanup" pending-decision).
- **console operator surface (`livespec-console-beads-fabro`):** solid;
  NO fixes needed — every claim verified true today (first plan to pass a
  round clean).
- **orchestrator engine (`livespec-orchestrator-beads-fabro`):** solid;
  one currency fix landed (design §5 stale "PR #136 cleanup"
  pending-decision).

### Fixed this round (finding → fix → merged PR)
1. **"PR #136 cleanup" listed as a pending maintainer decision** in the
   fabro-token-refresh landing-sequence parentheticals (core design §9;
   orchestrator design §5) — the PR #136 validation vehicle
   (`livespec-console-beads-fabro` PR #136) auto-merged 2026-07-10T04:26Z,
   BEFORE round 2's fixes landed (~06:26Z), so that decision is resolved
   by event; only the upstream-fabro-PR and production-pin decisions still
   gate the landing sequence. Both parentheticals now say so. →
   `thewoolleyman/livespec-orchestrator-beads-fabro` PR #410; the core
   half rides in this record's PR.
2. **Core design §2 called `livespec-zs22.6` a "closed epic"** — the live
   core tenant shows it is a closed *task* (`livespec-35s3zo` is the
   epic). Same precision class as round 2's `mb64bv` chore-not-task fix.
   → this record's PR.

### Non-blocking observations
1. **Active orchestrator thread `plan/codex-factory-telemetry/` is
   unmentioned by the plans but corroborates them**: the Honeycomb
   telemetry pipeline has been dark for every factory run since
   ~2026-06-13 (the emitter gap — Codex emits none of the telemetry the
   Claude-Code-native pipeline captures), which confirms the plans'
   "NO telemetry shipping" operability claim (via `livespec-0jxs`) is
   true today. No plan change needed: I2's gate deliberately requires
   only the verified cost ceiling + a real failure-surfacing path, and
   O2's per-decision audit journal is dispatcher-written (host-side), so
   the dark agent-telemetry leg invalidates no step. Driver awareness for
   I2's operability assessment.
2. **The core epic anchor for this thread remains unfiled** (carried from
   round 2; review rounds are barred from ledger writes — the DRIVER
   files it via `capture-work-item` at next touch).
3. **The fabro-token-refresh thread's own handoff still lists the moot
   PR #136 cleanup question** among its maintainer decisions — staleness
   in THAT thread's artifact, out of this loop's scope (this loop reviews
   the three autonomous-mode plans; the plans no longer repeat it).
   Its three load-bearing decisions (upstream fabro PR, production-fabro
   sequencing, fleet-wide gh-removal scope) remain genuinely pending, so
   the plans' "landing sequence awaits maintainer decisions" claim holds.
4. Console `plan/impl-dispatch/` remains unarchived — already recommended
   as separate housekeeping by the plans; not a dependency.
5. Convergence signal: round 1 = 9 observations + 4 corrections; round
   2 = 6 fixes; round 3 = 2 small currency/precision fixes with the
   console plan passing clean.

### Currency findings
1. **"PR #136 cleanup" pending-decision stale** (fixed — Fixed #1).
   Genuinely a pre-round-2 event that round 2 propagated, not new state.
2. **`livespec-zs22.6` mislabeled "epic"** (fixed — Fixed #2).
3. **Everything else verified TRUE today**, including: console spec v016 /
   orchestrator v032 current, both with zero pending proposals; master CI
   green ×3; every quoted spec clause verbatim-present (orchestrator
   spec.md:145-178 §"Full autonomous mode" incl. the `manual`-collapse
   clause, contracts.md:1331-1404 incl. the persistent
   `…dispatcher.autonomous_mode` key defaulting `false` + "MUST NOT
   persist beyond the current invocation", constraints.md:143-165,
   contracts.md:781 `manual` = "first-class realization of the prior
   `human-gated` spec-change marker" under §"Dispatcher grooming
   behavior", the Terminology three-pronged truly-unresolvable test
   naming no design-gated decision, Scenarios 33-37 with Scenario 36's
   `human-only` carve-out; console contracts.md:395 stale "`orchestrate
   run`" + :490 lane-ownership mis-attribution both still awaiting C1 as
   planned, §"Autonomous Mode" persistence block, §"TUI Contract",
   constraints §"Autonomous-Mode Safety", Scenario 10's first case
   verbatim; core spec.md:387 drift-acceptance normative quote, the
   non-normative grooming-guidance attributions at
   non-functional-requirements.md:134/149/162, no lane vocabulary and no
   `attention_item` schema in core SPECIFICATION/, the shipped runtime
   schema fields `id/kind/urgency/summary/source_ref/handoff` exact);
   every implementation-absence claim (console `CommandType` =
   `FactoryDrainRequested` only, zero `autonomous` hits in `crates/`,
   `TuiView`/`TuiOverlay`/`OperatorAction` exact, no `.livespec.jsonc`
   reading in any crate and no `autonomous_mode` block in the repo's
   `.livespec.jsonc`, read-side `AcceptancePolicy` = `AiThenHuman` only,
   real `DispatcherFactoryDrainPort` at `main.rs:104`/`:130` with honest
   `NotWired`; orchestrator `--mode autonomous` = queue-scope only
   (`dispatcher.py:84-86`), blocked never auto-resumes (`:100-102`),
   valves hold/park (`_dispatcher_valves.py` admission plan +
   `acceptance_decision` parking `human-only`/`ai-then-human`), runtime
   park at `dispatcher.py:1864-1883`, cost gate fail-closed on
   unobservable-in-autonomous (`_dispatcher_cost.py:211`), no
   `dispatcher.autonomous_mode` key in code (only the cost-label
   constant), `loop` carries `--mode` at `dispatcher.py:2594` while
   `bin/drive.py` exposes `--repo`/`--action` and no `--mode`); all
   ledger statuses exact (`rt4` feature backlog + stale v013 pointer,
   `pke3y3` epic backlog, `ipi` task backlog, `mb64bv` chore active with
   gate `iblkzp` closed, the six impl-dispatch items all closed,
   `bd-ib-82a` feature backlog no-deps + stale v025 pointer, open bugs
   `bd-ib-18r`/`bd-ib-6vu`, core `livespec-nrdk` epic + `livespec-0jxs`
   task both backlog, `livespec-35s3zo` closed epic + `livespec-zs22.6`
   closed task, and NO autonomous-mode epic among core's 8 open epics);
   "backlog-bounce" absent from live orchestrator spec+code with journal
   field `bounced_to_regroom` real; the fabro-token-refresh
   validated-live-not-landed state per that thread's handoff; and every
   cited PR merged (round 1 #395/#134/#1000, round 2 #1014/#141/#404,
   plus console #136).

## Loop consequence

FIXES LANDED → round 4 runs next, with ANOTHER fresh Fable session (this
session cannot clear the gate on its own fixes). The handoff's Loop state
and Next actions are updated accordingly in the same PR as this record.
