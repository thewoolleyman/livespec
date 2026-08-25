# homelab-loop-hardening-core — initial research (seeding charge)

Opened 2026-08-25 by the `homelab-loop-hardening-core` session in
`thewoolleyman/livespec`, executing the homelab maintainer's ruling on
`homelab/hl-nkuzaz` handoff 12 (2026-08-25, homelab-initiates model):
homelab seeds one upstream plan per owning repository; this is the
livespec-core plan. The seed request came from the homelab
`steady-state-loop-hardening` session after the maintainer triaged this
repository's two commissioned adversarial reviews (homelab PR #1029) in
homelab research/008.

## Read-first chain

All in `mi-homelab/homelab` on `main`:

1. Charge and triage:
   <https://github.com/mi-homelab/homelab/blob/main/plan/steady-state-loop-hardening/research/008-core-review-triage-and-shared-runtime-rule.md>
   — dispositions of the core reviews' findings, the two-tier charter
   this plan is seeded with, and the maintainer's shared-runtime routing
   rule.
2. The two core-side reviews this charter answers:
   <https://github.com/mi-homelab/homelab/blob/main/plan/steady-state-loop-hardening/research/reviews/livespec-review-fable.md>
   and
   <https://github.com/mi-homelab/homelab/blob/main/plan/steady-state-loop-hardening/research/reviews/livespec-review-sol.md>.
3. Runtime supersession (binds the attention-surface coordination fact
   below):
   <https://github.com/mi-homelab/homelab/blob/main/plan/steady-state-loop-hardening/research/010-runtime-review-triage.md>
   — R4: the runtime carrier is mandatory, baseline-first.
4. Background: the plan summary and research 001–007 of the homelab
   plan `steady-state-loop-hardening`, same directory.

## Charter — DECISION-FIRST, two tiers

Per homelab research/008 (disposition of this repository's review
findings fable 4 + sol 2), this plan is chartered decision-first: the
deliberate Tier-1 decision about what core's documents should SAY comes
before any edit, and the tier boundary is explicit.

**Tier 1 — documentation pull requests (no ratified-prose change):**

- (a) Audit D1 (homelab research/006): Control-Plane wording in
  `README.md` and `AGENTS.md`, presented realization-neutrally — the
  Control-Plane role with its shipped realizations (console: bounded
  dispatch AND the autonomous valve; overseer: plan-driven worker
  sessions), or naming none and pointing to a fleet-level list.
- (b) Audit D2, settled the OTHER way by this repository's own ledger
  (review finding fable 1): full autonomous mode is SHIPPED and
  live-accepted (`livespec/livespec-j4odoz`, closed 2026-07-20 with
  live-exercise evidence). D2 therefore becomes "attribute the
  autonomous-mode story to its owning realization and cite where it is
  specified" — NEVER "mark it explicitly future", which would regress
  core docs on a demonstrated capability. The Control-Plane taxonomy has
  at least three shipped modes; homelab's two-approach enumeration is
  homelab's deployment choice, acknowledged as such on the homelab side.
- (c) `README.md` §"The work-item lifecycle" (review finding sol 2's
  leg; also fable finding 4's surface addition): the same
  factory-loop/autonomous story one section below the console section
  gets the same realization-neutral treatment.

This Tier-1 decision also settles the orchestrator-review fable
finding 11 disposition recorded in homelab research/007: core's
"carries routine cross-repo work unattended" prose is a
possible-realization description — kept, presented neutrally.

**Tier 2 — CONDITIONAL spec revision (only if Tier 1's decision
requires it):**

propose-change → independent adversarial review → revise against the
conflicting `SPECIFICATION/spec.md` and
`SPECIFICATION/non-functional-requirements.md` paragraphs (the
single-console phrasing in the workflow/planes/Control-Plane-role
sections; the reference-Dispatcher invocation story in the
contract-architecture section) ONLY if the deliberate Tier-1 decision
rewords ratified prose. Per review finding fable 1 it likely does not:
the ratified prose describes a real, accepted realization and is
already explicitly non-normative on core's contract; a clarifying
invocation-ownership sentence may be the whole change. A docs-chartered
plan that must touch ratified prose widens its charter explicitly,
never silently. Any heading change carries the
`tests/heading-coverage.json` co-edit discipline.

## Coordination facts that bind this plan (settled elsewhere; not
re-decided here)

- **Detector binding (matrix §15, gap direction).** Settled: gap
  capture after a revise is THIS repository's revise Step 13 post-step
  (shipped in `.claude-plugin/prose/revise.md`, armed in homelab's
  committed config). The orchestrator files the gap-staleness fact as
  the BACKSTOP, citing this repository's ratified v081 coordinating
  epic (`coordinating-epic-stale-revise-enforcement`) — one binding,
  one backstop. No core action.
- **Intake corroboration travels.** Review finding fable 8 (core's
  intake pattern: wall at ready, advise at capture;
  `livespec/livespec-h95t` records the raw-`bd create`
  Definition-of-Ready bypass) is cited by the orchestrator's matrix §01
  filing. Expect a citation; no core action unless asked.
- **Shared-runtime rule + R4.** The attention surface (`AttentionItem`,
  `SourceRef`, `Handoff`, kind/ID vocabulary, composer) ratifies in
  `thewoolleyman/livespec-runtime` FIRST (baseline propose-change
  declaring the shipped surface, then extensions); core consumes via
  vendor-pin bump (this repository vendors `livespec-runtime` v0.21.1
  per `.vendor.jsonc`) per the ordered fan-out matrix the runtime
  filing owns. This plan carries NO attention-surface work of its own —
  the vendor-pin bump lands through the normal fleet fan-out when the
  runtime releases.
- **homelab's `compat.pinned` reconciliation** (review finding fable 5)
  is homelab-side work recorded on `homelab/hl-allzdn`. No core action.

## Sequencing and constraints

- The orchestrator plan (`homelab-loop-hardening-orchestrator` in
  `livespec-orchestrator-beads-fabro`) files first;
  `homelab-loop-hardening-runtime` (in `thewoolleyman/livespec-runtime`)
  is seeded in parallel. THIS plan is decision-first and can start
  Tier 1 immediately — it depends on no upstream filing.
- Generic-not-local: nothing homelab-specific lands in core prose;
  homelab is an example adopter at most.
- homelab proves consumption on its side with negative controls;
  merging is not deploying — core's Tier-1 outcome is "docs merged and
  published", and homelab's acceptance evidence is homelab's concern.
- This repository's tenant was swept 2026-08-25 during the PR #1029
  reviews (770 records, all statuses, zero hits on any
  `homelab-loop-hardening-*` or matrix slug): nothing pre-exists;
  this plan starts clean.

## What this plan does NOT own

- No orchestrator, console, overseer, or runtime work — each routes to
  its owning repository's own plan per the homelab-initiates model.
- No attention-schema or composer change (runtime-first rule above).
- No homelab-side edits (the deployment-choice acknowledgment in
  homelab's documents is homelab's leg, recorded in research/008).
- No Tier-2 spec revision unless the Tier-1 decision explicitly widens
  the charter.
