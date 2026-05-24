---
topic: constraints-md-no-orphan-blocker-rename
author: claude-opus-4-7
created_at: 2026-05-24T01:17:17Z
---

## Proposal: constraints-md-rename-no-orphan-blocker-to-no-orphan-dependency

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Rename the `no-orphan-blocker` slug to `no-orphan-dependency` in `constraints.md` §"Cross-boundary doctor static checks". v072 renamed the invariant in `contracts.md` but `constraints.md` line 285 was not updated in lockstep.

### Motivation

Doctor invariant slug drift: v072's contracts.md §"Doctor cross-boundary invariants" renames `no-orphan-blocker` → `no-orphan-dependency` (and the doctor module + check_id were renamed accordingly in livespec PR #169). However, `constraints.md` line 285's check-ID enumeration still lists `no-orphan-blocker` — a single-token typo-class drift between the two spec files. Per the `dont_halt_on_simple_typos` discipline this is a typo with one obviously-correct alternative aligned with the adjacent rules; propose-change + revise lands the fix as a small cycle.

### Proposed Changes

In `SPECIFICATION/constraints.md` §"Cross-boundary doctor static checks" (line 285), replace both occurrences of `no-orphan-blocker` with `no-orphan-dependency` so the enumeration matches the v072 contracts.md invariant catalogue.

```diff
-The five work-item structural invariants codified in `contracts.md` §"Doctor cross-boundary invariants" (`gap-tracking-one-to-one`, `no-orphan-blocker`, `no-stale-gap-tied`, `no-duplicate-gap-id`, `no-stalled-epic`)
+The five work-item structural invariants codified in `contracts.md` §"Doctor cross-boundary invariants" (`gap-tracking-one-to-one`, `no-orphan-dependency`, `no-stale-gap-tied`, `no-duplicate-gap-id`, `no-stalled-epic`)
```

and:

```diff
-The check IDs MUST follow the existing slug convention (lowercase-hyphenated, per §"File naming and invocation"): `gap-tracking-one-to-one`, `no-orphan-blocker`, `no-stale-gap-tied`, `no-duplicate-gap-id`, `no-stalled-epic`.
+The check IDs MUST follow the existing slug convention (lowercase-hyphenated, per §"File naming and invocation"): `gap-tracking-one-to-one`, `no-orphan-dependency`, `no-stale-gap-tied`, `no-duplicate-gap-id`, `no-stalled-epic`.
```
