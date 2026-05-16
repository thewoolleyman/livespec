# Draft — tool-agnostic workflow diagram

**Status:** DRAFT for review. Not yet integrated into the
canonical [`2026-05-11-architecture-summary.html`](./2026-05-11-architecture-summary.md);
expected to iterate based on review feedback before promotion.

**Purpose:** represent the fundamental spec ↔ implementation
workflow with **tool-agnostic, generic domain terminology**
(NOT bound to `livespec`, `/livespec:*` skill names, or any
specific implementation plugin). Most concepts map directly to
existing skills, but the diagram intentionally floats above the
tooling layer.

**Layout conventions:**

- **Left → right** primary process flow; feedback loops curve back R→L.
- **SPEC SIDE** (left, light pink) ▏ **IMPLEMENTATION SIDE** (right, light green).
  Lines crossing the package boundary are **hard contracts**
  between the two sides.
- **Shape vocabulary**:
  - `rectangle` (light blue) = activity / skill
  - `database` (tan cylinder) = artifact / store / queue
  - `actor` (stick figure) = user / agent
- **Arrow vocabulary**:
  - thin solid `→` = write / transition / file
  - dashed `⇢` = read-only observation / query
  - **thick `⇒` = cross-boundary hard contract**

## Diagram

![Draft tool-agnostic workflow](./diagrams/draft-tool-agnostic-workflow.svg)

[PlantUML source](./diagrams/draft-tool-agnostic-workflow.plantuml)

## Cross-boundary contracts (the load-bearing edges)

| # | Direction | Edge | Meaning |
|---|---|---|---|
| 1 | spec → impl | `Specification ⇒ Capture Impl Drift` | The prescription. Spec is the authority impl is checked against. |
| 2 | impl → spec | `Process Memos ⇒ Propose Change` | Spec-bound memo dispositions feed back into the spec lifecycle. |
| 3 | impl → spec | `Capture Spec Drift ⇒ Propose Change` | Impl-observed drift surfaces propose-changes. |
| 4 | spec → impl | `Doctor ⇢ Memos` | Doctor's hygiene query into the impl-side memo store (untriaged inventory). |

## Open uncertainties for review

- Layout density. 12 activities + 7 stores + 2 actors → PlantUML
  auto-layout may produce crossings worth manually adjusting.
- The dashed-thick `Doctor ⇢ Memos` arrow is unconventional;
  may want a different visual treatment for cross-boundary
  read-only edges.
- `List Memos` and `Prune History` are included for completeness
  but tangential to the spec ↔ impl drift story. Candidates to
  drop if simplification is desired.
- `Capture Spec Drift` receives both `Impl ⇢ ...` and
  `Spec ⇢ ...` to show the comparison; the `Spec ⇢` line crosses
  the boundary. Could drop and imply via positioning.
- Color choice (pink/green) is arbitrary.
