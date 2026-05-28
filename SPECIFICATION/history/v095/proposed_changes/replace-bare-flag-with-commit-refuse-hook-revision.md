---
proposal: replace-bare-flag-with-commit-refuse-hook.md
decision: accept
revised_at: 2026-05-28T08:11:12Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accept as authored. The bare-flag mechanism (landed in v091 as a livespec-private rule, promoted in v093 to a family-wide invariant) introduced a real bug: primary checkouts at /data/projects/<repo>/ are frozen at pre-bare-flag content and never refresh on git fetch because a bare repository has no working tree to update. This forced every on-disk read at primaries to route through `git show HEAD:<path>` (the feedback_bare_flag_use_git_show_not_filesystem workaround documented in agent memory) — a silent stale-read foot-gun for every doctor cross-boundary invariant and every ad-hoc agent read. The commit-refuse hook mechanism preserves the original goal (no commits at primary, every edit through a worktree) with strictly less collateral damage: filesystem reads, git fetch, and git pull --ff-only at the primary all work normally. The three-layer enforcement architecture (NFR rule + bootstrap step + doctor invariant) is preserved in shape; only the underlying mechanism swaps. The renamed shared check, the renamed doctor invariant slug, and the renamed NFR sections all flow naturally from the swap. Phase 2/3 work-items under epic li-unbare will implement the renamed shared check in livespec-dev-tooling and roll out the new bootstrap step and the core.bare unset across consumer primaries. No tests/heading-coverage.json co-edit required: both renamed sections are H3 (or inline-bold), and heading-coverage.json tracks only H2 entries.

## Resulting Changes

- non-functional-requirements.md
- contracts.md
