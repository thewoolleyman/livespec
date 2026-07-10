# Autonomous-mode MVP — overall cross-repo plan (livespec core)

**Repo:** `thewoolleyman/livespec` · **Thread:** `plan/autonomous-mode/` · **Role:** the
OVERALL orchestrating plan that ties the console and orchestrator repo plans
together, owns the cross-repo dependency graph, and defines the tmux/session
delegation model. This repo (livespec core) authors NO product code for this
effort; it holds the coordination plan and tracks the two upstream core items
the safety story depends on.

> **Sibling plans this coordinates (read alongside):**
> - Console operator surface — `livespec-console-beads-fabro/plan/autonomous-mode/design.md`
> - Orchestrator decision engine — `livespec-orchestrator-beads-fabro/plan/autonomous-mode/design.md`

---

## 1. Goal

Ship an MVP in which a human operator, from the `livespec-console-beads-fabro`
**terminal UI (TUI)** — the GUI is explicitly OUT of scope for this MVP — flips a
per-repository **full autonomous mode** that causes the Beads/Dolt + Fabro
factory to drive ready work-items all the way to `done` **unattended**: the human
gates that normally park an item (manual admission approval, the human leg of
acceptance, and in-loop `needs-human` blocks) are resolved by an LLM standing in
for the operator, while the console **observes, records, and reflects** every
auto-resolution through the same command-plus-audit-event path as a human action,
and surfaces only the **truly-unresolvable** decisions back to the operator as
in-TUI needs-attention items.

"Truly-unresolvable" is the residual the LLM must never guess — including, by
core-spec design, the irreducible human touchpoints (see §4).

## 2. What this plan supersedes

**Nothing, conceptually.** The autonomous-mode design is not greenfield: its
foundations already landed and are ratified in the specs of all three repos. This
plan does not re-open settled design; it sequences the remaining *implementation*
across two repos and reconciles the seams between their already-written specs.

Already landed (do not re-litigate):
- **livespec core** — the deterministic work-item lifecycle + the two
  human-delegable policy valves + the Control-Plane console guidance (closed epics
  `livespec-35s3zo` "Open Engine" and `livespec-zs22.6`). The plane boundary this
  MVP relies on is already spec law.
- **console (spec v016)** — a complete normative definition of the operator-facing
  Full Autonomous Mode, the TUI Contract, and the five `work_item.*` valve/policy
  commands. Zero pending proposals.
- **orchestrator (spec v032)** — a complete normative definition of the
  orchestrator-side Full autonomous mode engine (scenarios 33-37). Zero pending
  proposals.

The one active console plan thread, `plan/impl-dispatch/`, drove the
behavioral-coverage test chain to completion (all of `cvqcnx`, `cc3nlr`, `77t6mk`,
`rrr4i4`, `idgql3`, `qvrwag` are closed). It is effectively done and unrelated to
autonomous mode; this plan does not depend on it. Recommend archiving it as a
separate housekeeping step (not a dependency of this MVP).

## 3. The three planes and the plane boundary (why the work splits the way it does)

livespec core's specification already fixes the boundary this MVP lives inside
(`SPECIFICATION/spec.md` §"Workflow planes and the Planning Lane", §"The
Control-Plane role"; `SPECIFICATION/non-functional-requirements.md`
§"Control-Plane console guidance"):

- **Spec Plane** (livespec core) — owns *what* is built; the propose-change/revise
  lifecycle.
- **Orchestrator Plane** (the producer; reference: Beads/Dolt + Fabro) — owns the
  work-item ledger, the Dispatcher, the Loop, and **the autonomous-mode parameter
  and the valves**. The engine that auto-resolves gates lives HERE.
- **Control Plane** (the operator console; reference: `livespec-console-beads-fabro`)
  — OBSERVES every plane read-only through that plane's own published surface,
  INVOKES each plane's operations on the operator's behalf through that published
  surface, and COORDINATES the human. It **never owns** another plane's decision
  semantics and is **not a required dependency** of the workflow it observes.

The maintainer's split — "the TUI toggles autonomous mode; the orchestrator plane
holds the auto-resolution engine" — is therefore not a new architecture; it is the
existing plane boundary. That is why:
- the **console** builds the *operator surface* (toggle, persistence, audit,
  command issuance, observe/reflect), and
- the **orchestrator** builds the *decision engine* (the LLM gate-resolution),
- and neither repo reaches around the other.

## 4. Irreducible human touchpoints (a hard boundary on the engine)

core `SPECIFICATION/spec.md` §"Contract + reference implementations architecture"
and `non-functional-requirements.md` grooming guidance declare three decisions
that survive even a fully autonomous orchestrator and MUST remain human:
- **drift acceptance** — "Orchestrators MAY file drift (the machine path); only
  humans accept it."
- **spec-change slices** — human-gated; route through propose-change/revise; never
  auto-dispatched.
- **regroom / backlog-bounce** — "the one human-in-the-loop step: the Dispatcher
  SURFACES needs-regroom items (escalate, do not drop); a human grooms and
  approves."

These are part of the "truly-unresolvable" set **by design, not by low
confidence.** The orchestrator engine (step O2) MUST leave them as needs-attention;
Step-0 validation MUST confirm the orchestrator spec agrees.

## 5. Current state synthesis (from the 2026-07-10 surveys)

| Plane | Spec | Implementation |
|---|---|---|
| Console (`livespec-console-beads-fabro`, v016) | **Complete** — Full Autonomous Mode, TUI Contract, 5 `work_item.*` commands, `config.autonomous_mode_set` + `.livespec.jsonc` persistence + audit, Scenarios 9-12 | **~Absent** — `CommandType` has only `FactoryDrainRequested`; zero `autonomous` code; no Configuration context / `.livespec.jsonc` reading; TUI has generic modal/palette only. (The factory-drain port IS wired with an honest `NotWired` fallback.) |
| Orchestrator (`livespec-orchestrator-beads-fabro`, v032) | **Complete** — Full autonomous mode engine, scenarios 33-37 | **Absent** — `--mode autonomous` is only a queue-drain scope switch; valves still hold/park; no `dispatcher.autonomous_mode` config key in code; no LLM gate-resolution. Item `bd-ib-82a` tracks it, no slices. |
| Core (livespec) | Plane boundary + valves + Control-Plane guidance all landed | n/a for this MVP |

## 6. Integration seams / key design risks (what Step-0 validation must stress)

These are cross-repo tensions between two already-written specs. The plan SURFACES
them; the Step-0 multi-model validation (see §8) and the C1/O1 spec-currency steps
RESOLVE them via propose-change where a real gap exists.

1. **Persistence-model seam (the #1 risk).** The console spec persists a per-repo
   `autonomous_mode.enabled` preference in `.livespec.jsonc` (a durable operator
   intent). The orchestrator spec says autonomous mode is a per-invocation
   `drive --mode autonomous` opt-in that **MUST NOT persist beyond the
   invocation**, though it also names a `dispatcher.autonomous_mode` config key.
   Reconcile precisely: the console persists *intent*; whatever LAUNCHES the
   Dispatcher loop reads that intent and passes `--mode autonomous` per run. Define
   what published orchestrator surface the console's
   `factory.autonomous_mode_enable_requested` command maps to, given the
   orchestrator holds no persistent "enabled" state to flip.
2. **Division of resolution (avoid double-resolution).** The console spec says the
   console "MUST resolve — via an LLM standing in for the operator — the operator
   decisions it would otherwise prompt a human for" (Scenario 10) AND "where a
   plane owns a decision … MUST enable that plane's own autonomous resolution …
   MUST NOT reach around the plane." Pin down which decisions the console's own
   LLM-stand-in resolves versus which it delegates wholesale to the orchestrator
   engine, so the two layers never both resolve the same gate. Recommended MVP
   reading: the orchestrator engine owns all gate resolution; the console's
   autonomous responsibility is enable + observe + reflect + surface-unresolvable,
   keeping the console's own LLM layer thin or deferred.
3. **Vocabulary drift ("livespec moved forward").** The console spec cites the
   orchestrator contract by reference (the correct pattern), but confirm three
   vocabularies still match current core/orchestrator: (a) the seven lane names +
   the `blocked:dependency` overlay; (b) the acceptance-policy enum
   `{ai-only, human-only, ai-then-human}` and reject modes `{rework, regroom}`;
   (c) the `attention_item.*` schema versus core's current `needs-attention`
   schema (console item `ipi` / Scenario 12).
4. **Operability preconditions for SAFE unattended running.** core item
   `livespec-0jxs` records that the dark factory today has NO failure-notification
   path, NO escalation, NO telemetry shipping, and NO verified cost ceiling. An
   autonomous run that fails silently is worse than one that parks. The console's
   observe/reflect/needs-attention surface is part of the escalation answer, but
   the cost-ceiling and failure-notification pieces are core/orchestrator concerns
   this plan TRACKS (see §9).

## 7. Step catalogue — small, delegatable steps with explicit gates

Notation: **owner** = which delegate session drives it (see §10); **gate** = what
must be true before it may start; each step's *done* is a merged PR (or a ratified
spec revision) with the stated evidence.

### Step 0 — multi-model validation (FIRST STEP OF EVERY PLAN; hard gate)
- **Owner:** driver session `autonomous-mode`, with the maintainer running the
  Fable sessions.
- **What:** an independent multi-model (Fable) validation pass over ALL THREE plans
  (this overall plan + the console plan + the orchestrator plan) confirming they are
  internally sound, dependency-correct, seam-reconciled (§6), and will actually
  reach the console-MVP goal. Aligns with the standing "independent Fable review
  before every ratification" discipline.
- **Gate:** none — this is the entry gate for everything else.
- **Done:** a NO-BLOCKERS verdict recorded on this thread; any blocker routes back
  into the relevant plan before implementation starts.

### Console track — owner: session `console-autonomous-mode`
- **C1 — console spec currency + seam reconciliation.** Diff the console spec's
  borrowed vocab against current core/orchestrator (§6.3); resolve the persistence
  seam (§6.1) and the resolution-division question (§6.2); resolve the
  `config.autonomous_mode_set` naming-consistency question versus the factory
  `autonomous_mode_enable/disable_requested` pair. Route any real change via
  `/livespec:propose-change` → independent Fable review → `/livespec:revise`.
  Refresh the stale version pointer on item `rt4` (cites v013; spec is v016).
  **Gate:** Step 0. **Done:** console spec revision ratified (or a documented
  "no change needed" with the seams pinned).
- **C2 — console command foundation.** Add the five `work_item.*` valve/policy
  `CommandType` variants (`approve`, `accept`, `reject:…:{rework,regroom}`,
  `set-admission:…:{auto,manual}`, `set-acceptance:…:{ai-only,human-only,ai-then-human}`)
  + handlers + a port that issues them through the orchestrator's EXISTING published
  `orchestrate run` action surface (these actions already ship on the orchestrator
  `drive` skill — the console wires to them, it does not invent new orchestrator
  commands). Folds console items `pke3y3` (regroom against the current valve model)
  and the Scenario-11 test. **Gate:** C1. **Done:** merged PR; the TUI can issue
  each valve manually against a real tenant.
- **C3 — console autonomous-mode feature.** Add `config.autonomous_mode_set` +
  a Configuration context that reads/writes the `.livespec.jsonc` `autonomous_mode`
  block + the `config.autonomous_mode.enabled/.disabled` audit events + the
  `factory.autonomous_mode_enable/disable_requested` commands (with the honesty
  `factory.autonomous_mode.not_wired` outcome) + the TUI toggle, type-to-confirm
  modal (enable only), "dangerous / use with caution" label, and header mode
  indicator + the Scenario-10 auto-resolve-decidable/escalate-the-rest loop scoped
  per §6.2. Folds console item `rt4`. **Gate:** C1 AND C2 AND the orchestrator's
  published arming surface frozen (I1). **Done:** merged PR; the TUI toggle round-trips
  intent → orchestrator arming command → observed outcome.

### Orchestrator track — owner: session `orchestrator-autonomous-mode`
- **O1 — orchestrator spec currency + publish the arming contract.** The engine is
  already fully spec'd (v032, scenarios 33-37); this step VALIDATES currency, not
  authors design. Confirm internal consistency, confirm consistency with the
  core irreducible-touchpoints (§4), and — the contract-first deliverable — pin the
  exact PUBLISHED command surface the console calls to arm/disarm autonomous mode
  and to read per-decision audit, resolving the persistence seam (§6.1). Route any
  real change via propose-change → Fable review → revise. **Gate:** Step 0.
  **Done:** the arming/audit contract is frozen and cross-referenced by the console
  plan (this unblocks C3).
- **O2 — implement the engine (`bd-ib-82a`).** Groom `bd-ib-82a` into
  dependency-layered slices, then build: the `dispatcher.autonomous_mode` config key
  + `drive --mode autonomous` gate-collapse (effective admission→auto, effective
  acceptance→ai-only) + the NEW LLM decision stage that resolves
  `blocked_reason: needs-human` items instead of parking (routing resolved items
  back onto their normal path) + truly-unresolvable escalation (§4) + the
  per-decision audit journal. COMPOSES the shipped valve/escalation/cost-gate
  machinery; never bypasses it. **Gate:** O1. **Done:** scenarios 33-37 pass;
  merged slices.

### Integration — owner: driver session `autonomous-mode`
- **I1 — contract handshake.** O1's arming/audit contract is published EARLY and
  frozen so C3 builds against it. This is a coordination gate, not a code step.
- **I2 — end-to-end live exercise (MVP acceptance / "done").** On a REAL tenant:
  flip autonomous mode ON from the TUI → the orchestrator engine drives ready work
  to `done` unattended → the console observes and reflects each auto-resolution →
  a truly-unresolvable item surfaces in-TUI as needs-attention and is actionable
  there. Per the "done means rolled out and exercised live" discipline, this live
  evidence is the MVP acceptance. **Gate:** C3 AND O2.

**Dependency graph (text):**
```
Step 0 ─► C1 ─► C2 ─► C3 ─► I2
Step 0 ─► O1 ─► O2 ─────────► I2
        O1 (arming contract, I1) ─► C3
```
C2 (console) and O1→O2 (orchestrator) run **concurrently** after their spec steps —
that concurrency is the entire reason for two delegate sessions.

## 8. tmux / session delegation model

This overall plan is driven from a single **driver** Claude session named
`autonomous-mode`, running in the tmux pane/window **`livespec-autonomous-mode`**
(working directory `/data/projects/livespec`). The driver owns this plan, the
dependency gates, dispatch, and synthesis; it does NOT hand-code the repo work
inline.

Two **delegate** sessions, each a Claude session named the same as its tmux pane,
drive one repo apiece and resume their own repo's `plan/autonomous-mode/handoff.md`:

| tmux pane / Claude session | Working dir | Drives | Steps |
|---|---|---|---|
| `livespec-autonomous-mode` (driver session `autonomous-mode`) | `/data/projects/livespec` | this overall plan + Step 0 + integration | Step 0, I1, I2 |
| `console-autonomous-mode` | `/data/projects/livespec-console-beads-fabro` | console operator surface | C1, C2, C3 |
| `orchestrator-autonomous-mode` | `/data/projects/livespec-orchestrator-beads-fabro` | orchestrator decision engine | O1, O2 |

Coordination discipline:
- **Contract-first:** the orchestrator publishes its arming/audit contract (O1/I1)
  before the console builds against it (C3). This is the single most important
  sequencing rule — it lets the two tracks proceed in parallel without diverging.
- Each delegate uses the repo mutation protocol (worktree → PR → merge → cleanup)
  and its own tenant's ledger/credentials. Sessions do not touch another session's
  worktree or branch.
- The driver re-engages delegates only at clean boundaries (a merged PR, a ratified
  revision) and surfaces only genuinely unavoidable gates to the maintainer, each
  with a recommendation.

## 9. Upstream dependencies this plan TRACKS (does not re-own)

- **`livespec-nrdk` — factory-safe-by-default** (own active thread
  `livespec/plan/factory-safe-by-default/`, backlog). The admission gate that
  refuses a not-factory-safe item at dispatch decides *what an autonomous engine may
  auto-admit unattended.* The engine's auto-admission (O2) is only as safe as this
  gate. Sequence O2's auto-admit slice to land on or after `nrdk`'s admission-gate
  slice, or explicitly scope O2 to the current admission semantics and note the
  follow-up.
- **`livespec-0jxs` — dark-factory operability preconditions** (backlog):
  failure-notification, escalation, telemetry shipping, verified cost ceiling. Safe
  unattended running needs these. The console's observe/reflect/needs-attention
  surface answers the escalation/notification half; the cost-ceiling half already
  has a fail-closed seam in the orchestrator (`cost_gate_decision`). Track both;
  gate the I2 live exercise on at least the cost-ceiling and a failure-surfacing
  path being real.
- **`livespec-orchestrator-beads-fabro/plan/fabro-token-refresh/`** (active, infra):
  the Fabro GitHub-App installation-token 60-minute TTL kills long factory runs at
  the publish/PR node. A long autonomous run must be able to publish. No shared code
  surface with gate-resolution; track as a robustness precondition for I2.

## 10. Definition of done (MVP)

The MVP is done when I2's live-exercise evidence is journaled: on a real tenant,
the operator enables full autonomous mode from the TUI (dangerous-labelled,
type-to-confirm), the factory drives ready work to `done` unattended with every
auto-resolution audited, the console reflects it live, and a truly-unresolvable
item (including any irreducible human touchpoint) surfaces in-TUI as an actionable
needs-attention item. Merged + CI-green + AI-accepted is NOT done without that live
evidence.

## 11. Repo mutation discipline (applies to every step)

Worktree → PR → merge → cleanup, from each repo's own primary checkout on
`origin/master`; `mise exec -- git …` so hooks fire; never `--no-verify`; plan-doc
commits are `docs(plan): …` (no product code, so they skip the Red-Green-Replay
ritual). End every touched repo back on `master`, clean.
