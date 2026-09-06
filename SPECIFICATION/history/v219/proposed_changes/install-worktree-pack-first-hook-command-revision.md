---
proposal: install-worktree-pack-first-hook-command.md
decision: accept
revised_at: 2026-09-06T03:12:22Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5-1 (optimize-gates plan session, Claude Code)
---

## Decision and Rationale

Accept: amend §"Pre-commit step ordering" so lefthook pre-commit and pre-push each begin with `00-install-worktree-pack` (delegating to `just install-worktree-pack`), renumber the three existing pre-commit commands to 01/02/03, and make pre-push `00-install-worktree-pack` then `01-check-pre-push`; the installer MUST be idempotent, MUST write only ignored files, and MUST NOT relax the byte-identity verifier, and no hook command that reads the pack may precede it. Design record: plan optimize-gates research note §3(d) (epic livespec-xms725) — the pack is gitignored-and-installed, a raw `git worktree add` worktree is born without it, and the `check` aggregate runs its members alphabetically so members that read the pack precede the verifier; the lefthook hook is the one seam every local gate path funnels through, and CI already performs the same install step before its checks. The count words were dropped from the amended sentences so the clause no longer carries a number that must be re-derived when the enumeration changes (.ai/spec-proposal-review.md class 3). Both replace targets verified verbatim exactly once in the pre-revise file; the resulting text was derived mechanically from the proposal's own diff hunks; no `## ` heading added, changed, or removed (22 H2 headings before and after, counted as lines beginning `## `), so no tests/heading-coverage.json co-edit. Two-file change: the same review's first round (2026-09-06T02:53:15Z) raised one blocker — non-functional-requirements.md §"Developer-tooling layout" still called `just lint-autofix-staged` the first pre-commit step — which the proposal now amends in lockstep ("first check-bearing step, immediately after the `00-install-worktree-pack` installer"); the reviewer's second round on these exact bytes returned NO BLOCKERS at 2026-09-06T02:58:19Z (reviewer: a separately spawned read-only agent named ratification-reviewer-install-worktree-pack-first, self-reported model "Opus 5 (1M context), model ID claude-opus-5[1m]", digest independently recomputed and matching) with one cosmetic nit (prefer the § sign over the word "section" in that clause), deliberately left as filed so the reviewed bytes are the ratified bytes. Both files keep their H2 sets (22 and 5 physical lines beginning `## `).

## Resulting Changes

- contracts.md
- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-06T02:58:19Z
verdict: NO BLOCKERS
proposal_stem: install-worktree-pack-first-hook-command
content_digest: 398e43767587ce1a906d7626a9b81fe16420dfa6d643ce627ca980a0098a901a
