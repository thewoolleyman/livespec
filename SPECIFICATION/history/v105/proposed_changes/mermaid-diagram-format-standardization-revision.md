---
proposal: mermaid-diagram-format-standardization.md
decision: accept
revised_at: 2026-06-10T16:32:27Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Ratifies the 2026-06-10 user decision adopting Mermaid as livespec's standardized diagram format, backed by the committed research at research/workflow-processes/mermaid-vs-plantuml-llm-readable-specs.md (GitHub-native rendering eliminates the source-render pairing and render pipeline for common diagram types; training-data familiarity and token compactness favor Mermaid). Wave 0a of the v103-realization rollout (epic livespec-4moata, work-item livespec-0nfr). The existing diagram_source/diagram_rendered manifest mechanism is retained as the PlantUML escape hatch, so no capability is removed. The two riders are cosmetic fixes pre-recorded in memo livespec-bhwnuk: a Markdown blank-line rendering bug in constraints.md and two citation forms in contracts.md that violate the exact-heading-text rule of section 'Reference discipline'. No H2 headings change, so tests/heading-coverage.json needs no co-edit.

## Resulting Changes

- spec.md
- constraints.md
- contracts.md
