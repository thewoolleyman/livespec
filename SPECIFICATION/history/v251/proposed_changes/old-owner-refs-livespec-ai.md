---
topic: old-owner-refs-livespec-ai
author: claude-sonnet-5-5
created_at: 2026-11-16T18:46:01Z
---

## Proposal: Repoint fleet repo references in live spec text to livespec-ai

### Target specification files

- SPECIFICATION/constraints.md
- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/spec.md

### Summary

Live SPECIFICATION text still names fleet repositories under the old owner `thewoolleyman`. The repositories now live under the `livespec-ai` organization; repoint every such reference.

### Motivation

Plan stale-base-merge-options (epic livespec-dev-tooling-xowhol), definition-of-done assertion 7: the committed master tree of every fleet repository carries no graded reference to the old owner. Coordinator ruling 2026-11-16: live SPECIFICATION text goes through propose-change plus revise, riding the repo's next revise pass. Stale URLs such as the pi install command and the plugin-registration example would otherwise point consumers at the old owner.

### Proposed Changes

In each file below, rewrite every occurrence of a fleet repository reference whose owner is `thewoolleyman` so the owner is `livespec-ai`, leaving the repository name and every other character unchanged. The rewrite covers three shapes: URLs (`github.com/thewoolleyman/<repo>`, `https://github.com/thewoolleyman/<repo>.git`, `gh:thewoolleyman/<repo>`), slugs (`thewoolleyman/<repo>`, including `uses: thewoolleyman/livespec-dev-tooling/...@vX.Y.Z` and the `"repo": "thewoolleyman/<repo>"` JSON values in the plugin-registration example), and citations of the form `repo `thewoolleyman/livespec``. `<repo>` is one of `livespec`, `livespec-runtime`, `livespec-dev-tooling`, `livespec-driver-claude`, `livespec-orchestrator-beads-fabro`.

Affected locations (line numbers at master 8ee26b47):

- SPECIFICATION/constraints.md: line 72 (`thewoolleyman/livespec-runtime`).
- SPECIFICATION/contracts.md: lines 200, 207, 208, 209, 219, 384.
- SPECIFICATION/non-functional-requirements.md: lines 526, 528, 538, 544, 545, 573, 577, 587, 839, 869, 895, 1271.
- SPECIFICATION/spec.md: lines 232, 246, 248, 252, 299, 392 through 400, 458.

NOT changed by this proposal: the personal email address that non-functional-requirements.md line 1224 and contracts.md line 64 carry, and the bot account `thewoolleyman-factory-bot` (non-functional-requirements.md lines 1369 and 1371); these are identities, not repository owners. No `human:thewoolleyman` identifier exists in the live spec. Frozen `SPECIFICATION/history/` and `archive/` are untouched.

Verification after revise: `git grep -nE 'thewoolleyman/(livespec[a-z-]*)' -- SPECIFICATION/*.md` returns no match.
