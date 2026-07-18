---
topic: rop-enforcement-fleet-policy
author: claude-opus-4-8
created_at: 2026-07-18T05:06:08Z
---

## Proposal: Observability rides the railway as a pass-through tap, never a catch

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add the observability half of the ROP discipline to non-functional-requirements.md §"ROP composition" error-handling routing: side-effects (logging, metrics, telemetry) compose as value-preserving `.map`/`tap` pass-through steps that introduce no new catch; "the call can throw" is never itself a reason to lift a step onto the Result track (every call can throw, and an unexpected throw is a bug that MUST reach the supervisor); and a critical downstream effect is protected from an observability failure by ORDERING (perform the critical effect before the tap), not by catching the tap.

### Motivation

Corrected guidance from the rop-sweep-fleet-policy thread (livespec plan/rop-sweep-fleet-policy/handoff.md, Part B). The trigger was livespec-orchestrator-beads-fabro's blind-except bulkheads; the mechanical cleanup landed (beads-fabro 3d2ff13), but the observability half of the rule — the part that distinguishes ROP-done-right from a relocated bulkhead — was not written down anywhere normative. livespec-runtime/cross_repo/retry.py is a live instance of the exact anti-pattern: it catches `except Exception` broadly by documented design, converting bugs into a None/UNKNOWN degradation.

### Proposed Changes

In non-functional-requirements.md §"ROP composition", under the "Error-handling routing:" bullet list, insert TWO new bullets IMMEDIATELY AFTER the existing bullet that begins "**Third-party code that raises DOMAIN-meaningful exceptions**" (the narrowed-`@safe`/`@impure_safe` bullet) and BEFORE the bullet that begins "**Raising `LivespecError` subclasses**".

Exact verbatim anchor (the bullet the new bullets follow):
> - **Third-party code that raises DOMAIN-meaningful exceptions** (`FileNotFoundError`, `PermissionError`, `JSONDecodeError`, etc.) MUST be wrapped at the `io/` boundary using `@safe(exceptions=(ExcType1, ExcType2, ...))` or `@impure_safe(exceptions=(...))` with **explicit enumeration** of the expected exception types. A blanket `@safe` or `@impure_safe` with NO exception enumeration is forbidden — it would swallow bugs as domain failures.

New bullet 1 (insert after that anchor):
> - **Observability and other side-effects compose as pass-through steps, never as reasons to catch.** A logging, metrics, or telemetry effect rides the railway as a value-preserving `.map` step (a `tap`: it runs the effect and returns its input unchanged), threading the chain's value through untouched and introducing NO new catch. "The call can throw" is NEVER by itself a reason to wrap a step in `@safe` / `@impure_safe`: every call can throw, and an unexpected throw is a bug that MUST propagate to the supervisor bug-catcher (§"Supervisor discipline"). Only a NAMED, EXPECTED failure a step deliberately tolerates is lifted onto the Result track, and only via the narrowed `@impure_safe(exceptions=(…))` enumeration above — never a blanket lift that merely relocates a bulkhead onto the railway.

New bullet 2 (insert after new bullet 1):
> - **A critical step is protected from an observability failure by ORDERING, not by catching.** When a downstream effect (a commit, a state write) must not be lost to a failure in an observability step, the composition MUST perform the critical effect BEFORE the observability tap, so a tap failure surfaces as a bug (per the routing above) without having swallowed or reverted the critical effect. Wrapping the tap in a catch to "protect" the critical step is forbidden — it reintroduces exactly the blind bulkhead this discipline exists to remove.

No `## ` (H2) heading is added, changed, or removed (§"ROP composition" is an existing `### ` H3), so tests/heading-coverage.json needs no co-edit.

## Proposal: Add ruff BLE (flake8-blind-except) to the enumerated linter rule set

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add `BLE` (flake8-blind-except) to the spec-enumerated ruff rule selection in non-functional-requirements.md §"Linter rule set", raising the count from 27 to 28 categories, with a key-per-category meaning bullet. BLE bans the broad `except Exception` / bare `except:` construct directly, the construct-level companion to the AST `check-no-except-outside-io` and the belt-and-suspenders guard for the ROP expected-vs-unexpected-failure split.

### Motivation

rop-sweep-fleet-policy thread Part C + maintainer decision 2026-07-18 ("Add to template + backfill fleet"). BLE is currently enabled in only ONE fleet repo (livespec-orchestrator-beads-fabro, added during its cleanup) and not even in livespec core. Enumerating it in the spec makes it the fleet linter standard the copier template stamps and the backfill epic applies.

### Proposed Changes

EDIT 1 — in §"Linter rule set", replace the "Rule selection" bullet.

Exact verbatim replace-target:
> - **Rule selection** (27 categories): `E F I B UP SIM C90 N RUF PL PTH` (11 baseline categories) PLUS `TRY FBT PIE SLF LOG G TID ERA ARG RSE PT FURB SLOT ISC T20 S` (16 v012 additions = 27 total). Key per-category meanings:

Replace with:
> - **Rule selection** (28 categories): `E F I B UP SIM C90 N RUF PL PTH` (11 baseline categories) PLUS `TRY FBT PIE SLF LOG G TID ERA ARG RSE PT FURB SLOT ISC T20 S` (16 v012 additions) PLUS `BLE` (flake8-blind-except) = 28 total. Key per-category meanings:

EDIT 2 — insert one meaning bullet at the END of the "Key per-category meanings" sub-list, immediately AFTER the existing `S` bullet.

Exact verbatim anchor (the sub-bullet the new bullet follows):
>   - `S` (flake8-bandit) — security anti-patterns: `pickle.loads`, `subprocess` with `shell=True`, `eval`, `exec`, etc.

New sub-bullet (insert after that anchor):
>   - `BLE` (flake8-blind-except) — bans the broad `except Exception` and bare `except:` bulkhead directly at the construct level; the construct-level companion to the AST `check-no-except-outside-io`, and the belt-and-suspenders guard for the ROP railway's expected-vs-unexpected-failure split (§"ROP composition"). A deliberately fail-open boundary uses the per-line `# noqa: BLE001 — <reason>` escape.

No `## ` (H2) heading is added, changed, or removed (§"Linter rule set" is an existing `### ` H3), so tests/heading-coverage.json needs no co-edit.

## Proposal: The ROP railway is fleet+adopter-wide (full-ROP fleet bar)

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

State the fleet enforcement bar for error-handling in non-functional-requirements.md §"Shared content provenance", as a sibling bullet to "Red-green-replay is fleet+adopter-wide": every livespec-governed repo carrying first-party Python (Drivers and livespec-dev-tooling included) MUST put its product logic on the Result/IOResult railway — expected failures as failure-track values, `dry-python/returns` vendored, `reportUnusedCallResult` and ruff `BLE` enabled — with the ONLY permitted broad `except Exception` being a single outermost boundary (a CLI supervisor bug-catcher that logs and returns exit 1, OR a never-wedge-the-agent hook's fail-open silent pass-through the Driver hook contracts already require). No "thin repo" exemption; the sole exemption is a repo with zero first-party Python (e.g. the Rust operator console). New consumers inherit the railway scaffold through the copier template.

### Motivation

rop-sweep-fleet-policy thread Decision 1 + maintainer decision 2026-07-18 ("Flat: full ROP everywhere" — every Python-carrying fleet repo must vendor `returns` and be on the railway, including the thin driver plugins). Grounded in the existing fail-open hook discipline (contracts.md Driver-hook sections: "a hook failure MUST be a silent pass-through"), so the fail-open hook's top-level handler is a recognized boundary, not a blind bulkhead. Realized for new consumers by the copier template (this same slice adds BLE + the parameterized layout block); existing off-railway repos (livespec-orchestrator-git-jsonl, livespec-runtime, the Drivers, livespec-dev-tooling) converge via a tracked cross-repo epic.

### Proposed Changes

In §"Shared content provenance", insert ONE new bullet into the provenance bullet list IMMEDIATELY AFTER the existing "**Red-green-replay is fleet+adopter-wide.**" bullet and BEFORE the paragraph that begins "Drift between `livespec`'s requirements".

Exact verbatim anchor (the bullet the new bullet follows), ends with:
> ... New adopters inherit this wiring through the `templates/orchestrator-plugin/` copier scaffold.

New bullet (insert after that anchor):
> - **The ROP railway is fleet+adopter-wide.** Every livespec-governed repo carrying any first-party Python — the `livespec-driver-*` Drivers and `livespec-dev-tooling` included, not only the orchestrator plugins and sibling libraries named above — MUST put its product logic on the `Result` / `IOResult` railway (§"ROP composition"): expected failure modes flow as failure-track values, `dry-python/returns` is vendored under `_vendor/`, and the guardrails against silently discarding a `Result` or blindly catching a bug — `reportUnusedCallResult = "error"` (§"Typechecker rule set") and ruff `BLE` (§"Linter rule set") — are enabled. The ONLY permitted broad `except Exception` is a single outermost boundary handler: for a CLI wrapper, the supervisor bug-catcher that logs with full context and returns exit `1` (§"Supervisor discipline"); for a never-wedge-the-agent hook, the fail-open silent pass-through its Driver hook contract already requires (a hook failure is a silent pass-through, per `contracts.md`). There is NO "thin repo" exemption — a repo whose only Python is fail-open hooks still composes those hooks' bodies on the railway beneath that single boundary. The SOLE exemption is a governed repo with ZERO first-party Python (e.g. a Rust component such as the operator console). New consumers inherit the railway scaffold — ruff `BLE`, `reportUnusedCallResult`, and the parameterized `[tool.livespec_dev_tooling]` layout block — through the `templates/orchestrator-plugin/` copier template.

No `## ` (H2) heading is added, changed, or removed (§"Shared content provenance" is an existing `#### ` H4), so tests/heading-coverage.json needs no co-edit.
