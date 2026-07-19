# Diagnosis — why fleet pin propagation is stuck

**Captured:** 2026-07-19, from a direct sweep of all 8 fleet member repos
(GitHub PR state + each master's committed pin values).
**Status of this note:** point-in-time evidence. The numbers below are
measurements, not estimates; re-measure before acting on them.

## Bottom line

The fleet has **41 open pin-bump pull requests across 8 member repos**, and
every master branch is **green**. Those two facts together are the whole
story: the fleet is green *at rest* but cannot absorb upstream propagation,
and the green masters are exactly what hid the problem.

The 41 PRs are **not** 41 breakages. They are two different defects wearing
the same costume:

1. **Superseded bump PRs are never closed** (fleet-wide hygiene defect).
   ~29 of the 41 target a version OLDER than the version their own master
   already carries. They are dead weight.
2. **One repo is genuinely blocked** — `livespec-console-beads-fabro`, by a
   gate the fan-out structurally cannot satisfy. It is the only repo where
   propagation actually fails.

Mistaking (1) for (2) is the trap: a glance at "41 red PRs" reads as a dead
pipeline, and the noise from (1) camouflages the single real blockage in (2).

## Evidence — measured 2026-07-19

Each repo's master pin compared against what its open bump PRs target:

| Repo | master core-pin | open bump PRs target | count | verdict |
|---|---|---|---|---|
| `livespec-runtime` | v0.18.0 | v0.10.1 – v0.11.4, v0.17.2 | 18 | all superseded |
| `livespec-console-beads-fabro` | **v0.16.0** | v0.17.0 – v0.18.0 | 12 | **genuinely stuck** |
| `livespec-driver-claude` | v0.18.0 | v0.17.2, v0.15.1 | 2 | superseded |
| `livespec-driver-codex` | v0.18.0 | v0.17.2, v0.15.3 | 2 | superseded |
| `livespec-dev-tooling` | v0.18.0 | v0.17.2, v0.14.0 | 2 | superseded |
| `livespec-orchestrator-git-jsonl` | v0.18.0 | v0.17.2, v0.15.0 | 2 | superseded |
| `livespec` (core) | v0.17.5 | dev-tooling v0.49.0, v0.47.0 | 2 | superseded |
| `livespec-orchestrator-beads-fabro` | v0.18.0 | dev-tooling v0.48.2 | 1 | superseded |

Latest releases at capture: `livespec` v0.18.0, `livespec-dev-tooling` v0.49.2.
Master CI conclusion at capture: green on all 8.

### Consequence of the red noise

A superseded PR's branch is stale against a much-moved master, so its checks
fail for a boring reason unrelated to the pin. `livespec-driver-claude` #196
showed ~20 checks red at once — that is one stale branch, not twenty defects.
Reading those check names as a symptom list produces a wildly wrong diagnosis;
this note exists partly to stop the next session from doing that.

Every one of these PRs also burns a CI run on each push.

### A third, smaller defect

The fan-out opens **duplicate PRs for the same version**: in
`livespec-runtime`, #206 and #208 both bump dev-tooling to v0.44.0, and #207
and #209 both bump livespec to v0.10.1.

## The real blockage — the console's captured-manifest gate

`livespec-console-beads-fabro`'s `check-completeness` runs
`console-completeness-check`, which reads a **captured** orchestrator
config-manifest fixture stamped `captured_at_pin`, derived from
`.livespec.jsonc` `compat.pinned`. Its `justfile` comment states the design
outright: `--refresh` "stamps `captured_at_pin` so the gate fails until the
capture is refreshed at the new pin."

Refreshing runs `just refresh-config-manifest`, which shells out to the
**live** orchestrator drive surface and needs the orchestrator plugin plus
the credential wrapper. The fan-out is an automated push with neither.

So the gate is fail-closed on any pin change, and the only actor that can
clear it is a human at a workstation. Every core release therefore produces
a console PR that is born red. Twelve have accumulated; the console sits at
v0.16.0, twelve releases behind.

Two individually-correct mechanisms — a fail-closed staleness stamp, and a
per-release automated fan-out — that are jointly broken.

### The scope question this raises

The stamp invalidates on **any** `compat.pinned` change, but the capture only
goes stale when the **orchestrator's declared key set** changes. Narrowing
the invalidation trigger to what the fixture actually depends on would stop
core releases from touching this gate at all — which is the majority of the
backlog. That is a design decision this thread owes, not a settled one.

## The classification axis that decides each fix

For every consumer-side gate that a pin bump can redden, the deciding
question is:

> Is the refresh **(a) derivable from static text** the fan-out could compute
> itself, or **(b) does it require a live system, credentials, or human
> judgment**?

- **(a)** admits the settled "fan-out writes the wiring" mechanism.
- **(b)** does not. For those, the only options are to fail before the PR
  exists with an actionable diagnostic, or to redesign what the gate
  compares so the bump stops invalidating it.

The console's captured manifest is the clearest **(b)** case found so far.
The canonical-check justfile wiring is the clearest **(a)** case — and is
already decided (see below). A full per-gate sweep across all repos is owed
and is the thread's first research task; the earlier attempt at it did not
return usable output.

## Settled decisions this thread MUST honor, not re-litigate

**`livespec-dev-tooling-adqmnm`, maintainer-decided 2026-07-05**, recorded in
that item and originating in the `fleet-plugin-currency` plan thread (now
archived at `plan/archive/fleet-plugin-currency/`; the authoritative record is
the ledger item itself, not the archived thread). The
mechanism chosen was "fan-out writes the wiring": the fan-out RECONCILES each
consumer's `check:` recipe canonical block to the newly-pinned canonical set,
atomically in the same push that bumps the pin, because both justfile lines
are 100% derivable from dev-tooling's own registry.

**Three options were weighed in total.** The one above was CHOSEN; the other
two were **rejected**:

- *grace-period soft-warn* on `aggregate_completeness` for a brand-new slug —
  rejected as drift-prone per-slug "first-release version" state AND a
  deliberate softening of the check for a window, close to the escape-hatch
  pattern `.ai/ci-gate-discipline.md` steers away from;
- *accept the manual wave* / sequence consumers by hand — rejected as the
  status quo that produced the 2026-07-03/04 cascade, since it relies on
  always remembering to wire every consumer BEFORE the release.

(An earlier draft of this note miscounted these as "three rejected"; there are
two. The chosen mechanism is the third option.)

That decision generalizes to every **(a)**-class gate and should be applied
rather than re-derived. It explicitly does NOT generalize to **(b)**-class
gates, because its whole justification is derivability.

## Existing ledger items and their disposition

Consolidation verdicts proposed by this thread. `CHILD` = becomes a child of
this thread's epic largely as-is; `KEEP SEPARATE` = linked, not owned.

| Item | Tenant | Scope | Verdict |
|---|---|---|---|
| `livespec-dev-tooling-adqmnm` | dev-tooling | Fan-out reconciles consumer canonical-check block. BLOCKED, `blocked-reason:needs-human` | CHILD — the settled (a)-class mechanism; this thread unblocks it |
| `livespec-dev-tooling-fz4` | dev-tooling | bump-pin must cover the `workflow.toml` fabro-sandbox image tag (the missing 5th pin format). P1 | CHILD — an unmanaged pin is in scope by definition |
| `livespec-dev-tooling-xb7` | dev-tooling | CI container image tag in `ci.yml` is an unmanaged pin, already drifting. P1 | CHILD — same class as fz4 |
| `livespec-dev-tooling-p73` | dev-tooling | pin-freshness treats the FIRST record per `source_repo` as representative, so a stale sibling pin never triggers a bump | CHILD — a propagation-correctness defect |
| `livespec-dev-tooling-u0x` | dev-tooling | bump-pin can wire a canonical check the consumer's PINNED dev-tooling lacks (version skew → `aggregate_completeness` red) | CHILD — the ordering hazard inside the adqmnm mechanism |
| `livespec-o0x1` | livespec core | Fan-out must not redden master on stamped-projection drift (`canonical-slugs.yml`) | CHILD — an (a)-class instance; its acceptance criteria are written narrowly and should be re-scoped to the class |
| `livespec-p9s0` | livespec core | Cross-repo pin/wiring check reads local clone HEAD not origin; flaps on stale clones | CHILD — pin-state observability defect |
| `livespec-dev-tooling-9j8.6` | dev-tooling | Extract logic from `reusable-pin-freshness.yml` + `reusable-release-dispatch.yml` | KEEP SEPARATE — a CI-logic refactor epic with its own scope; this thread depends on it but must not absorb it |
| `livespec-dev-tooling-q9a` | dev-tooling | Exclude world-gate checks from `ci-matrix-completeness` | KEEP SEPARATE — CI matrix hygiene, not pin propagation |
| `livespec-console-beads-fabro-7wy` | console | Rewrite the section-sign spec citation before the next core-pin bump | CHILD — a latent blocker sitting directly on the console's unblock path |

Newly identified by this thread and FILED 2026-07-19. The `N`-labels are
drafting shorthand used nowhere else; each row's filed id is authoritative:

| Draft | Filed as | Tenant | Scope |
|---|---|---|---|
| N1 | `livespec-dev-tooling-q37xxt` | livespec-dev-tooling | Fan-out never closes superseded bump PRs (~29 dead PRs fleet-wide) |
| N2 | `livespec-dev-tooling-y6kqgr` | livespec-dev-tooling | Fan-out opens duplicate PRs for the same version |
| N3 | `livespec-console-beads-fabro-tafkuw` | livespec-console-beads-fabro | Console captured-manifest gate: invalidation trigger is wider than the fixture's real dependency, and the refresh is (b)-class |
| N4 | `livespec-xw65el` | livespec (core) | Per-gate sweep: classify every consumer-side gate as (a) or (b) — owed, not yet done |

## Boundary with the CI-substrate thread

`plan/fabro-ci-image-factoring/` owns the CI **substrate** — baked images,
hot runners, resource-health-gated rollout. This thread owns **pin
propagation and the gates pin bumps break**. They meet at exactly one seam:
the image tags are themselves unmanaged pins (`fz4`, `xb7`). Those items are
owned here; what goes *inside* an image is owned there. Maintainer-confirmed
scope boundary, 2026-07-19.

## What could invalidate this diagnosis

- The superseded-PR count is a snapshot; the fan-out keeps opening PRs, so it
  drifts upward between measurements.
- The per-gate (a)/(b) sweep has NOT been done. The claim that the console's
  manifest is the only (b)-class gate is unproven — it is the only one found
  so far, which is a much weaker statement.
- CI logs older than roughly a day have aged out on the self-hosted runners,
  so the specific assertion behind each historical red PR is no longer
  readable. Re-run a check to see a live failure rather than trusting a
  reconstructed cause.
