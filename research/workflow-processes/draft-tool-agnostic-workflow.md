# Draft — tool-agnostic workflow diagram

**Status:** DRAFT for review (v4, PlantUML with vertical
stacking achieved via flat layout). Not yet integrated into the
canonical
[`2026-05-11-architecture-summary.html`](./2026-05-11-architecture-summary.md);
expected to iterate based on review feedback before promotion.

**Purpose:** represent the fundamental spec ↔ implementation
workflow with **tool-agnostic, generic domain terminology**
(NOT bound to `livespec`, `/livespec:*` skill names, or any
specific implementation plugin).

**Layout conventions:**

- **Top → bottom** vertical stacking. SPEC SIDE on top, IMPLEMENTATION SIDE on bottom, with a horizontal yellow WALL divider in the middle.
- **Arrow direction = data flow.** A read goes `artifact → skill`; a write goes `skill → artifact`.
- **Shape vocabulary:**
  - light blue rounded rectangle = skill / operation (verb)
  - tan cylinder = artifact / store / queue (noun)
  - stick figure = user / agent (actor)
- Lines crossing the WALL are **hard contracts** between the two sides; rendered in red.
- Arrow labels are sparse — only where genuinely ambiguous (Process Memos disposition branches; Doctor's untriaged-memo query).

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

## How v4 finally got vertical stacking

PlantUML's `package` / `frame` / `rectangle` container shapes
refuse to stack vertically when there are bidirectional
cross-container edges — verified across v1 (default layout),
v2 (`top to bottom direction` + hidden edges), and v3
(`!pragma layout smetana` + nested wrapper package). The dot
layout engine consistently chose side-by-side cluster placement
because IMPL→SPEC feedback edges flowed "upward" and dot
minimizes edge length.

**v4 approach:** drop the outer containers entirely. All nodes
are free-floating, colored by function (skill = blue, artifact
= tan). A horizontal yellow "WALL" rectangle acts as the
visual divider. Aggressive hidden vertical edges enforce the
top-down order: actors → spec elements → WALL → impl elements.

Trade-off: no visible spec-side / impl-side container
outlines. The side-membership is conveyed by spatial position
(above vs. below the WALL) and by the SPEC SIDE /
IMPLEMENTATION SIDE label boxes.

## Open questions for review

- Intra-section layout has some quirks: Seed positioned after
  Propose Change rather than at the natural top; Critique
  floats to the right of the spec column; Capture Memo
  pulled to the right by the Agent actor. Can be tightened
  with more hidden edges.
- SPEC SIDE / IMPLEMENTATION SIDE label boxes float
  awkwardly — could be moved or restyled to read more clearly
  as section headers.
- Cross-boundary red arrows take long routes around the
  diagram instead of crossing the WALL directly. PlantUML
  routes lines around nodes; nothing to do about it short of
  using `skinparam linetype ortho` (may improve, may make
  worse).
- `List Memos` and `Prune History` still dropped (tangential
  to the spec ↔ impl drift story); re-add if they belong on
  the canonical diagram.

## Failed prior attempts (kept for context)

- **v1 (committed `32edbd5`):** PlantUML deployment with
  `package` containers, `top to bottom direction`. Rendered
  side-by-side.
- **v2 (committed `3e83aba`):** Added hidden vertical edges,
  reverted to plain arrows (dropped `===>`). Still side-by-side.
- **v3 (Mermaid, committed `dcd6335`, then reverted in spirit
  here):** Switched to Mermaid for `flowchart TB` + `subgraph`
  reliable vertical stacking. Rejected — staying on PlantUML.
- **v4 (this commit):** Flat layout, no outer containers,
  hidden vertical edges + WALL divider. First working vertical
  layout.
