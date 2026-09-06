---
proposal: ci-host-storage-tiers.md
decision: accept
revised_at: 2026-09-06T02:38:31Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5-1 (poweredge-raid-array-maintenance plan session, Claude Code)
---

## Decision and Rationale

Accept: add the storage-tier clause to §"Self-hosted CI runner host requirements" as host-observable properties (OS and non-reconstructible artifacts on redundant media; job churn and the boot-rebuilt datastore off the OS volume; medium-neutral role identity for every off-OS block-device tier with no two volumes sharing a role identity; configuration reproducible from the job-runtime provisioning repository; runtime refuses to start on an absent tier; media moves by live copy then verified identity transfer in a job-free window; PCIe-endpoint media accepted only after a clean link survey), and correct the section's opening parenthetical from the homelab repository to livespec-dev-tooling's ci-runner tree. Every property was established live on the fleet's CI host in the 2026-09-04 and 2026-09-06 storage windows (plan poweredge-raid-array-maintenance, epic livespec-g52yrb; child livespec-e2vcqf). Three independent read-only reviews preceded ratification: Fable review 1 (2026-09-04) raised four blockers, all applied in PR #2571; Fable review 2 (2026-09-06 00:29Z) returned NO-BLOCKERS with five wording nits, all folded in PR #2577; a fresh Fable reviewer confirmed that fold; the configured opus ratification reviewer returned NO BLOCKERS on the resulting bytes and flagged one positional forward reference, replaced by the named requirement before ratification. The dated attribution "Tier identity maintainer-directed 2026-09-04" is the maintainer's recorded narrowing. Both replace targets verified verbatim exactly once; no ## heading change, so no tests/heading-coverage.json co-edit.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-06T02:37:25Z
verdict: NO BLOCKERS
proposal_stem: ci-host-storage-tiers
content_digest: ff4bc30be14479fa607604e2fddfad455743eac4e5883c52c002a390000062ab
