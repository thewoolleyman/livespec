---
topic: python-style-testing
author: Claude Sonnet 4.6 (1M context)
created_at: 2026-05-06T16:30:00Z
---

## Proposal: Migrate style-doc §"Testing" into `SPECIFICATION/spec.md`

### Target specification files

- SPECIFICATION/spec.md

### Summary

Cycle 11 of Plan Phase 8 item 2 per-section migration. EXPAND existing `## Testing approach` in `spec.md` by appending the style-doc content not yet present: fixture-mutation prohibition, network-access prohibition, test-ordering independence, parametrize idiom, no-third-party-assertion, pytest-icdiff, heading-coverage and wrapper meta-test references, plus two `###` sub-sections (`### Property-based testing for pure modules`, `### Mutation testing as release-gate`). Source-doc lines 1173-1314. No new `##` headings.
