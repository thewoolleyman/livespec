# Tier-1 decision record — realization-neutral Control-Plane docs

Recorded 2026-08-25 by the `homelab-loop-hardening-core` session,
executing the plan's recorded next action (epic `livespec/livespec-xebypg`,
seeding handoff). This note IS the deliberate Tier-1 decision the
charter requires before any edit; the docs change lands in the same
pull request, implementing exactly what is decided here.

## The decision

**Tier 1 only. The charter is NOT widened into Tier 2.** No ratified
sentence needs rewording, because the peer-realization model the docs
must present is ALREADY ratified:

- `SPECIFICATION/non-functional-requirements.md`'s ratified **Fleet
  manifest** contract paragraph (miscited as `spec.md` §"Fleet manifest"
  in the original record and in epic handoff 5; corrected at archive
  time per the independent completeness review's non-blocking finding)
  ratifies the
  `control-plane-tool` repo class as a Control-Plane member that "ships
  an operator TOOL rather than the cockpit APPLICATION the `console`
  class carries; the two are PEERS", and the committed
  `.livespec-fleet-manifest.jsonc` classes `livespec-console-beads-fabro`
  as `console` and `livespec-overseer` as `control-plane-tool` — the
  peer model is ratified text plus committed fleet fact, not a new
  claim.
- `SPECIFICATION/spec.md` §"The Control-Plane role" already scopes the
  role as "general guidance any console fulfills", names the Beads/Dolt
  + Fabro console as its REFERENCE realization, and states the console
  is not a required dependency; `non-functional-requirements.md`
  §"Control-Plane console guidance" is explicitly non-normative on
  core's contract and rules that "no plane depends on the console".
- The "single human interface" phrasing in the ratified diagrams and
  §"The Control-Plane role" describes the ROLE's cockpit shape (one
  operator surface aggregating every plane) — not a claim that exactly
  one Control-Plane realization exists or is mandatory. Read together
  with the ratified peer-class clause, no contradiction arises, so no
  clarifying propose-change is required. This resolves the conditional
  branch of the charter: the ratified model is retained as the
  permitted reference realization; the README narrows accordingly and
  does not claim interchangeability as core doctrine (per the homelab
  research/008 disposition of review findings fable 4 + sol 2).

**Audit D2 is settled the other way, as the charge directs** (review
finding fable 1): full autonomous mode is SHIPPED and live-accepted —
`livespec/livespec-j4odoz`, closed 2026-07-20, bar met with two real
fleet work-items driven end-to-end solely through the live console TUI.
The autonomous-mode story is therefore KEPT and ATTRIBUTED to its
owning realization (the reference console's type-to-confirm valve,
enable flow documented in that repo), never marked future. This also
discharges the orchestrator-review fable finding 11 disposition from
homelab research/007: "carries routine cross-repo work unattended" is a
possible-realization description — kept, presented neutrally.

## What the docs edits do (this pull request)

1. **README §"Operator console (the Control Plane)" → retitled
   "The Control Plane (operator cockpit)".** Presents the ROLE first,
   then its two shipped realizations as peers per the ratified manifest
   classes: the reference console `livespec-console-beads-fabro`
   (cockpit application: observation, bounded dispatch drains, and the
   full-autonomous-mode valve — shipped and live-accepted,
   `livespec/livespec-j4odoz`) and the `livespec-overseer` operator
   tool (two-pane overseer: deterministic daemon + operator surface,
   foreman/grooming loops, plan-driven worker sessions). States that
   invocation ownership — a standing autonomous drain, operator-
   triggered bounded waves, or plan-driven worker sessions — is a
   deployment choice, and keeps the not-a-required-dependency fact.
   No inbound anchor links exist in-repo to the old heading (verified
   by grep before the rename).
2. **README §"The work-item lifecycle".** The factory-loop paragraph
   and the state-diagram note stop presenting the continuous
   standing drain as THE behavior: the Dispatcher drains ready items
   up to the per-repo cap; whether it runs continuously (the
   console-armed autonomous mode) or in operator-triggered bounded
   waves is a deployment choice. Everything else is unchanged.
3. **README §"Cross-repo orchestration" and the two AGENTS.md
   passages** (§"Cross-repo orchestration — retired Layer-3 skill; now
   the Dispatcher" and the Daily-commands bullet): "unattended" is
   kept and attributed — unattended operation is the shipped
   autonomous realization, one of the sanctioned invocation modes,
   not the sole definition of the Dispatcher.

## Explicitly out of scope

- **No ratified-prose edit** (Tier 2 not entered; recorded here as the
  charter requires an explicit widening if that ever changes).
- **No shared-runtime surface prose is touched**, so the v012 phrasing
  rule ("ratified at v012, implementation conformance pending" —
  epic handoff 4) is not triggered by this change.
- **No heading-coverage co-edit**: no `SPECIFICATION/` file changes,
  so `tests/heading-coverage.json` is untouched and the closed-owner
  TODO hazard recorded in epic handoff 4 is not tripped (it remains a
  named hazard for any future filing that edits the registry).
- **No homelab-side edits** (homelab's deployment-choice
  acknowledgment is homelab's leg, per homelab research/008).
