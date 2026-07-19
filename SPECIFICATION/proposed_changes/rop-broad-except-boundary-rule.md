---
topic: rop-broad-except-boundary-rule
author: claude-opus-4-8
created_at: 2026-07-19T07:56:59Z
---

## Proposal: Single-boundary cardinality and the no-rail-lifting-defense rule

### Target specification files

- non-functional-requirements.md

### Summary

Amends the ROP-railway bullet in the Shared content provenance section to state the boundary-handler cardinality explicitly (exactly one per process entry artifact, a direct child of main()'s body), to name the fail-closed guard-hook flavor alongside the CLI supervisor and fail-open hook, and to close the ambiguity that blocked acceptance: lifting onto the Result/IOResult track never justifies a broad catch below the boundary, because a hand-rolled `except Exception` returning Failure/IOFailure is the already-forbidden blanket lift written longhand.

### Motivation

Fleet ROP design-authority ruling, 2026-07-19, requested from the rop-sweep-fleet-policy plan thread (livespec repo, plan/rop-sweep-fleet-policy/). Two factory-produced conversion styles disagreed about whether a broad `except Exception` is permitted at an I/O seam when it lifts the exception onto the Result/IOResult failure track. STYLE A (livespec-driver-claude's block_auto_memory.py) used broad catches at the stdin/stdout seams, marked `# noqa: BLE001 - ... captured on IO rail`. STYLE B (livespec-orchestrator-git-jsonl's io/store.py) narrowed every catch. One reviewer called STYLE A's catches violations; another called them legitimate rail-lifting. Both readings were defensible under the current text, which blocked acceptance of three merged conversions and the briefing of ten further conversion slices. The ruling settles it for STYLE B and makes the rule mechanically checkable.

### Proposed Changes

The following current text MUST be replaced verbatim. The replacement target has been verified to occur exactly once in the live file.

CURRENT (verbatim):

The ONLY permitted broad `except Exception` is a single outermost boundary handler: for a CLI wrapper, the supervisor bug-catcher that logs with full context and returns exit `1` (§"Supervisor discipline"); for a never-wedge-the-agent hook, the fail-open silent pass-through its Driver hook contract already requires (a hook failure is a silent pass-through, per `contracts.md`).

REPLACEMENT:

The ONLY permitted broad `except Exception` is a single outermost boundary handler — EXACTLY ONE per process entry artifact, a direct child of `main()`'s body: for a CLI wrapper, the supervisor bug contract (§"Supervisor discipline" — implicit interpreter propagation by default, or the one explicit bug-catcher that logs with full context and returns exit `1`); for a never-wedge-the-agent hook, the fail-open silent pass-through its Driver hook contract already requires (a hook failure is a silent pass-through, per `contracts.md`); for a fail-closed guard hook, the single boundary catch that emits its deny decision. Lifting onto the `Result`/`IOResult` track NEVER justifies a broad catch below that boundary: the sanctioned lift is the enumerated narrow catch (§"ROP composition"), and a hand-rolled `except Exception` that returns `Failure(exc)`/`IOFailure(exc)` is the forbidden blanket lift written longhand, not a second boundary.


## Proposal: Hand-rolled catches bind by the same blanket-lift prohibition as the decorators

### Target specification files

- non-functional-requirements.md

### Summary

Extends the ROP composition section's existing prohibition on a blanket @safe/@impure_safe so it explicitly binds hand-rolled try/except catches too, and states the choice rule between the decorator form and the hand-rolled narrow form. This removes the reading under which a hand-rolled broad catch escaped a prohibition that applies to the decorator it reimplements.

### Motivation

Fleet ROP design-authority ruling, 2026-07-19, requested from the rop-sweep-fleet-policy plan thread (livespec repo, plan/rop-sweep-fleet-policy/). Two factory-produced conversion styles disagreed about whether a broad `except Exception` is permitted at an I/O seam when it lifts the exception onto the Result/IOResult failure track. STYLE A (livespec-driver-claude's block_auto_memory.py) used broad catches at the stdin/stdout seams, marked `# noqa: BLE001 - ... captured on IO rail`. STYLE B (livespec-orchestrator-git-jsonl's io/store.py) narrowed every catch. One reviewer called STYLE A's catches violations; another called them legitimate rail-lifting. Both readings were defensible under the current text, which blocked acceptance of three merged conversions and the briefing of ten further conversion slices. The ruling settles it for STYLE B and makes the rule mechanically checkable.

### Proposed Changes

The following current text MUST be replaced verbatim. The replacement target has been verified to occur exactly once in the live file.

CURRENT (verbatim):

A blanket `@safe` or `@impure_safe` with NO exception enumeration is forbidden — it would swallow bugs as domain failures.

REPLACEMENT:

A blanket `@safe` or `@impure_safe` with NO exception enumeration is forbidden — it would swallow bugs as domain failures. The same rule binds hand-rolled catches, which are the decorators' equal-citizen equivalent: `try/except (ExcType1, ExcType2)` returning `Failure(...)`/`IOFailure(...)` is the sanctioned hand-rolled form (prefer it when the failure payload is a constructed domain error carrying context; prefer the decorator when the raw exception IS the payload and the whole function body is the seam), and a hand-rolled `try/except Exception` that lifts is the SAME forbidden blanket lift regardless of the container it returns.


## Proposal: Catch placement in repos without an io/ tree, and the foreign-code isolation seam

### Target specification files

- non-functional-requirements.md

### Summary

Amends the catching-restriction bullet to say what governs a repo that has no io/ layered tree (io_trees unset, e.g. a hook-only Driver), where the check-no-except-outside-io AST check no-ops by config and only ruff BLE polices broad catches. Also defines the one narrowly-scoped case where a broad catch is permitted below a process boundary: invoking user-provided extension code, whose exceptions cannot be enumerated in principle.

### Motivation

Fleet ROP design-authority ruling, 2026-07-19, requested from the rop-sweep-fleet-policy plan thread (livespec repo, plan/rop-sweep-fleet-policy/). Two factory-produced conversion styles disagreed about whether a broad `except Exception` is permitted at an I/O seam when it lifts the exception onto the Result/IOResult failure track. STYLE A (livespec-driver-claude's block_auto_memory.py) used broad catches at the stdin/stdout seams, marked `# noqa: BLE001 - ... captured on IO rail`. STYLE B (livespec-orchestrator-git-jsonl's io/store.py) narrowed every catch. One reviewer called STYLE A's catches violations; another called them legitimate rail-lifting. Both readings were defensible under the current text, which blocked acceptance of three merged conversions and the briefing of ten further conversion slices. The ruling settles it for STYLE B and makes the rule mechanically checkable.

### Proposed Changes

The following current text MUST be replaced verbatim. The replacement target has been verified to occur exactly once in the live file.

CURRENT (verbatim):

- **Catching exceptions** outside `io/**` is restricted to ONE call site: the outermost supervisor's `try/except Exception` bug-catcher (see `## Supervisor discipline`). `check-no-except-outside-io` enforces.

REPLACEMENT:

- **Catching exceptions** outside `io/**` is restricted to ONE call site: the outermost supervisor's `try/except Exception` bug-catcher (see `## Supervisor discipline`). `check-no-except-outside-io` enforces. In a repo without an `io/` layered tree (`io_trees` unset — e.g. a hook-only Driver), that AST check no-ops by config; there, narrow seam lifts live in the entry artifact's helper functions, ruff `BLE` polices broad catches, and the single-boundary cardinality rule of §"Supervisor discipline" still binds. Where first-party code invokes a callable it does not own (a user-provided extension: a custom doctor check, a template hook), enumeration is impossible in principle and the host MAY carry one broad catch per extension invocation surface — it MUST capture the full traceback into a typed bug-class domain error naming the foreign unit, MUST surface the crash loudly in the artifact's findings (never silently skipped, never demoted to an ordinary tolerated failure), and MUST wrap only the foreign call; this is the only broad catch permitted below a process boundary.


## Proposal: Supervisor bug contract: implicit propagation as the default conforming form

### Target specification files

- non-functional-requirements.md

### Summary

Rewrites the Supervisor discipline bug-catcher paragraph so it states the GUARANTEE (an unexpected exception surfaces its full traceback and yields exit 1) rather than mandating one mechanism, and blesses two conforming forms: implicit interpreter propagation with zero catches (the default and stricter form, and what shipped supervisors actually do today), and the one explicit bug-catcher where structured logging context or an exit contract forbidding a raw-traceback escape requires it. Also states the absolute cardinality rule, covers the fail-open and fail-closed hook flavors, and sanctions a fifth category the first four did not cover: a long-running supervision loop's per-iteration resilience catch, which logs the full traceback and continues rather than exiting, so a bug in one supervised unit cannot strand the others.

### Motivation

Fleet ROP design-authority ruling, 2026-07-19, requested from the rop-sweep-fleet-policy plan thread (livespec repo, plan/rop-sweep-fleet-policy/). Two factory-produced conversion styles disagreed about whether a broad `except Exception` is permitted at an I/O seam when it lifts the exception onto the Result/IOResult failure track. STYLE A (livespec-driver-claude's block_auto_memory.py) used broad catches at the stdin/stdout seams, marked `# noqa: BLE001 - ... captured on IO rail`. STYLE B (livespec-orchestrator-git-jsonl's io/store.py) narrowed every catch. One reviewer called STYLE A's catches violations; another called them legitimate rail-lifting. Both readings were defensible under the current text, which blocked acceptance of three merged conversions and the briefing of ten further conversion slices. The ruling settles it for STYLE B and makes the rule mechanically checkable.

### Proposed Changes

The following current text MUST be replaced verbatim. The replacement target has been verified to occur exactly once in the live file.

CURRENT (verbatim):

Every supervisor MUST wrap its ROP chain body in one `try/except Exception` bug-catcher whose exclusive job is: (1) log the exception via `structlog` with full traceback and structured context (module, function, `run_id`); (2) return the bug-class exit code (`1`). This is the ONLY catch-all `except Exception` permitted in the codebase. `check-supervisor-discipline` enforces the scope: exactly one catch-all per supervisor; no catch-alls outside supervisors; no catch-alls swallow exceptions without logging and exit-1 return.

REPLACEMENT:

Every supervisor MUST guarantee the bug contract — an unexpected exception surfaces its FULL traceback and yields the bug-class exit code (`1`), never a domain-failure exit and never silence — in one of two conforming forms. **Implicit (the default):** no catch at all; the exception propagates through `raise SystemExit(main())` and the interpreter prints the full traceback to stderr and exits `1` — zero broad catches is the stricter form. **Explicit:** exactly one `try/except Exception` bug-catcher as a direct child of `main()`, required only when the supervisor must attach structured logging context (`structlog`, with full traceback plus module, function, `run_id`) before returning `1`, or when the process's exit contract forbids a raw-traceback escape — a Driver hook is that second case, and its single boundary catch IS its supervisor: a fail-open hook's boundary is the silent exit-`0` pass-through; a fail-closed guard hook's boundary emits its deny decision, with any mixed policy computed inside that ONE handler from state the body recorded, never via additional broad catches. In every form the cardinality rule is absolute: at most ONE broad catch per process entry artifact, a direct child of `main()`, carrying the standardized `# noqa: BLE001 — sole …` marker (§"Linter rule set"); ZERO broad catches anywhere else in the artifact. **Long-running supervision loop (per-iteration resilience):** a daemon that supervises N independent units MAY carry ONE ADDITIONAL broad catch as a direct child of its supervision-loop body, whose contract is to log the FULL traceback and CONTINUE to the next iteration, never exiting — because a bug while evaluating ONE unit MUST NOT terminate the process and strand the other N-1. It MUST log the full traceback (a silent `pass` is forbidden here), and it MUST NOT be used where the process should exit instead. Its cardinality is ONE PER SUPERVISION LOOP rather than one per entry artifact: an entry artifact running such a loop MAY therefore carry both its `main()` boundary handler and this loop-iteration catch, and no more. `check-supervisor-discipline` enforces the scope: at most one catch-all per supervisor; no catch-alls outside supervisors; no catch-all swallows an exception without discharging its flavor's contract.

NOTE: This edit also resolves a spec-versus-implementation divergence. The current text mandates an explicit try/except Exception bug-catcher in every supervisor, but shipped core supervisors carry none (verified in .claude-plugin/scripts/livespec/commands/next.py) and CI is green. Blessing the implicit form makes spec, code, and doctrine agree. The loop-iteration category has a worked example in this repo: the overseer daemon at .claude/skills/overseer/supervisor.py:2594 catches broadly inside Supervisor.run, logs the full traceback, and continues the loop, precisely so a bug evaluating one supervised track cannot take the daemon down and strand every other track. That catch fits none of the boundary categories (it never exits 1 and is not a direct child of main()), so without this fifth category the rule would force either a false marker or a wrong behavior change. ENFORCEMENT NOTE for a follow-up: check-supervisor-discipline scopes on source_tree_prefixes, which does NOT include .claude/skills/, so nothing mechanically enforces this rule over the overseer today; extending that scope is tracked separately and is not part of this proposal.


## Proposal: Closed set of standardized noqa BLE001 markers

### Target specification files

- non-functional-requirements.md

### Summary

Replaces the free-form `# noqa: BLE001 - <reason>` escape with a closed set of five standardized marker wordings, one per sanctioned category. This makes the escape mechanically auditable: a reviewer greps for the marker and audits a claim rather than reading prose. It also names the specific wording that must never appear again, since free-form wording is precisely how `captured on IO rail` passed as though it were sanctioned.

### Motivation

Fleet ROP design-authority ruling, 2026-07-19, requested from the rop-sweep-fleet-policy plan thread (livespec repo, plan/rop-sweep-fleet-policy/). Two factory-produced conversion styles disagreed about whether a broad `except Exception` is permitted at an I/O seam when it lifts the exception onto the Result/IOResult failure track. STYLE A (livespec-driver-claude's block_auto_memory.py) used broad catches at the stdin/stdout seams, marked `# noqa: BLE001 - ... captured on IO rail`. STYLE B (livespec-orchestrator-git-jsonl's io/store.py) narrowed every catch. One reviewer called STYLE A's catches violations; another called them legitimate rail-lifting. Both readings were defensible under the current text, which blocked acceptance of three merged conversions and the briefing of ten further conversion slices. The ruling settles it for STYLE B and makes the rule mechanically checkable.

### Proposed Changes

The following current text MUST be replaced verbatim. The replacement target has been verified to occur exactly once in the live file.

CURRENT (verbatim):

A deliberately fail-open boundary uses the per-line `# noqa: BLE001 — <reason>` escape.

REPLACEMENT:

The ONLY conforming `# noqa: BLE001` escapes are the five standardized markers (§"Supervisor discipline"): `— sole supervisor bug-catcher: log traceback, exit 1`; `— sole fail-open hook boundary: silent pass-through, exit 0`; `— sole fail-closed guard boundary: deny per policy, exit 0`; `— sole loop-iteration bug-catcher: log traceback, continue`; `— foreign-code isolation: <surface> crash captured as <ErrorType>, reported`. The word `sole` is load-bearing, but its scope differs by marker: for the three boundary markers it means at most one per process entry artifact, while for the loop-iteration marker it means at most one per supervision loop — so an entry artifact running a supervision loop MAY carry one boundary marker AND one loop-iteration marker, and no more. Any other `BLE001` reason wording — in particular any claim that the catch "lifts onto the IO rail" — marks a violation, not an escape.

