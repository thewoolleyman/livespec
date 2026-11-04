---
proposal: config-value-fast-path.md
decision: modify
revised_at: 2026-11-04T19:58:49Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude:ci-runtime-and-cost
---

## Decision and Rationale

Accepted under R301 by legacy-coordinator-agent on the maintainer's behalf. The maintainer direction is recorded verbatim on livespec-dev-tooling-6tgd2z (2026-11-04 ~18:4xZ): "why does it takes a whole PR just to make the change. Even if the file is committed, it should be a short circuit, no-tests change to change the wip or cap values. NO TEST SHOULD BE TIED TO CONFIG VALUE ACTUAL VALUES. IF any of this is the case, fix it." The new paragraph is a scoped exception to PR gate ≡ master gate: one committed predicate, applied identically on pull_request and master push, so a PR never runs fewer gating checks than master. An independent read-only sonnet reviewer found NO BLOCKERS on the exact bytes.

## Modifications

Formatting only: the proposal's scenario is written as a fenced gherkin block, split into three Scenarios (value-only, invalid value, any other line), to match the house style of scenarios.md. The NFR paragraph folds the proposal's bullets into prose and adds a one-line motivation sentence. No rule was added or dropped.

## Resulting Changes

- non-functional-requirements.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-04T19:58:17Z
verdict: NO BLOCKERS
proposal_stem: config-value-fast-path
content_digest: 04fa43b3a79bf435705fba0e9ff371f84570a5c94715dfdb75aac162132a3afe
