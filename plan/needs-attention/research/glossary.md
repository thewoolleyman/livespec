# needs-attention — glossary of terms

A human- and machine-readable reference for every term coined or
load-bearing in the `needs-attention` design dialogue. Companion to
`design.md` (the settled design) and `../handoff.md` (how to drive the
track).

**Status markers:** `[NEW]` introduced by this design · `[RENAMED]`
existing thing renamed here · `[EXISTING]` pre-existing fleet term used
as-is · `[DEFERRED]` in-scope concept parked for a later increment.

---

## Surfaces and skills

- **needs-attention** `[NEW]` — the first-class, **stateless, point-in-time**, per-repo surface answering *"is there anything actionable about livespec in this repo, spec-side or orchestrator/implementer-side, right now?"* A thin-transport reader shipped in both orchestrator plugins; renders Markdown (skill) or JSON (CLI). The awareness authority. Related: [needs-attention-fleet], [needs-attention-internal], [attention_item], [drive].
- **needs-attention-internal** `[NEW]` — maintainer-only sibling composing livespec-fleet-development signals (CI red, fleet-conformance, stale cross-repo pins, cross-repo drift). Local/unsynced in `livespec` core; never ships to the plugin or adopters. Related: [product vs internal], [needs-attention-fleet].
- **needs-attention-fleet** `[NEW]` — maintainer-only aggregator that fans out over the fleet manifest (fleet members + adopters), unions each repo's product `needs-attention` and folds in `needs-attention-internal`, into one flat `attention[]`. Pure aggregator (no cross-repo re-ranking). Local/unsynced in `livespec` core. Related: [fleet], [adopter].
- **drive** `[RENAMED]` — the executor peer (renamed from `orchestrate`): executes one operator action by id — `impl:` dispatch + human valves + policy dials. Coupled to `needs-attention` only by the [action-id grammar]. The fleet's verb for making the work-item machinery go; spans the factory and the ledger. Related: [orchestrate].
- **orchestrate** `[RENAMED]` → **drive** — the retiring operator skill. `orchestrate plan` (composition) is subsumed by `needs-attention`; `orchestrate run` (execution) becomes `drive`. Related: [drive].
- **next** `[EXISTING]` — a ranker. Spec-side `next` (livespec core) ranks revise/propose-change/critique/prune-history; impl-side `next` (orchestrator) ranks `ready` work only (action `implement`). The scope-asymmetry (spec-`next` includes human actions; impl-`next` does not) is why composing only the two is an *incomplete* attention picture. Related: [candidates].
- **list-work-items** `[EXISTING]` — thin-transport enumerator of work-items by lane; `needs-attention` uses it for the human-valve lanes.
- **list-plan-threads** `[NEW]` — thin-transport enumerator of open `plan/<topic>/` threads (sibling of `list-work-items`); a `needs-attention` read primitive. The pending `orchestrate-plan-surfaces-unarchived-plan-threads` proposal is redirected into it. Related: [plan thread].
- **hygiene-scan** `[NEW]` — thin CLI over a new `livespec-runtime` module emitting per-repo git-state findings (stale worktrees/branches/PRs, primary-checkout health). Shares stale-worktree detection with the core reaper. A `needs-attention` read primitive.
- **plan** `[EXISTING]` — the heavyweight skill that opens/resumes a `plan/<topic>/` planning thread, anchors a ledger epic, routes matured pieces, and archives on close. The Orchestrator-Plane realization of the [Planning Lane].
- **groom** `[EXISTING]` — the maintainer-owned skill that decomposes a backlog epic into ready, dependency-layered slices. A maintainer-owned gate the overseer surfaces but never performs.
- **overseer** `[EXISTING]` — the local-only (livespec core, unsynced) coordinator that keeps parallel tracks moving: resumes plan handoffs, dispatches ready work through the factory, surfaces maintainer gates. Retained until the console operator-cockpit replaces it.
- **ready-queue-drain** `[EXISTING]` — a prototype prompt driving one repo's *ready impl queue* to `done` autonomously (dispatch → land → AI-approve → accept-on-behalf → close). Ready items only; surfaces oversized items for `groom`. Temporary until `needs-attention` lands.

## The attention_item data shape

- **attention_item** `[NEW]` — the dedicated schema every primitive normalizes into; the single contract the console port, fleet aggregator, and both renderers bind to. Fields: `id`, `kind`, `urgency`, `summary`, `source_ref`, `handoff`.
- **id** `[NEW]` — a **stable natural key per kind** (never a positional index): `valve:<verb>:<work-item-id>`, `impl:<work-item-id>`, `hygiene:<type>:<resource>`, `plan:<topic>`, `spec:<op>:<spec-target>`. Load-bearing because it is the console's diff key.
- **kind** `[NEW]` — the item's category: `human-valve` | `impl` | `spec` | `plan` | `hygiene` | `internal`.
- **urgency** `[NEW]` — `high` | `medium` | `low`.
- **summary** `[NEW]` — one-line human description of what needs attention.
- **source_ref** `[NEW]` — `{repo, work_item|path}` locating the underlying fact; carries the repo so the flat fleet list stays attributable.
- **handoff** `[NEW]` — how to address the item: `{kind, action_id?, command}`. `kind` routes the consumer (`drive` | `livespec-op` | `plan` | `shell`); `action_id` is the drive-grammar token for executable items (the real contract); `command` is a ready-to-run string for humans.
- **drive_executable** `[NEW]` — the property that an item is runnable via `drive` (exactly the impl-side work-item mutations); encoded by `handoff.kind == "drive"`. Non-drive handoffs may still be executable by other means (a `/livespec:*` skill, a `just` target, a future console port).
- **action-id grammar** `[NEW/EXISTING]` — the token vocabulary shared between `needs-attention` (emits as handoffs) and `drive` (executes): `impl:<id>`, `approve:<id>`, `accept:<id>`, `reject:<id>:rework|regroom`, `set-admission:<id>:auto|manual`, `set-acceptance:<id>:...`, plus non-executable `spec:<op>` and `plan:<topic>`. The ONLY coupling between the two peers.
- **candidates[]** `[EXISTING]` — the existing `{action, reason, urgency, work_item_ref}` shape emitted by `next`/`orchestrate plan`. `attention_item` deliberately does NOT extend it (it would stretch "candidate" onto hygiene/plan items).

## Work-item lifecycle

- **lane** `[EXISTING]` — the rendered lifecycle state, one of seven: `backlog`, `pending-approval`, `ready`, `active`, `acceptance`, `blocked`, `done`. Owned by livespec core; consumed (never re-derived) via `lane`/`lane_reason`.
- **lane_reason** `[EXISTING]` — the rendered blocked reason (`needs-human` | `infra-external` | `dependency`).
- **human valves** `[EXISTING]` — the two human decision points bracketing the autonomous middle: **approve** (`pending-approval → ready`) and **accept** (`acceptance → done`), plus **reject** (`acceptance → active|backlog`).
- **admission_policy / acceptance_policy** `[EXISTING]` — the delegation dials: `admission_policy` (`auto` delegates approve; `manual` requires a human) and `acceptance_policy` (`ai-only`/`human-only`/`ai-then-human`). Toggling manual→auto is the "delegate to automation" option `needs-attention` surfaces.
- **Definition-of-Ready** `[EXISTING]` — the intake gate an item clears before it can be `ready`; a backlog item failed it (or is an epic needing decomposition).
- **rank** `[EXISTING]` — the fractional/lexicographic ordering key; the sole pull-order authority `next` uses.
- **ledger** `[EXISTING]` — the beads/Dolt work-items store; the source of truth for work-item state. Read via the [credential wrapper].

## Planes and architecture

- **Spec Plane** `[EXISTING]` — livespec core and the `/livespec:*` spec lifecycle.
- **Orchestrator Plane** `[EXISTING]` — the producer: the orchestrator plugin + Dispatcher + Fabro (the factory). Owns work-item execution.
- **Control Plane / operator cockpit / console** `[EXISTING]` — `livespec-console-beads-fabro`; observes every plane read-only, composes the cross-plane picture, invokes each plane's operations, coordinates the human — owning no plane's semantics. NOT a Driver.
- **Driver** `[EXISTING]` — the per-agent-runtime binding (`livespec-driver-claude`, `livespec-driver-codex`) exposing the `/livespec:*` surface. Distinct from the Control Plane.
- **Planning Lane / plan thread** `[EXISTING]` — the durable, multi-session *planning* work (`plan/<topic>/`) that decides what becomes spec, implementation, or research before any lane is committed. This design lives in `plan/needs-attention/`.
- **factory / Dispatcher / Fabro** `[EXISTING]` — the execution path: the Dispatcher (`dispatcher.py`) drains `ready` items and runs each in a Fabro sandbox (Red→Green), gated by the [janitor gate], then merges and closes. Dispatch is host-wide sequential.
- **janitor gate** `[EXISTING]` — the hard gate every factory run passes: `just check` + `/livespec:doctor`.

## Event-sourcing and the console boundary

- **canonical event** `[EXISTING]` — a durable fact in the console's append-only event log; projections rebuild from it.
- **projection** `[EXISTING]` — a derived read-model (e.g. the attention inbox) rebuilt from events.
- **adapter / port** `[EXISTING]` — a source-specific translator behind a port; console adapters poll sources and emit canonical events.
- **snapshot** `[NEW usage]` — one point-in-time `needs-attention` output. `needs-attention` only ever produces a snapshot ("now") — no timestamps, no history.
- **diff at ingest** `[NEW]` — the console's chosen model: its `needs-attention` adapter polls the snapshot, diffs against the prior one, and emits delta events. All event-sourcing stays console-side; `needs-attention` stays stateless.
- **attention_item.appeared / .changed / .resolved** `[NEW]` — the delta events the console emits, keyed by the stable `id` (idempotent — unchanged items emit nothing).
- **checkpoint / backfill / reconciliation** `[EXISTING]` — the console's ingestion-continuity machinery (per-adapter high-water mark; replay of a missed window; gap recovery). Part of the deferred [observability] context, not attention.

## Observability (deferred)

- **observability** `[DEFERRED]` — a separate first-class Control-Plane bounded context: OTel-style telemetry of the running console/adapters (poll spans, checkpoint-lag metrics, backfill traces, auth-error logs). Handled by a telemetry pipeline (signals → dashboards/alerts), NEVER the attention inbox; feeds `needs-attention` only where telemetry reveals a durable code defect → a work-item. Its source originates inside the orchestrator boundary, crossing a producer→consumer API seam to be specified when built.
- **OpenTelemetry (OTel)** `[DEFERRED]` — the standard observability data model (traces/spans, metrics, logs). Invariant: conform to it whenever emitting observability data.

## Fleet, distribution, discipline

- **fleet / fleet member** `[EXISTING]` — the livespec-family repos enumerated in `.livespec-fleet-manifest.jsonc` (`core`/`enforcement-suite`/`impl-plugin`/`driver-plugin`/`library`/`console`).
- **adopter** `[EXISTING]` — a governed repo that adopted the workflow but is not fleet (e.g. `openbrain`, `resume`). Contributes product `needs-attention` only.
- **product vs internal** `[NEW test]` — the dividing test: *does an end user have actionable control?* Yes → product (`needs-attention`, shipped); no → internal (`needs-attention-internal`, maintainer-only).
- **livespec-runtime** `[EXISTING]` — the shared library both orchestrators import; new home of the `needs-attention` compose function and the `hygiene-scan` module (the DRY structure that serves both reference orchestrators).
- **livespec-dev-tooling** `[EXISTING]` — the fleet-spanning enforcement-suite repo where conformance/pin checks live (signals `needs-attention-internal` composes).
- **consume-don't-recompute** `[EXISTING principle]` — the console consumes computed values (`lane`, and now `needs-attention` output) rather than re-deriving them.
- **peers not layers** `[NEW principle]` — `needs-attention` (read) and `drive` (execute) are peers coupled only by the action-id grammar; neither wraps the other, keeping each cohesive.
- **credential wrapper** `[EXISTING]` — the project-configured CLI (`with-livespec-env.sh --`) injecting the tenant `BEADS_DOLT_PASSWORD` + GitHub App env; every ledger read/write goes through it. Secrets are probe-only.
- **worktree → PR → rebase-merge** `[EXISTING]` — the repo mutation protocol every tracked-file change follows.
