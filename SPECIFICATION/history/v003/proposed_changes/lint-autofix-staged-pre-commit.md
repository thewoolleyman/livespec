## Proposal: Pre-commit auto-fixes ruff issues on staged Python files before running the gate

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md

### Summary

Add a `just lint-autofix-staged` target wired into lefthook pre-commit as the FIRST step (`00-lint-autofix-staged`), running ruff `--fix` + `format` on the staged Python files only and re-staging them, BEFORE the existing `01-commit-pairs-source-and-test` and `02-check-pre-commit` steps run. Removes the friction where a single auto-fixable lint trivia (import sort, format) costs a full ~5-min `just check-pre-commit` re-run on retry. The autofix runs BEFORE the v034 D3 commit-msg replay hook computes the Red trailer's test-file checksum, so the recorded checksum reflects the post-autofix bytes; at the Green amend the test file is unchanged (Green amend stages impl, not the test), so the checksum invariant holds.

### Motivation

Phase 7 sub-step 1.c cycle 1 hit this friction: the Red commit failed because three new test imports were not sorted per ruff I001. Ruff `--fix` resolved the issue in 200ms, but the full pre-commit retry took ~5 minutes (just check aggregate including pytest+coverage). User-gated 2026-05-03 as Mini-track item M1 in the Phase 7 enforcement-suite mini-track (Option C). Highest leverage of the five mini-track items: every subsequent cycle (sub-step 1.c cycles 2-4 plus all of sub-step 2 onward) avoids this retry tax.

### Proposed Changes

Two atomic edits — one extending `SPECIFICATION/spec.md` §"Developer-tooling layout", one adding a small new sub-section to `SPECIFICATION/contracts.md` describing the pre-commit step ordering.

**SPECIFICATION/spec.md §"Developer-tooling layout".** Append two sentences to the existing paragraph (currently ending: "Tool versions for non-Python binaries (`uv`, `just`, `lefthook`) pin via `.mise.toml`; Python and Python packages pin via `uv` against `pyproject.toml`'s `[dependency-groups.dev]`.") so it reads:

> `justfile` is the single source of truth for every dev-tooling invocation. `lefthook.yml` and CI workflows MUST delegate to `just <target>` and MUST NOT shell out to underlying tools directly (enforced by `dev-tooling/checks/no_direct_tool_invocation.py`). Tool versions for non-Python binaries (`uv`, `just`, `lefthook`) pin via `.mise.toml`; Python and Python packages pin via `uv` against `pyproject.toml`'s `[dependency-groups.dev]`. Lefthook pre-commit runs `just lint-autofix-staged` as its first step, which applies `ruff check --fix` + `ruff format` to the staged Python files only and re-stages them in place; this lets auto-fixable lint trivia (import ordering, formatting) get fixed without forcing a full pre-commit retry. The autofix step runs BEFORE the v034 D3 commit-msg replay hook computes the Red commit's test-file SHA-256 checksum, so the recorded checksum reflects post-autofix bytes; the Green amend stages impl files only (not the test), preserving the test-file-byte-identical invariant the replay hook enforces.

**SPECIFICATION/contracts.md.** Add a new top-level sub-section after the existing §"Per-sub-spec doctor parameterization" section (which currently is the last subsection before §"Resolved-template stdout contract"):

> ## Pre-commit step ordering
> 
> Lefthook pre-commit runs three commands in order: `00-lint-autofix-staged` (delegates to `just lint-autofix-staged`; ruff fix + format on staged `.py` files; non-blocking — unfixable issues fall through to be caught by `just check`'s `check-lint`/`check-format` later); `01-commit-pairs-source-and-test` (delegates to `just check-commit-pairs-source-and-test`; cheap staged-file-list inspection per v033 D3); `02-check-pre-commit` (delegates to `just check-pre-commit`; the heavy check aggregate, Red-mode-aware per v036 D1). Earlier steps fail-fast so the developer learns about a missing test pair without waiting for pytest. Commit-msg stage runs `just check-red-green-replay {1}` (the v034 D3 replay hook). Pre-push runs `just check` (the full aggregate).
