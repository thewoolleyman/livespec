# Planning Lane design — decisions and plan

Captured 2026-06-25 from the `workflow-planning` design session. **This
is research, not specification text.** Nothing here is normative until it
moves through `/livespec:propose-change` → `/livespec:revise`. This doc
is the durable reasoning + plan; the runnable handoff is
`prompts/livespec-zs22-handoff-planning-lane.md`; the queryable plan is
ledger epic **`livespec-zs22`**.

Companions:
[[missing-planning-workflow-thread]] (the original 2026-06-23 gap note),
`research/factory-conformance/cross-repo-conformance-pattern.md` (the
Conformance Pattern — a major concern that files its milestones through
this lane), and
`research/dark-factory-operability/work-breakdown.md` (the Grooming
thread — orthogonal and downstream).

## Bottom line

livespec has a codified, supported workflow for the spec lifecycle
(`/livespec:*`) and for tracked implementation work (the orchestrator
skills + the beads ledger). It has **no** codified surface for the
durable, multi-session **planning** work that decides what should *become*
spec vs. implementation vs. research — that work has lived in the
maintainer's head and in hand-written prompts. This is not new scope: the
abandoned bootstrap design (approach-1) specified a `plan` artifact, an
`explore` thinking-partner, and a `journal`, and dropped all three when
the project narrowed to "pure spec governance." The field (spec-kit,
Kiro, BMAD, Cline, beads) has since converged on the same three-lane
model livespec already half-runs. The move is to **re-adopt livespec's
own deferred design as a disciplined, codified convention**, place each
piece on the plane that owns what it touches, and mechanically enforce the
one rule the field has not solved: a planning artifact must never become a
second tracker.

## The three planes

The planning work spans planes; conflating them is the error. There are
three:

| Plane | Owns | Concerned with |
|---|---|---|
| **Spec Plane** (livespec core) | `SPECIFICATION/`, `research/`, the `/livespec:*` lifecycle | *what* the system should do |
| **Orchestrator Plane** (the producer) | the beads ledger, the Dispatcher, the Loop/Fabro | *producing* implementation from ripe work |
| **Control Plane** (the console — `livespec-console-*`) | the operator experience: observe all planes, coordinate the human through multi-session work | *running* the overall workflow |

Naming hazard, resolved: the console is **not** a "Driver." "Driver"
already means the per-agent-runtime binding (`livespec-driver-claude`,
`livespec-driver-codex`). The console is the **Control Plane / operator
cockpit**. Keep those distinct in all prose and diagrams.

## The Planning Lane

The Planning Lane is the durable, multi-session planning convention. It
has two artifacts, which map to two planes:

- `research/<topic>/*.md` — durable **reasoning** ("why this shape").
  Spec-Plane; matures into a `propose-change` when it becomes
  contractual. Analogue: spec-kit `plan.md` / Kiro `design.md`.
- `prompts/<topic>-handoff.md` — resumable **execution coordination**
  ("resume track T in a fresh session"). It references ledger ids and
  drives implementation, so it sits at the seam (below). Analogue: Cline
  `activeContext.md` + `progress.md`.

The discipline (the openbrain convention livespec copied the shape of but
dropped — see `/data/projects/openbrain/prompts/AGENTS.md`):

- **status is derived from the ledger as the first action, never stored
  in the prompt** (the no-shadow-ledger rule);
- a handoff's checklist items are each a session-local step **or** a
  pointer to a real ledger id — never a parallel work queue;
- refresh the handoff at ~context budget; archive on close via `git mv`
  with a completion banner;
- a per-repo `prompts/AGENTS.md` defines the convention locally.

### The two seams (the Spec/Orchestrator overlap)

The Planning Lane is Spec-Plane, but it touches the Orchestrator Plane at
exactly two explicit, one-directional seams — the same cross-boundary
discipline as the existing gap/drift flows:

1. **Prompt → ledger:** a handoff cites ledger ids **read-only**; it never
   writes the ledger. Status is composed from the orchestrator's
   `list-work-items`/`next`, never stored.
2. **Plan → work:** routing ripe work into the ledger is a cross-boundary
   handoff **through the orchestrator's `capture-work-item` CLI** — never a
   direct cross-plane write.

## Locked decisions (2026-06-25)

1. **The codified handoff/coordination skill lives Orchestrator-side**,
   beside `capture-work-item`/`groom` — not as a core spec-side
   `/livespec:plan`. Rationale: its job is execution coordination over the
   ledger (which the orchestrator owns), it re-homes the retired
   orchestrator handoff-prompt chain, and it keeps core's public
   *functional* surface pure. The *pattern* is non-functional core
   guidance (general, any orchestrator); the *realization* is the
   reference orchestrator's skill — the same split as Grooming. The
   reasoning-capture half (`research/`) stays a lightweight Spec-Plane
   convention; a planning thread that should become spec just becomes a
   `propose-change` (no new core op).
2. **Ubiquitous language:** `fleet` and `adopter` and `governed repo` are
   kept (`governed repo` is already established spec language). `factory
   profile` is renamed **`baseline` profile** — "factory" is already
   bound to the autonomous execution engine (the dark factory), and the
   baseline conformance floor applies even to repos not using that engine.
   Additive profiles layer on top (`fleet-infra`, `orchestrator-plugin`,
   `app`).
3. **`just` is mandated non-functionally only** — for the livespec fleet's
   own NFRs, adopters, and the reference orchestrators (which are
   reference implementations, not public plugins). It MUST NEVER appear in
   livespec core's *functional* spec, the `/livespec:*` plugin skills core
   ships, or the core↔orchestrator CLI contract. This dissolves the
   `just`-keystone vs. `ob-0x5` conflict along the functional/
   non-functional line and simplifies `ob-0x5` to a single-runner design
   (the runner is always `just`; only the per-ecosystem hydrate/verify
   recipes differ).
4. **The console is the Control Plane / runner.** "Scaffold + route +
   check, never run" for the skills is coherent because the console runs
   the overall workflow. The console must not become a dependency yet —
   the orchestrator-side handoff skill works standalone today; the console
   enriches it later. The Control-Plane *role* is general guidance; the
   beads-fabro console is its reference realization.

Posture update absorbed from the concurrent release-pinning work
(`livespec-bwyj`, 2026-06-25): the fleet now tracks **latest RELEASE, not
master HEAD** (releases carry mutation + full-heading + no-LLOC validation
that per-commit `just check` skips; release-please keeps latest-release
close to master). All new artifacts use the "track latest RELEASE"
posture; the old "always pull HEAD" guidance is superseded.

## Relationship to the other workstreams

- **Conformance Pattern** (companion doc): the cross-repo five-slot
  mechanism (Contract / Mechanism / Installer / Verifier / Exemption) that
  keeps shared policy consistent and provable. It *files its milestones
  through* the Planning Lane. Its concerns absorb the two defects this
  session surfaced (the Codex-missing-hook / cross-Driver DRY → the
  **Plugin-resolution** concern; the impl→orchestrator terminology
  leftover → the **Terminology-guard** concern) plus **Worktree-discipline**
  (reconciles `ob-0x5`), **No-shadow-ledger** (the Planning Lane's own
  enforcement), **Ledger-closure** (the merge-closes-item / 0-of-23 fix),
  and **Pin-freshness** (release fan-out + the `4v7v.6` deadlock guard +
  adopter auto-bump). Do NOT fix the defects tactically ahead of the
  pattern — a bespoke per-defect fix recreates the drift the pattern
  exists to kill.
- **Grooming / Work-Breakdown** (`research/dark-factory-operability/`):
  the epic → ready-slices decomposition. Orchestrator-internal, downstream,
  orthogonal to this — not in scope here.
- **Release-pinning** (`livespec-4v7v.6`, `livespec-besm`,
  `livespec-bwyj`): runs concurrently; it is a live preview of the
  **Pin-freshness** concern. **Adopter auto-bump** is recorded as a
  downstream piece of Pin-freshness (depends on the fan-out being fixed +
  the Conformance Pattern's `adopters` manifest section + a `posture`
  field per adopter: `released` / `pinned` / `none`; and it must ship with
  the `4v7v.6` deadlock guard, since more fan-out edges multiply the
  deadlock surface).

## Dependency direction

```
Planning Lane  →  Conformance Pattern  →  the named concerns
   (the medium)      (the framework)        (the instances)
```

Planning Lane is the thin upstream unblocker (the Conformance Pattern's
M0 names it as a soft prerequisite). Grooming is separate/downstream.
Release-pinning runs concurrently and previews the Pin-freshness concern.

## Increment sequence (the overall plan)

Small, cohesive, independently mergeable, nothing-breaks. Tracked under
epic `livespec-zs22`; children filed as each ripens (drafted here for
maintainer approval first — the human owns the cut).

0. **Capture** (this PR, `livespec-zs22`): this reasoning doc + the
   handoff prompt + the Conformance Pattern reconcile (`livespec-zs22.1`).
   Dogfoods the lane.
1. **README + `spec.md` architecture diagram:** the three planes, the
   Planning Lane, the two seams, the Control Plane — defensible and
   consistent with this design. (Maintainer requirements a + b.)
2. **Planning Lane → core `non-functional-requirements.md` guidance**
   (`propose-change`): the three-lane separation, the two seams, the
   no-shadow-ledger invariant, the openbrain discipline. The *pattern*
   only; no command in core's functional surface.
3. **Handoff skill (orchestrator-side) + shape-aware no-shadow-ledger
   hook**, DRY across both Drivers (this also discharges the
   Plugin-resolution concern's first slice — the hook must ship identically
   in both Drivers via single-sourced neutral logic + thin per-runtime
   adapters).
4. **Console control-plane contract** in both `livespec` and
   `livespec-console-beads-fabro` specs (+ mermaid both sides): what the
   console reads, composes, and coordinates; what it never owns.
5. **Conformance Pattern:** the five-slot anatomy, `baseline` profile +
   additive profiles, the declarative `adopters` manifest, the four-tier
   enforcement, the `just` NFR mandate, and the named concerns. Itself an
   epic (M0–M6 in the companion doc), filed when increment 2–3 land.

## Open / future

- Rename `research/factory-conformance/` → `research/cross-repo-conformance/`
  for consistency with the `baseline` rename (the dir reuses "factory").
  Light follow-up; check references first.
- Adopter auto-bump (under Pin-freshness): needs the fan-out fixed, the
  `adopters` manifest, the `posture` field, and the `4v7v.6` deadlock
  guard. Downstream.
- Whether the reasoning-capture (`research/`) ever needs its own thin
  skill, or stays served by `propose-change`/`critique` intake + the
  persistence hook. Lean: no new skill until the convention strains.
