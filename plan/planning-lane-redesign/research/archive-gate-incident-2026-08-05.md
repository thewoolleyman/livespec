# Incident, 2026-08-05: current archive-on-epic-close text let a live plan archive

Concrete, first-hand evidence for the "Two-leg archive gate" accepted
recommendation (`maintainer-rulings.md` §Accepted recommendations). Filed from
`livespec-overseer`, where the incident happened, into this plan because core
owns the Planning Lane contract (ruling 4).

## What happened

An agent session working `livespec-overseer`'s `plan/supervisor-scratch-discipline/`
groomed the plan's own anchor epic (`overseer-5jttov`) into two replacement
factory slices via the `groom` operation's regroom-out disposition. That
closed the epic (`status: done`, `resolution: no-longer-applicable`) — a
**procedural** closure: the ticket was retired because its content moved to
two new tickets, not because any work shipped.

The session then read the current archive rule literally —

> `livespec-orchestrator-beads-fabro/.claude-plugin/prose/plan.md` Step 5:
> "A plan thread's lifecycle binds to its ledger epic: `plan/<topic>/` is
> active if and only if its epic is open, and archived to
> `plan/archive/<topic>/` if and only if the epic is closed."
>
> `livespec-orchestrator-beads-fabro/SPECIFICATION/contracts.md`, same
> section: "whatever closes the epic also archives the directory."

(Both quoted verbatim from the still-shipping orchestrator prose/spec, hence
the pre-rename "plan thread" wording — not this repo's vocabulary.)

— and archived the plan. The PR merged (repo auto-merge) before the
maintainer caught it. At archive time, **both replacement slices were
`status: ready`, unassigned, undispatched — zero code written, zero PRs
open.** The actual deliverables the plan existed to produce (a charter rule,
an enforcement check) did not exist yet. Corrected same-day in a follow-up PR.

## Why the current text allowed it

Neither cited passage — nor the fleet-wide **Archive-on-epic-close**
Conformance Pattern member in `non-functional-requirements.md` ("a
`plan/<slug>/` record is active if and only if its ledger epic is open, and
the epic itself MAY close only through the archive gate") — distinguishes
*why* the epic closed. A **procedural** closure (grooming splits an epic's
content into new tickets) and a **completion** closure (the work shipped) are
both just "closed" to this rule. The mechanism gap is specific: `groom`'s
regroom-out disposition can close a work-item that is *also* a plan's own
anchor epic, and nothing anywhere flags that combination or checks whether
the epic's replacements are themselves done.

**There is no mechanical verifier for this anywhere in the fleet's shared
tooling** — checked `livespec-dev-tooling` and
`livespec-orchestrator-beads-fabro` directly, zero hits for anything
resembling an archive-on-close check. Despite being named as "always-on
enforcement... realized by the Conformance Pattern," today it is enforced by
nothing but an LLM reading prose correctly, and this incident is the proof
that fails.

## What this validates, concretely

The "Two-leg archive gate" recommendation's mechanical leg — "no undisposed
children" — would have caught this exact case *by construction*: both
replacement slices were open (`ready`) descendants of the closing epic at the
moment of archival. This incident is a real trigger case for that leg, not a
hypothetical one, and it sharpens the leg's requirement: the check must fire
regardless of *why* the epic closed (completion, regroom-out, or any other
resolution), because the archived-vs-not decision has to be about the state
of the WORK, never about the state of one ledger status field.

## Not decided here

This note adds evidence; it does not re-scope or re-rule anything the
maintainer has already decided. Whether/when `livespec-orchestrator-beads-fabro`
gets a tactical stopgap fix ahead of this redesign shipping is a separate,
open question the maintainer is tracking outside this plan.
