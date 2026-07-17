# factory-safe-by-default — planning handoff

**Thread summary:** invert livespec's factory doctrine to **factory-safe by
default** — assume any work-item runs in the factory, require a machine-readable
admission-enforced opt-out for a small enumerable host-only residue, widen
factory capability so that residue stays tiny, and give the residue a home as a
distinct needs-attention host-only-action kind. The design was **reshaped
2026-07-17** against the live code + ratified spec into a **two-orthogonal-axes**
model (maintainer-endorsed); the slices are filed. See `research/design.md`
§"Reshape (2026-07-17)".

The single resumable entry point for this thread: a fresh session can execute
the next action from this file alone via the read-first chain — no chat history
required.

## Read-first chain (open these, in order, before acting)

1. **The ledger epic `livespec-nrdk`** (livespec core tenant) — read status AND
   its comments **LIVE from the ledger**, never trust a status written in this
   file. The 2026-07-17 slicing comment records the filed children + the Slice-A
   route + the Slice-D decision:
   ```bash
   source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-nrdk
   ```
2. **`research/design.md`** §"Reshape (2026-07-17)" — the settled, code-grounded
   design: why the fail-fast gate already ships but the classification does not,
   the spec-vs-code contradiction, the two-axis resolution (`admission_policy` =
   permission vs. `factory_safety` = runnability), the label-prefix encoding, the
   cross-repo cost, and the settled A/B/C/D cut. (The earlier sections above it —
   the 2026-07-07 two-classes analysis and four moves — remain valid background.)

## Current state

Thread opened 2026-07-07; reshaped + sliced 2026-07-17. Status is **derived from
the ledger** — read it live via the read-first chain, do not trust any value
copied here. Filed under epic `livespec-nrdk`:

- **Slice A — spec contract. NOT a ledger item; NOT started.** The foundational
  piece: route via `/livespec:propose-change` in
  `livespec-orchestrator-beads-fabro`.
- **Slice B — `bd-ib-fv6wse`** (bd-ib / livespec-orchestrator-beads-fabro tenant,
  `backlog`): the `factory_safety` field + admission gate reads it. Cross-repo →
  awaits groom. Blocked-in-prose on A.
- **Slice C — `bd-ib-i6wfum`** (bd-ib tenant, `backlog`, `depends_on` B): the
  host-only needs-attention kind. Awaits B + groom.
- **Slice D — capability-widening (move #3): stays under `z2ctra`**, coordinated
  not absorbed. No new item here (recorded as the epic comment).

Cross-tenant note: B/C live in the bd-ib tenant, not the core tenant that holds
the epic — so `livespec-nrdk`'s %Complete tracks neither; they associate to the
epic by prose (the livespec-bj9x precedent).

## Resume command

```
/livespec-orchestrator-beads-fabro:plan factory-safe-by-default
```

## Next actions (in order)

1. **Slice A — file the spec contract change (FOUNDATIONAL, do this first).**
   Run `/livespec:propose-change` against `livespec-orchestrator-beads-fabro`'s
   `SPECIFICATION` to codify: (a) the first-class `factory_safety` opt-out field
   (3-reason enum `{needs-host-secrets, mutates-host-machinery,
   needs-privileged-host}`, label-prefix encoded like the six existing prefixes),
   (b) a CORRECTION of the false clause in `contracts.md` §"Admission valve
   (ready → active)" (~L1362) claiming `admission_policy` "replaces the prior
   host-only marker" — they are ORTHOGONAL axes (permission vs. runnability),
   (c) the `ready → active` refusal keys on `factory_safety`, cross-referencing
   the already-ratified "`--item` narrows-never-bypasses" rule (§"Dispatcher loop
   invocation surface", ~L1265). Then the mandatory **independent Fable review**
   (read-only) BEFORE `/livespec:revise` accepts it. Remember the
   `tests/heading-coverage.json` co-edit if any `## ` heading changes.
2. **After A ratifies: groom then dispatch B, then C.** `/livespec-orchestrator-beads-fabro:groom bd-ib-fv6wse`
   to cut B's cross-repo ready slices (runtime field first, then beads-fabro
   store/gate, then git-jsonl codec pop — the bj9x foundational-first order), then
   dispatch each ready slice **factory-side via the Dispatcher drain or
   `/livespec-orchestrator-beads-fabro:drive --action impl:<id>`** — never
   in-session implement. Repeat for C once B lands.
3. **Slice D stays under `z2ctra`** — no action here beyond the recorded
   coordination; the capability-widening work is driven from that item.

**Golden rule:** FILE ripe work + GROOM it; never hand-code factory-safe
implementation inline in the planning session. Spec-side contract changes go
through the normal `/livespec:*` lifecycle (propose-change → independent Fable
review → revise); ledger slices are built factory-side (Dispatcher / `drive`)
under the janitor gate.

## Standing constraints

- Status is derived from the ledger, never stored here (no shadow queue).
- Repo mutations: worktree → PR → rebase-merge; `mise exec -- git`; never
  `--no-verify`; doc-only plan edits use a `docs(plan): ...` subject.
- Ripe work is built factory-side under the janitor gate, never hand-coded.
