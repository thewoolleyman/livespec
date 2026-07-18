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

- **Slice A — spec contract. COMPLETE + RATIFIED (2026-07-17).** The two-axis
  model is live spec on `livespec-orchestrator-beads-fabro` master:
  `/livespec:propose-change` filed it (PR #722), independent Fable review passed
  NO-BLOCKERS, and `/livespec:revise` ratified it into
  `SPECIFICATION/history/v040/` (PR #733). The `factory_safety` field, the
  admission_policy-vs-factory_safety two-axis correction, the `ready → active`
  admission refusal, `## Scenario 48`, and the heading-coverage entry are all
  landed. Nothing left on A.
- **Slice B — GROOMED (2026-07-18).** `bd-ib-fv6wse` was regroomed out
  (maintainer-approved cut) into three dependency-layered slices across three
  tenants (bj9x cross-tenant model — **prose** deps, not machine deps, because no
  `cross_repo_targets` manifest declares `livespec-runtime`):
  - **B1 — `livespec-runtime-vkqer3`** (livespec-runtime tenant, **`ready`**):
    add the `factory_safety` field + `FactorySafety` enum to the shared
    `livespec_runtime` `WorkItem`. Foundational, no deps — **dispatch-eligible
    now**.
  - **B2 — `bd-ib-qcnbbp`** (bd-ib tenant, `backlog`): beads-fabro store encoding
    + admission gate (realizes v040 Scenario 48; replaces `is_host_only_item`
    regex; fixes the refusal message; updates the doctor invariant; migrates old
    host-only-marked items). **Prose-blocked on B1** (it re-vendors runtime +
    bumps the pin); promote `backlog → ready` when B1 lands.
  - **B3 — `bd-gj-7adugd`** (bd-gj / livespec-orchestrator-git-jsonl tenant,
    `backlog`): git-jsonl `store_codec` parity (pop-vs-persist is an implementer
    sub-decision). Prose-blocked on B1; promote when B1 lands.
- **Slice C — `bd-ib-i6wfum`** (bd-ib tenant, `backlog`): the host-only
  needs-attention kind. **Re-pointed (prose) to depend on B1**; its stale machine
  edge to the now-closed `bd-ib-fv6wse` is harmless while backlog. Groomed later,
  after B lands.
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

1. **Factory-dispatch B1 `livespec-runtime-vkqer3` (DO THIS FIRST).** It is
   `ready` with no deps. Dispatch it **factory-side** via the Dispatcher drain or
   `/livespec-orchestrator-beads-fabro:drive --action impl:livespec-runtime-vkqer3`
   — never in-session implement. It adds `factory_safety` + `FactorySafety` to the
   shared `livespec_runtime` `WorkItem`.
2. **When B1 lands: promote + factory-dispatch B2 and B3.** Their prose blocker
   (B1) is then satisfied, so promote `bd-ib-qcnbbp` (bd-ib) and `bd-gj-7adugd`
   (bd-gj) `backlog → ready` (e.g. `drive --action set-admission` / a status
   move), then factory-dispatch each. B2 realizes the v040 admission refusal +
   replaces the `is_host_only_item` regex + updates the paired doctor invariant +
   migrates old host-only-marked items; B3 is git-jsonl codec parity. They can run
   in parallel (both depend only on B1).
3. **Slice C — after B2 lands: groom + dispatch `bd-ib-i6wfum`** (host-only
   needs-attention kind), same factory-dispatch route. At C's groom, set its
   proper phased (prose) dependency on B1/B2.
4. **Slice D stays under `z2ctra`** — no action here beyond the recorded
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
