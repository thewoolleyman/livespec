---
proposal: fix-constraints-livespec-runtime-vendored-entries.md
decision: accept
revised_at: 2026-05-27T06:10:01Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Both sub-proposals are factual corrections of constraints.md to match already-merged reality. Sub-proposal 1: upstream livespec-runtime declares MIT in its pyproject.toml and the vendored LICENSE/NOTICES.md both record MIT; the BSD-3-Clause attribution in constraints.md is the only artifact carrying the wrong license token. MIT is on the permitted license set (§"Lib admission policy"), so the correction preserves the admission outcome. Sub-proposal 2: livespec_runtime was vendored in PR #284 and just vendor-update livespec_runtime is invoked by the reusable-bump-pin-from-dispatch.yml workflow, but the §"Vendoring procedure" re-vendoring enumeration was never updated, so the blessed-mutation-path rule does not formally cover this lib. Both edits are surgical (single bullet each) and leave the constraints.md H2 set untouched, so no tests/heading-coverage.json update is required.

## Resulting Changes

- constraints.md
