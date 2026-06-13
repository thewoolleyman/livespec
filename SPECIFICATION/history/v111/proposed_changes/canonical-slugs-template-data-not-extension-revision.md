---
proposal: canonical-slugs-template-data-not-extension.md
decision: accept
revised_at: 2026-06-13T19:16:33Z
author_human: E2E Test <e2e-test@example.com>
author_llm: livespec-fable-5
---

## Decision and Rationale

Accepted as ratified for work-item livespec-2jsj (Option 3' in research/copier-extension-distribution/recommendation.md). The render-time copier _jinja_extension can never be imported on the consumer `copier update` path by construction, so the canonical block renders empty on re-sync and canonical-set growth cannot propagate, defeating the Template-gate contract. Re-expressing the gate as a release-time projection of livespec_dev_tooling.canonical_checks into a committed canonical-slugs.yml (consumed as static template data, with an anti-drift enforcement check) keeps the single source of truth, makes the consumer path import-free and correct, restores propagation via the 3-way merge, and honors the static-vs-executable channel partition. No blocking contradiction with adjacent clauses: the existing 'or equivalent' language already permitted a non-extension mechanism; this tightens it. No `## ` heading is added, removed, or renamed, so tests/heading-coverage.json needs no co-edit.

## Resulting Changes

- contracts.md
