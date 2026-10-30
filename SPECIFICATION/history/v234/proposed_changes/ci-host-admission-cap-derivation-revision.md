---
proposal: ci-host-admission-cap-derivation.md
decision: accept
revised_at: 2026-10-30T21:11:27Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

ACCEPT. Adds the maintainer-directed (2026-09-06) property that a container host's job-admission cap is a throughput decision derived from job-duration growth and control-plane responsiveness, never from a CPU-utilization target, and that the control plane keeps enough CPU under full contention without idling cores. The clause matches the provisioning repository's derivation record (livespec-dev-tooling ci-runner/k3s/phase2/kueue/DERIVATION.md, C = 64 entry) and is stated as host-observable properties per the section's opening rule. Delegated decision; the independent reviewer returned NO BLOCKERS on these exact bytes. Reviewer: separately spawned read-only Sonnet 5.5 agent abbaca9a9ce1360a0.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-30T21:09:51Z
verdict: NO BLOCKERS
proposal_stem: ci-host-admission-cap-derivation
content_digest: 48998ef2527edc359e7b066614ce58950dfde8772e6107f449ab39a3b9c753f9
