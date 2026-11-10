---
proposal: hold-label-disarm-inherited-policy.md
decision: accept
revised_at: 2026-11-10T23:30:14Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted as filed under delegated revise authority (legacy-coordinator-agent R301, 2026-11-10, --only-topic). The inserted bullet, inherited-policy paragraph and error-path scenario are the proposal's text, byte for byte. The behaviour matches what shipped and was independently replayed host_verified in livespec-dev-tooling#4051 (t2ezzq) and livespec#3159 (jznfgw). The proposal's co-edits land in the same pull request, outside the spec bytes: the orchestrator-plugin template disarm-on-hold-label.yml.jinja (identical to livespec's root copy except that its App-token input is `app-id:`, matching the template's own auto-enable-merge.yml.jinja; livespec's copies use `client-id:`), the copier-template-workflow-coverage REQUIRED_WORKFLOW_FILES entry (by Red-Green), the four seed helpers' workflow lists, and the heading-coverage row backed by the integration test tests/integration/test_hold_label_disarm_template.py, which renders the template in-process with copier. The independent sonnet review reported NO BLOCKERS on the exact bytes.

## Resulting Changes

- non-functional-requirements.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-10T23:19:12Z
verdict: NO BLOCKERS
proposal_stem: hold-label-disarm-inherited-policy
content_digest: 3d0c44bdbf1cc7848897b650847568f6ca5bdaa99da27d7d988f02c15c658108
