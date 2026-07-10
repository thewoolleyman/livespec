# Fable revising-session SELF-ASSESSMENT — autonomous-mode MVP plans

> **THIS IS NOT THE PHASE-EXIT GATE.** This document was originally written
> as a "certification" by the SAME Fable session that revised the plans —
> a self-certification the maintainer rejected (2026-07-10). It is retained
> as the revising session's self-assessment and as input to the fresh
> reviews. The fable-review phase exits ONLY when a FRESH Fable session
> (per `fable-review-brief.md`) finds nothing blocking AND the MAINTAINER
> certifies; the loop state lives in `plan/autonomous-mode/handoff.md`.

**Author:** Fable-model session `livespec-autonomous-mode` (the session that
performed the Step-0 validation AND the fable-revise fixes).
**Date:** 2026-07-10.

## Basis

1. **Step-0 adversarial validation** of all three plans against the live spec
   trees, the crate/script sources on `origin/master`, the three Beads
   tenants, and master CI — every factual claim verified, all three
   integration seams stress-tested, goal-reachability judged end-to-end.
   Verdict: `step0-fable-verdict.md` (this directory) — **NO-BLOCKERS** on all
   three plans, with 9 non-blocking observations and 4 currency corrections.
2. **Fable-revise pass**: every observation and correction was then FIXED
   directly in the plan texts by the same full-context Fable session
   (maintainer-directed, superseding the review's original read-only
   constraint):
   - repo `thewoolleyman/livespec-orchestrator-beads-fabro` — PR #395
     (merged 2026-07-10): O1's touchpoints propose-change upgraded to
     REQUIRED with its three deliverables; the arming contract's three pins;
     attribution correction; the `bd-ib-18r` I2-plant consequence.
   - repo `thewoolleyman/livespec-console-beads-fabro` — PR #134
     (merged 2026-07-10): C1
     re-scoped to execute the verified findings (two citation-drift fixes,
     the Scenario-10 re-scope, persistence-seam portion gated on I1); C2
     `drive`-surface targeting, `pke3y3` split-not-narrow, `AcceptancePolicy`
     read-enum note; `mb64bv` journal-vocab caution.
   - repo `thewoolleyman/livespec` — this PR: §4 attribution correction,
     §6.1–6.3 seam resolutions/results, §7 step-text mirrors, plus this
     certification.

## Self-assessment (a fresh reviewer must independently re-verify all of this)

Having authored and re-verified the revisions against the validation
findings, I assess that the three autonomous-mode plans, as revised at the
commits named above, are:

- **SOLID** — internally consistent, dependency-correct (Step 0 → C1 → C2 →
  C3 → I2; Step 0 → O1 → O2 → I2; I1 → C3 and → C1's persistence-seam
  portion; no circular or missing edge), and seam-reconciled: each of the
  three integration seams now carries a pinned resolution path with the
  responsible step named, and no plan step rests on an unverified premise —
  every factual premise was checked against the real files, ledgers, and CI
  on 2026-07-10.
- **EXECUTABLE** — every step has an owner session, an explicit gate, and a
  checkable "done"; the disciplines (worktree → PR → merge, `mise exec --
  git`, never `--no-verify`, Red-Green-Replay for product code,
  `tests/heading-coverage.json` co-edits, independent Fable review before
  every ratification) are named in each plan; the delegate plans are
  self-sufficient (the Step-0 findings are baked into their own step texts,
  not held in a side channel).
- **WILL MEET THE MVP** — executing the steps in order produces the goal (a
  human flips per-repo full autonomous mode from the
  `livespec-console-beads-fabro` TUI; the factory drives ready work to `done`
  unattended with every auto-resolution audited; only the truly-unresolvable
  — including the three irreducible human touchpoints — surfaces back
  in-TUI) and passes the I2 live exercise under its expanded gate (cost
  ceiling + a real failure-surfacing path, with the `bd-ib-18r` ledger-level
  plant constraint).

## Scope limits (stated so the self-assessment stays honest)

- This assessment covers the PLANS as revised, not the future spec revisions or
  code they call for: the C1/O1 proposed changes still each require their own
  independent Fable review at ratification (standing rule, 2026-07-04), and
  O2/C2/C3 still gate on `just check`, review, and live evidence as the plans
  state.
- It assumes the upstream specs do not move materially before C1/O1 execute;
  both steps re-confirm currency if the 2026-07-10 baseline has moved.
