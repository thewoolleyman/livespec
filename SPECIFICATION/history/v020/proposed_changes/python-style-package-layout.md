---
topic: python-style-package-layout
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T05:00:00Z
---

## Proposal: Migrate style-doc §"Package layout" into `SPECIFICATION/constraints.md`

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Cycle 5 of Plan Phase 8 item 2 per-section migration. Lands the source doc's §"Package layout" content (lines 300-514, ~215 lines) as a new `## Package layout` section in `SPECIFICATION/constraints.md`, inserted between `## Vendored-library discipline` and `## Pure / IO boundary`. Preserves the 3 source-doc sub-sections as `###`: `### Dataclass authorship`, `### Context dataclasses` (with verbatim code block pinning the immutable dataclass contracts), `### CLI argument parsing seam`. The canonical directory tree itself remains in PROPOSAL.md §"Skill layout inside the plugin" and is referenced via "see PROPOSAL.md §..." (the directory-tree migration is out of scope for this cycle; it belongs to Plan Phase 8 item 7 `static-check-semantics` or a future cycle of item 3 `companion-docs-mapping`). Cross-references cycle 1's revise body for the deviation rationale from `deferred-items.md`'s "at seed time" guidance.

### Motivation

The source-doc §"Package layout" section codifies the layered Python-package architecture that every other constraint in `SPECIFICATION/constraints.md` implicitly assumes — `## Pure / IO boundary` references `livespec/parse/`, `livespec/validate/`, `livespec/io/`; `## ROP composition` references the railway-emitting layers; `## Supervisor discipline` references the `bin/` 6-statement wrapper shape and `commands/<cmd>.py main()` supervisors. Without a codified package-layout section in the spec, those constraints have no explicit foundation in `SPECIFICATION/`; future maintainers must infer the layer structure from PROPOSAL.md (frozen) or hand-trace the cross-references. Migrating §"Package layout" into `constraints.md` makes the architectural foundation explicit alongside the rules it underpins.

The destination is `SPECIFICATION/constraints.md` (not `spec.md`) per Plan Phase 8 item 2's "destination heading taxonomy fits better" heuristic: package layout is an architectural-constraint section (every per-subpackage rule is a MUST), parallel to the existing `## Pure / IO boundary` and `## ROP composition` constraints. Position is after `## Vendored-library discipline` and before `## Pure / IO boundary`: the layout introduces the layers (`io/`, `parse/`, `validate/`, `commands/`, `doctor/`), then `## Pure / IO boundary` codifies the import-direction rule between them.

### Proposed Changes

One atomic edit to **SPECIFICATION/constraints.md**: insert a new `## Package layout` section between the closing line of `## Vendored-library discipline` and `## Pure / IO boundary`:

> ## Package layout
>
> The plugin's Python surface lives under `.claude-plugin/scripts/`. The canonical directory tree (every subdirectory, every file at the tree root) is maintained in PROPOSAL.md §"Skill layout inside the plugin" and MUST NOT be duplicated here.
>
> The top-level layout has three roots:
>
> - **`bin/`** — executable shebang-wrappers plus the shared `_bootstrap.py`. Each wrapper file MUST be exactly 6 statements matching the canonical wrapper shape (plus an optional single blank line between the imports and `raise SystemExit(main())` per v016 P5). No logic. `chmod +x` MUST be applied.
> - **`_vendor/`** — vendored third-party libs, EXEMPT from livespec rules per `## Constraint scope` above.
> - **`livespec/`** — the Python package. Every other file under this root MUST follow every rule in `SPECIFICATION/constraints.md`.
>
> Per-subpackage conventions:
>
> - **`commands/<cmd>.py`** — one module per sub-command. MUST export `run()` (railway-emitting; returns `IOResult`) and `main()` (the supervisor that unwraps the final `IOResult` to a process exit code).
> - **`doctor/run_static.py`** — the static-phase orchestrator. MUST compose every check module in `doctor/static/` via a single railway chain. The composition primitive (e.g., `Fold.collect`, manual fan-out) is implementer choice under the architecture-level constraints elsewhere in this file.
> - **`doctor/static/__init__.py`** — the **static check registry**. MUST import every check module by explicit name and re-export a tuple of `(SLUG, run)` pairs. Adding or removing a check MUST be one explicit edit to the registry; dynamic discovery is forbidden so pyright strict can fully type-check the composition.
> - **`doctor/static/<check>.py`** — one module per static check. MUST export a `SLUG` constant and a `run(ctx) -> IOResult[Finding, E]` function where `E` is any `LivespecError` subclass. (See `## ROP composition` and the supervisor discipline sections below for the railway/error contract.)
> - **`io/`** — the impure boundary. Every function MUST wrap a side-effecting operation (filesystem, subprocess, git, argparse) with `@impure_safe` from the `returns` library. `io/` also hosts thin typed facades over vendored libs whose surface types are not strict-pyright-clean (e.g., `fastjsonschema`, `structlog`); see `### Vendored-lib type-safety integration` under `## Type safety`.
> - **`parse/`** — pure parsers. Every function MUST take a string/bytes/dict and return `Result[T, ParseError]`. Includes the restricted-YAML parser at `parse/front_matter.py`.
> - **`validate/`** — pure validators using the **factory shape**. Each validator at `validate/<name>.py` MUST export `validate_<name>(payload: dict, schema: dict) -> Result[<Dataclass>, ValidationError]`, where `<Dataclass>` is the paired dataclass at `schemas/dataclasses/<name>.py`. Callers in `commands/` or `doctor/` read schemas from disk via `io/` wrappers and pass the parsed dict. Validators invoke `livespec.io.fastjsonschema_facade.compile_schema` for the actual compile (the facade owns the compile cache). `validate/` MUST stay strictly pure: no module-level mutable state, no filesystem I/O. Every schema at `schemas/*.schema.json` MUST have a paired validator at `validate/<name>.py` AND a paired dataclass at `schemas/dataclasses/<name>.py`; three-way drift is caught by `check-schema-dataclass-pairing` per v013 M6.
> - **`schemas/`** — JSON Schema Draft-7 files plus the `dataclasses/` subdirectory holding the paired hand-authored dataclasses. Filename matches the dataclass: `LivespecConfig` → `livespec_config.schema.json` paired with `schemas/dataclasses/livespec_config.py` AND `validate/livespec_config.py`. `check-schema-dataclass-pairing` enforces three-way drift-freedom (every schema has matching dataclass + validator; every dataclass has matching schema + validator; every validator has matching schema + dataclass).
> - **`context.py`** — immutable context dataclasses (`DoctorContext`, `SeedContext`, etc.). The railway payload threaded through every command. See `### Context dataclasses` below for the field sets.
> - **`errors.py`** — the `LivespecError` hierarchy with per-subclass `exit_code` class attribute. The hierarchy MUST hold ONLY expected-failure (domain error) classes per the error-handling discipline; bugs MUST NOT be represented as `LivespecError` subclasses (they propagate as raised exceptions to the supervisor's bug-catcher).
>
> ### Dataclass authorship
>
> Each JSON Schema under `schemas/*.schema.json` MUST have a paired hand-authored `@dataclass(frozen=True, kw_only=True, slots=True)` at `schemas/dataclasses/<name>.py`. The dataclass and the schema are co-authoritative: the schema is the wire contract (validated at the boundary by `fastjsonschema`); the dataclass is the Python type threaded through the railway (`Result[<Dataclass>, ValidationError]` from each validator per the factory shape). Domain-meaningful field types MUST use the canonical `NewType` aliases from `livespec/types.py`.
>
> - The file name MUST match the `$id`-derived snake_case dataclass name (e.g., `LivespecConfig` → `livespec_config.py`).
> - Fields MUST match the schema one-to-one in name and Python type.
> - `schemas/__init__.py` MUST re-export every dataclass name for convenient import.
> - No codegen toolchain. No generator. Drift between schema, dataclass, and validator MUST be caught mechanically by `check-schema-dataclass-pairing` (three-way AST walker per v013 M6: schema ↔ dataclass ↔ validator).
>
> ### Context dataclasses
>
> Every context dataclass MUST be `@dataclass(frozen=True, kw_only=True, slots=True)` and carry exactly the fields below at minimum. Sub-command contexts MUST embed `DoctorContext` rather than inheriting so the type checker can narrow each sub-command's payload independently. Domain-meaningful fields MUST use `NewType` aliases from `livespec/types.py`.
>
> ```python
> from dataclasses import dataclass
> from pathlib import Path
> from typing import Literal
>
> from livespec.types import Author, RunId, SpecRoot, TopicSlug
>
> @dataclass(frozen=True, kw_only=True, slots=True)
> class DoctorContext:
>     project_root: Path          # repo root containing the spec tree
>     spec_root: SpecRoot         # resolved template.json spec_root (default: Path("SPECIFICATION/"))
>     config: LivespecConfig      # parsed .livespec.jsonc (dataclass; see validate/livespec_config.py)
>     config_load_status: Literal["ok", "absent", "malformed", "schema_invalid"]  # v014 N3 bootstrap-lenience
>     template_root: Path         # resolved template directory (built-in path or custom)
>     template_load_status: Literal["ok", "absent", "malformed", "schema_invalid"]  # v014 N3 bootstrap-lenience
>     run_id: RunId               # uuid4 string bound at wrapper startup
>     git_head_available: bool    # false when not a git repo or no HEAD commit
>
> @dataclass(frozen=True, kw_only=True, slots=True)
> class SeedContext:
>     doctor: DoctorContext
>     seed_input: SeedInput       # parsed seed_input.schema.json payload
>
> @dataclass(frozen=True, kw_only=True, slots=True)
> class ProposeChangeContext:
>     doctor: DoctorContext
>     findings: ProposalFindings  # parsed proposal_findings.schema.json payload
>     topic: TopicSlug
>
> @dataclass(frozen=True, kw_only=True, slots=True)
> class CritiqueContext:
>     doctor: DoctorContext
>     findings: ProposalFindings
>     author: Author
>
> @dataclass(frozen=True, kw_only=True, slots=True)
> class ReviseContext:
>     doctor: DoctorContext
>     revise_input: ReviseInput   # parsed revise_input.schema.json payload
>     steering_intent: str | None
>
> @dataclass(frozen=True, kw_only=True, slots=True)
> class PruneHistoryContext:
>     doctor: DoctorContext
> ```
>
> `LivespecConfig`, `SeedInput`, `ProposalFindings`, and `ReviseInput` are dataclasses paired with the corresponding `*.schema.json` files; each schema carries a `$id` naming the dataclass. Fields MUST be filled at validation time via the factory-shape validators under `livespec/validate/`.
>
> ### CLI argument parsing seam
>
> `argparse` MUST be the sole CLI parser and MUST live in `livespec/io/cli.py`. Rationale: `ArgumentParser.parse_args()` raises `SystemExit` on usage errors and `--help`; the 6-statement wrapper shape leaves no room for it; `check-supervisor-discipline` forbids `SystemExit` outside `bin/*.py`. Routing argparse through the impure boundary keeps the railway intact.
>
> Contract:
>
> - **`livespec/io/cli.py`** MUST expose `@impure_safe`-wrapped functions that construct argparse invocations with `exit_on_error=False` (Python 3.9+), returning `IOResult[Namespace, UsageError | HelpRequested]`. `-h` / `--help` MUST be detected explicitly before `parse_args` runs; on detection, the function MUST return `IOFailure(HelpRequested("<help text>"))` (NOT `UsageError`). The supervisor pattern-matches `HelpRequested` into an exit-0 path (help text to stdout), distinct from `UsageError`'s exit-2 path (bad flag / wrong arg count to stderr). This avoids argparse's implicit `SystemExit(0)` without conflating help requests with usage errors.
> - **`livespec/commands/<cmd>.py`** MUST expose a pure `build_parser() -> ArgumentParser` factory. The factory MUST construct the parser (subparsers, flags, help strings) but MUST NOT parse. Keeping construction pure lets tests introspect the parser shape without effectful invocation.
> - **`livespec.commands.<cmd>.main()`** MUST thread argv through the railway. The supervisor pattern-match derives the exit code from the final `IOResult` payload:
>   - `IOFailure(HelpRequested(text))`: emit `text` to stdout; exit 0.
>   - `IOFailure(err)` where `err` is a `LivespecError` subclass: emit a structured-error JSON line to stderr via structlog; exit `err.exit_code` (`2` for `UsageError`, `3` for `PreconditionError` / `GitUnavailableError`, `4` for `ValidationError`, `126` for `PermissionDeniedError`, `127` for `ToolMissingError`).
>   - `IOSuccess(...)` with any `status: "fail"` finding: exit `3`.
>   - `IOSuccess(...)` otherwise: exit `0`.
>   - Uncaught exception (bug): the supervisor's top-level `try/except Exception` MUST log via structlog with traceback and return `1`.
> - `check-supervisor-discipline` scope: `.claude-plugin/scripts/livespec/**` is in scope; `bin/*.py` (including `_bootstrap.py`) is the sole exempt subtree. `argparse`'s `SystemExit` path is impossible under `exit_on_error=False`; the AST check has no special case for it.
