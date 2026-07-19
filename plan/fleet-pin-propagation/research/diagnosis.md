# Diagnosis — why fleet pin propagation is stuck

**Captured:** 2026-07-19, from a direct sweep of all 8 fleet member repos
(GitHub PR state + each master's committed pin values).
**Revised:** 2026-07-19, same day, after three detailed research inventories
were recovered (see §"Recovered inventories" at the end). The revision
CORRECTS several claims in the original draft; corrections are marked inline.
**Status of this note:** point-in-time evidence. The numbers below are
measurements, not estimates; re-measure before acting on them.

## ⚠ MAJOR REVISION — read before acting on anything below

Three research inventories were produced and then lost to a harness fault (the
sub-agents completed their work but their final reports never reached the
driver session). They were recovered from the agent transcripts and folded in
here. They changed four load-bearing conclusions:

1. **6 of the 10 pre-existing ledger items are ALREADY FIXED on master.** The
   original disposition table below marked them `CHILD`. They are not work;
   they are stale ledger records. Fix commits verified as ancestors of
   `origin/master` — see §"ALREADY DONE".
2. **There are 12 reddenable gates, split 8 (a)-derivable / 4 (b)-not** — not
   the single (b) instance the original draft could confirm. The thread's
   central open question is therefore mostly ANSWERED; the sweep item
   (`livespec-xw65el`) is re-scoped from "do the sweep" to "verify and
   complete this recovered inventory".
3. **The `livespec-console-beads-fabro-7wy` premise does NOT reproduce.**
   Independently re-verified here: `no_spec_section_citation_in_code.py` is
   BYTE-IDENTICAL between core `v0.16.0` and core master (sha256 prefix
   `74bd494da6cdef5f` at both refs), and NO static-check module changed across
   that range. So a console core-pin bump does NOT newly trip that check, and
   `7wy` is NOT a blocker on the console's unblock path. The original draft
   said to sequence it first — that was wrong.
4. **Three genuinely-new gaps surfaced**, none previously filed: the fan-out
   producer is outside its own fan-out; no adopter is wired into the fan-out
   at all; and the fan-out has NO dedupe against already-open bump PRs (the
   direct mechanical cause of the stacking).

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

### The sweep — RECOVERED, 12 gates, 8 (a) / 4 (b)

The per-gate sweep was in fact completed; its report was lost to the harness
fault and has been recovered. Headline: **12 distinct reddenable gates across
8 fleet repos. 8 are (a)-derivable, 4 are (b).** Adopters carry ZERO — none of
`openbrain`, `resume`, `homelab` runs a livespec gate in CI.

The 8 derivable ones are dominated by ONE mechanism: a new
`livespec_dev_tooling/checks/<name>.py` upstream simultaneously invalidates the
consumer's `justfile` targets array, its `check-<slug>:` recipe body, and its
CI matrix — three gates × 7 repos. All three now have shipped reconcilers.

**The four (b)-class gates** — where "fan-out writes the fix" cannot apply:

| # | Gate | Why (b) |
|---|---|---|
| 8 | console `check-completeness` | Refresh shells to the LIVE orchestrator drive surface; needs the plugin, credential wrapper, and cargo. The fan-out has none of the three. |
| 9 | `check-doctor-static` (6 repos) | Re-evaluates the consumer's own spec + source against core's checker AT THE NEW PIN. The fix is a human source edit, not a regeneration. Highest-count gate; `ci-green`-blocking in all 6. |
| 10 | `github_workflow_uses_ref` | The required-input DELTA is computable, but the VALUE for a new required input is a judgment call. |
| 11 | `fabro_sandbox_docker_image` | Needs a published image in the registry — purely external. Blast radius total: every CI job runs in that container, so a bad tag fails everything at job start, including the repair PR's own CI. |

**Precedent that matters for the (a) class:** the fan-out ALREADY solves this
shape once — `vendor_jsonc` records trigger `just vendor-update <lib>` and
`pyproject_toml_uv_sources` records trigger a `uv.lock` refresh, both landing
atomically in the bump commit (`bump-pin-rewrite/action.yml:203-227`). Any new
"regenerate the derived artifact" step should follow that pattern rather than
invent one.

### Three new gaps, none previously filed

1. **The producer is outside its own fan-out.** `livespec-dev-tooling` pins its
   own reusable workflows at `@v0.46.5` and its CI image at `python-v0.43.2`,
   while all 7 consumers sit at `@v0.49.2` / `python-v0.49.2`. Nothing fans out
   to dev-tooling itself.
2. **No adopter is wired into the fan-out at all.** None of `openbrain`,
   `resume`, `homelab` carries `bump-pin-from-dispatch.yml`,
   `pin-freshness.yml`, or `release-dispatch.yml`. Visible consequence:
   `resume` is pinned at core v0.7.1 against a current v0.18.0 — 11 minors
   stale, drifting silently.
3. **No dedupe against already-open bump PRs.** Grepping
   `reusable-pin-freshness.yml` and `bump-pin-rewrite/action.yml` for
   `pr list` / `existing` / `dedupe` finds no guard. Branch names are
   deterministic per tag, so a same-tag re-run collides harmlessly — but every
   NEW tag opens a brand-new PR regardless of how many already sit open. This
   is the direct mechanical cause of the stacking, and it is what
   `livespec-dev-tooling-q37xxt` must fix.

### One contradiction the plan must resolve FIRST

`adqmnm`'s ratified acceptance states the reconcile edits `justfile` ONLY,
"never `.github/workflows/`", so it stays within the fleet App's push
permission — and a standing decision records that the App
(`livespec-pr-bot`) DELIBERATELY lacks `workflows` permission. But
`ci_yaml_canonical_reconcile.py` (shipped 2026-07-14, `7dc0d9b`) writes
`.github/workflows/ci.yml`. Either the App gained the scope or those bump PRs
silently fail to push their ci.yml edits. UNRESOLVED — resolve before building
anything that assumes the fan-out can write workflow files.

### A documentation discrepancy worth correcting

`bump-pin-from-dispatch.yml`, `reusable-bump-pin-from-dispatch.yml:38`, and
`reusable-pin-freshness.yml:52,60` all claim the workflow "runs `just check` to
verify the consumer's checks still pass." **No such step exists.** The action
deliberately never runs the consumer's `just check`
(`bump-pin-rewrite/action.yml:26-32`); the consumer's own PR CI is the sole
gate. The prose is stale and misleads anyone reasoning about what the fan-out
verifies.

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

## ALREADY DONE — six items the ledger still shows as open work

**This supersedes six `CHILD` rows in the disposition table below.** Each fix
commit was independently verified in this session as an ancestor of its repo's
`origin/master` (`git merge-base --is-ancestor <sha> origin/master`).

| Item | Tenant | Fixed by | Date |
|---|---|---|---|
| `livespec-dev-tooling-adqmnm` | dev-tooling | `8975025` "reconcile canonical check wiring in bump pins" (+ `d90494b`) | 2026-07-09 |
| `livespec-dev-tooling-q9a` | dev-tooling | `5693955` "exclude world-gate checks from ci-matrix-completeness" | 2026-07-10 |
| `livespec-dev-tooling-fz4` | dev-tooling | `ebf54cc` "cover fabro-sandbox docker image tag as the 5th bump-pin format" | 2026-07-12 |
| `livespec-dev-tooling-u0x` | dev-tooling | `7dc0d9b` "reconcile the consumer ci.yml canonical matrix in the pin bump" | 2026-07-14 |
| `livespec-dev-tooling-xb7` | dev-tooling | `b0c320d` "walk the fabro-sandbox CI container image pin (xb7)" | 2026-07-19 |
| `livespec-o0x1` | livespec core | fan-out now runs the consumer's own `stamp-canonical-slugs` — verified live at `bump-pin-rewrite/action.yml:379` | 2026-07-10 |

`livespec-dev-tooling-9j8.1` (the ported pin-rewriters) was already closed in
the ledger 2026-07-15, and the port is verified: a self-guarding regression
test asserts `"python - <<PYEOF" not in text` against the live `action.yml`, so
reintroducing a heredoc fails master.

**The consequence for this thread's shape.** The original draft framed this as
a build job. It is substantially a **ledger-reconciliation and closure** job
plus a small number of genuinely-open defects. Note especially that `adqmnm` —
the settled "fan-out writes the wiring" decision the plan was written to
honor — has ALREADY SHIPPED, and its `blocked-reason:needs-human` is stale
because its blocking dependency `9j8.1` closed. Do not re-implement it.

**Do not bulk-close these.** Each fix commit is verified to exist on master,
but whether it fully satisfies that item's written acceptance criteria is a
per-item judgment. Closing them is scoped into `livespec-xw65el`.

## Existing ledger items and their disposition

Consolidation verdicts proposed by this thread. `CHILD` = becomes a child of
this thread's epic largely as-is; `KEEP SEPARATE` = linked, not owned.
**Six rows below are SUPERSEDED by §"ALREADY DONE" above** — where the two
disagree, the ALREADY DONE section is correct.

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

## Boundary with the console's `cockpit-ux-docs-release` thread

Maintainer-directed check, 2026-07-19: **this thread must not overlap
`livespec-console-beads-fabro:plan/cockpit-ux-docs-release/`.**

There is exactly ONE contact point, and it is a real one. Both threads edit
`crates/console-completeness-check/src/lib.rs`:

| Thread | Edit site | Concern |
|---|---|---|
| cockpit **B6** | ~line 165 (the settings-doc anchor + its README doc-comment) | WHICH documentation surface the key-coverage check reads — repointing README → `docs/detailed-usage.md`, per ratified spec v029 |
| this thread (`…-tafkuw`) | lines 366–400 (`captured_at_pin` / `check_pin`) | WHEN the pin stamp invalidates the captured fixture |

**Same file, ~200 lines apart, different functions, different concerns.** This
is a sequencing and merge-conflict risk, NOT duplicated work — neither thread
can do the other's job.

**Resolution — B6 goes first, unconditionally.** Its spec is already ratified
(console `SPECIFICATION/history/v029/`) and its impl is the next deliverable in
the cockpit thread's own RESUME ORDER. `…-tafkuw` is `blocked`/needs-grooming
regardless, so it cannot start first anyway. Whoever grooms `…-tafkuw` MUST
first confirm B6's impl has landed on console master, then rebase onto it.

**What this thread must NOT do in the console repo:** touch the `docs/` tree,
the settings-doc anchor, the Scenario 22 structural test, the README, or
anything else in the cockpit thread's B6/B7/B8 scope. Its console footprint is
confined to the pin-staleness semantics of `check_pin` and the fixture it
reads. Conversely, the cockpit thread owns no pin-propagation concern; the 12
stale console bump PRs are this thread's, not B6's.

## Boundary with the CI-substrate thread

`plan/fabro-ci-image-factoring/` owns the CI **substrate** — baked images,
hot runners, resource-health-gated rollout. This thread owns **pin
propagation and the gates pin bumps break**. They meet at exactly one seam:
the image tags are themselves unmanaged pins (`fz4`, `xb7`). Those items are
owned here; what goes *inside* an image is owned there. Maintainer-confirmed
scope boundary, 2026-07-19.

## Recovered inventories — provenance and residual unknowns

The three inventories folded into this note were produced by research agents
whose reports never reached the driver session (a harness fault: agents running
the driver's own model completed their work but their final message was not
delivered; agents on a different model delivered normally). They were recovered
from the agent transcripts. Every load-bearing claim taken from them —
the six ALREADY DONE fix commits, the `7wy` non-reproduction, the B6/`tafkuw`
edit sites — was INDEPENDENTLY RE-VERIFIED in this session before being written
here. Claims NOT independently re-verified are marked as such below.

Their own explicitly-flagged unknowns, carried forward rather than dropped:

- **How a red bump PR reached `livespec` master.** `f5380aa8` (a
  dev-tooling pin bump) landed despite `check-canonical-slugs-projection`
  already being wired into both `just check` and `ci.yml`; the restamp repair
  came 4 commits later. Actions history for those SHAs has aged out, so the
  mechanism is undetermined — candidates are a warm uv cache resolving the old
  dev-tooling, or a required-checks configuration not including the failing
  context. **Decision-relevant:** if auto-merge genuinely gates, the (a) class
  is PR-only annoyance; if not, it reddens master and trips
  `check-master-ci-green`, blocking the repair push.
- **Adopter ledgers were unreachable** (`Access denied` per-tenant; the fleet
  wrapper does not carry their passwords), so no adopter work-items appear in
  any disposition here. The adopter fan-out gap above is from committed state,
  not from their ledgers.
- **`_vendor` exclusion completeness** for `partition_completeness` and
  `tests_mirror_pairing` was not exhaustively verified.
- Several dev-tooling items in the recovered consolidation map were listed from
  `bd list` without pulling full bodies, so their scope lines are
  title-derived. NOT independently re-verified.

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
