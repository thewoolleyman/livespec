---
proposal: primary-playwright-artifact-guard.md
decision: modify
revised_at: 2026-08-05T22:19:48Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: gpt-5.6
---

## Decision and Rationale

Ratify the user-directed invariant that governed primary checkouts remain artifact-free. The contract refuses the complete Playwright MCP surface because both explicit screenshots and automatic browser logs can write files, allows linked worktrees, preserves fail-open behavior unless a governed primary is positively identified, and records host cache redirection only as defense in depth. The modification adds the required local lockstep test and clause/scenario registry links and re-derives the existing runtime-specific-hook enumeration.

## Modifications

Add a local core lockstep test for the new contract/scenario/registry triad, map the scenario heading to that test instead of a cross-repo test identifier, add the self-application-required clause-to-scenario gap link, and include the new guard in the existing runtime-specific-hook enumeration.

## Resulting Changes

- contracts.md
- scenarios.md
- ../tests/heading-coverage.json
- ../tests/test_plugin_distribution.py

## Ratification Review

ratification_review: manual-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-05T22:48:53Z
verdict: NO BLOCKERS
proposal_stem: primary-playwright-artifact-guard
content_digest: f2f58319978ea2097b2f98b69e9403b234cfe055123ef1c2d7ac1b33b49f0a9b
