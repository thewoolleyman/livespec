---
proposal: the-stale-worktree-reaper-force.md
decision: accept
revised_at: 2026-11-12T06:03:16Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted as filed under delegated revise authority, in the livespec revise slot legacy-coordinator-agent assigned to the dev-host-disk-retention plan (livespec-dev-tooling-qgwxo4), which owns livespec-inmgc7. The independent sonnet review found the single inserted paragraph matches the proposal word for word, and found no blockers. Its nits are not acted on. (1) The example path `dev-tooling/reap_stale_worktrees.py` follows wide precedent in the live spec, which names `dev-tooling/` paths in many places, and it is illustrative only. (2) A resulting_files path without the `SPECIFICATION/` prefix is the revise CLI's required form. (3) The ids in the motivation stay in the proposal, not in the spec text. Implementation: livespec-inmgc7.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-12T06:02:15Z
verdict: NO BLOCKERS
proposal_stem: the-stale-worktree-reaper-force
content_digest: 33d4fe943b7b082fe2adca2638569ed68ddda9c0bedfb0187858a82ea820a15d
