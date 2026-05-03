## Proposal: tests-mirror-pairing exempts private-helper modules and pure-declaration modules; re-aggregate check into just check

### Target specification files

- SPECIFICATION/spec.md

### Summary

Update `dev-tooling/checks/tests_mirror_pairing.py` to exempt two categories of source files from the 1:1 mirror-pairing rule: (1) private-helper modules — `.py` files whose filename starts with `_` and is NOT `__init__.py` (e.g., `_seed_railway_emits.py`); their behavior is exercised through the public function that imports them. (2) Pure-declaration modules — files whose AST contains no `FunctionDef` / `AsyncFunctionDef` anywhere (no module-level or class-level functions). This catches boilerplate `__init__.py`, pure dataclass declarations under `schemas/dataclasses/`, the `DoctorContext` value-object, the `LivespecError` hierarchy, and the static-check registry — none of which have testable behavior independent of the consumers tested elsewhere. After the exemptions are wired in, re-aggregate `check-tests-mirror-pairing` into the `just check` target list (it was deferred from the v033 D5b drain pending the `__init__.py` exemption per the comment at justfile lines 76-83).

### Motivation

The current `tests_mirror_pairing.py` requires every `.py` under the three covered trees to have a paired test file. Real-repo state surfaces three categories that don't fit cleanly: (a) three private-helper modules under `livespec/commands/` (`_seed_railway_emits.py`, `_seed_railway_emits_per_tree.py`, `_seed_railway_writes.py`) — covered through `test_seed.py`'s integration tests; (b) eleven pure dataclass modules under `livespec/schemas/dataclasses/` plus `livespec/context.py`, `livespec/errors.py`, and `livespec/doctor/static/__init__.py` — none have functions or methods to test independently; (c) the structlog-configuring `livespec/__init__.py` and the validator `livespec/validate/proposal_findings.py` — these DO have logic and need paired stub tests, which land alongside this revise. The pure-declaration heuristic (no `FunctionDef` / `AsyncFunctionDef` anywhere in the AST) is a principled, mechanical filter that catches all the legitimate non-testable cases without needing a per-module allowlist. v033 D1 anticipated the boilerplate `__init__.py` exemption; this widens the exemption to its natural generalization. User-gated 2026-05-03 as Mini-track item M4 in the Phase 7 enforcement-suite mini-track (Option C).

### Proposed Changes

Single atomic edit: amend the first sentence of `SPECIFICATION/spec.md` §"Testing approach" to enumerate the two exemptions.

**SPECIFICATION/spec.md §"Testing approach".** Replace the first sentence:

> Every Python source file under `livespec/`, `bin/`, and `dev-tooling/checks/` MUST have a paired test file at the mirrored path under `tests/`.

With:

> Every Python source file under `livespec/`, `bin/`, and `dev-tooling/checks/` MUST have a paired test file at the mirrored path under `tests/`, except: (a) **private-helper modules** — `.py` files whose filename starts with `_` and is NOT `__init__.py` (e.g., `_seed_railway_emits.py`); these are covered transitively through the public function that imports them. (b) **Pure-declaration modules** — files whose AST contains no `FunctionDef` / `AsyncFunctionDef` anywhere (no module-level or class-level functions); covers boilerplate `__init__.py`, pure dataclass declarations, value-object modules, and the `LivespecError` hierarchy — none have testable behavior independent of their consumers. The `bin/_bootstrap.py` shebang preamble has its own special-cased test at `tests/bin/test_bootstrap.py`. The `dev-tooling/checks/tests_mirror_pairing.py` script enforces the binding mechanically and runs in the `just check` aggregate.

Implementation work that lands atomically with the revise commit: extend `dev-tooling/checks/tests_mirror_pairing.py` to skip private-helper modules (filename matches `_<name>.py` where `<name>` is not `init__`) and pure-declaration modules (AST inspection: no `FunctionDef` / `AsyncFunctionDef` anywhere); update the paired test at `tests/dev-tooling/checks/test_tests_mirror_pairing.py` to cover both exemption categories (private helper, pure-declaration init, pure-dataclass module) and the corresponding non-exempt cases (module with FunctionDef, module with AsyncFunctionDef, class with method); re-add `check-tests-mirror-pairing` to the `just check` target list in `justfile`. Two stub tests for the residual flagged-and-not-exempt cases also land in this commit: `tests/livespec/test__init__.py` (verifies the structlog run_id binding) and `tests/livespec/validate/test_proposal_findings.py` (validator round-trip + schema-violation cases plus a hypothesis-based property test per `check-pbt-coverage-pure-modules`).
