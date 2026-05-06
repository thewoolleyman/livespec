## Proposal: file_lloc soft-warns at 200 LLOC, hard-fails at 250 LLOC

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Spec the per-file LLOC ceiling in `SPECIFICATION/constraints.md` and split the single 200-LLOC hard-fail threshold into a two-tier policy: soft warn at 200 LLOC (exit 0, structured warning emitted), hard fail at 250 LLOC (exit 1). Removes the mid-Green-amend wedge: when a Red→Green amend incrementally drives LLOC above 200, the developer can finish the amend and refactor in a follow-up cycle rather than being blocked by the gate. Implementation lands atomically via `dev-tooling/checks/file_lloc.py` rewrite + paired test update.

### Motivation

Phase 7 sub-step 1.c cycle 1 wedge: the Green amend hit the 200-LLOC ceiling on `_seed_railway_emits.py` (205 LLOC after the new function + constant landed). The cycle was unblocked by extracting the new function + constant to a sibling module `_seed_railway_emits_per_tree.py` per the cycle-4e precedent, but the extraction was forced by the LLOC gate, not by a cohesion / SRP signal. Two-tier policy lets the gate flag growing files (200-LLOC warning) without forcing mid-amend refactors; refactor work lands in its own cycle when natural. User-gated 2026-05-03 as Mini-track item M3 in the Phase 7 enforcement-suite mini-track (Option C).

### Proposed Changes

Add a new top-level subsection to `SPECIFICATION/constraints.md` after the existing §"Typechecker constraints (Phase 1 pin)" section (which ends with the strict-plus diagnostics paragraph), before §"Heading taxonomy":

> ## File LLOC ceiling
> 
> Every `.py` file under `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**` SHOULD have at most 200 logical lines of code (LLOC) and MUST have at most 250 LLOC. LLOC excludes blank lines, comment-only lines, and module/class/function docstrings — it counts only executable statements.
> 
> The two-tier policy splits the prior single-threshold cap: 200 LLOC is a SOFT ceiling — files at 201-250 LLOC pass the check with a structured warning emitted to stderr (so `just check` stays green) but are flagged for refactoring. 250 LLOC is the HARD ceiling — files above 250 LLOC fail the check (exit 1). The `dev-tooling/checks/file_lloc.py` script enforces the binding mechanically. The two-tier policy removes the mid-Green-amend wedge where an in-progress refactor naturally pushes LLOC just above 200 and would otherwise force a sibling-module extraction in the same amend; instead, the warning surfaces the growing file and the refactor lands in its own cycle when natural.

Implementation work that lands atomically with the revise commit: rewrite `dev-tooling/checks/file_lloc.py` to emit a structured `warning` diagnostic for each 201-250 LLOC file (still exit 0) and a structured `error` diagnostic for each >250 LLOC file (exit 1); update the paired test at `tests/dev-tooling/checks/test_file_lloc.py` to cover both tiers (soft-warn-emits-warning-but-passes and hard-fail-rejects-over-250-but-not-201).
