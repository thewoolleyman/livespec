# needs-attention — handoff

**Thread:** `plan/needs-attention/` (repo `thewoolleyman/livespec`)
**Ledger epic anchor:** `livespec-bj9x` (read status from the ledger; never trust a status written here)

## Read-first chain

1. **`research/design.md`** — the complete, settled design and the full
   rollout list. Read it in full before acting; it is the single source
   of truth for every decision (the four surfaces, the `attention_item`
   schema, the peer `needs-attention`/`drive` split, the console
   snapshot/diff boundary, product-vs-internal, and the deferred
   observability context).

That is the whole chain — everything needed to proceed is in
`design.md`. Do not consult chat history.

## Status (derive, never store)

Compose current status by reading the ledger, not this file:

```bash
# open children of the epic + ripest next impl action
/usr/local/bin/with-livespec-env.sh -- python3 \
  "$CLAUDE_PLUGIN_ROOT/scripts/bin/list_work_items.py" --json --project-root /data/projects/livespec
```

At the time this handoff was written the epic `livespec-bj9x` had **no
children yet** — the design is settled and anchored, but the rollout is
not yet decomposed into work-items.

## Next action (exactly one)

**Decompose the rollout in `research/design.md` §"Rollout — one
cross-repo epic" into this epic's children.** Route each piece by kind
(per the `plan` operation's two seams — this session FILES ripe work
and NEVER hand-codes it):

- *code work* → file via the `capture-work-item` operation as a CHILD
  of `livespec-bj9x` (linked `depends_on`, typed dicts
  `{"kind":"local","work_item_id":"..."}`).
- *spec change* → open via `/livespec:propose-change` against the owning
  repo's spec, then independent Fable review → `/livespec:revise`.

**Dependency order (foundational first):**

1. `livespec-runtime` — the shared `needs-attention` compose function + the `hygiene-scan` module + thin CLI. Everything composes over this; do it first.
2. orchestrator plugins (`livespec-orchestrator-beads-fabro` first, then `livespec-orchestrator-git-jsonl` in parallel where independent) — the `needs-attention` thin binding; `list-plan-threads`; the `orchestrate`→`drive` rename + retire `orchestrate plan`; `list-work-items` lane filters if needed. Spec proposals here: the `orchestrate`→`drive` rename and the `next` scope-asymmetry note.
3. `livespec` core — `needs-attention-internal` + `needs-attention-fleet` local/unsynced skills; refactor the reaper to share `hygiene-scan` detection.
4. `livespec-console-beads-fabro` — spec proposal reconciling the narrow/broad Attention contradiction + the ubiquitous-language rename to `needs-attention`; then the snapshot port + diff adapter + `attention_item.*` events.
5. adopters (`openbrain`, `resume`) — grep-and-migrate committed `orchestrate`→`drive`; verify pins.

The rename blast radius (both driver bindings, console Scenario 11, the
pending proposals) travels with step 2's rename work-item.

**Redirect note:** the pending `orchestrate-plan-surfaces-unarchived-
plan-threads` proposal in `livespec-orchestrator-beads-fabro` must be
redirected into the new `list-plan-threads` primitive rather than a
third source inside the retiring `orchestrate plan` — fold this into
step 2.

## Constraints (standing)

- Spec touches: `propose-change` → independent Fable review → `revise`;
  co-edit `tests/heading-coverage.json` for any `##` heading change.
- Code: worktree → PR → merge → cleanup; TDD red-green-replay for
  product `.py`.
- Ripe work is built **factory-side** under the janitor gate (the
  Dispatcher / `drive`), never hand-coded in the planning session.
- Observability/telemetry is deferred (design.md §"Deferred"); do not
  scope it into the initial rollout.
