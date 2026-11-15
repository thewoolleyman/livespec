---
proposal: wrapper-cli-surface-pre-check-pair.md
decision: accept
revised_at: 2026-11-15T05:08:09Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted by the decider, legacy-coordinator-agent, under its R301 authority (plan epic overseer-iyfjbo), as a conformance proposal. contracts.md §"Sub-command wire contracts" requires the mutually exclusive `--skip-pre-check` / `--run-pre-check` pair on the propose-change, critique, revise and prune-history wrappers, while the §"Wrapper CLI surface" table listed it only for prune-history. The shipped wrappers already accept the pair (livespec-b37cfx, 4aef25f1, v0.47.11), so this conforms the table to the normative clause and to the implementation; no behavior changes, so no new scenario is owed. seed is not given the pair because the wire contract omits it. Stale-branch precondition (Step 3.5) skipped via `--skip-stale-branch-check` at the decider's ruling. Warning, recorded verbatim: "spec/doctor-surfaces-open-spec-pull-requests (livespec#3250, e887b75b) is a live, graded PASS, unrelated proposal by throughput-plans-coordinator; neither merged nor abandoned; no file overlap with fleet secrets or the wrapper table."

## Resulting Changes

- contracts.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-15T05:07:39Z
verdict: NO BLOCKERS
proposal_stem: wrapper-cli-surface-pre-check-pair
content_digest: ef64043b62e2b8272d91d1d9ea3f55c445c65b9042b531e009c7da5b3fe4ceb0
