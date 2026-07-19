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
   NOT be re-litigated.

That is the whole chain. Everything needed to pick up the next action is in
those two files plus the ledger.

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

## Filed this session (children of `livespec-n4ptl2`)

Cited read-only; check live status in the ledger before acting.

| Item | Tenant | Covers |
|---|---|---|
| `livespec-xw65el` | livespec (core) | Classify every consumer-side gate as (a)-derivable or (b)-needs-live-system — **groomed out 2026-07-19**; superseded by the three slices below |
| `livespec-dev-tooling-q37xxt` | livespec-dev-tooling | Fan-out never closes superseded bump PRs |
| `livespec-dev-tooling-y6kqgr` | livespec-dev-tooling | Fan-out opens duplicate PRs for the same version |
| `livespec-console-beads-fabro-tafkuw` | livespec-console-beads-fabro | The console's captured-manifest gate; the one real blockage |

Each needs a grooming pass before it can be dispatched, because none carries
an autonomy tier yet — the same posture as `livespec-dev-tooling-adqmnm`,
whose description ends "Autonomy tier at groom."

**Correction, verified against the live ledger 2026-07-19.** An earlier
revision of this file claimed all four were routed to status `blocked` with
`blocked_reason: needs-human`. They were not: in the core tenant
`livespec-xw65el`, `livespec-o0x1`, `livespec-p9s0` and the epic itself all
read plain `backlog` with `blocked_reason: null`. Read status from the ledger,
never from this file — which is why this file does not carry a status column.

`livespec-xw65el` carried a mechanical `parent-child` edge to the epic (now
inherited by its groom slices; see below). The epic ALSO carries typed
`sibling_work_item` `depends_on` edges to the three cross-tenant children —
epic→child, the direction open question 1 below speculates may be correct —
so that question is further along than its text implies.

## Pre-existing items this thread absorbs

Not re-filed; they stay in their own tenants. Verdicts and justification are
in the diagnosis note's disposition table.

Absorbed as children in spirit: `livespec-dev-tooling-adqmnm`,
`livespec-dev-tooling-fz4`, `livespec-dev-tooling-xb7`,
`livespec-dev-tooling-p73`, `livespec-dev-tooling-u0x`, `livespec-o0x1`,
`livespec-p9s0`, `livespec-console-beads-fabro-7wy`.

Linked but NOT owned: `livespec-dev-tooling-9j8.6` (CI-logic extraction epic —
this thread depends on it, must not absorb it), `livespec-dev-tooling-q9a`
(CI-matrix hygiene, not pin propagation).

## Groomed 2026-07-19 — `livespec-xw65el` decomposed into three slices

`livespec-xw65el` was groomed (maintainer-approved cut) and is now `done`
with resolution `no-longer-applicable` — regroomed out, not dropped. It was
replaced by three slices in the `livespec` core tenant, each carrying a
`parent-child` edge to the epic:

| Slice | Status at filing | Deps | Produces (under `plan/fleet-pin-propagation/research/`) |
|---|---|---|---|
| `livespec-e7lanq` | `ready` | none | `gate-inventory.md` — every gate enumerated, each candidate or excluded-with-reason |
| `livespec-u7x5zn` | `pending-approval` | blocked by `livespec-e7lanq` | `gate-classification.md` — the (a)/(b) call per candidate |
| `livespec-b7ropo` | `ready` | none | `reverse-hazard.md` — upstream checks that TIGHTEN |

Two facts about that table that will otherwise look like defects:

- **`livespec-u7x5zn` at `pending-approval` is correct-by-design**, not a
  stuck valve. It cleared all six intake Definition-of-Ready gates, but the
  intake router deliberately keeps any dependency-linked item out of direct
  `ready` routing regardless of admission policy. It moves to `ready` on the
  `approve:` valve once `livespec-e7lanq` lands.
- **The slices did NOT inherit the epic edge automatically.**
  `file_approved_slices` filed them unlinked to `livespec-n4ptl2`; the three
  `parent-child` edges were added afterward with direct `bd dep add`. This is
  the same store-wrapper class of gap as open question 2 below. Adding a
  `parent-child` edge does not gate a slice — `ready` survived it.

**Why the cut.** The sweep is far larger than the item implied: measured
2026-07-19 from `git show origin/master:justfile` on each member clone, the 8
members carry **106 distinct `check-*` recipe names** across ~490 instances
plus 72 workflow files, with only 6 gate names universal and 37 repo-local.
The earlier undivided attempt returning no usable output is consistent with
that scale. So slice 1 is purely mechanical enumeration, slice 2 is judgment
over slice 1's bounded output, and slice 3 — the reverse hazard, previously a
sub-bullet a dispatched agent would likely skip — is broken out as an
independent search.

**Adopter scope, resolved 2026-07-19 — do not re-litigate.** The manifest's
`adopters` (`openbrain`, `resume`, `homelab`) are OUT of scope. Nothing in
`livespec-dev-tooling` consumes `manifest.adopters`; `merged_branch_sweep`,
`fleet_conformance`, and `wire_fleet_member` all iterate `.members` only, so
adopters are not fan-out targets. The sweep is the 8 `fleet[]` members.

## NEXT ACTION

**Dispatch `livespec-e7lanq` and `livespec-b7ropo`** — both `ready`, neither
depends on the other, so send them in parallel. Then `approve:`
`livespec-u7x5zn` once `livespec-e7lanq` lands.

They are first because every other decision in this thread depends on the
sweep's output: until the (a)/(b) classification exists, we do not know how
many gates are in the (b) class that the settled "fan-out writes the wiring"
mechanism cannot serve. The current belief — that the console's captured
manifest is the only one — is UNPROVEN; it is merely the only one found so far.

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

## Open questions this thread owes the maintainer

1. **Cross-tenant epic links.** Three of the four children live in other beads
   tenants, and beads `parent-child` edges do not span tenants. The typed
   `sibling_work_item` dependency kind exists in `livespec_runtime`'s
   cross-repo types and would express it, but it requires the target repo to
   be a key in the citing repo's `.livespec.jsonc` `cross_repo_targets` —
   and core currently declares only `livespec` and
   `livespec-orchestrator-git-jsonl`. Adding `livespec-dev-tooling` there has
   a **No-Circular-Dependency dimension** (`.ai/no-circular-dependency.md`):
   the natural edge direction is child→epic, i.e. an upstream repo's item
   referencing a downstream consumer's, which is the direction the directive
   forbids. Inverting to epic→children keeps the reference pointing upstream
   and may be the correct modeling. NOT resolved — deliberately left for the
   maintainer.

   **Observed 2026-07-19, after this question was written.** The epic
   `livespec-n4ptl2` ALREADY carries three typed `sibling_work_item`
   `depends_on` edges — to `livespec-dev-tooling-q37xxt`,
   `livespec-dev-tooling-y6kqgr`, and `livespec-console-beads-fabro-tafkuw`.
   That is the epic→children inversion this question proposes, already wired.
   Two things follow, neither resolved:
   - `livespec-dev-tooling` and `livespec-console-beads-fabro` are still NOT
     keys in core's `.livespec.jsonc` `cross_repo_targets` (which declares
     only `livespec` and `livespec-orchestrator-git-jsonl`), so those edges
     name undeclared targets. `just check-doctor-static` passes regardless —
     it validates spec structure, not work-item dep targets — so nothing
     currently catches the mismatch. Either the declarations are owed, or the
     `cross_repo_targets` requirement in `livespec_runtime/cross_repo/types.py`
     is unenforced for this path; which of those is the intended design is the
     maintainer's call.
   - The No-Circular-Dependency dimension is unchanged and still the crux.
2. **Store-wrapper gap (candidate for `.ai/beads-gaps-workarounds.md`).**
   `append_work_item` hardcodes `--type blocks` for every `depends_on` entry,
   but beads rejects a task blocking an epic ("tasks can only block other
   tasks, not epics"). So the wrapper CANNOT file a child linked to an epic in
   one call — the item is created, then the edge fails, leaving a partially
   linked record. Worked around here by filing without `depends_on` and adding
   the `parent-child` edge with a direct `bd dep add`. This is a genuine
   upstream-liftable gap.
3. **Re-scoping `livespec-o0x1`.** Its acceptance criteria are written
   narrowly for the `canonical-slugs.yml` instance, but the defect is the
   whole (a)-class. Re-scope it to the class, or keep it narrow and let the
   sweep file siblings — a judgment call, unresolved.

## What could invalidate the plan

The superseded-PR count is a snapshot and drifts upward as the fan-out keeps
opening PRs. CI logs older than roughly a day have aged out on the self-hosted
runners, so historical red PRs can no longer be diagnosed from their logs —
re-run a check to observe a live failure rather than trusting a reconstructed
cause. And the (a)/(b) sweep is genuinely not done: an earlier dispatched
attempt returned no usable output, so treat its absence as absence.
