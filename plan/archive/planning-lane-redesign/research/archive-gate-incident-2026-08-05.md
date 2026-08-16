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

**CORRECTED 2026-08-06 — the claim below was wrong; kept struck-through-in-
spirit rather than deleted, since the correction is itself evidence.**
~~There is no mechanical verifier for this anywhere in the fleet's shared
tooling — checked `livespec-dev-tooling` and `livespec-orchestrator-beads-fabro`
directly, zero hits for anything resembling an archive-on-close check.~~ That
grep searched for the wrong substrings (`archive.on.epic.close` /
`epic_close` / `archive_on_epic`). A real check family exists in
`livespec-dev-tooling`: `plan_thread_anchor_declared` (static) and
`plan_thread_epic_parity` (ledger-aware, credential/lever-gated). The
latter's own remediation text, verbatim, on an active thread pointing at a
closed epic: *"the plan thread is complete — archive it."* That is this same
conflation, found baked into shipped code — deliberately designed (epic
`livespec-dev-tooling-scsj5e`, closed 2026-07-18), motivated by a real prior
incident with the opposite ground truth (a genuinely-complete epic that sat
un-archived).

Two things survive the correction: (1) that check is unarmed everywhere in
the fleet today (zero `LIVESPEC_RUN_PLAN_EPIC_PARITY` references in any
`.github/workflows/` checked; `livespec-dev-tooling-d1j`, "establish a
standing armed home," is still `backlog`); (2) even fully armed, it would
not have caught THIS incident — its assertion direction is "active thread +
closed epic → fail," but by the time this mistake existed on disk the thread
itself had already moved to `plan/archive/`, structurally outside that
check's glob (a distinct defect, `livespec-dev-tooling-q3emww`, found
independently the same day by a different thread). Catching this incident's
specific shape needed a third check — descendant completion, not anchor
status — filed as `livespec-dev-tooling-5asgvm`.

So: despite `SPECIFICATION/contracts.md` naming this as "always-on
enforcement... realized by the Conformance Pattern," in practice it is STILL
enforced by nothing but an LLM reading prose correctly — not because no
check was ever built, but because the check that was built is unarmed, and
even armed, points the wrong direction for this incident's specific failure
mode. The practical conclusion is unchanged; the reasoning under it was
sloppier than it should have been. Full detail:
`livespec-orchestrator-beads-fabro` PR #1317.

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
