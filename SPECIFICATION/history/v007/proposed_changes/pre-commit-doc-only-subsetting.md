## Proposal: Pre-commit conservatively subsets to doc-only checks when zero .py files are staged

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Extend `just check-pre-commit` (the lefthook pre-commit step's heavy aggregate) with a CONSERVATIVE doc-only mode: when the staged tree contains ZERO `.py` files, run only a small whitelist of non-Python-related checks (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`) instead of the full 30-target aggregate. Pre-push and CI keep invoking `just check` directly with no subsetting — the full aggregate is the load-bearing safety net for any path that lands on `master`. Conservative because the ONLY classification trigger is "zero .py staged"; ANY .py file in the staged tree (even one) routes through the full aggregate.

### Motivation

Bookkeeping commits (STATUS.md updates, decisions.md notes, heading-coverage.json edits, propose-change file authoring) currently incur the full ~5-minute pre-commit aggregate even though no Python source has changed. Phase 7 sub-step 2's mini-track has authored ~15 such bookkeeping/spec-only commits in this session alone; cumulative time-cost is real. Pre-push and CI keep the full aggregate so any code-change branch is always validated end-to-end before reaching `master`. User-gated 2026-05-03 as Mini-track item M5 in the Phase 7 enforcement-suite mini-track (Option C). Last item — completes the mini-track.

### Proposed Changes

Single atomic edit: amend `SPECIFICATION/contracts.md` §"Pre-commit step ordering" to describe the doc-only subsetting.

**SPECIFICATION/contracts.md §"Pre-commit step ordering".** Append a new sentence to the existing paragraph (currently ending with "Pre-push runs `just check` (the full aggregate)."):

> Lefthook pre-commit runs three commands in order: `00-lint-autofix-staged` (delegates to `just lint-autofix-staged`; ruff fix + format on staged `.py` files; non-blocking — unfixable issues fall through to be caught by `just check`'s `check-lint`/`check-format` later); `01-commit-pairs-source-and-test` (delegates to `just check-commit-pairs-source-and-test`; cheap staged-file-list inspection per v033 D3); `02-check-pre-commit` (delegates to `just check-pre-commit`; the heavy check aggregate, Red-mode-aware per v036 D1). Earlier steps fail-fast so the developer learns about a missing test pair without waiting for pytest. Commit-msg stage runs `just check-red-green-replay {1}` (the v034 D3 replay hook). Pre-push runs `just check` (the full aggregate).
>
> When the staged tree contains ZERO `.py` files, `just check-pre-commit` runs a CONSERVATIVE doc-only subset (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`) instead of the full aggregate, since the Python-related gates have no work to do on doc-only commits. The classification trigger is the strict "zero `.py` staged" predicate; any `.py` file in the staged tree (even a single test file in Red mode) routes through the full aggregate. Pre-push and CI never apply this subsetting — the full aggregate is the load-bearing safety net for any branch landing on `master`.

Implementation work that lands atomically with the revise commit: extend `just check-pre-commit` recipe in `justfile` to detect the zero-`.py`-staged condition and delegate to a new `just check-pre-commit-doc-only` recipe (the five-target whitelist); add the `check-pre-commit-doc-only` recipe.
