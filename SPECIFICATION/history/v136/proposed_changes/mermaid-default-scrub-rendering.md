---
topic: mermaid-default-scrub-rendering
author: claude-opus-4-8
created_at: 2026-06-24T15:45:00Z
---

## Proposal: Mermaid as the default diagram format; remove the diagram-rendering machinery

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

Make Mermaid livespec's standard AND default (and only first-class) diagram format, and remove the PlantUML-oriented diagram-rendering machinery from the contract entirely. Collapse the `spec_files` manifest `kind` discriminator to its single remaining value `markdown`; drop the `diagram_source` and `diagram_rendered` kinds, the `derived_from` cross-property invariant, the `.livespec.jsonc` `render_commands` shape, the revise-lifecycle rendering integration, and the `doctor-diagram-source-rendered-drift` static check. The history snapshot is redefined to capture the WHOLE spec tree (every file under the spec root except the `history/`, `proposed_changes/`, and `templates/` sibling subdirs), so any committed image is preserved across revisions without the manifest having to enumerate rendered outputs. PlantUML/Graphviz survive only as a single acknowledgment: an author MAY use an alternate diagram tool by rendering an image OUTSIDE livespec and committing it as an opaque asset livespec does not manage.

### Motivation

The entire `diagram_source` → `diagram_rendered` → `render_commands` → render-on-revise → drift-check pipeline exists for one reason: PlantUML and similar tools do not render natively on GitHub, so livespec had to commit a pre-rendered SVG and keep it in sync with its source. Mermaid renders natively in GitHub, IDEs, and markdown previewers and is read natively by LLMs, so it needs none of that machinery. Research concluded Mermaid is superior in virtually all cases; PlantUML/Graphviz are rare escape hatches at most. Keeping a whole slab of first-class contract surface (two extra file kinds, a config contract, a render lifecycle, a doctor check, rendered-files-in-history) for a rarely-appropriate tool violates "specify architecture, not mechanism" and the escape-hatch-reshaping principle. Removing it also dissolves work-item `livespec-lly4` at the root: with no required PlantUML starter files, a Mermaid-only project using `livespec-with-diagrams` passes `template-files-present` with no extra files.

### Proposed Changes

1. spec.md §"Template manifest": `kind`'s only value is `markdown`; Mermaid is the standard AND default diagram format (fenced blocks in markdown, native rendering, no manifest/render/history special-casing); add one paragraph that alternate tools (PlantUML/Graphviz) MAY be used by committing an externally-rendered image livespec treats as an opaque asset.
2. spec.md: rename §"Per-kind behavior axes" → §"Lifecycle participation"; markdown-shaped checks + LLM-context apply to `kind: markdown`; history snapshots capture the WHOLE spec tree (preserving committed image assets). Delete §"Rendering in the revise lifecycle" and §"Multi-diagram-per-source accommodation". Drop the `doctor-diagram-source-rendered-drift` paragraph from §"Heading-coverage and doctor-static rewiring". Trim §"Explicitly rejected alternatives" to the one non-diagram bullet (proposals-not-patches).
3. contracts.md §"Template manifest wire contract": each declaration carries `{"kind": "markdown"}` only; remove the `diagram_source`/`diagram_rendered` shapes and the `derived_from` rule. Delete §"`.livespec.jsonc` render-commands shape".
4. constraints.md §"Renderer non-vendoring": livespec MUST NOT vendor OR invoke any diagram renderer; Mermaid renders natively; an alternate tool's image is rendered outside livespec and committed as an opaque asset; livespec never detects/recommends/installs/invokes a renderer.

The paired code + built-in-template changes (deleting the render modules, the drift check, and the `render_commands` config; collapsing the `SpecFileKind` Literal; whole-tree history snapshot; scrubbing the `livespec-with-diagrams` template and `prose/seed.md`) land alongside this revision in the same branch/PR but outside the propose-change/revise loop, as they touch product `.py`, template data, and prose rather than the main spec tree.
