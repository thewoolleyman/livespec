# Handoff: Formalize the livespec blessed workflow (epic livespec-zs22)

**Track:** planning-lane · **Epic:** `livespec-zs22` · **Tenant:** livespec

This is the resumable runbook for the Planning Lane + Conformance Pattern
formalization. It carries *instructions*; the *rationale* lives in
`research/planning-workflow-gap/planning-lane-design.md`, and the
*authoritative status* lives in the ledger — never in this file.

## FIRST ACTION — print live status (do not trust this file for status)

```
/data/projects/1password-env-wrapper/with-livespec-env.sh bd show livespec-zs22
```

Derive every "what's done / what's next" answer from that, plus
`bd ready` and `git log`. This file lists the *plan*, not the *state*.

## Read first

1. `research/planning-workflow-gap/planning-lane-design.md` — the design,
   the three planes, the locked decisions, the increment sequence, and the
   three FINAL diagrams (§"Architecture diagrams") ready to land in the spec.
2. `research/factory-conformance/cross-repo-conformance-pattern.md` — the
   companion Conformance Pattern (files its milestones through this lane).
3. `research/planning-workflow-gap/missing-planning-workflow-thread.md` —
   the original gap note.

## Objective

Re-adopt livespec's own deferred planning design as a codified, disciplined
convention, place each piece on the plane that owns it (Spec /
Orchestrator / Control), and mechanically enforce the no-shadow-ledger
rule — then build the Conformance Pattern on top of it. Locked decisions
(see the design doc): handoff skill **orchestrator-side**; **`baseline`**
profile (not "factory"); **`just` mandated non-functionally only** (never
in core's public functional surface); fleet pins track **latest RELEASE**
not HEAD; the **console** is the Control-Plane runner.

## Status (refreshed 2026-06-25, post-increment-1)

Increment 0 and the design refinements have landed (PRs #568, #572);
`livespec-zs22.1` is closed. **Increment 1 (`livespec-zs22.2`) has
landed** (PR #575, merge `54f8763`): the `## Workflow planes and the
Planning Lane` framing section plus the planes and skills diagrams are in
`SPECIFICATION/spec.md`, the canonical architecture diagram now carries
the Control Plane + the `plan/<topic>/` store (cut `v137` via the
governed propose-change → revise lifecycle), the field-comparison
section is in the repo `README`, and the diagram authoring conventions
are in `AGENTS.md` (closing `livespec-1bvl`). The epic is 2/3 children
complete. Increments 2-5 are drafted in the design doc §"Increment
sequence" and filed as ledger children as each ripens (the maintainer
owns the cut: draft, get approval, then file). `livespec-zs22.3`
(plan-skill self-sufficiency check) is also open and ready.

## Next concrete action

Increment 2 — a `livespec-zs22` child not yet filed; the maintainer owns
the cut. Land the **Planning Lane → core `non-functional-requirements.md`
guidance** via `/livespec:propose-change` then `/livespec:revise`: the
three-lane separation, the two seams, the no-shadow-ledger invariant, and
the openbrain discipline (design doc §"Increment sequence" item 2 +
§"The Planning Lane"). The *pattern* only; no command in core's
functional surface, and `just` never leaks into core's functional spec.
Draft the cut from the design doc, get maintainer approval, file the
child, then execute. (`livespec-zs22.3` — plan-skill self-sufficiency —
is the alternative ready pickup.)

## Constraints / non-negotiables

- **Dogfood the discipline.** All work in a worktree under
  `~/.worktrees/livespec/<branch>`; land via PR → rebase-merge; never
  commit on the primary checkout. `mise exec -- git …`; never
  `--no-verify`; halt and report on any hook failure.
- **No shadow ledger.** This handoff and every artifact point at ledger
  ids for status; they never embed a `[ ]`/`[x]` task queue.
- **Respect the planes.** The handoff/coordination skill is
  orchestrator-side; the reasoning capture is a Spec-Plane convention; the
  console is the Control Plane. `just` never leaks into core's functional
  surface or the `/livespec:*` skills.
- **Increment discipline.** Small, cohesive, independently mergeable,
  nothing breaks. One increment per PR.

## Handoff refresh

If context approaches budget mid-increment: wrap the in-flight increment
to a committed+pushed state, update the ledger (`bd`), print the closing
status table, and refresh this file (same epic id) with the exact
remaining work. End every session by naming the literal next-session
command.

## Archive condition

When `livespec-zs22` closes (all increments landed, the Planning Lane
guidance in core NFR, the Conformance Pattern shipped), `git mv` this file
to `archive/prompts/` with a completion banner. The durable history then
lives in the spec, the spec history, the commits, and the ledger.
