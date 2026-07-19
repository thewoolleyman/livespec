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
in the diagnosis note's disposition table.

Absorbed as children in spirit: `livespec-dev-tooling-adqmnm`,
`livespec-dev-tooling-fz4`, `livespec-dev-tooling-xb7`,
`livespec-dev-tooling-p73`, `livespec-dev-tooling-u0x`, `livespec-o0x1`,
`livespec-p9s0`, `livespec-console-beads-fabro-7wy`.

Linked but NOT owned: `livespec-dev-tooling-9j8.6` (CI-logic extraction epic —
this thread depends on it, must not absorb it), `livespec-dev-tooling-q9a`
(CI-matrix hygiene, not pin propagation).

## NEXT ACTION

**Groom `livespec-xw65el`** (the gate-classification sweep), then dispatch it.

It is first because every other decision in this thread depends on its output:
until the (a)/(b) classification exists, we do not know how many gates are in
the (b) class that the settled "fan-out writes the wiring" mechanism cannot
serve. The current belief — that the console's captured manifest is the only
one — is UNPROVEN; it is merely the only one found so far.

Grooming route: the `groom` operation on `livespec-xw65el`. The maintainer
owns the cut.

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
cause. And the (a)/(b) sweep is genuinely not done: an earlier dispatched
attempt returned no usable output, so treat its absence as absence.
