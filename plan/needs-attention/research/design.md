# needs-attention — design record

Durable reasoning for the `needs-attention` family: a first-class,
per-repo surface that answers *"is there anything actionable about
livespec in this repo, spec-side or orchestrator/implementer-side?"*,
plus its fleet aggregator and its livespec-internal-dev sibling. This
is the settled design from the design dialogue; the rollout is anchored
by this thread's ledger epic (see `../handoff.md`).

## Origin and problem

The concept began as the **"attention pane"** planned for the Control
Plane console (`livespec-console-beads-fabro`). Investigation found the
console spec's `Attention` concept was internally contradictory — a
narrow *"derived only from a work item"* definition (`spec.md`
§"Terminology", §"Bounded Contexts") versus a broad diagram + Scenario 1
that also pull in spec-side revise, source health, and hygiene. Neither
was a clean, reusable surface, and the closest existing thing
(`orchestrate plan`, which composes only spec-`next` + impl-`next`) is
an *incomplete* awareness picture: impl-`next` is a pure ranker of
dispatchable `ready` work and deliberately excludes the human valves.

Decision: extract "what needs attention" into a **first-class,
reusable surface** consumed by the console AND directly by a human/CLI,
rather than leaving it half-specified inside a Rust event-sourced
product.

## The four surfaces

| Surface | Role | Home | Ships? |
|---|---|---|---|
| `needs-attention` | Read/awareness authority; no-arg "what needs attention?"; Markdown (skill) + JSON (CLI); **stateless, point-in-time** | thin binding in **both** orchestrator plugins (`livespec-orchestrator-beads-fabro` + `livespec-orchestrator-git-jsonl`) | Yes (plugin) |
| `drive` (renamed from `orchestrate`) | Execute one operator action by id: `impl:` dispatch + valves (approve/accept/reject) + policy (set-admission/set-acceptance) | orchestrator plugin(s) | Yes (plugin) |
| `needs-attention-internal` | Compose livespec-fleet-dev signals (CI red, fleet-conformance, stale cross-repo pins, cross-repo drift) | `livespec` core, **local/unsynced** (the `overseer` precedent) | No |
| `needs-attention-fleet` | Pure aggregator across fleet members **+ adopters**; folds in `-internal` | `livespec` core, **local/unsynced** | No |

`needs-attention` and `drive` are **peers**, not layered — coupled ONLY
by the shared action-id grammar. Neither calls the other. Rationale:
layering (`orchestrate` presenting things it cannot action — spec,
plan, hygiene) is low cohesion; the interactive "see → select →
execute" loop belongs to the **console** (its whole reason to exist),
and for a terminal human it is just "read `needs-attention`, run the
handoff." `orchestrate` was demoted to a pure executor, so it no longer
deserves the name of the whole plane — hence `drive`, the fleet's own
verb for making the work-item machinery go (it spans both the factory
and the ledger). `orchestrate plan` retires; its composition role moves
to `needs-attention`.

## Read primitives `needs-attention` composes

`needs-attention` is a **thin-transport reader** that delegates to
cohesive primitives (it does not re-detect):

- spec-`next` (`livespec` core, cross-plane) — revise / propose-change / critique / prune-history
- impl-`next` (orchestrator) — ranked `ready` work
- `list-work-items` (orchestrator) — the human-valve lanes (`pending-approval`+manual admission, `acceptance`+ai-then-human, `blocked`+needs-human); may need one or two lane filters added
- **`list-plan-threads`** (NEW thin-transport primitive; sibling of `list-work-items`) — open `plan/<topic>/` threads. The pending `orchestrate-plan-surfaces-unarchived-plan-threads` proposal in `livespec-orchestrator-beads-fabro` is **redirected** into this primitive rather than a third source inside the retiring `orchestrate plan`.
- **`hygiene-scan`** (NEW) — per-repo git state findings.

The **shared compose logic lives in `livespec-runtime`** (orchestrator-
agnostic pure function); each orchestrator plugin ships a thin
`needs-attention` binding over it, calling that plugin's own gather
primitives. This is the DRY structure that lets both reference
orchestrators (beads-fabro AND git-jsonl) reuse one composition.

`hygiene-scan` is a `livespec-runtime` module + thin CLI (git-level,
orchestrator-agnostic), and the existing core reaper
(`just reap-stale-worktrees`) is refactored to consume the SAME
stale-worktree detection so scan and reap cannot drift.

## Why the two `next` primitives are NOT mis-designed

impl-`next` is a pure ranker of dispatchable `ready` work (action type
`implement` only); spec-`next` includes human actions (`revise`). The
asymmetry is correct per each primitive's job — but it means composing
*only the two `next`s* (what `orchestrate plan` does) misses the impl-
side human valves. `needs-attention` therefore composes a wider
primitive set. Document this asymmetry in the orchestrator spec so no
one rebuilds the incomplete two-`next` composition.

## The `attention_item` schema

A **dedicated** schema the primitives normalize INTO (not an extension
of `candidates[]`, which stretches "candidate" onto hygiene/plan
items). Consumers (console port, fleet aggregator, both renderers) bind
to this one shape:

```jsonc
{
  "attention": [
    {
      "id": "valve:approve:abc123",          // STABLE natural key per kind — no positional indices
      "kind": "human-valve",                  // human-valve | impl | spec | plan | hygiene | internal
      "urgency": "high",                       // high | medium | low
      "summary": "abc123 awaits your approval",
      "source_ref": { "repo": "livespec", "work_item": "abc123" },
      "handoff": {
        "kind": "drive",                       // drive | livespec-op | plan | shell  (routes the consumer)
        "action_id": "approve:abc123",         // the drive-grammar token (the real contract); null for non-drive
        "command": "drive approve:abc123"       // ready-to-run string for humans/Markdown
      }
    }
  ]
}
```

Id stability is load-bearing (it is the console's diff key): `id` is a
stable natural key per kind — `valve:<verb>:<work-item-id>`,
`impl:<work-item-id>`, `hygiene:<type>:<resource>`, `plan:<topic>`,
`spec:<op>:<spec-target>`. NO positional indices (the old
`spec:revise:0` form is out).

`handoff.drive_executable` is exactly the impl-side work-item mutations
(`impl:` dispatch + approve/accept/reject + set-admission/set-
acceptance); everything else is a pure human handoff — some still
executable by other means (a `/livespec:*` skill, a `just` target, or a
future console port), just not by `drive`. This is encoded by
`handoff.kind` (drive vs livespec-op vs plan vs shell).

## Statelessness and the console event-sourcing boundary

`needs-attention` is **stateless / point-in-time** — one question,
*"what needs attention RIGHT NOW"*, over current state (ledger + spec
tree + plan dir + hygiene). NO timestamps, NO events, NO history. This
preserves the standalone single-entry-point and keeps the (non-event-
sourced) orchestrator uncontaminated.

- Two renderers only (the one real axis): Markdown (skill, human) / JSON (CLI, machine).
- The console consumes `needs-attention` snapshots **via a port** and
  **diffs at ingest**, emitting `attention_item.appeared` /
  `.changed` / `.resolved` keyed by the stable `id` (idempotent —
  unchanged items emit nothing). This is the console's existing
  snapshot-source pattern (its Scenario 4, work-items snapshot without
  transition history). **All event-sourcing stays in the console.**

Rejected as bleed/over-engineering: passing a UTC timestamp to
`needs-attention` (would force it to know deltas/history), and making
`needs-attention` a pure function over an injected historical state
snapshot (unnecessary — the console records the snapshot outputs as
events over time; replaying its own log rebuilds projections; rule
changes correctly apply forward, history is not retroactively
rewritten). The re-derivation invariant holds without either.

## Product vs. internal — the dividing test

*Does an end user have actionable control?* → **product** (the shipped
`needs-attention`). Else → **internal** (`needs-attention-internal`).
Examples: plugin version out of date → product (they can update); a
stale worktree in their repo → product; livespec CI red / fleet-
conformance drift / cross-repo pin currency → internal.

Consequently `hygiene-scan`'s finding set is per-repo git state the
end-user controls (stale worktrees, stale local branches, stale/
abandoned open PRs, primary-checkout health — dirty/detached/off-
default), all product; GitHub-dependent parts (PRs) degrade gracefully
when creds/network are absent. Fleet-dev hygiene (CI, conformance,
pins) is internal and belongs to `needs-attention-internal`, not
`hygiene-scan`.

`needs-attention-internal` composes signals ALREADY computed elsewhere
(the dev-tooling conformance/pin checks, GitHub for CI, doctor for
drift) — it detects nothing new. It lives local/unsynced in `livespec`
core beside `needs-attention-fleet` and the fleet manifest, correctly
scoped so it never ships to the plugin or to adopters.

## `needs-attention-fleet` shape

Home: `livespec` core, local/unsynced. A **pure aggregator** — fans out
over `.livespec-fleet-manifest.jsonc` (fleet members + adopters
`openbrain`, `resume`), invokes each repo's product `needs-attention`
and folds in `-internal`, with **no cross-repo re-ranking** (the same
restraint impl-`next` has). Output is a **flat merged `attention[]`
reusing the SAME `attention_item` schema**, repo carried in each
`source_ref`; grouping (by repo or urgency) is a renderer concern (the
Markdown human view groups; JSON stays flat). Adopters contribute
product `needs-attention` only (`-internal` is livespec-fleet-dev-
specific).

`-fleet` is a strict superset that consumes both product per-repo
`needs-attention` and `-internal`; the two are orthogonal (content
category vs. scope aggregation), so they compose without collision.

## Deferred (the only deferral)

**Observability / telemetry** — a separate first-class Control-Plane
bounded context (adapter poll spans, checkpoint-lag metrics, backfill/
reconciliation traces, auth-error logs). Its source originates inside
the **orchestrator** boundary (which owns the factory), so it crosses a
producer(orchestrator)→consumer(console) API seam that must be
specified explicitly when built. It is handled by a telemetry pipeline
(signals → dashboards/alerts), NEVER the attention inbox; it feeds
`needs-attention` only at the one seam where telemetry reveals a
*durable code defect* → a captured work-item. **Invariant when built:
conform to OpenTelemetry standards.** Out of scope for the initial
rollout.

## Rollout — one cross-repo epic (anchored by this thread)

- **`livespec-runtime`** — `hygiene-scan` module + CLI; the shared `needs-attention` compose function.
- **orchestrator plugins (×2, beads-fabro + git-jsonl)** — `needs-attention` thin binding; `list-plan-threads` primitive; `orchestrate`→`drive` rename + retire `orchestrate plan`; `list-work-items` lane filters if needed; document the `next` scope-asymmetry.
- **`livespec` core** — `needs-attention-internal` + `needs-attention-fleet` local/unsynced skills; refactor the reaper to share `hygiene-scan` detection.
- **`livespec-console-beads-fabro`** — ubiquitous-language rename `Attention` → `needs-attention`; snapshot port + diff adapter + `attention_item.*` events; reconcile the narrow/broad Attention contradiction (Attention = the product `needs-attention` core; hygiene now arrives THROUGH `needs-attention`, so the separate "Repository Hygiene → Attention" edge is subsumed and the "Ingestion → Attention" edge belongs to the deferred observability context).
- **adopters (`openbrain`, `resume`)** — grep-and-migrate any committed `orchestrate` references to `drive`; verify pins pick up the new surface (`needs-attention` is additive, no migration).
- **rename blast radius** — orchestrator spec `orchestrate` section, both driver bindings (`livespec-driver-claude` + `livespec-driver-codex`), console Scenario 11 references to "the `orchestrate` action surface", and the pending proposals that cite `orchestrate`.

Every spec touch goes through its repo's `propose-change` → independent
Fable review → `revise` cycle; every code change through the
worktree→PR flow. Ripe pieces are FILED into the ledger (as children of
this thread's epic) and built factory-side under the janitor gate —
never hand-coded in the planning session.
