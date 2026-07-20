---
topic: widen-uncommitted-edits-to-plan
author: claude-opus-4-8
created_at: 2026-07-20T00:39:05Z
---

## Proposal: Widen master-direct-uncommitted-spec-edits to cover plan/

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The `master-direct-uncommitted-spec-edits` invariant is scoped to `<spec-root>/` only, so a plan-thread handoff left uncommitted on a default-branch worktree is invisible to it. Widen the path scope to cover `plan/` as well, keeping severity at `warn`, keeping the default-branch-worktree scope unchanged, and correcting the corrective-action narration so a `plan/` finding never recommends discarding the file.

### Motivation

On 2026-07-19 `plan/overseer-productization/handoff.md` sat uncommitted in the primary checkout carrying 153 unversioned lines. It was rescued, so no data was lost. But in that same session the first `just check-doctor-static` run reported `"doctor-master-direct-uncommitted-spec-edits", "status": "pass", "message": "no worktrees on master carry uncommitted spec-tree edits (1 worktree(s) on master scanned)"` — the check ran, scanned the very worktree holding the dirty file, and reported clean, because §"master-direct-uncommitted-spec-edits" scopes `git status --porcelain` to `<spec-root>/` and a handoff lives under `plan/`. The gap is a path scope, not a missing concept. `plan/` is already first-class to the check suite (`check-plan-thread-anchor-declared`, `check-plan-thread-epic-parity` are canonical slugs), so widening scope is not a boundary violation. Maintainer-chosen 2026-07-19 (recorded in `plan/overseer-productization/handoff.md` §"Spun out — handoff-durability root-cause fix", introduced in commit 2312b4e4) and re-stated as the bar: plan files must not be orphaned on the main branch, detectable after the fact if necessary. Scoped and adversarially reviewed in `plan/plan-thread-integrity/plan.md` (epic livespec-nr5h), where three larger mechanisms were considered and cut as disproportionate to a single rescued near-miss.

### Proposed Changes

In `SPECIFICATION/contracts.md` §`master-direct-uncommitted-spec-edits`, replace the opening paragraph and the numbered corrective-action list.

Replace this sentence:

> Every worktree (primary or secondary, per `git worktree list --porcelain`) whose HEAD points at the default branch MUST NOT carry uncommitted modifications under `<spec-root>/`. The check enumerates every worktree, identifies the subset whose HEAD is the default branch (typically `master`), and for each invokes `git status --porcelain` scoped to `<spec-root>/`. Any non-empty output fires `warn` with corrective action narration that:

with:

> Every worktree (primary or secondary, per `git worktree list --porcelain`) whose HEAD points at the default branch MUST NOT carry uncommitted modifications under `<spec-root>/` **or under `plan/`**. The check enumerates every worktree, identifies the subset whose HEAD is the default branch (typically `master`), and for each invokes `git status --porcelain` scoped to those two path prefixes. Any non-empty output fires `warn` with corrective action narration that:

Replace numbered items 2 and 3:

> 2. Names the modified files under `<spec-root>/`.
> 3. Directs the user to commit-into-a-feature-branch (`git checkout -b <branch>` then commit) per the workflow discipline, OR to discard the edits if they were unintentional (`git checkout -- <files>`).

with:

> 2. Names the modified files, under `<spec-root>/` and under `plan/` respectively.
> 3. Directs the user to commit-into-a-feature-branch per the workflow discipline. For `<spec-root>/` paths the narration MAY additionally offer discarding unintentional edits (`git checkout -- <files>`). For `plan/` paths it MUST NOT: a plan-thread handoff is the durable record of a planning thread and an uncommitted one is frequently the ONLY copy, so a discard suggestion against it risks destroying the very artifact the finding exists to protect. The `plan/` narration leads with the commit path and does not present discard as a symmetric option.

Add this paragraph after the existing closing `warn`-rationale paragraph:

> **Detection surface (stated so it is not overclaimed).** The check enumerates only the worktrees of the checkout in which it runs, so it reports a dirty file on **any full `just check` or doctor invocation in the affected checkout**. It does NOT detect uncommitted state on another machine or in a CI job's fresh clone, and it does not run in the doc-only pre-commit/pre-push subset. This is detection, not enforcement: the finding is `warn` (wrapper exit 0) and blocks nothing.

The check's slug is deliberately NOT renamed. A widened check under a name that says `spec-edits` under-claims its scope, which is the safe direction of imprecision, and the contract text above now states the real scope; renaming would touch roughly ten live files for a `warn`-grade check.
