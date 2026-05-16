# Draft — tool-agnostic workflow diagram

**Status:** DRAFT for review (v2). Not yet integrated into the
canonical [`2026-05-11-architecture-summary.html`](./2026-05-11-architecture-summary.md);
expected to iterate based on review feedback before promotion.

**Purpose:** represent the fundamental spec ↔ implementation
workflow with **tool-agnostic, generic domain terminology**
(NOT bound to `livespec`, `/livespec:*` skill names, or any
specific implementation plugin). Most concepts map directly to
existing skills, but the diagram intentionally floats above the
tooling layer.

**Layout conventions:**

- **Top → bottom** vertical stacking. SPEC SIDE on top, IMPLEMENTATION SIDE on bottom.
- Lines crossing the package boundary are **hard contracts**
  between the two sides; rendered in red for visibility.
- **Arrow direction = data flow.** An arrow from `A → B` means
  data flows from `A` into `B` (so a read goes
  `artifact → skill`; a write goes `skill → artifact`).
- **Shape vocabulary:**
  - rounded blue rectangle = skill / operation (the verb is the node's name)
  - tan cylinder = artifact / store / queue (noun)
  - stick figure = user / agent
- **Arrow labels** are used sparingly — only where the arrow's
  meaning is genuinely ambiguous (e.g., the multiple
  dispositions out of `Process Memos`). Otherwise the verb
  lives in the source node and the direction carries the
  semantic.

## Diagram

![Draft tool-agnostic workflow](./diagrams/draft-tool-agnostic-workflow.svg)

[PlantUML source](./diagrams/draft-tool-agnostic-workflow.plantuml)

## Cross-boundary contracts (the load-bearing red edges)

| # | Direction | Edge | Meaning |
|---|---|---|---|
| 1 | spec ⇣ impl | `Specification → Capture Impl Drift` | The prescription. Capture Impl Drift reads the spec to detect what impl is missing. |
| 2 | impl ⇡ spec | `Capture Spec Drift → Propose Change` | Drift findings (impl observed correct, spec lagging) feed into the spec lifecycle as proposals. |
| 3 | impl ⇡ spec | `Process Memos → Propose Change` (spec-bound) | Spec-bound memo dispositions become proposals. |
| 4 | impl ⇡ spec | `Memos → Doctor` (untriaged) | Doctor reads untriaged-memo inventory for its hygiene invariant check. |

## Changes from v1

- Vertical stacking (was horizontal — got too wide).
- All arrows are now directional **data-flow** edges; verbs live
  in source-node names, not in arrow labels.
- Cross-boundary arrows visually distinguished by **color**
  (red) instead of the confusing `===>` thick-arrow convention.
- Doctor's hygiene query renders as `Memos → Doctor` (data
  flows back to doctor as query result), not `Doctor → Memos`.
- Dropped `List Memos` and `Prune History` from the diagram
  (tangential to the spec ↔ impl drift story; can re-add if
  needed).
- Removed `Spec → Capture Spec Drift` cross-boundary read
  (implied by positioning; was creating crossing).
- Inspired by the layout style of
  [`archive/.../2026-04-19-nlspec-lifecycle-diagram.md`](../../archive/brainstorming/approach-2-nlspec-based/2026-04-19-nlspec-lifecycle-diagram.md).
