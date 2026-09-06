---
topic: install-worktree-pack-first-hook-command
author: claude-fable-5-1 (optimize-gates plan session, Claude Code)
created_at: 2026-09-06T02:48:44Z
---

## Proposal: Hook step ordering: the worktree-pack installer runs first at pre-commit and pre-push

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Amend contracts.md section "Pre-commit step ordering" so the lefthook pre-commit and pre-push hooks each begin with a `00-install-worktree-pack` command that delegates to `just install-worktree-pack`, and renumber the three existing pre-commit commands to `01-lint-autofix-staged`, `02-commit-pairs-source-and-test`, `03-check-pre-commit`; pre-push becomes `00-install-worktree-pack` then `01-check-pre-push`. The installer materializes the canonical worktree-discipline pack into the checkout's gitignored `dev-tooling/` from the `livespec-dev-tooling` package that checkout resolves, so every later gate member that reads the pack finds it present and current whether the worktree was created by `just worktree-create`, by a raw `git worktree add`, or before a pin bump. The installer MUST be idempotent, MUST write only files the repository ignores, and MUST NOT relax the byte-identity verifier, which still asserts the installed bytes after the install. The commit-msg stage and the doc-only subset paragraph are unchanged. The count words in the amended sentences are dropped in favor of the enumerations themselves so the clause does not carry a number that must be re-derived when the list changes.

### Motivation

Plan `optimize-gates` (livespec epic livespec-xms725, research note plan/optimize-gates/research/001-fresh-worktree-gate-waste-and-enforcement-2026-09-06.md). The worktree-discipline pack is gitignored-and-installed by design, so a worktree created with raw `git worktree add` — the command this repo's own Repository mutation protocol prescribes — is born without it; the pre-push aggregate then fails `worktree_pack_absent`, the remedy names the full `just bootstrap`, and the whole aggregate runs a second time. The pre-push and pre-commit lefthook hooks are the one seam every local gate path funnels through (the shared commit-refuse hook body delegates to lefthook at worktrees), and CI already performs exactly this install step before its checks. Placing the installer inside a single gate member cannot work because the `check` aggregate runs its members alphabetically and members that read the pack precede the verifier. This is the ratified-text half of the change; the implementing children are livespec-igowet (this repo's `lefthook.yml` and `templates/orchestrator-plugin/lefthook.yml.jinja`), livespec-ltthxr (the other nine fleet members), and livespec-dev-tooling-lptplj (the central fleet-conformance row that asserts the first-command on every member's committed master).

### Proposed Changes

```diff
@@ SPECIFICATION/contracts.md — "## Pre-commit step ordering", first paragraph: replace the sentence beginning "Lefthook pre-commit runs three commands in order:" through "Earlier steps fail-fast so the developer learns about a missing test pair without waiting for pytest." and replace the final sentence "Pre-push runs `just check` (the full aggregate)." The commit-msg sentences between them are unchanged. @@
-Lefthook pre-commit runs three commands in order: `00-lint-autofix-staged` (delegates to `just lint-autofix-staged`; ruff fix + format on staged `.py` files; non-blocking — unfixable issues fall through to be caught by `just check`'s `check-lint`/`check-format` later); `01-commit-pairs-source-and-test` (delegates to `just check-commit-pairs-source-and-test`; cheap staged-file-list inspection per v033 D3); `02-check-pre-commit` (delegates to `just check-pre-commit`; the heavy check aggregate, Red-mode-aware per v036 D1). Earlier steps fail-fast so the developer learns about a missing test pair without waiting for pytest.
+Lefthook pre-commit runs these commands in order: `00-install-worktree-pack` (delegates to `just install-worktree-pack`; materializes the canonical worktree-discipline pack into the checkout's gitignored `dev-tooling/` from the `livespec-dev-tooling` package that checkout resolves, so every later gate member that reads the pack finds it present and current whether the worktree was created by `just worktree-create`, by a raw `git worktree add`, or before a pin bump; the installer MUST be idempotent, MUST write only files the repository ignores, and MUST NOT relax the byte-identity verifier, which still asserts the installed bytes after the install); `01-lint-autofix-staged` (delegates to `just lint-autofix-staged`; ruff fix + format on staged `.py` files; non-blocking — unfixable issues fall through to be caught by `just check`'s `check-lint`/`check-format` later); `02-commit-pairs-source-and-test` (delegates to `just check-commit-pairs-source-and-test`; cheap staged-file-list inspection per v033 D3); `03-check-pre-commit` (delegates to `just check-pre-commit`; the heavy check aggregate, Red-mode-aware per v036 D1). Earlier steps fail-fast so the developer learns about a missing test pair without waiting for pytest.
-Pre-push runs `just check` (the full aggregate).
+Pre-push runs these commands in order: `00-install-worktree-pack` (the same installer, for the same reason) then `01-check-pre-push` (delegates to `just check-pre-push`, which runs `just check` — the full aggregate — behind the memoizing short-circuit described below). A repository governed by this contract MUST NOT place any hook command that reads the worktree-discipline pack ahead of `00-install-worktree-pack`.
```
