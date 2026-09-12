# Citation contract — a normative clause names its executable evidence

Revived 2026-09-12 (maintainer direction) as a standalone livespec-core plan
from the **deferred Gate 2-concept** of the now-archived cross-repo program
`pre-foreman-livespec-hardening` (coordinated from `mi-homelab/homelab`,
archived at `homelab/plan/archive/pre-foreman-livespec-hardening/`). The
maintainer deferred this concept *out of* that program on 2026-08-24; it is not
tied to the archived program and carries no homelab dependency. It is held here
as future work under livespec CORE's own ownership, PARKED until the maintainer
decides whether and when it lands.

The sibling Gate 0 (spec-tree path closure) is DONE — ratified
(`SPECIFICATION/history/v215/`), implemented (`doctor-spec-tree-manifested`),
released as `livespec` v0.38.0, and consumed with a negative control by
homelab — and its plan `spec-tree-manifest-and-clause-citation` (epic
`livespec-r6siae`) was archived when this plan was opened. The two work items
below were reparented here from that archived plan on 2026-09-12.

## The concept

A normative clause (MUST/SHOULD) in a spec **names, by path, the executable
check on the implementation side that settles it**. A clause with no such
citation is **NOT BINDING** and may not be cited as authorization to build.
livespec core already practises exactly this on itself — the
`SPECIFICATION/contracts.md` clauses of the form "Drift is caught by
`dev-tooling/checks/<name>.py`" — so the gate *generalizes an existing,
in-production core precedent* rather than inventing a new mechanism.

## Why it was deferred, not abandoned

Per the homelab re-scope record (`homelab/plan/archive/pre-foreman-livespec-hardening/research/006-rescope-gate-0-only-orchestrator-next.md` §2):
Gate 2 was found to be **an enhancement, not an unblocker**. The two claims that
had put it on the critical path did not hold — the homelab checks moved to a
repo-root `checks/` with prose path citations (what core already does), and the
orchestrator's gap-tied closure (Gate 3) records the check path *on the work
item*, which the orchestrator owns. So nothing was blocked on Gate 2. What it
adds is making "binding" **machine-knowable**, which is useful for a future
spec-side WIP cap (the also-deferred "Gate 4") and for any consumer that wants
to distinguish enforced clauses from aspirational ones.

## Revived work items (reparented from `livespec-r6siae`, 2026-09-12)

- **`livespec-jid5i6`** — Gate 2-concept spec: ratify the citation contract
  through this repo's propose-change → ratification-review → revise lifecycle.
  (host-route / `factory-safety:needs-host-secrets`; the spec lifecycle is
  driven in a plan session, not by the factory.) It blocks the impl item below.
- **`livespec-cmhw5z`** — Gate 2-concept impl: a mechanical binding
  classification — a clause citing an implementation-side check path is
  classified binding; an uncited MUST/SHOULD clause is refused as binding, never
  silently treated as binding. Blocked by `livespec-jid5i6` until it ratifies.

## Open design questions this repo owns (from homelab archived research/003 §6)

1. **How the citation is expressed** — inline in the clause text in a fixed
   machine-parseable form (grooming's non-binding recommendation: generalize the
   existing "Drift is caught by `<path>`" shape into a stable marker) vs. a
   sidecar file.
2. **How binding-ness is surfaced in core** — a doctor static finding that
   classifies every normative clause (grooming's recommendation), a detector
   field (that is the orchestrator's Track-2 consumption, out of core scope), or
   both.
3. **The `scenarios.md` overlap** — how declarative evidence in `scenarios.md`
   relates to the executable check the clause cites. The clean split: evidence
   declared in `scenarios.md`; the executable check and its controls live on the
   implementation side; the clause cites the check's path.
4. **Core's own uncited MUST/SHOULD clauses** — a migration posture (e.g.
   non-binding-until-cited) with core's own tree as the first consumer.

## Primary constraint (generic, never local)

This MUST land as a **citation contract** and MUST NOT land as a
`SPECIFICATION/checks/` directory added to any template or spec tree. The three
measured reasons: phantom gaps (a negative-control fixture under the spec root
manufactures a requirement the detector then reports), code versioned at prose
cadence (a script frozen inside `history/vNNN/`), and a forced carve-out in an
edit guard. Anyone who finds themselves creating a checks directory under a spec
root has taken the wrong path — stop.

## Exit proofs (each leg needs its negative control)

- **Positive:** a clause citing a real implementation-side check is recognized
  as binding.
- **Negative control:** a MUST/SHOULD clause lacking a citation is REFUSED as
  binding — not silently treated as binding. A dangling citation (a cited path
  that does not resolve) is a distinct reported failure, not silent binding.

## Status and next action

**PARKED.** `next_action = human`. No work is admissible until the maintainer
decides whether and when the citation contract lands. When revived: Gate 2 spec
(`livespec-jid5i6`) is driven through this repo's spec lifecycle first; the impl
(`livespec-cmhw5z`) becomes admissible only after ratification.

## Read-first chain

1. This note.
2. `homelab/plan/archive/pre-foreman-livespec-hardening/research/006-rescope-gate-0-only-orchestrator-next.md`
   §2–§3 (the deferral record and re-scoped tracks) — local clone at
   `/data/projects/homelab`.
3. `homelab/plan/archive/pre-foreman-livespec-hardening/research/001-findings-and-gates.md`
   §"Gate 2" / §F7, and `research/003-reasoning-and-rejected-alternatives.md`
   §citation-contract and §6 (open questions).
4. This repo: `SPECIFICATION/contracts.md` — the existing "Drift is caught by
   `dev-tooling/checks/…`" clauses (the in-production precedent to generalize).
5. Ledger items `livespec-jid5i6` (spec) and `livespec-cmhw5z` (impl) in the
   `livespec` beads tenant.
