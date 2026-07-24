---
topic: no-inheritance-allowlist-generic
author: claude-fable-5
created_at: 2026-07-24T08:56:17Z
---

## Proposal: Add Generic to the check-no-inheritance direct-parent allowlist

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Both enumerations of the `check-no-inheritance` direct-parent allowlist in non-functional-requirements.md predate the v165 flat-full-ROP railway ratification and omit `Generic`, leaving two ratified clauses in tension: the railway (v165 §"Shared content provenance", Drivers explicitly included) requires `Success(Generic[_T])`/`Failure(Generic[_E])` containers landed by the ACCEPTED Driver adoptions (livespec-driver-claude-7u7 / livespec-driver-codex-96q), while the older closed-set enumeration textually forbids the `Generic[...]` base they carry — and the 3.10 fleet floor rules out the PEP 695 type-parameter syntax that would remove the base. This amendment adds `Generic` to both enumerated sets and codifies the semantics the shipped check now implements (livespec-dev-tooling-mg53, landed in livespec-dev-tooling PR #607, released v0.54.6): `Generic[...]` parameterization is structural typing machinery like the already-allowed `Protocol`/`NamedTuple`/`TypedDict`, not implementation inheritance; a subscripted base unwraps to its value for allowlist matching; a subscripted DISALLOWED base (e.g. `list[int]`) still fails exactly like its bare form.

### Motivation

The livespec-driver-claude-y21 dispatch failed honestly against this tension: the sandbox agent completed the cvz Driver hardening, then `check-no-inheritance` rejected the 7u7-landed railway containers the ratified design requires, and the agent correctly refused to cheat. The check-side fix is live (livespec-dev-tooling-mg53, PR #607, v0.54.6); this proposal repairs the spec-side enumeration so the ratified text and the shipped check agree — per the clause-lockstep discipline, an enumeration must be re-derived when the set it describes changes.

### Proposed Changes

Two byte-exact edits to SPECIFICATION/non-functional-requirements.md, both replacing the same enumeration string; the FIND string `{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict}` occurs exactly twice in the live spec tree, both in this file (verified against origin/master at filing time).

EDIT 1 (the §"ROP composition" RopPipeline-marker rationale sentence, currently line 663): replace

> (`{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict}`)

with

> (`{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict, Generic}`)

The surrounding clause ("the allowlist is intentionally small … adding `RopPipeline` would expand the open-extension-point set") remains true and unamended: `Generic`, like `Protocol`, is typing machinery, not an application extension point.

EDIT 2 (the §"Linter rule set"-adjacent class-inheritance restriction paragraph, currently line 734): replace

> The AST check `check-no-inheritance` rejects any `class X(Y):` definition where `Y` is not in the **direct-parent allowlist**: `{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict}`.

with

> The AST check `check-no-inheritance` rejects any `class X(Y):` definition where `Y` is not in the **direct-parent allowlist**: `{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict, Generic}`. `Generic` is allowlisted because `Generic[...]` parameterization is structural typing machinery, not implementation inheritance: the flat-full-ROP railway (§"Shared content provenance") requires `Success(Generic[_T])`-shaped containers, and the Python 3.10 fleet floor rules out the PEP 695 type-parameter syntax that would remove the base. A SUBSCRIPTED base (`Generic[_T]`, `Protocol[_T]`) is matched against the allowlist by its unsubscripted value; a subscripted DISALLOWED base (`list[int]`) fails exactly like its bare form.

No `## ` heading is added, renamed, or removed, so no tests/heading-coverage.json co-edit is owed. Drift-sweep note for the reviewer: the only other live-tree statements of this enumeration are in frozen `SPECIFICATION/history/` snapshots (correctly untouched) and the check's own module docstring in livespec-dev-tooling (already updated by PR #607).
