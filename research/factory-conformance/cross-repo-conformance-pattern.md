# Cross-repo conformance pattern (factory-conformance)

Captured 2026-06-24 from an Open Brain session that started on the
worktree-only commit discipline and generalized into "how do we manage
cross-cutting patterns across every repo on the livespec + beads/Fabro
factory approach." **This is research, not specification text.** If any
part becomes a rule for livespec itself, it still moves through
`/livespec:propose-change` → `/livespec:revise`. Companion to
[`research/planning-workflow-gap/missing-planning-workflow-thread.md`](../planning-workflow-gap/missing-planning-workflow-thread.md)
— that doc defines the planning lane this effort files its milestones
through; this doc is the research file in that lane.

See also `research/planning-workflow-gap/planning-lane-design.md`, which
records this lane's locked decisions and the three-plane model (Spec /
Orchestrator / Control) this effort sits within.

## Bottom line

livespec already is, in effect, a policy-as-code conformance framework —
for its own fleet: a member manifest, copier for static-scaffold sync,
livespec-dev-tooling for executable shared checks, doctor cross-boundary
invariants, and an orchestrator that gates every dispatch on `just check`.
Two things are missing to make it a *general* pattern: (1) a repeatable
recipe for adding a new cross-cutting concern, and (2) the boundary is
"fleet member," not "any repo on the factory approach" (Open Brain is
exempt today only because it lacks `.copier-answers.yml`). The pattern
below closes both, leaning entirely on existing primitives plus the
`just`-as-sole-task-runner standard.

## Problem

Cross-cutting operational policies (worktree-only commits, the
beads-access guard, the task-runner standard, the agent-instruction core,
plugin-resolution-across-harnesses) must hold in every governed repo, but
they drift: each repo carries its own copy or its own realization, and
nothing keeps them consistent or proves conformance. Three concrete
failures from this session:

- **Open Brain** hand-rolled the worktree commit-refuse hook (lefthook +
  a structural detector) because livespec's canonical hook never reached
  it — Open Brain is not a fleet member.
- **livespec-console-beads-fabro** committed three times on its primary
  `master` despite being a full fleet member: the canonical hook was
  *installed but not armed* (`livespec.primaryPath` was written 11h late,
  by a bootstrap nobody ran), and the hook fails **open** when
  `primaryPath` is unset. An installed-but-unarmed hook reads as
  protected but is a silent no-op.
- **Open Brain's plugin adoption** (epic ob-4ts) shipped "done" while the
  `/livespec*:*` slash commands didn't resolve, because no item owned
  "verify from a fresh session" and the acceptance test tolerated the
  `bd` fallback.

These are the same shape: a policy, a mechanism, a propagation gap, and a
verification gap.

## Ubiquitous language

The audience axis and the baseline axis are different; "core" conflated
them (and collides with livespec CORE). Name them separately:

- **fleet** — a project's repo family (the converged term). **the
  livespec fleet** = livespec's own self-application family.
- **adopter** — a fleet or repo that *adopts* the factory workflow but is
  not the livespec fleet (Open Brain). Adopters are not "non-fleet" (they
  may be fleets themselves) and not merely "consumers" (fleet members
  consume too); they *adopted* the approach. livespec did not adopt
  itself.
- **governed repo** — the union (anything under the approach; carries a
  `.livespec.jsonc`).
- **baseline profile** (`baseline`) — the universal participant-conformance
  floor every governed repo satisfies (worktree discipline, `just`
  standard, beads-access guard, plugin-resolution). Applies to fleet AND
  adopters, and holds whatever orchestrator (or none) a repo uses — it is
  the conformance floor, not a tie to the autonomous factory engine.
  Renamed from the earlier "factory profile" (which collided with the dark
  factory) and the still-earlier "core" (which collided with livespec CORE).

## The pattern — anatomy of a concern (five slots)

Every cross-cutting concern shaped like the worktree problem fills the
same five slots. Make this the standard so adding a concern is fill-in-
the-blanks, not a design:

| Slot | What it is |
|---|---|
| **Contract** | the normative invariant, stated once (spec-side) |
| **Mechanism** | the one canonical executable that satisfies it |
| **Installer** | the idempotent verb that puts it in place (a `just` recipe) |
| **Verifier** | the mechanical check, **fail-closed**, wired into `just check` |
| **Exemption** | *explicit, declared* opt-outs for legitimate variation |

Concerns already of this shape: worktree/commit-refuse discipline, the
beads-access guard, `just`-as-sole-runner / no-direct-tool-invocation,
`with-<id>-env.sh` secret injection, the AGENTS.md/CLAUDE.md symlink +
agent-instruction core, mise toolchain pins, plugin-resolution across
harnesses.

## Delivery rule — reuse by default, templatize only divergence

Per concern, the Mechanism ships one of two ways, and the choice is
mechanical:

- **Reuse (pin + import)** for anything executable or that must be
  byte-identical → from livespec-dev-tooling (the verifier) or a shared
  `just` module (the recipe/hook body). No copies → no drift.
- **Templatize (copier, 3-way merge)** only for static scaffold a repo
  legitimately customizes → the justfile skeleton that *imports* the
  shared module.

**`just` is the keystone.** It is the single task-management standard for
every governed repo — fleet and adopter, JavaScript app or Python fleet
repo. Everything else delegates to it: git hooks (`run: just <recipe>`),
CI (`just <recipe>`), per-language tools (pnpm/uv/cargo) are
implementation details *inside* a recipe, and a foreign runner that
insists on existing is allowed only as a thin 1:1 passthrough
(`"build": "just build"`). Because the entry point is always `just
<recipe>`, the same shared recipe and the same verifier run everywhere —
which is what lets an adopter consume the fleet's machinery without being
a fleet member, and what makes the standard self-enforcing (a check can
assert lefthook/CI contain only `just …`).

**The boundary that keeps this honest.** `just` is mandated as a
*non-functional* standard — for the livespec fleet's own NFRs, adopters,
and the reference orchestrators (reference implementations, not public
plugins). It MUST NEVER appear in livespec core's *functional* spec, the
`/livespec:*` plugin skills core ships, or the core↔orchestrator CLI
contract; those stay tool-agnostic so livespec remains a generic
deployable plugin. The mandate cannot leak through that contract because
the contract is the CLI seam, not the tooling behind it.

## Boundary — profiles + a declarative manifest (no scan)

Replace "fleet member or not" with a **profile** = the set of concerns a
repo must satisfy: `baseline` (every governed repo) + additive layers
(`fleet-infra`, `orchestrator-plugin`, `app`, …).

Membership is **declarative**, not a filesystem scan (scans are slow,
brittle, non-deterministic). Extend the existing manifest with an
`adopters` section beside the fleet members; each entry carries its
profile:

```jsonc
// .livespec-fleet-manifest.jsonc  (single file; graduate to a separate
// file only when the baseline tooling splits to its own repo)
{
  "fleet":     [ { "repo": "livespec", "class": "core", "profile": ["baseline","fleet-infra"] }, … ],
  "adopters":  [ { "repo": "openbrain", "profile": ["baseline","app"], "posture": "released" }, … ]
}
```

The per-repo `.livespec.jsonc` carries the same `profile` as the *local*
declaration the verifier reads; the manifest is the *central* list the
fleet sweep and the orchestrator iterate. Deterministic, no drift.

## Enforcement in depth (four tiers)

No single tier covers every repo/moment, so layer the same verifier:

- **Author-time** — copier scaffolds the profile into a new repo.
- **Commit-time** — lefthook → `just check` runs the profile's verifiers.
- **Dispatch-time** — the orchestrator runs installer + verifier before
  driving *any* tenant → "uses the factory ⟹ conformant," fleet or
  adopter.
- **Fleet-time** — a sweep (`just conformance` over the manifest) + drift
  CI, for repos nothing has committed-to or dispatched lately.

## The hard rule the worktree saga proved

**Every exemption is explicit and declared; the default is fail-closed.**
The console incident was an *implicit* exemption (`primaryPath`-unset
*accidentally* meant "allow"). The legitimate Fabro sandbox relied on the
same implicitness. Generalize: a variation point is a **marker the
verifier reads**, never an incidental side effect.

### Applied to the worktree concern (the first instance)

- **Mechanism = structural detection** (`git-dir == git-common-dir` ⇒
  refuse; worktrees differ), which Open Brain proved superior:
  armed-on-install, no `primaryPath` arming step to forget, no fail-open
  window. Unify on it.
- **But pure structural breaks Fabro as-is**: the sandbox is a fresh full
  clone that *deliberately installs the hook but leaves it inert via
  `primaryPath`-unset* so Red-Green-Replay can commit; structural can't
  tell that sandbox full clone from a primary full clone and would refuse
  it.
- **Resolution (preferred):** make the *verifier* sandbox-aware so the
  sandbox no longer needs to install the hook at all (it installs it today
  only to satisfy the content check). Then the hook is pure structural
  everywhere it actually lives, `primaryPath` is retired, and console's
  fail-open cannot recur. The one new requirement is a "this is a Fabro
  sandbox" marker the verifier reads — Fabro already has the prepare step
  to set it. **Fallback:** keep the hook installed in the sandbox and use
  a combined body (structural OR `primaryPath`) with an explicit sandbox
  opt-out marker.

## dev-tooling cohesion — fleet vs baseline tooling

livespec-dev-tooling exists to abstract the *fleet's* tooling; serving
adopters too would erode that. But a new repo now is premature. Sequence:

1. **Now — partition internally.** Tag each check module `baseline`
   (any governed repo) vs `fleet` (livespec-infra-only); expose a
   `baseline` import surface. Open Brain imports only `baseline`.
2. **Later — extract `baseline` tooling to its own repo** once the surface
   is stable and a second adopter proves the boundary;
   livespec-dev-tooling then depends on it for the `fleet` layer. The
   manifest's `adopters` section can graduate to a separate file at the
   same point.

## Cross-harness plugin-resolution (concern #2)

Enforcing that the plugins/skills actually *work* is the same five-slot
shape, and ob-4ts is its live failure:

| Slot | plugin-resolution |
|---|---|
| Contract | a governed repo's documented command/skill surface MUST resolve **and run** from a **fresh session** of each *declared* harness |
| Mechanism | real per-harness install records (Claude: project-scoped `/plugin install`; Codex: host-wide `codex plugin add`; Pi: TBD) + marketplace registration |
| Installer | documented per-harness install procedure (Claude's is client-side → the verifier is the enforcement) |
| Verifier | a fresh-session resolution smoke: invoke a canonical command, assert it resolves+returns — per declared harness, and **must reject a `bd`/raw fallback as proof** |
| Exemption | unsupported harnesses (Pi today) declared explicitly — "Pi unsupported" is a declared state, not a silent gap |

A fail-closed verifier here would have made ob-4ts un-shippable (its
acceptance was written to tolerate the `bd` fallback). Register it as the
second `baseline` concern.

## Pin-freshness and adopter auto-bump (a further concern)

The release-pin fan-out is the same five-slot shape and is being built out
concurrently (`livespec-4v7v` + follow-ups). Two refinements this lane adds:

- **Posture, not forced-HEAD.** The fleet now tracks *latest RELEASE*, not
  master HEAD (`livespec-bwyj`, 2026-06-25): a release carries mutation +
  full-heading + no-LLOC validation that per-commit `just check` skips, and
  release-please cuts a release on every feat/fix so latest-release stays
  close to master. A per-repo `posture` field (`released` / `pinned` /
  `none`) replaces the old always-pull-HEAD rule; fleet members are
  `released`, adopters declare theirs.
- **Adopter auto-bump.** Extend the fan-out to opted-in adopters via the
  `adopters` manifest + each entry's `posture`. It MUST ship with a
  fail-closed pin-freshness guard on the *releasing* repo's own
  discover-step — a stale released shim globally deadlocked the fleet
  fan-out once (`livespec-4v7v.6`), and more adopter edges multiply that
  surface. Downstream of the fan-out fix + the `adopters` manifest.

## Milestones (each gated on real dogfooding)

- **M0 — Decisions locked** (this thread): the naming (fleet/adopter/
  governed; `baseline` profile), the dev-tooling sequencing, the manifest
  shape, the initial `baseline` concern set. *No code.* Soft prerequisite:
  the planning-workflow-gap doc's planning-lane decision (so milestones
  are filed through it, not a parallel format).
- **M1 — Pattern + concern registry specified** (livespec
  `propose-change`): the five-slot anatomy; profiles; the `adopters`
  manifest section; concern #1 = worktree discipline; concern #2 =
  cross-harness plugin-resolution.
- **M2 — `baseline` machinery built, reuse-first**: structural
  commit-refuse hook body + `just install-commit-refuse-hooks` (shared
  `just` module) + sandbox-aware verifier (dev-tooling, tagged `baseline`)
  + copier import.
- **M3 — Fleet dogfood: livespec-console-beads-fabro** carries `baseline`;
  `just check` green; commit-refuse fail-closed; can no longer commit on
  its primary. Proves the self-application path.
- **M4 — Adopter dogfood: Open Brain** migrated to `just` as sole runner
  (lefthook→`just`, pnpm→1:1 wrappers/recipes), registered as
  `adopter`/`baseline`, its hand-rolled hook reconciled to the canonical
  structural body, `baseline` verifiers green via the *same* machinery.
  Proves the pattern reaches outside the fleet.
- **M5 — Second concern + repeatability**: ship concern #2
  (cross-harness resolution) and show it catches the ob-4ts breakage
  class — proving "add a concern = fill five slots."
- **M6 — Enforcement-in-depth wired**: `baseline` verifiers at all four
  tiers; the orchestrator gates every dispatch (fleet and adopter) on
  `baseline` conformance. Self-sustaining.

## Open questions

- Does the sandbox-aware-verifier path (retire `primaryPath`) have any
  edge case beyond the Fabro sandbox — e.g. a host-side fresh full clone
  that legitimately commits? (None found in the dispatch flow; the
  janitor is a worktree.) Confirm before M2.
- Manifest ownership once `baseline` tooling splits out: does the
  `adopters` registry move with it, or stay in livespec?
- Where the orchestrator's per-dispatch installer reads the per-repo
  install command (uniform `just install-commit-refuse-hooks` once `just`
  is universal — no harness-aware branching needed).

## Recommended next step

Not "build the framework." Lock M0 (naming + the three structural
decisions), then file M1 as a single livespec `propose-change`, with
livespec-console-beads-fabro (fleet) and Open Brain (adopter) named as
the M3/M4 dogfood proofs. Use the convention manually for these two
concerns first. The planning-lane decision has since landed: the codified
handoff skill is **orchestrator-side**, not a core `/livespec:plan` — see
`planning-lane-design.md`.
