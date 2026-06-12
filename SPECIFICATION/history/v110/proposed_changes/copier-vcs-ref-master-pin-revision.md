---
proposal: copier-vcs-ref-master-pin.md
decision: accept
revised_at: 2026-06-12T17:56:17Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accepted as proposed (decision pre-made by standing directive on work-item livespec-3hnd). Premise verified against origin/master: contracts.md §"Shared content sync — copier template" and §"Doctor cross-boundary invariants" plus non-functional-requirements.md §"Shared content provenance" still prescribed bare `copier update` / `copier update --dry-run`, and the generation sentence prescribed `--vcs-ref=<core-release-tag>` with a URL-path subdirectory form copier does not support. The accepted text mirrors the implemented blessed invocations from PR #420 (templates/impl-plugin/copier.yml header, the copier-update-drift workflow command, and the shipped copier-template-workflow-coverage corrective-action text, all of which pin --vcs-ref=master). Descriptive mentions (the historical "`copier update` was never run" clause and the 3-way-merge/copy-time mechanism references) are deliberately left unpinned. No `## ` headings are added, changed, or removed, so tests/heading-coverage.json is unaffected.

## Resulting Changes

- contracts.md
- non-functional-requirements.md
