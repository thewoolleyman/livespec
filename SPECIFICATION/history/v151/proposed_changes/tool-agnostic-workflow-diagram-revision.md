---
proposal: tool-agnostic-workflow-diagram.md
decision: modify
revised_at: 2026-06-27T06:23:04Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accept additively as a new top '## ' section of spec.md. Per the maintainer's ruling, the overlap with the existing architecture diagrams is INTENTIONAL (different zoom levels) — an explicit exception to the no-duplication discipline; NO existing diagram is retired or consolidated. The proposal's four open framing questions are all resolved: keep heading/detail/spine as proposed; overlap deliberate.

## Modifications

Appended an exception-note paragraph to the section caption recording the maintainer's intentional-overlap ruling and naming the related diagrams (§'Workflow planes and the Planning Lane', §'Lifecycle', §'Contract + reference implementations architecture'). Co-edited tests/heading-coverage.json (../tests/heading-coverage.json) with a TODO+reason entry for the new H2 (diagram-only, no clauses[] link), per the proposal's required co-edit. The README-link remains a declared spec_commitments impl-followup (readme-link-lifecycle-diagram), captured as a separate impl work-item after this revise lands — not part of this spec diff.

## Resulting Changes

- spec.md
- ../tests/heading-coverage.json
