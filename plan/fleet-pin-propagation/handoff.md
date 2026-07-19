# fleet-pin-propagation — handoff

**Ledger anchor:** epic `livespec-n4ptl2` (livespec CORE tenant).
**Opened:** 2026-07-19.

Status is READ from the ledger, never stored here. This file carries no
checkbox queue.

**Composing status.** Each operation named in this file is a skill of the
`livespec-orchestrator-beads-fabro` plugin — invoke as
`/livespec-orchestrator-beads-fabro:<operation>` (`list-work-items`, `next`,
`groom`, `drive`). Each repo is its OWN beads tenant and the read surfaces
resolve the tenant from the working directory, so to read a non-core tenant,
run from that repo's clone (`/data/projects/<repo>`) — there is no `--repo`
flag on `list-work-items`. This thread spans three tenants: `livespec`,
`livespec-dev-tooling`, `livespec-console-beads-fabro`.

**"Autonomy tier"** is the per-item dispatch-eligibility rating assigned
during the `groom` operation, with the maintainer owning the call; an item
without one cannot be dispatched. The vocabulary is the orchestrator's, not
this thread's — read it from the `groom` operation and from a groomed
exemplar in the ledger rather than from this file, which deliberately does
not restate it. Every item this thread filed carries the marker
"Autonomy tier at groom." for exactly this reason, matching
`livespec-dev-tooling-adqmnm`.

## Read-first chain

1. This file.
2. `plan/fleet-pin-propagation/research/diagnosis.md` — the measured evidence,
   the classification axis every decision turns on, the consolidation verdicts
   for the ten pre-existing ledger items, and the settled decisions that must
   NOT be re-litigated. **Start with its "⚠ MAJOR REVISION" section**, which
   corrects four load-bearing claims from the first draft.

That is the whole chain. Everything needed to pick up the next action is in
those two files plus the ledger.

Optional depth, not required to act:
`plan/fleet-pin-propagation/research/recovered/` holds the three raw research
inventories the diagnosis summarizes — per-gate `file:line` citations, the full
pin-format table, and each agent's own flagged unknowns. Read them when you
need evidence behind a specific claim; the diagnosis note is the authority.

## What this thread owns

Fleet-wide **pin propagation** and the **consumer-side gates that pin bumps
break** — every pin format, including the image-tag pins.

It does NOT own `plan/fabro-ci-image-factoring/`, which owns the CI substrate
(baked images, hot runners, resource-health-gated rollout). The two threads
meet at exactly one seam: image tags are themselves unmanaged pins, and those
items (`livespec-dev-tooling-fz4`, `livespec-dev-tooling-xb7`) are owned HERE
while what goes *inside* an image is owned THERE. Scope boundary confirmed by
the maintainer 2026-07-19.

## The situation in one paragraph

41 open pin-bump PRs across 8 member repos, every master green. Those two
facts together are the diagnosis: the fleet is green *at rest* but cannot
absorb propagation, and the green masters are what hid it. The 41 are not 41
breakages — ~29 are superseded PRs nothing ever closed, and exactly one repo
(`livespec-console-beads-fabro`) is genuinely blocked, 12 releases behind,
by a gate the fan-out structurally cannot satisfy. Do not read the red check
names on a superseded PR as a symptom list; its branch is simply stale.

**The noise half is now CLEARED (2026-07-19).** The paragraph above is the
original diagnosis and is kept for the reasoning; the counts in it are
historical. Re-measured immediately before cleanup: **43** open bump PRs, not
41 — it had drifted up by 2 exactly as predicted. Each was classified
individually (target version vs. the version its own master carries for the
same source repo): **30 provably superseded, 13 not, 0 ambiguous.** The 30 were
closed with an explanatory comment and their branches deleted.

**Fleet-wide open bump PRs: 43 → 13. Seven of eight member repos now carry
ZERO.** All 13 remaining are `livespec-console-beads-fabro`, so "exactly one
repo is genuinely blocked" is now directly visible in the PR listing instead of
buried under the noise. Subsequent fleet sweeps read true.

**A third supersession category the diagnosis did not name.** Of those 13
console PRs, only **one** is genuinely live — `#320`, targeting the latest
`v0.18.2`. The other **twelve** are superseded by a *newer open sibling PR*
rather than by master (console pins core at `v0.16.0`; they target `v0.17.0` ..
`v0.18.1`, all newer than the pin but older than #320). So:

| Category | Count | Disposition |
|---|---|---|
| Superseded by master | 30 | CLOSED by this pass |
| Superseded by a newer OPEN sibling PR | 12 | left open deliberately |
| Genuinely live | 1 (console `#320`) | left open |

The twelve were left open on purpose: they are the console's own blocked pin
train, and collapsing it belongs to `livespec-console-beads-fabro-tafkuw`, not
to the cleanup. **Whoever implements the `livespec-dev-tooling-q37xxt`
automation must handle BOTH supersession categories**, or the console
re-accumulates a stack the moment it unblocks.

The one-time cleanup is DONE and journaled on `livespec-dev-tooling-q37xxt`;
that item now tracks the AUTOMATION only. The same pass also confirmed
`livespec-dev-tooling-y6kqgr`'s duplicate defect live: `livespec-runtime`
#206/#208 both targeted dev-tooling `v0.44.0`, and #207/#209 both targeted core
`v0.10.1`.

## Filed this session (children of `livespec-n4ptl2`)

Cited read-only; check live status in the ledger before acting.

| Item | Tenant | Covers |
|---|---|---|
| `livespec-xw65el` | livespec (core) | Classify every consumer-side gate as (a)-derivable or (b)-needs-live-system |
| `livespec-dev-tooling-q37xxt` | livespec-dev-tooling | Fan-out never closes superseded bump PRs |
| `livespec-dev-tooling-y6kqgr` | livespec-dev-tooling | Fan-out opens duplicate PRs for the same version |
| `livespec-console-beads-fabro-tafkuw` | livespec-console-beads-fabro | The console's captured-manifest gate; the one real blockage |

All four were routed by the intake Definition-of-Ready checklist to the single
status `blocked`, carrying `blocked_reason: needs-human` (one status plus a
reason, not two statuses), because they carry no autonomy tier yet — the same
posture as `livespec-dev-tooling-adqmnm`, whose description ends "Autonomy
tier at groom." Each needs a grooming pass before it can be dispatched.

All four are mechanically linked to the epic, in two different ways because
beads edges do not span tenants:

- `livespec-xw65el` (same tenant) — a native beads `parent-child` edge, so it
  renders indented under the epic in `bd list`.
- The other three (other tenants) — typed `sibling_work_item` entries in the
  EPIC's `depends_on`, riding in beads metadata under `non_local_depends_on`
  and resolved by livespec's cross-repo layer. Core's `.livespec.jsonc`
  `cross_repo_targets` declares both tenants so the refs resolve.

The directions differ (child→epic for the local edge, epic→children for the
sibling refs) purely because of that tenant boundary; both are correct. Per
`.ai/no-circular-dependency.md` §"Scope", direction carries no
circular-dependency significance for ledger records.

## Pre-existing items this thread absorbs

Not re-filed; they stay in their own tenants. Verdicts and justification are
in the diagnosis note.

**ALREADY FIXED on master — close-or-narrow, do not implement** (fix commits
verified as ancestors of `origin/master`; per-item acceptance check is scoped
into `livespec-xw65el`): `livespec-dev-tooling-adqmnm` (`8975025`),
`livespec-dev-tooling-q9a` (`5693955`), `livespec-dev-tooling-fz4`
(`ebf54cc`), `livespec-dev-tooling-u0x` (`7dc0d9b`),
`livespec-dev-tooling-xb7` (`b0c320d`), `livespec-o0x1` (fan-out stamps at
`bump-pin-rewrite/action.yml:379`).

**Genuinely open, absorbed as children in spirit:** ~~`livespec-p9s0` (stale
local-clone false reds), `livespec-dev-tooling-p73` (pin-freshness
first-record blind spot).~~ — see the verification sweep below; `p73` is closed,
`p9s0` is confirmed live.

**Premise does not reproduce — re-derive or close:**
`livespec-console-beads-fabro-7wy`.

### Verification sweep, 2026-07-19/20 — every remaining item checked live

Each was re-verified against `origin/master` before any disposition, because six
items in this thread had already turned out to be stale records. The sweep found
the population genuinely mixed — one fixed, one live, one settled, one stale
evidence — which is why "verify before implementing" is the standing rule here.

| Item | Verdict | Evidence |
|---|---|---|
| `livespec-dev-tooling-p73` | **CLOSED — already fixed** | The `.[0].current_value` jq collapse is gone; selection now comes from the tested `pin_staleness` module, and the surviving comment names the item by id as the resolved cause. Fix `4ad8344`, confirmed an ancestor of `origin/master` |
| `livespec-p9s0` | **LIVE — do not assume fixed** | Path A still does `git -C <local_clone> show HEAD:justfile`; the GitHub-API read is only a FALLBACK taken when Path A *fails*, so a stale-but-valid clone never reaches it |
| `livespec-console-beads-fabro-tafkuw` | **LIVE, and its owed design decision is now SETTLED** | See the diagnosis note's §"scope question" — the stamp is keyed to the core pin while the fixture depends on the orchestrator's key set, whose two emitting modules have 1 and 2 commits ever |
| `livespec-dev-tooling-tuyje7` | **LIVE** | All three workflow files still claim `just check` runs; `bump-pin-rewrite/action.yml` explicitly documents that it deliberately does NOT run the consumer's `just check` |
| `livespec-dev-tooling-f5or5c` | **EVIDENCE STALE, framing too strong — NOT closed** | Claimed producer at `python-v0.43.2` vs consumers `v0.49.2`; both now `python-v0.50.3`. Self-bumps DO happen and ARE automated (`4f47762`, bot-authored). Real defect is SPORADIC-WITH-SKIPS (v0.46.5 → v0.50.1 skipped v0.47–v0.49), not absent |

`livespec-p9s0` gained a new dimension worth carrying: it and `livespec-fxxfq6`
are two faces of one weakness — the cross-repo wiring check's notion of "the
sibling's state" is **environment-dependent**, reading local clone `HEAD`
locally and a fresh clone in CI. That split is exactly why the 2026-07-19
breakage blocked every local push while master CI stayed green. Fix either with
the other in view.

Linked but NOT owned: `livespec-dev-tooling-9j8.6` (CI-logic extraction epic —
this thread depends on it, must not absorb it), `livespec-dev-tooling-q9a`
(CI-matrix hygiene, not pin propagation).

## ⚠ TWO SESSIONS ARE IN THIS EPIC — read before dispatching anything

A second session groomed `livespec-xw65el` into three replacement slices
(`livespec-e7lanq`, `livespec-u7x5zn`, `livespec-b7ropo`) while this session
was working. **Dispatch is theirs**; maintainer-directed 2026-07-19, this
session stood down from dispatching rather than risk duplicate worktrees and
conflicting closes.

**RESOLVED — the grooming session dispatched them, so this coordination note is
now history rather than an open hazard.** `livespec-e7lanq` and
`livespec-b7ropo` are both merged (PRs #1459 / #1462); `livespec-u7x5zn` waits
on the acceptance gate. No duplicate worktrees or conflicting closes occurred.
See §"NEXT ACTION" for the single remaining human step.

**The groom was cut against a STALE diagnosis** — it predates the recovery, so
each slice carried "treat the earlier attempt's absence as absence," which is
no longer true. All three bodies have since been corrected, in two different
ways (maintainer-approved 2026-07-19; the CUT was left intact, since grooming
is maintainer-owned):

- `livespec-e7lanq` and `livespec-u7x5zn` were **fully re-scoped**, not merely
  annotated. `e7lanq` now verifies and completes the recovered 12-gate table
  instead of producing it. `u7x5zn` was re-scoped twice: its second body told
  an agent to close six items and file three gaps that a Fable review then
  found were ALREADY closed and filed (handoff §"COMPLETED 2026-07-19"), so it
  now carries only the genuine residue — naming the 4 (b)-class gates as owing
  design decisions, and chasing the `u0x` facet-(b) and `o0x1` residues.
- `livespec-b7ropo` keeps its original scope (the reverse-hazard search is NOT
  covered by the recovery) with a `READ FIRST` correction: its worked example
  `livespec-console-beads-fabro-7wy` is DISPROVEN and closed, so the sweep
  starts from zero confirmed instances, and its acceptance now admits a
  zero-instance outcome as a valid result.

**Anyone dispatching those slices must read the current bodies, not the
original framing** — two of them would otherwise re-derive an inventory already
committed to master, or re-close closed items.

That session also contributed a measurement this thread lacked: the 8 members
carry **106 distinct `check-*` recipe names across ~490 instances**, of which
only 6 names appear in all 8 repos and 37 are repo-local. That is the
UNFILTERED universe; the recovered inventory's 12 is the pin-bump-reachable
SUBSET. Reconciling those two numbers is the sharpest remaining sweep task.

## NEXT ACTION

**Blocked on the maintainer — TWO acceptances, then a grooming queue.** The
grooming session dispatched both `READY` slices; both are merged and their
artifacts are on master. No further work here is agent-eligible.

**Correction:** an earlier revision of this section said "one acceptance". It is
**two** — `livespec-e7lanq` AND `livespec-b7ropo` are both at `acceptance`.
Verified live 2026-07-20.

Everything else in the thread has now been re-verified against `origin/master`
and needs exactly one thing: **grooming**, which is maintainer-owned by design
(the `groom` operation's cut belongs to the maintainer, and none of these items
carries an autonomy tier yet). The evidence work is done; the cuts are not.

Ids are written tenant-prefixed IN FULL, and each tenant repo is named in full,
because this queue spans three tenants and a bare suffix cannot be turned into a
command. Read each tenant from its own clone (`/data/projects/<repo>`) — the read
surfaces resolve the tenant from the working directory.

| Item | Tenant repo | Verified state | What grooming must decide |
|---|---|---|---|
| `livespec-fxxfq6` | `livespec` | backlog | Which of the two fixes; **both are single-repo edits** (the "cross-repo + pin bump" claim was false). Re-read its corrected workflow-permission paragraph first |
| `livespec-p9s0` | `livespec` | LIVE | Whether to make the canonical ref the default rather than the fallback. Design with `livespec-fxxfq6` in view — same weakness |
| `livespec-bg47fr` | `livespec` | LIVE, understated | Whether adopters get the SAME fan-out as members or only a staleness signal. Note `openbrain` is at `v0.6.10` — staler than `resume`, and the body never measured it |
| `livespec-console-beads-fabro-tafkuw` | `livespec-console-beads-fabro` | LIVE, design settled | Only the implementation shape remains; the invalidation-trigger question is answered (see diagnosis §"scope question") |
| `livespec-dev-tooling-q37xxt` | `livespec-dev-tooling` | backlog CLEARED | Automation only. Must handle BOTH supersession categories |
| `livespec-dev-tooling-y6kqgr` | `livespec-dev-tooling` | CONFIRMED live | Dedupe design; co-design with `livespec-dev-tooling-q37xxt` — same `(source_repo, target_version, consumer)` tuple |
| `livespec-dev-tooling-tuyje7` | `livespec-dev-tooling` | CONFIRMED live | Docs-vs-implementation contradiction; decide whether to fix the prose or add the step |
| `livespec-dev-tooling-f5or5c` | `livespec-dev-tooling` | evidence STALE | **Re-scope before grooming** — "nothing fans out to it" is wrong; the real defect is sporadic-with-skips |

**A trap for whoever grooms `y6kqgr` or `q37xxt`:** the duplicate-PR evidence is
no longer observable in the open-PR population, because that population went
43 → 13 and the four PRs that demonstrated it (`livespec-runtime` #206–#209) are
among the 30 closed. Validate a fix against the fan-out's dedupe logic or the
next real releases — **not** by inspecting today's open PRs.

**Accept (or reject) `livespec-e7lanq`.** It sits at `acceptance` under
`acceptance_policy: ai-then-human`; the AI pass verdict was PASS. It was
deliberately NOT self-accepted — that policy exists to require a human, and an
operator accepting on the maintainer's behalf would defeat it.

That one acceptance is load-bearing for the rest of the thread:
`livespec-u7x5zn` is `pending-approval` and NOT rankable, because its blocker
`livespec-e7lanq` must reach `done`, which only the acceptance produces. Note
the `approve:` valve does NOT apply to it — `approve:` requires an
effective-MANUAL item, and `u7x5zn` carries `admission_policy: auto`, so it
routes itself into `ready` once the dependency clears. Do not try to force it.

| Slice | State | What landed |
|---|---|---|
| `livespec-e7lanq` | `acceptance` — **awaits human** | PR #1459 (`63c62dc5`) → `research/recovered-gate-verification.md` |
| `livespec-b7ropo` | merged, dispatcher green | PR #1462 (`805a9dcc`) → `research/reverse-hazard.md` |
| `livespec-u7x5zn` | `pending-approval` | blocked until `e7lanq` is `done` |

**What the two artifacts settled:**

- The recovered 12-gate table is VERIFIED against live sibling clones at named
  SHAs — 9 clean, 3 verified-with-correction (reusable-workflow refs and Fabro
  image tags have moved `v0.49.2` → `v0.50.3`). Both (b) classifications held.
  One recovered unknown resolved (`_vendor` is excluded by both
  `tests_mirror_pairing` and `partition_completeness`); the `f5380aa8`
  auto-merge-bypass unknown remains honestly unconfirmable (Actions history
  aged out). No missed gate found, by a stated method — the fan-out's managed
  pin formats compared against the recipes reading those artifacts. That
  negative is scoped to fan-out-managed artifacts, NOT to all ~106 recipes.
- The reverse-hazard sweep found **ZERO live instances**, and that is a real
  result rather than an absence of effort: the dev-tooling canonical check tree
  is byte-identical from every active consumer's pinned ref (`v0.50.3`) to
  `origin/master`, the core doctor static-check tree is byte-identical from
  every consumer's core pin to master INCLUDING the console's older `v0.16.0`,
  and the reusable-workflow callable contracts are unchanged. The disproven
  `…-7wy` example was re-confirmed disproven from a third direction (identical
  tree object `c6e69209…` at both refs).

**A defect found while dispatching — read before trusting any `drive` verdict.**
`drive --action impl:<id>` reported `status: green` / "Dispatcher reported
green" for `livespec-b7ropo` while dispatching NOTHING; the item stayed `ready`.
Cause: `drive`'s impl path runs the dispatcher with `--budget 1 --parallel 1`,
so with another item already `active` there was no capacity, the loop ran zero
iterations, and `commands/drive.py::_dispatch_status` maps an EMPTY journal plus
exit 0 onto `green`. Filed as **`bd-ib-c4jfp6`** in the
`livespec-orchestrator-beads-fabro` tenant. Until it is fixed, **always confirm
a dispatch by re-reading the item's status** — never trust the green alone. The
re-dispatch after capacity freed worked normally.

## COMPLETED 2026-07-19 — the answerable half of `livespec-xw65el`

- **Workflow-permission contradiction RESOLVED.** The fleet App DOES have
  `workflows` permission: `livespec-pr-bot[bot]` authored real `ci.yml` content
  changes that landed on master (`livespec-runtime 0d6b3a2`, bumping the
  container image across two `container:` blocks). The standing "the App
  deliberately lacks `workflows` permission" decision record is STALE for the
  fan-out path, and `adqmnm`'s "never `.github/workflows/`" acceptance clause is
  MOOT rather than violated. **(a)-class auto-fix design may assume the fan-out
  can write workflow files.**
- **Six already-done items CLOSED**, each checked against its own written
  acceptance with per-item evidence — not bulk-closed: `adqmnm` (`8975025`),
  `q9a` (`5693955`), `fz4` (`ebf54cc`, live-exercise satisfied in production by
  console `a6d7221`), `u0x` (`7dc0d9b`), `xb7` (`b0c320d`), `livespec-o0x1`
  (fan-out stamps at `action.yml:379`). Two carry recorded residue rather than a
  clean close: `u0x` facet (b) (ordered cross-repo merge sequencing — no
  evidence of a fix) and `o0x1` (how a red bump PR reached master remains
  undetermined; Actions history aged out).
- **Three new gaps FILED**: `livespec-dev-tooling-f5or5c` (the producer is
  outside its own fan-out), `livespec-dev-tooling-tuyje7` (three workflow files
  document a `just check` step that does not exist),
  `livespec-bg47fr` (no adopter is wired into the fan-out; `resume` 11 minors
  stale).
- **`livespec-console-beads-fabro-7wy` closed by an independent console-side
  session**, which verified zero `§"` marker hits under `crates/**/src/` and
  confirmed `…-tafkuw` is the ONLY console-side gate on the pin train —
  corroborating this thread's byte-identity disproof from the other direction.

**Do NOT re-run the sweep from scratch.**

Grooming route: the `groom` operation on `livespec-xw65el`. The maintainer
owns the cut.

### The single most important correction

Six of the ten pre-existing ledger items this thread set out to absorb are
**already fixed on master** — including `livespec-dev-tooling-adqmnm`, the
settled "fan-out writes the wiring" decision the whole plan was written to
honor. It shipped 2026-07-09 (`8975025`) and its `blocked-reason:needs-human`
is stale because its blocking dependency closed 2026-07-15. **Do not
re-implement it.** This thread is substantially a ledger-reconciliation job
plus a small number of genuinely-open defects, not the build job the first
draft assumed.

### Scope boundary — the console's cockpit thread

`livespec-console-beads-fabro-tafkuw` and the console's
`plan/cockpit-ux-docs-release/` deliverable **B6** both edit
`crates/console-completeness-check/src/lib.rs` — ~200 lines apart, different
functions, different concerns (B6: which doc surface is read; `tafkuw`: when
the pin stamp invalidates). **B6 goes first, unconditionally.** Full boundary
in the diagnosis note; do not start `tafkuw` before B6's impl lands on console
master.

**Implementation route, for this and every item in this thread: the FACTORY.**
Dispatch through the `drive` operation with action `impl:<work-item-id>`, or
let the Dispatcher drain it once it is `ready`. Do NOT hand-code these in a
planning session and do NOT use the in-session Red→Green `implement`
operation — none of these items is recorded as factory-ineligible.

### Recommended order after the sweep

Ids are written tenant-prefixed in full, because this list mixes three
tenants and a bare suffix cannot be turned into a command.

1. `livespec-dev-tooling-q37xxt` (close superseded PRs) — cheapest, and it
   removes the noise that camouflages everything else. Do it early so
   subsequent fleet sweeps read true.
2. `livespec-console-beads-fabro-tafkuw` — the real blockage. Sequence
   `livespec-console-beads-fabro-7wy` before or with it, or the unblock trades
   one red for another.
3. `livespec-dev-tooling-adqmnm` (already-decided (a)-class mechanism) and the
   unmanaged-pin pair `livespec-dev-tooling-fz4` / `livespec-dev-tooling-xb7`.
4. `livespec-dev-tooling-y6kqgr`, `livespec-dev-tooling-p73`,
   `livespec-dev-tooling-u0x`, `livespec-o0x1`, `livespec-p9s0` as the sweep's
   findings rank them.

## Decisions taken (all three open questions RESOLVED 2026-07-19)

1. **Cross-tenant epic links — LINK THEM, in whichever direction is true.**
   An earlier draft of this handoff withheld these links, citing a
   No-Circular-Dependency concern. **That was a misapplication of the
   directive** and the maintainer corrected it: `.ai/no-circular-dependency.md`
   governs CODE and hard dependencies — checks, tools, reads, clones, pinned
   artifacts — NOT work-items. The ledger is a planning tool; a work-item
   dependency states that one piece of work genuinely blocks or contains
   another, and it may point in EITHER direction across repos when that
   relationship is real. No CI clones anything because of a ledger edge, so no
   cycle exists. The directive now carries an explicit scope section saying so.
   Do not re-raise this.
2. **Store-wrapper defect — FILED against the orchestrator plugin.**
   `append_work_item` hardcodes `--type blocks` for every `depends_on` entry,
   but beads rejects a task blocking an epic ("tasks can only block other
   tasks, not epics"), so the wrapper creates the item and THEN fails the edge,
   leaving a partially-linked record. It is our wrapper's defect, not a beads
   gap — beads' restriction is a legitimate upstream constraint the wrapper
   fails to accommodate — so it is filed in the
   `livespec-orchestrator-beads-fabro` tenant, which owns the wrapper, rather
   than catalogued in `.ai/beads-gaps-workarounds.md`. Workaround until fixed:
   file without `depends_on`, then add the edge with a direct
   `bd dep add <child> <epic> --type parent-child`.
3. **`livespec-o0x1` stays NARROW** — its acceptance criteria remain specific
   to the `canonical-slugs.yml` instance until `livespec-xw65el`'s sweep
   reveals how many (a)-class instances actually exist. Deliberately not
   generalized ahead of the data; revisit once the sweep lands.

## What could invalidate the plan

The superseded-PR count is a snapshot and drifts upward as the fan-out keeps
opening PRs. CI logs older than roughly a day have aged out on the self-hosted
runners, so historical red PRs can no longer be diagnosed from their logs —
re-run a check to observe a live failure rather than trusting a reconstructed
cause.

**Superseded 2026-07-19 — this paragraph used to end with a claim that is now
false.** It read: "the (a)/(b) sweep is genuinely not done: an earlier
dispatched attempt returned no usable output, so treat its absence as absence."
The sweep WAS done. Its inventories were lost to a harness fault and have been
RECOVERED into `research/diagnosis.md` (see its ⚠ MAJOR REVISION section):
12 reddenable gates, 8 (a)-derivable / 4 (b)-needs-live-system, adopters zero.
**Do NOT re-run the sweep from scratch** — this file says so above, and the
stale sentence here contradicted it. What remains is verification of the
recovered table, not discovery.
