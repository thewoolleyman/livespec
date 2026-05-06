## Proposal: Add release-gate check-no-lloc-soft-warnings to close the M3 soft-band drift loophole

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Close the gap M3 introduced: the SOFT 200-LLOC ceiling emits a structured warning but otherwise passes — without a release-gate paired with it, files would drift unchecked from 201 to 250 LLOC across many cycles, just shifting the original wedge upward. Add a `check-no-lloc-soft-warnings` release-gate check (parallel to `check-no-todo-registry`): rejects any first-party `.py` file in the 201-250 LLOC band; runs ONLY on the release-tag CI workflow (NOT in `just check`); fires on `git push --tags v*`. Forces refactor work to land before any release tag, while keeping the per-commit pre-commit gate ergonomic (the wedge fix stays).

### Motivation

M3's two-tier policy (SOFT 200, HARD 250) by itself is just a deferred wedge — files drift to 250 across many cycles and the original 200-LLOC wedge re-appears at 250. Without a release-gate, the soft warning is honor-system content: nothing reads structlog warnings on green commits, no aggregator surfaces accumulated debt, no boundary blocks merge. User-flagged 2026-05-03: 'what drives a refactor after hitting soft LOC? instead of just hitting hard and having original problem eventually'. The fix is the release-gate analog of `check-no-todo-registry`: per-commit ergonomic (warning), tag-push enforcement (block).

### Proposed Changes

Single atomic edit: amend `SPECIFICATION/constraints.md` §"File LLOC ceiling" to describe the release-gate enforcement.

**SPECIFICATION/constraints.md §"File LLOC ceiling".** Replace the second paragraph (currently ending: "...the warning surfaces the growing file and the refactor lands in its own cycle when natural.") with:

> The two-tier policy splits the prior single-threshold cap: 200 LLOC is a SOFT ceiling — files at 201-250 LLOC pass the per-commit `check-complexity` target with a structured warning emitted to stderr (so `just check` stays green) but are flagged for refactoring. 250 LLOC is the HARD ceiling — files above 250 LLOC fail the check (exit 1). The `dev-tooling/checks/file_lloc.py` script enforces both bindings mechanically. The two-tier policy removes the mid-Green-amend wedge where an in-progress refactor naturally pushes LLOC just above 200 and would otherwise force a sibling-module extraction in the same amend; instead, the warning surfaces the growing file and the refactor lands in its own cycle when natural.
>
> The `check-no-lloc-soft-warnings` release-gate target (parallel to `check-no-todo-registry`) closes the soft-band drift loophole. The release-gate is NOT included in `just check` and does NOT run per-commit; it runs ONLY on the release-tag CI workflow (`.github/workflows/release-tag.yml`, fires on `v*` tag push). The release-gate rejects any first-party `.py` file in the 201-250 LLOC soft band, forcing refactor work to land before any release tag. Per-commit ergonomic (warning, no block); tag-push enforcement (block until clean).

Implementation work that lands atomically with the revise commit:

- New `dev-tooling/checks/no_lloc_soft_warnings.py` script: walks the same three covered trees as `file_lloc.py`, counts LLOC per file, fails if any file is in the 201-250 band. Reuses the LLOC-counting helpers from `file_lloc.py` (factor them into a shared module if needed, or duplicate the small token-walk).
- Paired test at `tests/dev-tooling/checks/test_no_lloc_soft_warnings.py`: at-least-one in-band-file rejection, all-files-below-soft acceptance, files-above-hard ignored (the hard ceiling is `file_lloc.py`'s job; this check is soft-band-specific).
- New `justfile` `check-no-lloc-soft-warnings` recipe (NOT added to the `check` aggregate per the release-gate-only convention).
- `.github/workflows/release-tag.yml`: add `check-no-lloc-soft-warnings` to the existing `release-gate` matrix (alongside `check-mutation` and `check-no-todo-registry`).
