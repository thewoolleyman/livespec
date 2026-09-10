---
proposal: operator-authored-git-commits.md
decision: accept
revised_at: 2026-09-10T15:14:53Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: codex
---

## Decision and Rationale

Accept after independent exact-byte review. The resulting specification defines the opt-in git_author wire shape, binds every livespec fleet member to Chad Woolley <thewoolleyman@gmail.com>, separates author from transport identity, preserves narrowly classified mechanical and genuine third-party authors, and requires fail-closed effective-identity enforcement across installer, commit, dispatch, pre-push, fleet, Red-Green-Replay, revision-metadata, low-level Git, and process-reconciliation paths, with end-to-end scenarios and integration-tier coverage ownership.

## Resulting Changes

- contracts.md
- non-functional-requirements.md
- scenarios.md
- ../tests/heading-coverage.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-10T15:10:00Z
verdict: NO BLOCKERS
proposal_stem: operator-authored-git-commits
content_digest: b511ecac9e0297af975a34d16df38631a9d9445e214c91a5f56ef475d3a0c525
