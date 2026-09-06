---
proposal: ci-host-backlog-object-bound.md
decision: accept
revised_at: 2026-09-06T09:11:47Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5-1 (poweredge-raid-array-maintenance plan session, Claude Code)
---

## Decision and Rationale

Accept: insert one bold-led clause into section "Self-hosted CI runner host requirements", immediately after the schedulable-unit-capacity clause and before the storage-tiers clause, requiring a host that caps job concurrency through a scheduler to bound the jobs it represents as control-plane objects (running, and pending admission) to a small multiple of the admission cap, with queued work beyond that bound waiting at the forge; property only, the multiple, floor and mechanism stay with the provisioning repository. Design record: livespec-dev-tooling ci-runner/k3s/phase2/kueue/DERIVATION.md "Bounding maxRunners to the quota (2026-09-06)" and the measurement on child livespec-e2vcqf and epic livespec-ifwnqj (2026-09-06 07:38Z-07:50Z: 122 gated runner objects and 119 pending scheduler workloads at 25-30 running, 11 kine writes over one second in ten minutes; the first bounded backlog at 08:58Z held 31 pending under the bound with zero such writes). Maintainer-directed 2026-09-06 in session. Both anchors verified verbatim exactly once in the pre-revise file; the resulting text was derived mechanically from the proposal's blockquoted paragraph; no `## ` heading added, changed, or removed, so no tests/heading-coverage.json co-edit. Independent adversarial review (Fable, read-only) found two blockers and four nits, all folded in livespec PR #2599 and re-confirmed NO-BLOCKERS on the folded bytes; the configured opus ratification reviewer then returned NO BLOCKERS on these exact resulting bytes with the digest recomputed independently. Companion clause in the provisioning repository: livespec-dev-tooling proposed change scale-set-ceiling-bounded-to-fair-share.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-06T09:10:22Z
verdict: NO BLOCKERS
proposal_stem: ci-host-backlog-object-bound
content_digest: 8c5df86c3d8b2d3d31bc967cddc2d64fffcca18212769be87cf53b99ec5e8c0d
