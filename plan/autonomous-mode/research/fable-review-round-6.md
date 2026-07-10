# Fable fresh-review round 6 — autonomous-mode MVP plans

**Reviewer:** a FRESH Fable-model session (no prior involvement in authoring
or revising these plans; spawned by the driver session with
`research/fable-review-brief.md` and ran it end-to-end). **Date:** 2026-07-10.

Scope: all three plans at `origin/master` as revised by rounds 1-5 —
`livespec/plan/autonomous-mode/{handoff,design}.md`,
`livespec-console-beads-fabro/plan/autonomous-mode/{handoff,design}.md`,
`livespec-orchestrator-beads-fabro/plan/autonomous-mode/{handoff,design}.md`.
Every load-bearing claim independently verified against live state BEFORE
reading any prior round: the spec trees via `git show origin/master:<path>`,
the crate/script sources, all three Beads tenants (`bd show … --json` via
the credential wrapper, from inside each repo), and master CI (`gh run list
--workflow CI`). The round was purely read-only: no defect warranting a fix
was found, so NO PR was landed and NO worktree/branch was created.

## Round 6 fresh review: NOTHING-BLOCKING

The convergence trajectory (round 1 = 9 observations + 4 corrections;
round 2 = 6 fixes; round 3 = 2; round 4 = 2; round 5 = 1) reaches ZERO
this round. The reviewer found no genuine defect and did not manufacture
one to avoid certifying.

### Per-plan
- **livespec (overall):** SOLID — acyclic dependency graph agreeing with
  its own prose and both siblings; the round-4-added `O1/I1 ─► C3 (and
  C1's persistence-seam portion)` edge is present; every step has
  owner/gate/checkable "done"; Loop state current. No fix needed.
- **console operator surface (`livespec-console-beads-fabro`):** SOLID —
  spec v016, zero real pending proposals; both C1 citation drifts still
  present as planned (`contracts.md:395` "orchestrate run", `:490`
  "owned by livespec core"); `CommandType` = `FactoryDrainRequested`
  only, zero `autonomous` hits, `AcceptancePolicy` = `AiThenHuman` only;
  `rt4` still cites v013. Fourth consecutive clean round. No fix needed.
- **orchestrator engine (`livespec-orchestrator-beads-fabro`):** SOLID —
  spec v032, zero real pending proposals; no `dispatcher.autonomous_mode`
  key in code (only the cost-label constant); the O1 collapse-hazard is
  verbatim real (`contracts.md:1345` auto-approves "even items whose
  stored `admission_policy` is `manual`" vs `:781` under §"Dispatcher
  grooming behavior" naming `manual` "the first-class realization of the
  prior `human-gated` spec-change marker"); Scenario 36's `human-only`
  carve-out present; five valve action-ids ship in `commands/drive.py`;
  `bd-ib-82a` still cites v025. Third consecutive clean round. No fix
  needed.

### Fixed this round
None. No genuine defect found; none manufactured to avoid certifying.

### Non-blocking observations
1. **One slightly-stale line pointer (below fix threshold — NOT fixed).**
   Console `design.md` §2 cites `crates/console-domain/src/lib.rs:310-313`
   for "`CommandType` has only `FactoryDrainRequested`", but `pub enum
   CommandType` is at line 290 (:310-313 is the tail of the impl block).
   The claim is TRUE, the citation is explicitly hedged "(file:line from
   the survey)", the region is CommandType code, and rounds 4-5 both
   passed console clean without flagging it. Fixing a survey-snapshot
   line number that re-drifts on the next edit is manufactured churn;
   reported for transparency, not a blocker.
2. **Carried from prior rounds, no change needed:** console
   `plan/impl-dispatch/` remains unarchived (separate housekeeping); the
   `livespec-orchestrator-beads-fabro/plan/fabro-token-refresh/` thread's
   OWN handoff still lists the moot "PR #136 cleanup" question (out of
   this loop's scope; console PR #136 is merged).
3. **Repo states:** core (`livespec`) clean on master, up to date with
   origin (read-only round, no PR). Console left exactly as found — on
   master, clean, behind origin by 3 (fetch+read only). Orchestrator left
   exactly as found — behind origin by 1 with the pre-existing
   maintainer-owned dirty `orchestrator-image/real-work-dispatch.sh` and
   untracked `plan/fabro-token-refresh/design-notes.md` untouched.

### Currency findings
Every state claim re-verified TRUE today, first-hand:
- **Specs/proposals:** console v016, orchestrator v032; both zero real
  pending proposals (console `proposed_changes/` = README only;
  orchestrator = `.gitkeep` only).
- **Ledger (via each repo's credential wrapper):** core `livespec-bvuy4w`
  (epic/backlog; `livespec-nrdk` [epic] `blocks`, `livespec-0jxs` [task]
  `related` — exact edge shapes), `livespec-nrdk` (epic/backlog),
  `livespec-0jxs` (task/backlog); console `rt4` (feature/backlog/v013),
  `pke3y3` (epic/backlog), `ipi` (task/backlog), `mb64bv` (chore/active);
  orchestrator `bd-ib-82a` (feature/backlog/no deps/v025), `bd-ib-18r` +
  `bd-ib-6vu` (bugs/backlog).
- **PRs (all `thewoolleyman/livespec`, all MERGED):** #1020 (epic anchor
  filed), #1022 (round-4 fixes), #1023 (round-4 record), #1024 (round-5
  fix), #1026 (round-5 record); console
  `livespec-console-beads-fabro` PR #136 merged. The handoff Loop state
  (round-4 bullet cites #1023; round-5 bullet cites #1024 + #1026) is
  accurate.
- **Code/spec anchors:** core `spec.md:387` drift-acceptance normative
  quote verbatim; orchestrator `bin/drive.py` published surface exists
  and "orchestrate run" absent from its live contracts;
  `dispatcher.autonomous_mode` absent from orchestrator code (only
  `_dispatcher_cost.py:109` cost label); shipped `attention_item.py`
  fields (id, kind, urgency, summary, source_ref, handoff) match;
  `drive.py` acceptance enum `{ai-only, human-only, ai-then-human}` and
  reject modes `{rework, regroom}` match §6.3(b).

## Affirmative certification (NOTHING-BLOCKING → for the maintainer)

- **SOLID.** Every step (Step 0, C1, C2, C3, O1, O2, I1, I2) has an
  owner, a gate, and a checkable "done"; the dependency graph is acyclic
  and self-consistent (`Step0→C1→C2→C3→I2`; `Step0→O1→O2→I2`; `O1/I1→C3
  and C1's persistence-seam portion`), with the two-phase C1 (main
  ratification unblocks C2; the I1-gated persistence amendment unblocks
  C3) coherent and non-circular; the three seam pins (single persistent
  permission key = the orchestrator's `dispatcher.autonomous_mode`;
  engine-owns-all-gate-resolution + the Scenario-10 re-scope; the two
  vocabulary fixes) are consistent with BOTH live specs; the O1 REQUIRED
  propose-change rests on a verbatim-real `:1345`-vs-`:781` spec tension,
  not an inference.
- **EXECUTABLE.** Every factual precondition an implementer relies on is
  true today: the spec versions, the zero-pending-proposal state, the
  code absences C2/C3/O2 fill (`CommandType`, `AcceptancePolicy`,
  `dispatcher.autonomous_mode`), the stale pointers C1/O1 refresh (`rt4`
  v013, `bd-ib-82a` v025), the `drive.py` action surface C2 wires to,
  and the `attention_item` schema C3 consumes are all verified present;
  and each plan names the required disciplines (worktree → PR → merge,
  `mise exec -- git`, never `--no-verify`, Red-Green-Replay for the
  Rust/Python product code, `tests/heading-coverage.json` co-edits for
  H2 changes, independent Fable review before every ratification).
- **MVP-MEETING.** Executing the steps in order produces exactly the
  §1/§10 MVP — TUI toggle → unattended factory drives ready work to
  `done` → every auto-resolution audited and reflected →
  truly-unresolvable decisions surface in-TUI as needs-attention — and
  I2's gate (verified cost ceiling + a real failure-surfacing path via
  `livespec-0jxs`, with the `bd-ib-18r` ledger-write-back caveat carried
  so the truly-unresolvable plant is ledger-level) ensures the
  escalation leg genuinely surfaces; the irreducible human touchpoints
  (drift acceptance, spec-change slices, regroom/backlog-bounce) are
  protected by design through O1's touchpoints propose-change, not left
  to LLM confidence.

## Loop consequence

NOTHING-BLOCKING → per the loop's double gate, this verdict exits the
fable-review phase ONLY once the MAINTAINER records certification in
this handoff's Loop state. The round-6 session landed no fixes (so the
no-self-certification rule is satisfied: the verdict comes from a fresh
session with nothing of its own to certify), and C1/O1 dispatch remains
hard-gated until the maintainer's certification lands.
