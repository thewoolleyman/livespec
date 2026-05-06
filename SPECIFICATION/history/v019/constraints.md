# Constraints — `livespec`

This file enumerates the architecture-level constraints `livespec` MUST satisfy. The Phase-6 seed contained only constraints stated directly in PROPOSAL.md; the bulk of the python-skill-script style requirements migrate per-section via Phase-8 propose-change cycles per Plan Phase 8 item 2 (`python-style-doc-into-constraints`).

## Constraint scope

The constraints in this file MUST be satisfied by:

- Every Python module bundled with the plugin under `.claude-plugin/scripts/livespec/**`.
- Every Python shebang-wrapper executable under `.claude-plugin/scripts/bin/*.py`, including the shared `_bootstrap.py` module.
- Every Python module or script under `<repo-root>/dev-tooling/**`.

The constraints DO NOT apply to:

- Vendored third-party code under `.claude-plugin/scripts/_vendor/**`. Vendored libs ship at pinned upstream versions per the v018 Q3 / v026 D1 vendoring procedure and are EXEMPT from livespec's own style rules.
- User-provided Python modules loaded via custom-template extension hooks (e.g., `template.json`'s `doctor_static_check_modules`). Extension code is the extension author's responsibility; livespec's enforcement suite MUST NOT scope to it. Extension authors MUST satisfy only the calling-API contract — the `TEMPLATE_CHECKS` export shape, the `CheckRunFn` signature, and the `Finding` payload shape, all defined inside `livespec/`. Inside an extension module, the author MAY use any library, architecture, and patterns of their choosing; livespec MUST NOT impose requirements beyond invocability per the contract.

Tests under `<repo-root>/tests/` MUST comply unless a test explicitly exercises a non-conforming input, in which case the non-conformance MUST be declared in a docstring at the top of the fixture.

## Non-interactive execution

Scripts MUST NOT prompt the user via the terminal: `input()`, `getpass.getpass()`, and any other prompt-and-wait construct are forbidden. Scripts MUST NOT manipulate terminal modes or open `/dev/tty`. Scripts MUST NOT rely on `sys.stdout.isatty()` or `os.isatty(...)` to gate interactive behavior; they MAY use these checks to select between stdin-piped and stdin-file-redirect handling, provided neither branch prompts the user.

A script that requires a human-confirmation step MUST fail with an actionable message and exit code `3` (precondition failed), leaving the decision to the caller.

All configuration and input MUST arrive through one of: positional arguments, flags via `argparse`, environment variables, files named by the above, or stdin pipe when documented.

## Python runtime constraint

`livespec`'s Python wrappers and library code MUST run on Python 3.10 or newer. Python 3.10's `X | Y` union syntax, `match` statements, `ParamSpec`, `TypeAlias`, and improved typing syntax are expected idioms. Features introduced in Python 3.11+ (e.g., `Self`, `tomllib`, `ExceptionGroup`) MUST NOT be used.

The shared `bin/_bootstrap.py:bootstrap()` function MUST assert `sys.version_info >= (3, 10)` and exit `127` with an actionable install-instruction message on older interpreters. `bin/_bootstrap.py` is the canonical location for the version check; `.claude-plugin/scripts/livespec/__init__.py` MUST NOT raise (the railway requires unconditional importability).

Bundled executables MUST use the shebang `#!/usr/bin/env python3`. No other interpreter path is valid.

`.python-version` at the repo root pins the developer and CI Python version to an exact 3.10.x release (managed by `uv python pin` per v024 D1). `pyproject.toml`'s `[project.requires-python]` declares the same constraint as the user-facing minimum. `.mise.toml` pins only the non-Python binaries (`uv`, `just`, `lefthook`); developers run `mise install` then `uv sync --all-groups` to materialize the matched environment.

## End-user runtime dependencies

`python3` >= 3.10 MUST be the sole runtime dependency the skill imposes on end-user machines. Python 3.10+ is preinstalled on Debian ≥ 12, Ubuntu ≥ 22.04, Fedora, Arch, RHEL ≥ 9; one-command install on macOS via Homebrew or Xcode CLT.

The skill MUST NOT require any PyPI install step from end users; runtime imports MUST be satisfiable from the stdlib plus the vendored tree under `.claude-plugin/scripts/_vendor/<lib>/`. `jq` is NOT a runtime dependency (stdlib `json` covers every use). Bash MUST NOT be invoked anywhere in the bundle — every executable path is `python3` (or shebang scripts that `exec` Python).

## Vendored-library discipline

The bundle MUST ship a curated set of pure-Python third-party libraries under `.claude-plugin/scripts/_vendor/<lib>/`. The vendored tree is the only runtime-import root for non-stdlib code, apart from the dev-time tooling layer at `pyproject.toml`'s `[dependency-groups.dev]`. `livespec` MUST NOT install runtime dependencies via pip or any other package manager at user invocation time.

### Lib admission policy

Every vendored lib MUST be:

- Pure Python — no compiled wheels, no C/Rust extensions.
- Permissively licensed — MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, or PSF-2.0. PSF-2.0 was admitted in v013 M1 to vendor `typing_extensions`; the narrow extension is deliberate and MUST NOT generalize to other licenses without an explicit PROPOSAL revision.
- Actively maintained by a reputable upstream.
- Either zero-transitive-dep, or all transitive deps also vendored.

Each vendored lib's `LICENSE` file MUST be preserved at `_vendor/<lib>/LICENSE`. A `NOTICES.md` at the repo root MUST list every vendored lib with its license and copyright.

### Locked vendored libs

Each lib is pinned to an exact upstream ref recorded in `<repo-root>/.vendor.jsonc`:

- **`returns`** (dry-python/returns, BSD-3-Clause) — ROP primitives: `Result`, `IOResult`, `@safe`, `@impure_safe`, `flow`, `bind`, `Fold.collect`, `lash`. NO pyright plugin is vendored: pyright has no plugin system by design (microsoft/pyright#607) and dry-python/returns explicitly does not support pyright (dry-python/returns#1513). The seven strict-plus diagnostics in `[tool.pyright]` (especially `reportUnusedCallResult = "error"`) are the load-bearing guardrails against silent `Result` / `IOResult` discards. See PROPOSAL.md §"Runtime dependencies" v025 D1 for the full disposition.
- **`fastjsonschema`** (horejsek/python-fastjsonschema, MIT) — JSON Schema Draft-7 validator.
- **`structlog`** (hynek/structlog, BSD-2 / MIT dual) — structured JSON logging.
- **`jsoncomment`** (MIT, derivative work) — vendored as a minimal hand-authored shim per v026 D1. The shim at `.claude-plugin/scripts/_vendor/jsoncomment/__init__.py` faithfully replicates jsoncomment 0.4.2's `//` line-comment and `/* */` block-comment stripping semantics. The canonical upstream (`bitbucket.org/Dando_Real_ITA/json-comment`) was sunset by Atlassian and no live git mirror exists; the shim's `LICENSE` carries verbatim MIT attribution to Gaspare Iengo (citing jsoncomment 0.4.2's `COPYING` file). Used by `livespec/parse/jsonc.py` as a comment-stripping pre-pass over stdlib `json.loads`.
- **`typing_extensions`** (python/typing_extensions, PSF-2.0) — vendored full upstream verbatim at tag `4.12.2` per v027 D1. Provides `override`, `assert_never`, `Self`, `Never`, `TypedDict`, `ParamSpec`, `TypeVarTuple`, `Unpack` plus the variadic-generics symbols transitively required at import time by `returns`, `structlog`, `fastjsonschema` on Python 3.10. The verbatim PSF-2.0 `LICENSE` is shipped at `_vendor/typing_extensions/LICENSE`.

The shared `bin/_bootstrap.py:bootstrap()` function MUST insert BOTH the bundle's `scripts/` directory AND the bundle's `scripts/_vendor/` directory into `sys.path`. Adding `scripts/` makes the `livespec` package resolvable (`from livespec.commands.seed import main`); adding `scripts/_vendor/` makes each vendored top-level package resolvable under its natural name (`from returns.io import IOResult`, `import structlog`, etc.).

### Vendoring procedure

Source-tree population is governed by two paths:

- **Re-vendoring** of upstream-sourced libs (`returns`, `fastjsonschema`, `structlog`, `typing_extensions`) MUST go through `just vendor-update <lib>` — the only blessed mutation path. The recipe fetches the upstream ref, copies it under `_vendor/<lib>/`, preserves `LICENSE`, and updates `.vendor.jsonc`'s recorded ref.
- **Initial vendoring** is a one-time MANUAL procedure (the v018 Q3 exception, executed once per livespec repo at Phase 2 of the bootstrap plan): `git clone` the upstream repo at a working ref into a throwaway directory, `git checkout <ref>` matching `.vendor.jsonc`'s `upstream_ref`, copy the library's source tree under `_vendor/<lib>/`, copy the upstream `LICENSE` verbatim to `_vendor/<lib>/LICENSE`, record the lib's provenance (`upstream_url`, `upstream_ref`, `vendored_at` ISO-8601 UTC), delete the throwaway clone, and smoke-test that the wrapper bootstrap imports the vendored lib successfully. The exception resolves the circularity that `just vendor-update` invokes Python through `livespec.parse.jsonc` (which imports `jsoncomment`); the recipe cannot run before `jsoncomment` exists.
- **Shim libs** are livespec-authored and DO NOT go through `just vendor-update`. The `jsoncomment` shim is the sole shim post-v027; it is widened (one-line edit per added feature) or replaced with a full upstream vendoring via a new propose-change cycle. `.vendor.jsonc` records the shim's upstream attribution ref (for provenance) and a `shim: true` flag.

Direct edits to `_vendor/` files are forbidden for upstream-sourced libs — any such edit is treated as drift and caught at code review. The "never edit `_vendor/`" rule applies only to upstream-sourced libs; shim updates go through normal code-review.

`.vendor.jsonc` records `{upstream_url, upstream_ref, vendored_at}` per lib; for shims, additionally `shim: true` and the provenance ref from which the shim's `LICENSE` was derived.

`_vendor/` is EXEMPT from livespec's own style rules, type-checking strictness, coverage measurement, and CLAUDE.md coverage enforcement per `## Constraint scope` above.

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

## File LLOC ceiling

Every `.py` file under `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**` SHOULD have at most 200 logical lines of code (LLOC) and MUST have at most 250 LLOC. LLOC excludes blank lines, comment-only lines, and module/class/function docstrings — it counts only executable statements.

The two-tier policy splits the prior single-threshold cap: 200 LLOC is a SOFT ceiling — files at 201-250 LLOC pass the per-commit `check-complexity` target with a structured warning emitted to stderr (so `just check` stays green) but are flagged for refactoring. 250 LLOC is the HARD ceiling — files above 250 LLOC fail the check (exit 1). The `dev-tooling/checks/file_lloc.py` script enforces both bindings mechanically. The two-tier policy removes the mid-Green-amend wedge where an in-progress refactor naturally pushes LLOC just above 200 and would otherwise force a sibling-module extraction in the same amend; instead, the warning surfaces the growing file and the refactor lands in its own cycle when natural.

The `check-no-lloc-soft-warnings` release-gate target (parallel to `check-no-todo-registry`) closes the soft-band drift loophole. The release-gate is NOT included in `just check` and does NOT run per-commit; it runs ONLY on the release-tag CI workflow (`.github/workflows/release-tag.yml`, fires on `v*` tag push). The release-gate rejects any first-party `.py` file in the 201-250 LLOC soft band, forcing refactor work to land before any release tag. Per-commit ergonomic (warning, no block); tag-push enforcement (block until clean).

## Heading taxonomy

Top-level `#` headings in spec files SHOULD reflect intent rather than a fixed taxonomy.

Every `##` heading in a **template-declared NLSpec file at a spec-tree root** MUST have a corresponding entry in `tests/heading-coverage.json`. The registry maps `(spec_root, spec_file, heading)` triples to pytest test identifiers per PROPOSAL.md §"Coverage registry" (lines 3771-3813). The `spec_root` field is the repo-root-relative path to the spec tree's root (main spec = `SPECIFICATION`; sub-specs = `SPECIFICATION/templates/<name>`). The `spec_file` field is the `spec_root`-relative path to the spec file containing the heading (e.g., `spec.md`, `contracts.md`). The `heading` field is the exact `##` heading text. Each entry's `test` field is a pytest node identifier (`<path>::<function>`) OR the literal `"TODO"`; `"TODO"` entries MUST also carry a non-empty `reason` field.

The `dev-tooling/checks/heading_coverage.py` script enforces the binding mechanically at `just check` time. Per tree, the check walks **only the template-declared NLSpec files at the tree root** — for the `livespec` template, the four files `spec.md`, `contracts.md`, `constraints.md`, and `scenarios.md`. The check does NOT recurse into `proposed_changes/`, `history/`, `templates/<name>/history/`, or any other subdirectory; it does NOT include the skill-owned `README.md` at the tree root. Boilerplate headings such as `## Proposal: ...` in propose-change files, `## Decision and Rationale` in revision records, and per-version snapshot headings under `history/v*/` are out of scope for the registry and are NOT counted by the check.

The check fails in three directions:

1. **Uncovered heading** — a `(spec_root, spec_file, heading)` triple appears in some template-declared spec file but no matching registry entry exists. Diagnostic: `spec heading missing coverage entry`.
2. **Orphan registry entry** — a registry entry's `(spec_root, spec_file, heading)` triple does not match any heading in any template-declared spec file (heading was renamed or removed without updating the registry). Diagnostic: `registry entry orphaned — no matching spec heading`.
3. **Missing `reason` on a `TODO` entry** — entry carries `test: "TODO"` but no non-empty `reason` field. Diagnostic: `TODO registry entry missing reason`.

The check SKIPS `##` headings whose text begins with the literal `Scenario:` prefix per PROPOSAL.md lines 3779-3782: scenario blocks are exercised by the per-spec-file rule test for the scenario-carrying spec file; per-scenario registry entries are not required.

Pre-Phase-6 the check tolerated an empty `[]` array; from the Phase 6 seed forward (this revision and later), emptiness is a failure if any spec tree exists.

## BCP14 normative language

Spec-file prose MUST use BCP 14 (RFC 2119 + RFC 8174) requirement language: `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`, `OPTIONAL`. The keywords MUST be uppercase to be normative; lowercase use is non-normative descriptive prose. The `livespec`-template's NLSpec discipline doc enumerates BCP14 well-formedness rules in detail; this constraints file states only the meta-rule.

## Self-application bootstrap exception

The Phase 0–6 imperative window per PROPOSAL.md §"Self-application" v018 Q2 / v019 Q1 closes at the Phase 6 seed commit (this revision). From Phase 7 onward, every mutation to this `SPECIFICATION/` MUST flow through `/livespec:propose-change` → `/livespec:revise` against the appropriate spec target. Hand-edits to spec files outside the propose-change/revise loop are forbidden and would be caught by `dev-tooling/checks` plus the doctor static phase.

The bootstrap scaffolding under `bootstrap/` is removed at Phase 11 per the plan; once removed, this constraint operates without the bootstrap-window carve-out.
