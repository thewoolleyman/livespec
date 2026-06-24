---
proposal: mermaid-default-scrub-rendering.md
decision: accept
revised_at: 2026-06-24T21:23:18Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accept: make Mermaid the standard and default diagram format and remove the PlantUML-oriented rendering machinery from the contract. Collapse the spec_files kind discriminator to markdown only; drop the diagram_source/diagram_rendered kinds, the derived_from invariant, the .livespec.jsonc render_commands shape, the revise render lifecycle, and the doctor-diagram-source-rendered-drift check; redefine the history snapshot to capture the whole spec tree so committed image assets survive without manifest enumeration. Alternate tools (PlantUML/Graphviz) survive only as a single acknowledgment: render outside livespec and commit an opaque image. This dissolves livespec-lly4 at the root. Paired code/template/prose changes land in the same branch outside the propose-change/revise loop.

## Resulting Changes

- spec.md
- contracts.md
- constraints.md
