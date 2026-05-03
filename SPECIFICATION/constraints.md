# Constraints — `livespec`

This file enumerates the architecture-level constraints `livespec` MUST satisfy. Per the plan's Phase-6 scope guidance, only the constraints PROPOSAL.md states directly land here; the bulk of the python-skill-script style requirements migrate via a Phase 8 propose-change cycle and are NOT seeded into this file.

## Python runtime constraint

`livespec`'s Python wrappers and library code MUST run on Python 3.10 or newer. The `_bootstrap.py` shebang preamble MUST refuse to import `livespec` on older interpreters (exit 127 with an install-instruction message). The exact version pin is `.python-version`; the user-facing minimum is encoded in `pyproject.toml`'s `[project].requires-python`.

## Vendored-library discipline

Runtime dependencies that are NOT part of the standard library MUST be vendored under `.claude-plugin/scripts/_vendor/<lib>/`. The vendoring procedure is the v018 Q3 / v026 D1 procedure: clone the upstream repo at a fixed ref (or fetch the sdist tarball when no live upstream git mirror exists, per v026 D1), copy the source tree, copy the LICENSE file, and record the entry in `.vendor.jsonc` with non-placeholder `upstream_url`, `upstream_ref`, and `vendored_at` fields plus a `shim: true` flag for hand-authored shims.

`livespec` MUST NOT install runtime dependencies via pip or any other package manager at user invocation time. The vendored tree is the only runtime-import root for non-stdlib code (apart from the dev-time tooling layer at `pyproject.toml`'s `[dependency-groups.dev]`).

## Pure / IO boundary

Filesystem operations, subprocess invocations, CLI parsing, and any other side effect MUST live under `livespec/io/<facade>.py` behind `@impure_safe` carriers from the `returns` library. Pure layers (`livespec/parse/`, `livespec/validate/`) MUST NOT import from `livespec/io/`; the `import-linter` `parse-and-validate-are-pure` contract enforces the boundary.

`LivespecError` raise-sites are restricted to `livespec/io/`. Pure layers convert exceptions into `Failure(<LivespecError>)` only after `IOResult` produces a concrete value. The `dev-tooling/checks/no_raise_outside_io.py` AST check enforces the constraint mechanically.

## ROP composition

Every command railway MUST flow through `IOResult` via `.bind(...)` chaining. Stages compose left-to-right; failures short-circuit via the `IOResult` track without explicit `if`-style branching. Domain errors (expected failures) flow as `Failure(<LivespecError>)`; bugs (unexpected failures) propagate as raised exceptions to the supervisor's bug-catcher.

## Supervisor discipline

Each command's `main()` function MUST be the only place outside `livespec/io/` where `sys.exit` (or its `raise SystemExit(...)` shape inside `bin/`) MAY appear. The supervisor pattern-matches the final railway `IOResult` onto an exit code via `unsafe_perform_io` plus a `match` statement that ends in `case _: assert_never(unwrapped)` for exhaustiveness. The `dev-tooling/checks/supervisor_discipline.py` AST check enforces this shape.

The shebang-wrapper layer at `bin/<sub-command>.py` MUST conform to the canonical 6-statement shape per PROPOSAL.md §"Wrapper shape": shebang → docstring → `from _bootstrap import bootstrap` → `bootstrap()` → `from livespec.<...> import main` → `raise SystemExit(main())`. The optional blank line between statements 4 and 5 is permitted per v016 P5.

## Typechecker constraints (Phase 1 pin)

`pyright` MUST run in strict mode against the `livespec/**` surface. The diagnostics enabled beyond `strict` baseline are: `reportImplicitOverride`, `reportImportCycles`, `reportPropertyTypeMismatch`, `reportShadowedImports`, `reportMissingSuperCall`, `reportUnnecessaryComparison`, and `reportUnnecessaryTypeIgnoreComment` (the seven strict-plus diagnostics per v025 D1).

`returns` library typechecker integration MUST use plain pyright strict (no plugin); the v018 Q4 returns-pyright-plugin assumption was falsified at v025 D1 — pyright has no plugin system and dry-python/returns explicitly does not support pyright. Strict-plus diagnostics carry the load.

## Heading taxonomy

Top-level `#` headings in spec files SHOULD reflect intent rather than a fixed taxonomy. `##` headings within each spec file form the test-anchor surface: every `##` heading MUST have a corresponding entry in `tests/heading-coverage.json` whose `spec_root` field matches the heading's tree per v021 Q3.

The `dev-tooling/checks/heading_coverage.py` script enforces the binding mechanically. Pre-Phase-6 the check tolerates an empty `[]` array; from this seed forward (Phase 6 onward), emptiness is a failure if any spec tree exists.

## BCP14 normative language

Spec-file prose MUST use BCP 14 (RFC 2119 + RFC 8174) requirement language: `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`, `OPTIONAL`. The keywords MUST be uppercase to be normative; lowercase use is non-normative descriptive prose. The `livespec`-template's NLSpec discipline doc enumerates BCP14 well-formedness rules in detail; this constraints file states only the meta-rule.

## Self-application bootstrap exception

The Phase 0–6 imperative window per PROPOSAL.md §"Self-application" v018 Q2 / v019 Q1 closes at the Phase 6 seed commit (this revision). From Phase 7 onward, every mutation to this `SPECIFICATION/` MUST flow through `/livespec:propose-change` → `/livespec:revise` against the appropriate spec target. Hand-edits to spec files outside the propose-change/revise loop are forbidden and would be caught by `dev-tooling/checks` plus the doctor static phase.

The bootstrap scaffolding under `bootstrap/` is removed at Phase 11 per the plan; once removed, this constraint operates without the bootstrap-window carve-out.
