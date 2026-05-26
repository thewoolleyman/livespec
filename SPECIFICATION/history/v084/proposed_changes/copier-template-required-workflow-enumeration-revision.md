---
proposal: copier-template-required-workflow-enumeration.md
decision: accept
revised_at: 2026-05-26T08:17:59Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

PC #5 of the Wave 1 safety-net ratification per tmp/prompt.md. Enumerates the exhaustive set of required .github/workflows/ files in the copier template (replacing the loose .github/workflows/*.yml placeholder) and adds the copier-template-workflow-coverage doctor cross-boundary invariant that fails when a consumer is missing any required file. Pairs with PC #2 Layer 2 to close the workflow-coverage gap that caused the 2026-05-26 incident (livespec-impl-plaintext PR #26 OPEN/CLEAN for 10+ minutes because auto-enable-merge.yml was absent). Pre-existing work-items li-tmpwfs (add missing Jinja templates) and li-dctwfc (implement the doctor invariant) gate on this acceptance.

## Resulting Changes

- contracts.md
