---
topic: merge-queue-exception-names-the-recovery-principal
author: claude-opus-5-5
created_at: 2026-11-14T08:29:21Z
---

## Proposal: The merge-queue exception names the recovery principal, in contracts.md's own terms

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Condition (b) of NFR "Merge queue on organization-owned repositories" (v246) exempts "the recovery bypass actor" of contracts.md §"Expedited incident response policy". That section never uses the phrase. It names an independently provisioned recovery principal acting with no-check recovery authority. Rename the exception to match, with no change in meaning.

### Motivation

throughput-plans-coordinator's grade of livespec#3223 (v246) noted, non-blocking, that condition (b) cites a term its referenced section does not define. contracts.md §"Expedited incident response policy" says "An independently provisioned recovery principal MUST merge only the validated complete inverse…" and speaks of "no-check recovery authority". The same NFR section's incident-precedence clause already says "Recovery-principal authorization". A reader following the cross-reference should find the actor by name. The text was carried verbatim from the accepted proposal, so it is corrected by its own proposal rather than silently in the revise. Plan stale-base-merge-options, livespec-dev-tooling epic livespec-dev-tooling-xowhol.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §"CI as a merge gate (branch protection)", paragraph **Merge queue on organization-owned repositories**, replace:

> the one exception being the recovery bypass actor of `contracts.md` §"Expedited incident response policy", whose push still runs the full aggregate on `master`;

with:

> the one exception being the independently provisioned recovery principal of `contracts.md` §"Expedited incident response policy", acting with its no-check recovery authority, whose push still runs the full aggregate on `master`;

Nothing else changes. No heading or scenario is added or changed, because the clause's behavior is unchanged.
