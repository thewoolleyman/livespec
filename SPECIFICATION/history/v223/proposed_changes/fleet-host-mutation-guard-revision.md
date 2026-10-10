---
proposal: fleet-host-mutation-guard.md
decision: accept
revised_at: 2026-10-10T08:05:47Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-fable-5-1
---

## Decision and Rationale

ACCEPT. The clause states the required surface and behavioural discipline of the fleet-host mutation guard shipped in livespec-driver-claude#750 (head 3130d8a), decoupled from the deferred gitops-deployment-topic clause per the maintainer's 2026-10-10 Definition of Done on epic livespec-qurhq2. Where the clause departs from its design record, livespec plan/gitops-deployment-discipline/research/000-failures-root-causes-and-binding-fixes-2026-09-12.md section 3 (the clause now stands without the deferred topic requirement, and states the guard's required surface rather than its detection internals), the departure is deliberate and was ruled on the epic's scope event of 2026-10-10. Independent ratification review: a separate read-only opus reviewer returned NO BLOCKERS on a narrow delta verification of these exact bytes (replace-target fidelity, byte-for-byte reconstruction of all four resulting files, presence of the four round-3 fixes, and passing heading-coverage and debt-register checks), after full review rounds 1-3.

## Resulting Changes

- contracts.md
- scenarios.md
- ../tests/heading-coverage.json
- ../tests/heading-coverage-debt.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-10T08:05:00Z
verdict: NO BLOCKERS
proposal_stem: fleet-host-mutation-guard
content_digest: 7c66e230542aaafaee2f48ea7f47a8357a91d4a15fb5a14c82e2d6d008c67a73
