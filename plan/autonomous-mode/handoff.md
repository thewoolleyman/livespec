# Autonomous-mode MVP — overall plan handoff (livespec core)

**Status: FABLE-REVIEW LOOP OPEN — implementation is HARD-GATED.** The loop
(maintainer-declared 2026-07-10): each round, a FRESH Fable session reviews
ALL THREE plans AND FIXES every problem it finds — in-session, in the plan
texts, via worktree → PR → merge. A read-only findings dump is NOT a valid
round output (maintainer-corrected 2026-07-10: "the read-only handoff
instructions were WRONG … FIX ALL THE PROBLEMS WITH ALL THREE OF THE PLANS.
Not just randomly spew some non-actioned text."). The loop exits only on the
double gate: (1) a FRESH session's review finds NOTHING BLOCKING —
affirmatively certifying all three plans SOLID, EXECUTABLE, and MVP-MEETING —
and (2) the MAINTAINER certifies. A session that landed fixes MUST NOT be the
one that clears the gate (no self-certification); the clean verdict always
comes from the NEXT fresh session. C1/O1 dispatch MUST NOT happen before the
gate is met.

**Loop state:**
- Round 1 (2026-07-10, Fable session `livespec-autonomous-mode`): Step-0
  validation of the ORIGINAL plans → NO-BLOCKERS with 9 observations
  (`research/step0-fable-verdict.md`); the SAME session then FIXED every
  finding in all three plans (orchestrator PR #395, console PR #134, core
  PRs #1000 + this one) and wrote
  `research/fable-revising-session-self-assessment.md` — which does NOT
  clear the gate, because reviser and reviewer were the same session.
- Round 2 (2026-07-10, fresh Fable session, this repo's session
  `livespec-autonomous-mode` pane): first fresh-session review-AND-FIX over the
  REVISED plans → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-2.md`; core PR #1014, console PR #141,
  orchestrator PR #404). All round-1 revisions re-verified against live state;
  fixes were currency + internal-soundness precision (stale `orchestrate run`
  in core C2 step text; C2-gate two-phase-C1 ambiguity; fabro-token-refresh
  state moved; mb64bv type; O2 done-surface pin). Because fixes landed, this
  round does NOT clear the gate.
- Round 3 (2026-07-10, fresh Fable session): second fresh-session
  review-AND-FIX → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-3.md`; orchestrator PR #410 + the core PR
  carrying that record). Every rounds-1-2 revision re-verified against live
  state; no structural defect anywhere; the two fixes were small currency/
  precision (stale "PR #136 cleanup" pending-decision in core §9 +
  orchestrator §5 — the validation vehicle auto-merged 2026-07-10;
  `livespec-zs22.6` is a closed task, not an epic). The CONSOLE plan passed
  clean — its first no-fix round. Because fixes landed, this round does NOT
  clear the gate.
- Round 4: NOT YET RUN — the next fresh-session review-AND-FIX round.
  → This is the next action.
- Maintainer certification: NOT YET GIVEN.

**Thread role:** the OVERALL cross-repo plan. Ties together the console operator
surface and the orchestrator decision engine, owns the dependency graph, and
defines the tmux/session delegation model. livespec core authors no product code
here.

## Read first
1. This file, then `design.md` in this directory (the full plan).
2. For the review loop: `research/fable-review-brief.md` (the brief each
   fresh reviewer runs), then the prior rounds
   (`research/step0-fable-verdict.md`,
   `research/fable-revising-session-self-assessment.md`,
   `research/fable-review-round-N.md` as they accumulate).
3. The two sibling repo plans this coordinates (both carry the accumulated
   review-round findings in their own step texts, kept current across the
   review-loop rounds):
   - `livespec-console-beads-fabro/plan/autonomous-mode/design.md`
   - `livespec-orchestrator-beads-fabro/plan/autonomous-mode/design.md`

## Goal (one line)
A human flips per-repo **full autonomous mode** from the
`livespec-console-beads-fabro` **TUI** (GUI out of scope) and the Beads/Dolt +
Fabro factory drives ready work to `done` unattended — LLM-resolving the human
gates, auditing every decision, surfacing only the truly-unresolvable back to the
operator.

## The spine (see design.md §7 for the full step catalogue)
```
Step 0 (fable-review LOOP — HARD GATE, exit = fresh-session nothing-blocking + MAINTAINER certification)
  status: rounds 1-3 done (each landed fixes); round 4 fresh review-and-fix PENDING; maintainer certification PENDING
  ├─ Console track (session console-autonomous-mode):  C1 spec fixes ─► C2 command foundation ─► C3 autonomous feature
  └─ Orchestrator track (session orchestrator-autonomous-mode): O1 spec fixes + publish arming contract ─► O2 build engine (bd-ib-82a)
                          O1 arming contract (I1) ─► C3 (and C1's persistence-seam portion)
  Integration (driver session autonomous-mode): I2 end-to-end live exercise on a real tenant = MVP "done"
```
Console C2 and orchestrator O1→O2 run in parallel — but ONLY after the Step-0
loop exits. Contract-first: O1 publishes the arming/audit contract before C3
builds on it.

## Next actions (exact steps for a new session)

1. **Run the next review round (per Loop state above — currently round 4)**:
   spawn (or have the maintainer run) a FRESH Fable
   session with `research/fable-review-brief.md`. Fresh = no prior involvement
   in authoring or revising these plans. The session REVIEWS all three plans
   AND FIXES every problem it finds in-session — plan-text changes landed via
   worktree → PR → merge in the affected repo(s). It never emits a
   non-actioned findings dump.
2. **Record the round**: commit the round record — the verdict PLUS what was
   fixed, with PR links — as `research/fable-review-round-N.md` (a
   `docs(plan):` PR) and update this handoff's Loop state. If the session
   nears ~50% context mid-fix, it updates this handoff so the NEXT session
   CONTINUES the same round's fixes where it left off (a continuation, not a
   new round), then stops cleanly.
3. **Branch on the round's outcome**:
   - FIXES LANDED (anything blocking was found) → go to step 1 with round
     N+1 and ANOTHER fresh session. A session that landed fixes never clears
     the gate on its own round (no self-certification).
   - NOTHING-BLOCKING (a round that needed no fixes) → the round verdict must
     affirmatively certify all three plans SOLID, EXECUTABLE, and MVP-MEETING;
     present it to the MAINTAINER for certification. Only the maintainer's
     recorded certification (update the Loop state above) exits the phase.
4. **Only after the gate is met — dispatch O1 and C1 in parallel** to the two
   delegate sessions per the delegation model below. Briefs point each
   delegate at its OWN revised plan (`plan/autonomous-mode/handoff.md` in its
   repo — the review-round findings are baked in; no side-channel content).
   Both briefs MUST forbid `--no-verify`, require worktree → PR → merge, and
   instruct halt-and-report on hook failure.
5. **Gates thereafter:** C2 after C1's MAIN ratification (the I1-gated
   persistence-seam amendment gates C3, not C2 — that keeps C2 concurrent
   with O1→O2); C3 after C1 + C2 + I1; O2 after O1; I2
   after C3 + O2 AND the design.md §9 operability conditions (verified cost
   ceiling + a real failure-surfacing path — note orchestrator bug `bd-ib-18r`:
   an in-loop park today orphans without ledger write-back, so I2's
   truly-unresolvable plant must be ledger-level or `bd-ib-18r` triaged first).
6. Every spec change in either repo routes propose-change → independent Fable
   review → revise, co-editing `tests/heading-coverage.json` for any H2 change.

## Delegation model (design.md §8)
- Driver: Claude session `autonomous-mode` in tmux pane `livespec-autonomous-mode` (cwd `/data/projects/livespec`).
- Delegate: session/pane `console-autonomous-mode` (cwd console repo) → C1/C2/C3.
- Delegate: session/pane `orchestrator-autonomous-mode` (cwd orchestrator repo) → O1/O2.
- Reviewer: a FRESH Fable session per round (any pane; review-AND-FIX — it
  lands its own fixes; no continuity with sessions whose fixes it reviews).

## Ledger items in play (per repo tenant)
- Core: `livespec-bvuy4w` — this thread's epic anchor (driver filed it
  2026-07-10 via the `capture-work-item` operation, closing the round-2
  finding; epic-shaped → `backlog` per the intake Definition-of-Ready
  checklist; edges: `livespec-nrdk` blocks, `livespec-0jxs` related — bd
  refuses an epic→task `blocks` edge by design, so the task dependency
  carries a `related` edge instead).
- Console: `rt4` (operator surface; epic-shaped feature, stale v013 pointer), `pke3y3` (epic, "7 unimplemented commands" — regroom + split per its plan), `ipi` (attention-stream TUI migration), `mb64bv` (chore: backlog-bounce vocab rename — verify the rename target against the orchestrator's actual journal field `bounced_to_regroom` before landing).
- Orchestrator: `bd-ib-82a` (the engine; stale v025 pointer).
- Core deps TRACKED not re-owned: `livespec-nrdk` (factory-safe admission gate), `livespec-0jxs` (operability preconditions); orchestrator `plan/fabro-token-refresh` (long-run publish robustness); orchestrator bugs `bd-ib-18r` / `bd-ib-6vu` (unattended-run robustness — sequence around).

## Key cross-repo risks (design.md §6) — round-1 disposition
1. Persistence-model seam: RESOLVABLE as planned; O1 must additionally pin the
   orchestrator's own config key, the launcher identity, and the
   `drive`-vs-`loop` mode placement (round-1 verdict obs. 2).
2. Division of resolution: RESOLVABLE via the engine-owns-all-gate-resolution
   reading; C1 ratifies the console Scenario-10 re-scope (round-1 verdict obs. 3).
3. Vocab drift: lanes/enums verified clean; two drift instances fixed into C1's
   scope (`orchestrate run` → `drive`; lane-ownership attribution) (obs. 4).

## Next action
Run review round 4 (Next actions, step 1). Nothing dispatches to
implementation until the Step-0 loop exits with maintainer certification.

## Pointers
- Ledger read (per tenant): `bd list --json` (or `bd show <id> --json`) run from
  inside the repo, via the credential wrapper
  `/usr/local/bin/with-livespec-env.sh -- bd …`; prefer it over the shared
  `list_work_items.py` cache path, which can mis-resolve the tenant.
- Repo mutation: worktree → PR → merge → cleanup; `mise exec -- git …`; never `--no-verify`; plan docs are `docs(plan):` commits.
