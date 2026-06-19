---
proposal: ci-telemetry-export.md
decision: accept
revised_at: 2026-06-19T18:27:31Z
author_human: E2E Test <e2e-test@example.com>
author_llm: livespec-claude-opus-4-8
---

## Decision and Rationale

Accept as-proposed. The CI-telemetry export is already deployed and merged across all six family repos plus the impl-plugin template; this revise records the durable contract (family-wide CI export of per-run job timings to the shared Honeycomb environment; closed-loop self-verification that fails the run on non-receipt so the pipeline cannot die silently; master-push/merge_group-only gating; write-only least-privilege per-repo ingest-key discipline; copier-template inheritance) in core's non-functional-requirements as its canonical home. The section is an H3 sibling under `## Contracts` with no new `## ` heading, so no `tests/heading-coverage.json` co-edit is required.

## Resulting Changes

- non-functional-requirements.md
