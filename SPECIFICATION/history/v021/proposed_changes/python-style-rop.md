---
topic: python-style-rop
author: Claude Sonnet 4.6 (1M context)
created_at: 2026-05-06T15:00:00Z
---

## Proposal: Migrate style-doc §"Railway-Oriented Programming (ROP)" into `SPECIFICATION/constraints.md`

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Cycle 6 of Plan Phase 8 item 2 per-section migration. Lands the source doc's §"Railway-Oriented Programming (ROP)" content (lines 516-643, ~128 lines) into `SPECIFICATION/constraints.md` via two atomic edits: (1) EXPAND existing `## ROP composition` (retain heading, replace 1-paragraph body with the merged content from source-doc lines 516-579 + the `### ROP pipeline shape` sub-section from lines 581-618); (2) EXPAND existing `## Supervisor discipline` (append the bug-catcher contract paragraph from source-doc `### Supervisor discipline (bug-catcher)` lines 620-641, which maps to the existing top-level heading rather than a sub-heading). BCP-14-restructured throughout. Cross-references cycle 1's deviation rationale.

### Motivation

The source-doc §"ROP" section covers three nested concerns: (a) the railway-type discipline for pure/impure/composition functions; (b) error-handling routing rules (domain errors vs. bugs vs. third-party-exception wrapping); (c) the `@rop_pipeline` decorator shape; (d) the supervisor bug-catcher contract. In `SPECIFICATION/constraints.md`, concerns (a)/(b)/(c) map naturally to `## ROP composition` (the existing heading is an under-specified stub); concern (d) maps to the existing separate `## Supervisor discipline`. Splitting across two destination headings preserves the constraint topology already in the seeded spec — both headings exist; neither needs to be added; only their bodies need expansion.

The `### ROP pipeline shape` decorator-shape rule is new content in constraints.md (no existing stub). It lands as a `###` sub-section under `## ROP composition` since it is the mechanical enforcement arm of the ROP discipline at the class level.

### Proposed Changes

Two atomic edits to **SPECIFICATION/constraints.md**:

**Edit 1: EXPAND `## ROP composition`** — replace the existing 1-paragraph body and terminate before `## Supervisor discipline`:

> ## ROP composition
>
> Every public function in `livespec/` MUST compose via ROP using `dry-python/returns` primitives:
>
> - **Pure functions** (in `parse/`, `validate/`) MUST return `Result[T, E]`.
> - **Impure functions** (in `io/`) MUST return `IOResult[T, E]`.
> - **Composition code** (`commands/`, `doctor/`) threads steps together using `dry-python/returns` composition primitives (`flow`, `bind`, `bind_result`, `bind_ioresult`, `Fold.collect`, `.map`, `.lash`, etc.). The specific primitives chosen for a given chain are **implementer choice** under the architecture-level constraints. Mixed-monad chains (e.g., `IOResult`-returning I/O steps followed by `Result`-returning pure steps) MUST use the appropriate lifting primitive (such as `bind_result` on an `IOResult` chain, or explicit `IOResult.from_result(...)`); pyright strict and `check-public-api-result-typed` are the guardrails that catch mis-composition.
>
> Error-handling routing:
>
> - **Expected failure modes** — user input, environment, infra, timing — MUST flow through the Result track as `LivespecError` subclass payloads (*domain errors*).
> - **Unrecoverable bugs** — type mismatches, unreachable-branch assertions, broken invariants, dependency misuse — MUST propagate as raised exceptions, not via the Result track.
> - **Third-party code that raises DOMAIN-meaningful exceptions** (`FileNotFoundError`, `PermissionError`, `JSONDecodeError`, etc.) MUST be wrapped at the `io/` boundary using `@safe(exceptions=(ExcType1, ExcType2, ...))` or `@impure_safe(exceptions=(...))` with **explicit enumeration** of the expected exception types. A blanket `@safe` or `@impure_safe` with NO exception enumeration is forbidden — it would swallow bugs as domain failures.
> - **Raising `LivespecError` subclasses** is restricted to `io/**` and `errors.py`. Enforced by `check-no-raise-outside-io` (AST). Raising bug-class exceptions (`TypeError`, `NotImplementedError`, `AssertionError`, `RuntimeError` for unreachable branches, etc.) is **permitted anywhere**; the AST check distinguishes the two by subclass relationship to `LivespecError`.
> - **Catching exceptions** outside `io/**` is restricted to ONE call site: the outermost supervisor's `try/except Exception` bug-catcher (see `## Supervisor discipline`). `check-no-except-outside-io` enforces.
> - **`assert` statements are first-class.** Use them for invariants the implementer believes always hold. An `AssertionError` is a bug; it propagates to the supervisor bug-catcher.
> - **`sys.exit` and `raise SystemExit`** MUST appear ONLY in `bin/*.py` files. Enforced by `check-supervisor-discipline`.
>
> Every public function's `return` annotation MUST be `Result[_, _]` or `IOResult[_, _]`, unless the function is a supervisor at a deliberate side-effect boundary (`main() -> int` in `commands/*.py` and `doctor/run_static.py`, or any function returning `None`). The rule exempts only such supervisors. Enforced by `check-public-api-result-typed` (AST).
>
> ### ROP pipeline shape
>
> A class decorated with `@rop_pipeline` MUST carry exactly ONE public method (the entry point). Every other method MUST be `_`-prefixed (private). Dunder methods (`__init__`, `__call__`, etc., matching `^__.+__$`) are not counted toward the public-method quota.
>
> The decorator is a runtime no-op (returns the decorated class unchanged) declared in `livespec.types`. AST enforcement lives in `dev-tooling/checks/rop_pipeline_shape.py`. The decorator serves as an AST marker for the static check and as documentation at the def-site.
>
> Each pipeline class encapsulates one cohesive railway chain. Enforcing the shape prevents the public surface from drifting as new chain steps are added — agent-authored code that grows a second public method is caught at check time. Helper classes and helper modules (anything NOT carrying `@rop_pipeline`) are exempt and MAY export multiple public names.
>
> The marker is a decorator rather than a base class because the `check-no-inheritance` allowlist is intentionally small (`{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict}`); adding `RopPipeline` to the allowlist would expand the open-extension-point set for an application pattern.
>
> Enforced by `just check-rop-pipeline-shape`.

**Edit 2: EXPAND `## Supervisor discipline`** — append a bug-catcher-contract paragraph after the existing two-paragraph body:

> Every supervisor MUST wrap its ROP chain body in one `try/except Exception` bug-catcher whose exclusive job is: (1) log the exception via `structlog` with full traceback and structured context (module, function, `run_id`); (2) return the bug-class exit code (`1`). This is the ONLY catch-all `except Exception` permitted in the codebase. `check-supervisor-discipline` enforces the scope: exactly one catch-all per supervisor; no catch-alls outside supervisors; no catch-alls swallow exceptions without logging and exit-1 return.
