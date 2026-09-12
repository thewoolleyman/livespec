# Spec-tree path manifest + normative-clause citation contract (Track 1 of the pre-foreman livespec hardening program)

Recorded 2026-08-24 by the `livespec-grooming` drain pass, from the seed sent by
`homelab-rewrite` (the coordinating session of the cross-repo
`pre-foreman-livespec-hardening` program, whose plan lives in the
`mi-homelab/homelab` repo at `plan/pre-foreman-livespec-hardening/`). This
repository — `thewoolleyman/livespec`, livespec CORE — holds Track 1. The
program is serial: the orchestrator track (Gates 1, 2-consumption, 3 in
`livespec-orchestrator-beads-fabro`) cannot open until this track's gates have
their exit proofs demonstrated in homelab with negative controls.

## Read-first chain

1. `mi-homelab/homelab`: `plan/pre-foreman-livespec-hardening/research/001-findings-and-gates.md`
   §F6 (spec tree has no closed structural definition), §F7 (executable checks
   do not belong inside the spec tree), §"Gate 0", §"Gate 2". A local clone is
   at `/data/projects/homelab`.
2. `mi-homelab/homelab`: `research/003-reasoning-and-rejected-alternatives.md`
   §6 (open questions — item 3 is the scenarios.md / citation-contract overlap),
   and `research/004-single-track-execution-order.md` (why core goes first).
3. This repo: `SPECIFICATION/spec.md` §"Template manifest" (the `spec_files`
   manifest, its lifecycle participation, and the "Alternate diagram tools"
   clause), `SPECIFICATION/contracts.md` §"Template manifest wire contract",
   and `.claude-plugin/scripts/livespec/doctor/static/template_files_present.py`
   (the check that today computes a MISSING list only).
4. This repo: `SPECIFICATION/contracts.md` — the two existing clauses of the form
   "Drift is caught by `dev-tooling/checks/schema_dataclass_pairing.py`", which
   are the in-production precedent for the citation contract.

## The two gates this thread carries

### Gate 0 — an unmanifested path under the spec root is a doctor FAILURE

Finding F6 (measured, with control): a `SPECIFICATION/checks/` directory was
created inside homelab's spec tree by a factory bot; it is in no template, no
ratified clause references it, and homelab's full 21-check static doctor run
PASSED `template-files-present` with it present. The snapshot mechanism then
copied it into `history/v004/`, so an unratified artifact now sits in an
immutable ratified snapshot. Ratification governs file CONTENTS with rigour and
tree SHAPE not at all. This is the only gate that would have prevented the
originating event.

Change: the set of paths permitted under a spec root becomes ratified content
(the `spec_files` manifest already exists and the spec already names it "the
source of truth"; nothing re-validates the tree against it after seed). A path
present under the spec root and absent from the manifest becomes a doctor
`fail` naming that path.

Design wrinkle this repo must resolve in the proposal (found at grooming, not in
the seed): `spec.md` §"Template manifest" → "Alternate diagram tools" today
DELIBERATELY permits a committed image (e.g. `diagrams/foo.svg`) that the
manifest does not declare, relying on the whole-tree snapshot to carry it. A
naive "every path must be manifested" rule contradicts that ratified clause.
The proposal has to reconcile the two — for example a non-markdown manifest
`kind` for opaque assets, or an explicit permitted-path declaration — so the
alternate-diagram clause stays true or is amended in the same revise. The
`history/`, `proposed_changes/`, and `templates/` siblings are already
lifecycle-owned and are not "unmanifested".

### Gate 2-concept — a normative clause names its executable evidence (citation contract)

Finding F7 with F1 (measured, with control): the orchestrator's
`detect-impl-gaps` never reads the implementation; four rules measured as
honored in homelab are still reported as gaps, so "is this implemented?" is a
per-clause human judgement whose failure mode at 44 open clauses is bulk
consent.

Change: a citation contract in livespec core. A normative clause (MUST/SHOULD)
names, by path, the executable check on the IMPLEMENTATION side that settles
it. A clause with no such citation is NOT BINDING and may not be cited as
authorization to build. Core already practises this on itself (the "Drift is
caught by `dev-tooling/checks/…`" clauses); the gate generalizes it.

PRIMARY CONSTRAINT — generic, never local: this MUST land as a citation
contract and MUST NOT land as a `SPECIFICATION/checks/` directory added to any
template. Three measured reasons: phantom gaps (the detector iterates every
`.md` under the spec root, so a negative-control fixture manufactures a
requirement), code versioned at prose cadence (a script frozen in
`history/vNNN/`), and a forced carve-out in an edit guard. The clean split:
`scenarios.md` holds the evidence that settles a clause declaratively; the
implementation side holds the executable check and its controls; the clause
cites the check's path. Anyone starting a checks directory in this repo is the
first drift signal the program watches for — stop and tell `homelab-rewrite`.

Open design question this repo decides (homelab research/003 §6): how the
citation is expressed (inline clause text vs a sidecar) and how "binding" is
surfaced (doctor finding, detector field, or both). Grooming's recommendation,
recorded for the proposal author and NOT a decision: inline, adjacent to the
clause, in a fixed machine-parseable form (the existing "Drift is caught by
`<path>`" shape generalized to a stable marker), surfaced in core as a doctor
static finding that classifies every normative clause as binding or
non-binding; a detector field is the orchestrator's consumption (Track 2) and
is out of this thread's scope. Whichever is chosen, the negative control must be
mechanically checkable.

## Exit proofs (each gate needs BOTH legs; a probe with no control is a claim)

- Gate 0 positive: a ratified tree whose paths all appear in the manifest passes
  doctor. Gate 0 negative control: an unmanifested path introduced in a scratch
  branch makes doctor FAIL naming that path.
- Gate 2 positive: a clause citing a check outside the spec tree is recognized
  as binding. Gate 2 negative control: a clause lacking a citation is REFUSED
  as binding (not silently treated as binding).

## Finish line

Each gate goes through THIS repo's propose-change → revise → ratification-review
lifecycle, is implemented (Red→Green), merged, and RELEASED on the channel
homelab pins (homelab consumes the plugin cache at `f92bf5948e74`, which is
release v0.37.1; a `feat:`/`fix:` push cuts the next release). "Merged" is
reported with the release ref. A gate is DONE only when homelab refreshes its
pin and demonstrates the behavior with the negative control. A negative result —
a gate is unfixable as specified or contradicts the ratified spec — is a valid
result to report as a finding, never to work around.

## Explicit deferrals

- Gate 4 (a spec-side WIP cap in revise) belongs to core but depends on Gate 2
  being CONSUMED by the orchestrator before "unsatisfied" is computable. Not in
  this thread; not to be filed without asking `homelab-rewrite` first.
- Gates 1, 2-consumption, and 3 belong to `livespec-orchestrator-beads-fabro`
  (Track 2). Not filed here.
- No broader redesign of the template manifest, the doctor static suite, or the
  gap detector: file what the seed carries; new scope goes back to
  `homelab-rewrite` as a question.

## Reply contract with the coordinator

Reply to `homelab-rewrite` with: this plan slug, the ledger epic id in the
`livespec` tenant, the work items filed (ids, titles), and BOTH async queues
left draining (session starts behind the foreman tick; dispatches behind the
credential pool and factory queue).
