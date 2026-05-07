---
proposal: add-non-functional-requirements-file-to-template.md
decision: accept
revised_at: 2026-05-07T22:30:02Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Co-authored with the user earlier in this session via a sketch-and-approve dialogue. Adds non-functional-requirements.md as a sixth member of the livespec template's seedable file set with a clearly-defined boundary against spec.md/contracts.md/constraints.md/scenarios.md. No content migration in this revision; that is a separate atomic propose-change against the main spec tree once the main-tree file is created. Companion code/asset changes (seed-time scaffolding stub at .claude-plugin/specification-templates/livespec/specification-template/SPECIFICATION/non-functional-requirements.md, seed prompt update, doctor template-files-present widening, test-fixture updates) land in the same PR outside the spec tree.

## Resulting Changes

- spec.md
- constraints.md
