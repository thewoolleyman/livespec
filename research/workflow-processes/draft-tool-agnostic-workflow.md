# Draft — tool-agnostic workflow diagram

**Status:** DRAFT for review (v8). Not yet integrated into the
canonical
[`2026-05-11-architecture-summary.html`](./2026-05-11-architecture-summary.md);
expected to iterate based on review feedback before promotion.

**Purpose:** represent the fundamental spec ↔ implementation
workflow with **tool-agnostic, generic domain terminology**
(NOT bound to `livespec`, `/livespec:*` skill names, or any
specific implementation plugin).

**Layout conventions:**

- **SPEC SIDE** (pink package, left) ▏ **IMPLEMENTATION SIDE** (green package, right). Side-by-side rather than vertically stacked — see *Layout history* below for why.
- **Arrow direction = data flow.** A read goes `artifact → skill`; a write goes `skill → artifact`.
- **Shape vocabulary:**
  - light blue rounded rectangle = skill / operation (verb is in the node name)
  - tan cylinder = artifact / store / queue (noun)
  - yellow rectangle = external input (the single entry point)
- No actor figures. Any action can be taken by a human or an agent; the actor distinction isn't load-bearing. A single yellow input rectangle ("initial intent / prompt / instruction / seed") represents the external entry point into Seed.
- **Cross-boundary edges** between the two packages are **hard contracts**; rendered as thick red lines.
- All arrows are pure black for contrast; all node text is dark.
- Arrow labels are sparse — only where genuinely ambiguous (Process Memos disposition branches; Doctor's untriaged-memo query).

## Diagram

![Draft tool-agnostic workflow](./diagrams/draft-tool-agnostic-workflow.svg)

[PlantUML source](./diagrams/draft-tool-agnostic-workflow.plantuml)

## Cross-boundary contracts (the load-bearing red edges)

| # | Direction | Edge | Meaning |
|---|---|---|---|
| 1 | spec → impl | `Specification → Capture Impl Drift` | The prescription. Capture Impl Drift reads the spec to detect what impl is missing. |
| 2 | spec → impl | `Specification → Capture Spec Drift` | Capture Spec Drift compares observed impl against the spec to find spec-side drift. |
| 3 | impl → spec | `Capture Spec Drift → Propose Change` | Drift findings (impl observed correct, spec lagging) feed back as proposals. |
| 4 | impl → spec | `Process Memos → Propose Change` (spec-bound) | Spec-bound memo dispositions become proposals. |
| 5 | impl → spec | `Memos → Doctor` (untriaged) | Doctor reads untriaged-memo inventory for its hygiene invariant check. |

## Open questions for review

- Cross-boundary red arrows take long winding routes around the
  diagram instead of crossing the wall directly. PlantUML routes
  edges around nodes; constrained by the side-by-side layout.
- `spec-bound` and `untriaged` labels sit on the far right edge,
  semantically detached from where the visual arrow turns.
- `List Memos` and `Prune History` still dropped (tangential to
  the spec ↔ impl drift story); re-add if they belong on the
  canonical diagram.
- Vertical stacking was attempted (v4-v7) but the trade-offs
  weren't worth it — see *Layout history*.

## Layout history

The layout has gone through several iterations:

- **v1 (`32edbd5`):** PlantUML deployment with `package`
  containers, `top to bottom direction`. Rendered side-by-side
  (dot won't stack containers vertically when there are
  bidirectional cross-container edges).
- **v2 (`3e83aba`):** Added hidden vertical edges, reverted to
  plain arrows. Still side-by-side.
- **v3 (Mermaid, `dcd6335`):** Switched to Mermaid for
  reliable `flowchart TB` + `subgraph` vertical stacking.
  Reverted — staying on PlantUML.
- **v4 (`e96efb1`):** Flat layout, no outer containers,
  hidden vertical edges + horizontal yellow WALL divider.
  First working vertical stacking, but intra-section layout
  was loose.
- **v5-v6 (unpushed):** Tried `linetype ortho`, aggressive
  hidden edges anchoring the WALL. WALL kept getting pulled
  out of position by visible cross-boundary edges.
- **v7 (`6a0dfbb`):** Added `together { }` blocks. Vertical
  stacking mostly worked, but the WALL rendered as a
  fixed-width rectangle (not a real divider), Capture Impl
  Drift and Capture Memo were pulled above the WALL by
  visible Spec edges, and cross-boundary arrows took long
  winding paths.
- **v8 (this version, `4383ff2`):** Back to `package`
  containers (side-by-side). Reviewer judges container
  grouping cleaner than flat-layout vertical with messy
  positioning. All v7 content improvements kept:
  - Single yellow input box (no User/Agent actor figures)
  - Spec → Capture Spec Drift cross-boundary edge
  - Pure black ArrowColor
  - Explicit dark FontColor on all nodes
  - No bold-markup artifacts
