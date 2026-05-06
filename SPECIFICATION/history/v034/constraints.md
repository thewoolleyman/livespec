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

## Package layout

The plugin's Python surface lives under `.claude-plugin/scripts/`. The canonical directory tree (every subdirectory, every file at the tree root) is maintained in PROPOSAL.md §"Skill layout inside the plugin" and MUST NOT be duplicated here.

The top-level layout has three roots:

- **`bin/`** — executable shebang-wrappers plus the shared `_bootstrap.py`. Each wrapper file MUST be exactly 6 statements matching the canonical wrapper shape (plus an optional single blank line between the imports and `raise SystemExit(main())` per v016 P5). No logic. `chmod +x` MUST be applied.
- **`_vendor/`** — vendored third-party libs, EXEMPT from livespec rules per `## Constraint scope` above.
- **`livespec/`** — the Python package. Every other file under this root MUST follow every rule in `SPECIFICATION/constraints.md`.

Per-subpackage conventions:

- **`commands/<cmd>.py`** — one module per sub-command. MUST export `run()` (railway-emitting; returns `IOResult`) and `main()` (the supervisor that unwraps the final `IOResult` to a process exit code).
- **`doctor/run_static.py`** — the static-phase orchestrator. MUST compose every check module in `doctor/static/` via a single railway chain. The composition primitive (e.g., `Fold.collect`, manual fan-out) is implementer choice under the architecture-level constraints elsewhere in this file.
- **`doctor/static/__init__.py`** — the **static check registry**. MUST import every check module by explicit name and re-export a tuple of `(SLUG, run)` pairs. Adding or removing a check MUST be one explicit edit to the registry; dynamic discovery is forbidden so pyright strict can fully type-check the composition.
- **`doctor/static/<check>.py`** — one module per static check. MUST export a `SLUG` constant and a `run(ctx) -> IOResult[Finding, E]` function where `E` is any `LivespecError` subclass. (See `## ROP composition` and the supervisor discipline sections below for the railway/error contract.)
- **`io/`** — the impure boundary. Every function MUST wrap a side-effecting operation (filesystem, subprocess, git, argparse) with `@impure_safe` from the `returns` library. `io/` also hosts thin typed facades over vendored libs whose surface types are not strict-pyright-clean (e.g., `fastjsonschema`, `structlog`); see `### Vendored-lib type-safety integration` under `## Type safety`.
- **`parse/`** — pure parsers. Every function MUST take a string/bytes/dict and return `Result[T, ParseError]`. Includes the restricted-YAML parser at `parse/front_matter.py`.
- **`validate/`** — pure validators using the **factory shape**. Each validator at `validate/<name>.py` MUST export `validate_<name>(payload: dict, schema: dict) -> Result[<Dataclass>, ValidationError]`, where `<Dataclass>` is the paired dataclass at `schemas/dataclasses/<name>.py`. Callers in `commands/` or `doctor/` read schemas from disk via `io/` wrappers and pass the parsed dict. Validators invoke `livespec.io.fastjsonschema_facade.compile_schema` for the actual compile (the facade owns the compile cache). `validate/` MUST stay strictly pure: no module-level mutable state, no filesystem I/O. Every schema at `schemas/*.schema.json` MUST have a paired validator at `validate/<name>.py` AND a paired dataclass at `schemas/dataclasses/<name>.py`; three-way drift is caught by `check-schema-dataclass-pairing` per v013 M6.
- **`schemas/`** — JSON Schema Draft-7 files plus the `dataclasses/` subdirectory holding the paired hand-authored dataclasses. Filename matches the dataclass: `LivespecConfig` → `livespec_config.schema.json` paired with `schemas/dataclasses/livespec_config.py` AND `validate/livespec_config.py`. `check-schema-dataclass-pairing` enforces three-way drift-freedom (every schema has matching dataclass + validator; every dataclass has matching schema + validator; every validator has matching schema + dataclass).
- **`context.py`** — immutable context dataclasses (`DoctorContext`, `SeedContext`, etc.). The railway payload threaded through every command. See `### Context dataclasses` below for the field sets.
- **`errors.py`** — the `LivespecError` hierarchy with per-subclass `exit_code` class attribute. The hierarchy MUST hold ONLY expected-failure (domain error) classes per the error-handling discipline; bugs MUST NOT be represented as `LivespecError` subclasses (they propagate as raised exceptions to the supervisor's bug-catcher).

### Dataclass authorship

Each JSON Schema under `schemas/*.schema.json` MUST have a paired hand-authored `@dataclass(frozen=True, kw_only=True, slots=True)` at `schemas/dataclasses/<name>.py`. The dataclass and the schema are co-authoritative: the schema is the wire contract (validated at the boundary by `fastjsonschema`); the dataclass is the Python type threaded through the railway (`Result[<Dataclass>, ValidationError]` from each validator per the factory shape). Domain-meaningful field types MUST use the canonical `NewType` aliases from `livespec/types.py`.

- The file name MUST match the `$id`-derived snake_case dataclass name (e.g., `LivespecConfig` → `livespec_config.py`).
- Fields MUST match the schema one-to-one in name and Python type.
- `schemas/__init__.py` MUST re-export every dataclass name for convenient import.
- No codegen toolchain. No generator. Drift between schema, dataclass, and validator MUST be caught mechanically by `check-schema-dataclass-pairing` (three-way AST walker per v013 M6: schema ↔ dataclass ↔ validator).

### Context dataclasses

Every context dataclass MUST be `@dataclass(frozen=True, kw_only=True, slots=True)` and carry exactly the fields below at minimum. Sub-command contexts MUST embed `DoctorContext` rather than inheriting so the type checker can narrow each sub-command's payload independently. Domain-meaningful fields MUST use `NewType` aliases from `livespec/types.py`.

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from livespec.types import Author, RunId, SpecRoot, TopicSlug

@dataclass(frozen=True, kw_only=True, slots=True)
class DoctorContext:
    project_root: Path          # repo root containing the spec tree
    spec_root: SpecRoot         # resolved template.json spec_root (default: Path("SPECIFICATION/"))
    config: LivespecConfig      # parsed .livespec.jsonc (dataclass; see validate/livespec_config.py)
    config_load_status: Literal["ok", "absent", "malformed", "schema_invalid"]  # v014 N3 bootstrap-lenience
    template_root: Path         # resolved template directory (built-in path or custom)
    template_load_status: Literal["ok", "absent", "malformed", "schema_invalid"]  # v014 N3 bootstrap-lenience
    run_id: RunId               # uuid4 string bound at wrapper startup
    git_head_available: bool    # false when not a git repo or no HEAD commit

@dataclass(frozen=True, kw_only=True, slots=True)
class SeedContext:
    doctor: DoctorContext
    seed_input: SeedInput       # parsed seed_input.schema.json payload

@dataclass(frozen=True, kw_only=True, slots=True)
class ProposeChangeContext:
    doctor: DoctorContext
    findings: ProposalFindings  # parsed proposal_findings.schema.json payload
    topic: TopicSlug

@dataclass(frozen=True, kw_only=True, slots=True)
class CritiqueContext:
    doctor: DoctorContext
    findings: ProposalFindings
    author: Author

@dataclass(frozen=True, kw_only=True, slots=True)
class ReviseContext:
    doctor: DoctorContext
    revise_input: ReviseInput   # parsed revise_input.schema.json payload
    steering_intent: str | None

@dataclass(frozen=True, kw_only=True, slots=True)
class PruneHistoryContext:
    doctor: DoctorContext
```

`LivespecConfig`, `SeedInput`, `ProposalFindings`, and `ReviseInput` are dataclasses paired with the corresponding `*.schema.json` files; each schema carries a `$id` naming the dataclass. Fields MUST be filled at validation time via the factory-shape validators under `livespec/validate/`.

### CLI argument parsing seam

`argparse` MUST be the sole CLI parser and MUST live in `livespec/io/cli.py`. Rationale: `ArgumentParser.parse_args()` raises `SystemExit` on usage errors and `--help`; the 6-statement wrapper shape leaves no room for it; `check-supervisor-discipline` forbids `SystemExit` outside `bin/*.py`. Routing argparse through the impure boundary keeps the railway intact.

Contract:

- **`livespec/io/cli.py`** MUST expose `@impure_safe`-wrapped functions that construct argparse invocations with `exit_on_error=False` (Python 3.9+), returning `IOResult[Namespace, UsageError | HelpRequested]`. `-h` / `--help` MUST be detected explicitly before `parse_args` runs; on detection, the function MUST return `IOFailure(HelpRequested("<help text>"))` (NOT `UsageError`). The supervisor pattern-matches `HelpRequested` into an exit-0 path (help text to stdout), distinct from `UsageError`'s exit-2 path (bad flag / wrong arg count to stderr). This avoids argparse's implicit `SystemExit(0)` without conflating help requests with usage errors.
- **`livespec/commands/<cmd>.py`** MUST expose a pure `build_parser() -> ArgumentParser` factory. The factory MUST construct the parser (subparsers, flags, help strings) but MUST NOT parse. Keeping construction pure lets tests introspect the parser shape without effectful invocation.
- **`livespec.commands.<cmd>.main()`** MUST thread argv through the railway. The supervisor pattern-match derives the exit code from the final `IOResult` payload:
  - `IOFailure(HelpRequested(text))`: emit `text` to stdout; exit 0.
  - `IOFailure(err)` where `err` is a `LivespecError` subclass: emit a structured-error JSON line to stderr via structlog; exit `err.exit_code` (`2` for `UsageError`, `3` for `PreconditionError` / `GitUnavailableError`, `4` for `ValidationError`, `126` for `PermissionDeniedError`, `127` for `ToolMissingError`).
  - `IOSuccess(...)` with any `status: "fail"` finding: exit `3`.
  - `IOSuccess(...)` otherwise: exit `0`.
  - Uncaught exception (bug): the supervisor's top-level `try/except Exception` MUST log via structlog with traceback and return `1`.
- `check-supervisor-discipline` scope: `.claude-plugin/scripts/livespec/**` is in scope; `bin/*.py` (including `_bootstrap.py`) is the sole exempt subtree. `argparse`'s `SystemExit` path is impossible under `exit_on_error=False`; the AST check has no special case for it.

## Pure / IO boundary

Purity is enforced **structurally** by directory, not by per-file markers:

- **`livespec/parse/**` and `livespec/validate/**` are PURE.** Modules here MUST NOT import from: `livespec.io.*`, `subprocess`, filesystem APIs (`open`, `pathlib.Path.read_text`, `.read_bytes`, `.write_text`, `.write_bytes`, any `os.*` I/O function), `returns.io.*` (pure code uses `Result`, not `IOResult`), or `socket`/`http.*`/`urllib.*` (no network).
- **`livespec/io/**` is IMPURE.** Every function MUST be decorated with `@impure_safe` from `dry-python/returns`. Functions here are thin wrappers over one side-effecting operation each. `io/` also hosts thin typed facades over vendored libs whose surface types are not strict-pyright-clean.
- **Everything else** (`commands/`, `doctor/**`, `context.py`, `errors.py`) MAY call both pure and impure layers; these are composition layers.

`LivespecError` raise-sites are restricted to `livespec/io/` and `errors.py`. The `dev-tooling/checks/no_raise_outside_io.py` AST check enforces the raise-site discipline mechanically.

Validators MUST stay pure by accepting their schema as a parameter (factory shape). The schema dict is read from disk by an `io/` wrapper and passed in by the caller; `fastjsonschema.compile` is cached in the impure `io/fastjsonschema_facade.py` module-level cache keyed on the schema's `$id`. This separates "reading" (impure) from "checking" (pure).

Enforced by `check-imports-architecture` (Import-Linter contracts over `parse/` and `validate/` imports) and `check-no-raise-outside-io` (AST raise-site check).

### Import-Linter contracts (minimum configuration)

Per v013 M7 (scope narrowed in v017 Q3), the Import-Linter contracts in `pyproject.toml`'s `[tool.importlinter]` section MUST collectively enforce purity and layered architecture. The minimum concrete configuration below is **illustrative** of the canonical shape; contract names, layer names, and ignore-import globs MAY be restructured so long as the two authoritative rules below are enforced. (The v012 L15a third contract covering the raise-discipline import surface was retracted in v017 Q3; raise-site enforcement via `check-no-raise-outside-io` is the sole enforcement point.)

```toml
[tool.importlinter]
root_packages = ["livespec"]

[[tool.importlinter.contracts]]
name = "parse-and-validate-are-pure"
type = "forbidden"
source_modules = ["livespec.parse", "livespec.validate"]
forbidden_modules = [
    "livespec.io",
    "subprocess",
    "returns.io",
    "socket",
    "http",
    "urllib",
    "pathlib",
]

[[tool.importlinter.contracts]]
name = "layered-architecture"
type = "layers"
layers = [
    "livespec.commands | livespec.doctor",
    "livespec.io",
    "livespec.validate",
    "livespec.parse",
]
```

The authoritative rules (enforced by ANY valid Import-Linter configuration satisfying these two statements):

1. Modules in `livespec.parse` and `livespec.validate` MUST NOT import `livespec.io`, `subprocess`, filesystem APIs (`pathlib`, `open`), `returns.io`, `socket`, `http`, or `urllib`.
2. Higher layers MAY import lower layers but MUST NOT vice-versa; the layer stack is `parse` < `validate` < `io` < `commands` | `doctor`. No circular imports follow by construction.

**Raise-discipline is NOT an Import-Linter concern (v017 Q3).** `LivespecError` raise-sites are restricted to `livespec.io.*` and `livespec.errors` (enforced by `check-no-raise-outside-io`). `livespec.errors` MAY be imported from any module that needs to reference `LivespecError` or a subclass in a type annotation, `match` pattern, or attribute access (e.g., `err.exit_code`).

**Implementation overlay (Phase 4 sub-step 26 reconciliation).** Two items from rule 1 — `returns.io` and `pathlib` — are intentionally absent from the realized `pyproject.toml` `forbidden_modules` list per the architecture-vs-mechanism principle. `returns.io` is a subpackage of an external package; Import-Linter v2 rejects subpackage forbids on externals — the `IOResult`/`IOFailure` ban in pure layers is enforced at raise-site by `check-no-raise-outside-io`. `pathlib` is required by `livespec.types` (for `SpecRoot = NewType("SpecRoot", Path)`) and flows transitively into pure layers through wire dataclasses; importing the `Path` class is not I/O — only its method calls are. The no-I/O-at-runtime intent is caught by `check-no-write-direct`, `check-supervisor-discipline`, and `check-no-raise-outside-io`.

## ROP composition

Every public function in `livespec/` MUST compose via ROP using `dry-python/returns` primitives:

- **Pure functions** (in `parse/`, `validate/`) MUST return `Result[T, E]`.
- **Impure functions** (in `io/`) MUST return `IOResult[T, E]`.
- **Composition code** (`commands/`, `doctor/`) threads steps together using `dry-python/returns` composition primitives (`flow`, `bind`, `bind_result`, `bind_ioresult`, `Fold.collect`, `.map`, `.lash`, etc.). The specific primitives chosen for a given chain are **implementer choice** under the architecture-level constraints. Mixed-monad chains (e.g., `IOResult`-returning I/O steps followed by `Result`-returning pure steps) MUST use the appropriate lifting primitive (such as `bind_result` on an `IOResult` chain, or explicit `IOResult.from_result(...)`); pyright strict and `check-public-api-result-typed` are the guardrails that catch mis-composition.

Error-handling routing:

- **Expected failure modes** — user input, environment, infra, timing — MUST flow through the Result track as `LivespecError` subclass payloads (*domain errors*).
- **Unrecoverable bugs** — type mismatches, unreachable-branch assertions, broken invariants, dependency misuse — MUST propagate as raised exceptions, not via the Result track.
- **Third-party code that raises DOMAIN-meaningful exceptions** (`FileNotFoundError`, `PermissionError`, `JSONDecodeError`, etc.) MUST be wrapped at the `io/` boundary using `@safe(exceptions=(ExcType1, ExcType2, ...))` or `@impure_safe(exceptions=(...))` with **explicit enumeration** of the expected exception types. A blanket `@safe` or `@impure_safe` with NO exception enumeration is forbidden — it would swallow bugs as domain failures.
- **Raising `LivespecError` subclasses** is restricted to `io/**` and `errors.py`. Enforced by `check-no-raise-outside-io` (AST). Raising bug-class exceptions (`TypeError`, `NotImplementedError`, `AssertionError`, `RuntimeError` for unreachable branches, etc.) is **permitted anywhere**; the AST check distinguishes the two by subclass relationship to `LivespecError`.
- **Catching exceptions** outside `io/**` is restricted to ONE call site: the outermost supervisor's `try/except Exception` bug-catcher (see `## Supervisor discipline`). `check-no-except-outside-io` enforces.
- **`assert` statements are first-class.** Use them for invariants the implementer believes always hold. An `AssertionError` is a bug; it propagates to the supervisor bug-catcher.
- **`sys.exit` and `raise SystemExit`** MUST appear ONLY in `bin/*.py` files. Enforced by `check-supervisor-discipline`.

Every public function's `return` annotation MUST be `Result[_, _]` or `IOResult[_, _]`, unless the function is a supervisor at a deliberate side-effect boundary (`main() -> int` in `commands/*.py` and `doctor/run_static.py`, or any function returning `None`). The rule exempts only such supervisors. Enforced by `check-public-api-result-typed` (AST).

### ROP pipeline shape

A class decorated with `@rop_pipeline` MUST carry exactly ONE public method (the entry point). Every other method MUST be `_`-prefixed (private). Dunder methods (`__init__`, `__call__`, etc., matching `^__.+__$`) are not counted toward the public-method quota.

The decorator is a runtime no-op (returns the decorated class unchanged) declared in `livespec.types`. AST enforcement lives in `dev-tooling/checks/rop_pipeline_shape.py`. The decorator serves as an AST marker for the static check and as documentation at the def-site.

Each pipeline class encapsulates one cohesive railway chain. Enforcing the shape prevents the public surface from drifting as new chain steps are added — agent-authored code that grows a second public method is caught at check time. Helper classes and helper modules (anything NOT carrying `@rop_pipeline`) are exempt and MAY export multiple public names.

The marker is a decorator rather than a base class because the `check-no-inheritance` allowlist is intentionally small (`{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict}`); adding `RopPipeline` to the allowlist would expand the open-extension-point set for an application pattern.

Enforced by `just check-rop-pipeline-shape`.

## Supervisor discipline

Each command's `main()` function MUST be the only place outside `livespec/io/` where `sys.exit` (or its `raise SystemExit(...)` shape inside `bin/`) MAY appear. The supervisor pattern-matches the final railway `IOResult` onto an exit code via `unsafe_perform_io` plus a `match` statement that ends in `case _: assert_never(unwrapped)` for exhaustiveness. The `dev-tooling/checks/supervisor_discipline.py` AST check enforces this shape.

The shebang-wrapper layer at `bin/<sub-command>.py` MUST conform to the canonical 6-statement shape per PROPOSAL.md §"Wrapper shape": shebang → docstring → `from _bootstrap import bootstrap` → `bootstrap()` → `from livespec.<...> import main` → `raise SystemExit(main())`. The optional blank line between statements 4 and 5 is permitted per v016 P5.

Every supervisor MUST wrap its ROP chain body in one `try/except Exception` bug-catcher whose exclusive job is: (1) log the exception via `structlog` with full traceback and structured context (module, function, `run_id`); (2) return the bug-class exit code (`1`). This is the ONLY catch-all `except Exception` permitted in the codebase. `check-supervisor-discipline` enforces the scope: exactly one catch-all per supervisor; no catch-alls outside supervisors; no catch-alls swallow exceptions without logging and exit-1 return.

## Typechecker constraints (Phase 1 pin)

`pyright` MUST run in strict mode against the `livespec/**` surface. `pyproject.toml`'s `[tool.pyright]` MUST set `typeCheckingMode = "strict"` and exclude `_vendor/**` from strict scope while keeping `useLibraryCodeForTypes = true`. NO `pluginPaths` entry: per v025 D1, pyright has no plugin system (microsoft/pyright#607) and no `returns_pyright_plugin` exists upstream.

`returns` library typechecker integration MUST use plain pyright strict (no plugin); the v018 Q4 returns-pyright-plugin assumption was falsified at v025 D1 — pyright has no plugin system and dry-python/returns explicitly does not support pyright. The seven strict-plus diagnostics below carry the load.

**The following seven strict-plus diagnostics MUST be enabled in `[tool.pyright]`.** Each closes a documented LLM-authored-code failure pattern:

- `reportUnusedCallResult = "error"` — every call to a function whose return type is non-`None` MUST be bound or passed on; the rare legitimate fire-and-forget pattern uses `_ = do_something(ctx)` explicit-discard binding. **This is the load-bearing diagnostic for the ROP discipline:** without it, an LLM can silently discard the entire `Result` / `IOResult` failure track.
- `reportImplicitOverride = "error"` — every method override MUST carry `@override` (imported from `typing_extensions` per the uniform-import discipline). Renaming a base-class method without `@override` silently strands the override.
- `reportUninitializedInstanceVariable = "error"` — every instance attribute MUST be initialized in `__init__` or have a class-level default.
- `reportUnnecessaryTypeIgnoreComment = "error"` — flags `# type: ignore` comments that no longer suppress any diagnostic.
- `reportUnnecessaryCast = "error"` — flags `cast(X, value)` where `value` is already typed `X`.
- `reportUnnecessaryIsInstance = "error"` — flags `isinstance(x, T)` when the type checker already knows `x: T`.
- `reportImplicitStringConcatenation = "error"` — catches `["foo" "bar"]` (missing comma) bugs in lists / sets / tuples.

Every public function (per the `__all__` declaration; see `### Module API surface`) and every dataclass field MUST have type annotations. Private helpers (single-leading-underscore prefix or not in `__all__`) SHOULD be annotated.

Every public function's `return` annotation MUST be `Result[_, _]` or `IOResult[_, _]`, unless the function is a supervisor at a deliberate side-effect boundary (e.g., `main() -> int` in `commands/*.py` and `doctor/run_static.py`, or any function returning `None`), OR the `build_parser() -> ArgumentParser` factory in `commands/**.py`. Enforced by `check-public-api-result-typed` (AST).

**`Any` is forbidden outside `io/` boundary wrappers and vendored-lib facades.** The thin facades under `livespec/io/<lib>_facade.py` are the ONLY place `Any` MAY appear. An AST check rejects `Any` annotations elsewhere.

**`# type: ignore` is forbidden without a narrow justification comment** of the form `# type: ignore[<specific-code>] — <reason>`. Vendored-lib facades MAY use `# type: ignore` for vendored-lib types pyright cannot see; livespec code outside the facades MUST NOT.

Implicit `Optional` via `None` default without `| None` annotation is forbidden (pyright strict flags this). `mypy` is not used; there is no mypy configuration file.

### @override and assert_never import source

Both symbols MUST be imported uniformly from `typing_extensions`, not from stdlib `typing`, regardless of Python version. `typing_extensions` is vendored full upstream verbatim at tag `4.12.2` per v027 D1 at `.claude-plugin/scripts/_vendor/typing_extensions/__init__.py`. The upstream-canonical module name is retained so pyright's `reportImplicitOverride` recognizes the import path and `check-assert-never-exhaustiveness` recognizes the `Never`-narrowing signature. Uniform import discipline (`from typing_extensions import override, assert_never`) eliminates per-version conditionals.

### Module API surface

Every module in `.claude-plugin/scripts/livespec/**` MUST declare a module-top `__all__: list[str]` listing the public API names. Public functions, public classes, and public `NewType` aliases belong in `__all__`; private helpers (single-leading-underscore prefix) MUST NOT appear in `__all__`. `__init__.py` files MAY declare `__all__` for re-export composition; every name listed MUST resolve in the module's namespace, including imported names.

Enforced by AST check `check-all-declared`: walks every module under `.claude-plugin/scripts/livespec/**`; verifies a module-level `__all__: list[str]` assignment exists; verifies every name in `__all__` is actually defined in the module (catches stale entries after a rename).

### Domain primitives via NewType

Domain identifiers in `.claude-plugin/scripts/livespec/**` MUST use a `typing.NewType` alias from the canonical declarations in `livespec/types.py`. `NewType` creates a zero-runtime-cost type alias that pyright treats as distinct from the underlying primitive — passing a `RunId` where a `CheckId` is expected becomes a type error.

Canonical role → NewType mapping (field-name → NewType):

| Field name | NewType | Underlying | Concept |
|---|---|---|---|
| `check_id` | `CheckId` | `str` | doctor-static check slug |
| `run_id` | `RunId` | `str` | per-invocation UUID |
| `topic` | `TopicSlug` | `str` | proposed-change topic |
| `spec_root` | `SpecRoot` | `Path` | resolved spec-root path |
| `schema_id` | `SchemaId` | `str` | JSON Schema `$id` |
| `template` | `TemplateName` | `str` | `.livespec.jsonc` template field |
| `author` / `author_human` / `author_llm` | `Author` | `str` | author identifier |
| `version_tag` | `VersionTag` | `str` | `vNNN` version identifier |

Note: `template_root` in `DoctorContext` is the resolved-directory `Path` and MUST use raw `Path`, NOT `TemplateName`. Dataclass fields and function signatures handling these roles MUST use the `NewType`, not the underlying primitive. Construction uses the `NewType` as a callable: `CheckId("doctor-out-of-band-edits")`.

Enforced by `check-newtype-domain-primitives` (AST): walks `schemas/dataclasses/*.py` and function signatures; verifies field annotations matching the listed roles use the corresponding `NewType`.

### Inheritance and structural typing

Class inheritance in `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**` is RESTRICTED. The AST check `check-no-inheritance` rejects any `class X(Y):` definition where `Y` is not in the **direct-parent allowlist**: `{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict}`. The rule is DIRECT-PARENT only; `LivespecError` subclasses (e.g., `UsageError`, `ValidationError`) are NOT acceptable bases for further subclassing (v013 M5). This enforces the flat-composition direction: `class RateLimitError(UsageError):` is rejected; `class RateLimitError(LivespecError):` is permitted.

Structural interfaces MUST be declared via `typing.Protocol`. `abc.ABC`, `abc.ABCMeta`, and `abc.abstractmethod` imports are banned via the ruff TID rule configuration.

The `@final` decorator (imported from `typing_extensions`) is OPTIONAL; the AST check is the source of truth. Authors MAY use `@final` as documentation-by-decorator for clarity.

### Exhaustiveness

Every `match` statement in `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**` MUST terminate with `case _: assert_never(<subject>)` regardless of subject type. `assert_never` MUST be imported from `typing_extensions`.

When all variants of a closed-union subject are handled by preceding `case` arms, the residual type at the default arm is `Never` and pyright accepts the call. When a new variant is added without updating the dispatch site, the residual type narrows to the unhandled variant and `assert_never` becomes a type error. The conservative scope (every `match`, regardless of subject type) is preferred over a precise scope (only closed-union subjects) because false positives are cheap and the simpler check is more maintainable.

Enforced by AST check `check-assert-never-exhaustiveness`.

### Vendored-lib type-safety integration

- **`fastjsonschema`** exposes generated callables typed as `Callable[[Any], Any]`. The thin facade at `livespec/io/fastjsonschema_facade.py` MUST expose a fully-typed surface: `compile_schema(schema_id: str, schema: dict) -> Callable[[dict], Result[dict, ValidationError]]`. The facade holds a module-level `_COMPILED: dict[str, Callable] = {}` keyed on `$id` to dedupe compiles across calls. `functools.lru_cache` cannot be used directly (dicts are unhashable), and a module-level cache would trip `check-global-writes` in pure code — the cache lives in the impure facade layer and is explicitly exempted.
- **`structlog`** logger calls are dynamically typed. The thin facade at `livespec/io/structlog_facade.py` MUST expose typed logging functions: `info(message: str, **kwargs: object) -> None`, etc.
- **`dry-python/returns`**: `Result` and `IOResult` types are used pervasively. The facade pattern does not apply uniformly; pyright strict plus the seven strict-plus diagnostics (especially `reportUnusedCallResult`) are the guardrails.

## Linter and formatter

`ruff` (astral-sh/ruff) is the sole linter, formatter, import-sorter, and complexity checker. Uv-managed per v024 via `pyproject.toml` `[dependency-groups.dev]`.

`pyproject.toml`'s `[tool.ruff]` MUST configure:

- `target-version = "py310"`.
- `line-length = 100`.
- **Rule selection** (27 categories): `E F I B UP SIM C90 N RUF PL PTH` (11 baseline categories) PLUS `TRY FBT PIE SLF LOG G TID ERA ARG RSE PT FURB SLOT ISC T20 S` (16 v012 additions = 27 total). Key per-category meanings:
  - `TRY` (tryceratops) — exception-handling discipline.
  - `FBT` — boolean-trap; forbids boolean POSITIONAL arguments; reinforces keyword-only discipline.
  - `SLF` — forbids accessing `_`-prefixed attributes from outside the defining class.
  - `LOG` + `G` — logging discipline (no f-strings in log calls; kwargs only).
  - `TID` — tidy imports (no relative imports; banned-module list via `flake8-tidy-imports`).
  - `ERA` — eradicate commented-out code (a frequent LLM artifact).
  - `T20` (flake8-print) — bans `print` and `pprint`.
  - `S` (flake8-bandit) — security anti-patterns: `pickle.loads`, `subprocess` with `shell=True`, `eval`, `exec`, etc.
- `[tool.ruff.lint.pylint]` MUST set `max-args = 6`, `max-positional-args = 6`, `max-branches = 10`, `max-statements = 30`.
- `[tool.ruff.lint.flake8-tidy-imports]` MUST set `ban-relative-imports = "all"` and a banned-imports list including: `abc.ABC`, `abc.ABCMeta`, `abc.abstractmethod` (structural interfaces MUST use `typing.Protocol` instead); `pickle`, `marshal`, `shelve` (arbitrary-code-execution surface on `load()`; livespec uses JSON/JSONC for all serialization).

`just check-lint` runs `ruff check .`. Any finding fails the gate. `just check-format` runs `ruff format --check .`. Any diff fails. Mutating targets for developers: `just fmt` (`ruff format`), `just lint-fix` (`ruff check --fix`).

`# noqa: <CODE> — <reason>` is the only permitted per-line escape. Bare `# noqa` without a code and reason is forbidden; the `check-lint` enforcement inspects the comment shape.

## Complexity thresholds

The following complexity thresholds MUST be satisfied by all first-party `.py` files under `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**`. **Waivers are not permitted.** A function or file that cannot meet a threshold MUST be decomposed; no escape hatch exists.

- **Cyclomatic complexity ≤ 10** per function (ruff `C901`).
- **Function body ≤ 30 logical lines** (ruff `PLR0915`).
- **File ≤ 200 LLOC (SOFT) / ≤ 250 LLOC (HARD).** LLOC excludes blank lines, comment-only lines, and docstrings. Files at 201-250 LLOC pass the per-commit `check-complexity` target with a structured warning emitted to stderr; `just check` stays green but the file is flagged for refactoring. Files above 250 LLOC fail the check (exit 1). The `dev-tooling/checks/file_lloc.py` script enforces both tiers. The `check-no-lloc-soft-warnings` release-gate (NOT in `just check`; fires on release-tag CI only) rejects any file in the 201-250 LLOC soft band before a release tag.
- **Max nesting depth ≤ 4** (ruff PLR rule).
- **Arguments ≤ 6** per function, counted TWO ways, both enforced: total args (ruff `PLR0913`, `max-args = 6`) AND positional args (ruff `PLR0917`, `max-positional-args = 6`). Functions needing more parameters MUST be refactored to accept a dataclass.

Enforced by `just check-complexity`.

## Code coverage

**100% line + branch coverage** is mandatory across the whole Python surface in `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**`. No tier split. `_vendor/` is excluded. `bin/` is included because `_bootstrap.py` carries real logic (version check + sys.path setup) AND the 6-statement wrapper bodies carry the `bootstrap()` call + `raise SystemExit(main())` dispatch — all executable lines covered by dedicated `tests/bin/test_<cmd>.py` files. NO `# pragma: no cover` is applied to wrapper bodies; NO `[tool.coverage.run].omit` for `bin/`.

`pyproject.toml`'s `[tool.coverage.run]` MUST set `branch = true` and `source` to include both the `livespec` package and the `bin/` directory. `[tool.coverage.report]` MUST set `fail_under = 100`, `show_missing = true`, `skip_covered = false`. Enforced by `just check-coverage`.

**No line-level pragma escape hatch.** `# pragma: no cover` comments are forbidden anywhere in covered trees. The ONLY coverage exclusions permitted are the four structural patterns in `[tool.coverage.report].exclude_also`: `if TYPE_CHECKING:`, `raise NotImplementedError`, `@overload`, and `case _:` (the assert_never exhaustiveness arm). These are block-level patterns recognized by coverage.py without per-instance annotation:

- `if TYPE_CHECKING:` guards are matched by the `exclude_also` pattern.
- `sys.version_info` gates in `bin/_bootstrap.py` are covered by dedicated `tests/bin/test_bootstrap.py` tests that monkeypatch `sys.version_info` to exercise both branches.
- `case _: assert_never(<subject>)` arms are structurally unreachable by the spec mandate (every `match` MUST terminate with the pattern; `check-assert-never-exhaustiveness` enforces the body shape). The `case _:` exclude_also pattern catches the entire arm.

A targeted check (`# pragma: no cover` literal match) in `dev-tooling/checks/` rejects any commit that introduces the comment in covered code.

**Wrapper coverage.** Each wrapper has a matching `tests/bin/test_<cmd>.py` that imports the wrapper and catches `SystemExit` via `pytest.raises`, with `monkeypatch` stubbing the target `main` to a no-op returning exit `0`. The import triggers the 6-statement wrapper body under coverage.py's tracer.

## Keyword-only arguments

All user-defined callables in livespec's scope (`.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, `dev-tooling/**`) MUST accept every parameter as keyword-only. Call-site ambiguity over positional order is eliminated by construction.

Rules:

- Every `def` MUST place a lone `*` as its first parameter (or, for methods, immediately after `self` / `cls`) so that every subsequent parameter is in `kwonlyargs`.
- Every `@dataclass` decorator MUST include the full strict-dataclass triple: `frozen=True, kw_only=True, slots=True`. `frozen=True` prevents reassigning attributes after construction. `kw_only=True` makes the generated `__init__` keyword-only. `slots=True` uses `__slots__` storage — attribute-name typos raise `AttributeError` rather than silently creating new attributes.
- Callers MUST pass arguments by keyword wherever the callee permits it.

**Exempt from the `*`-separator rule:**

- Dunder methods whose signatures are fixed by Python (`__eq__(self, other)`, `__hash__(self)`, `__getitem__(self, key)`, `__iter__(self)`, `__next__(self)`, etc.).
- `__init__` of `Exception` subclasses when the only positional argument is the message forwarded to `super().__init__(msg)`.
- `__post_init__(self)` on dataclasses.
- Call-sites into stdlib / third-party / vendored-lib APIs that require positional arguments; the rule binds only livespec-authored definitions.
- **ROP-chain DSL callbacks.** Functions whose name appears as a positional argument to a `dry-python/returns` chain method (`.bind`, `.map`, `.alt`, `.lash`, `.apply`, `.bind_result`, `.bind_ioresult`) are exempt. The library invokes these callbacks positionally with the unwrapped `Success` / `Failure` value; positional-order ambiguity does not arise.
- **Protocol method definitions.** Methods declared inside a class whose direct-parent base is `Protocol` are exempt; a `Protocol` class is a structural type-system surface documenting the shape of an external API.

Enforced by `just check-keyword-only-args` (AST).

## Structural pattern matching

`match` statements destructuring livespec-authored classes MUST use keyword patterns, not positional patterns. Concrete form: `case Foo(x=x, y=y)` (keyword) rather than `case Foo(x, y)` (positional). This eliminates the need for `__match_args__` on any livespec class — the class pattern binds attributes by name directly from the instance.

Rules:

- Livespec-authored classes (anything under `.claude-plugin/scripts/livespec/**`, `dev-tooling/**`, or `.claude-plugin/scripts/bin/**`) MUST NOT declare `__match_args__` at class scope.
- Class patterns in `match` statements whose class resolves to a livespec-authored class MUST use keyword sub-patterns.
- Class patterns resolving to third-party types (e.g., `dry-python/returns`'s `IOFailure`, `IOSuccess`, `Result.Success`, `Result.Failure`) MAY use positional destructure, because those libraries define `__match_args__` idiomatically for sum-type wrappers.

Enforced by `just check-match-keyword-only` (AST).

**HelpRequested example.** Under the keyword-only rules, the supervisor's three-way match dispatch reads:

```python
from typing_extensions import assert_never

match result:
    case IOFailure(HelpRequested(text=text)):
        sys.stdout.write(text)
        return 0
    case IOFailure(err):
        log.error("livespec failed", error=err)
        return err.exit_code
    case IOSuccess(report):
        return 0
    case _:
        assert_never(result)
```

The outer `IOFailure(...)` uses positional destructure (permitted — `IOFailure` is from `dry-python/returns`). The inner `HelpRequested(text=text)` uses keyword destructure. `HelpRequested` declares no `__match_args__`. The trailing `case _: assert_never(result)` is mandatory per `## ROP composition — Exhaustiveness`.

## Exit code contract

Scripts bundled with the skill MUST use the following exit codes:

| Code | Meaning |
|---|---|
| `0` | Success. Also covers intentional `--help` output: a `-h` / `--help` request exits with `0` via the `HelpRequested` supervisor pattern-match path. |
| `1` | Script-internal failure (unexpected runtime error; likely a bug). |
| `2` | Usage error: bad flag, wrong argument count, malformed invocation. |
| `3` | Input or precondition failed: referenced file/path/value missing, malformed, or in an incompatible state. |
| `4` | Schema validation failed (retryable): LLM-provided JSON payload does not conform to the wrapper's input schema. |
| `126` | Permission denied: a required file exists but is not executable/readable/writable. |
| `127` | Required external tool not on PATH, or Python version too old. |

`livespec/errors.py` MUST define the hierarchy. It MUST hold ONLY expected-failure (domain error) classes; bugs MUST NOT be represented as `LivespecError` subclasses:

```python
from typing import ClassVar

class LivespecError(Exception):
    exit_code: ClassVar[int] = 1

class UsageError(LivespecError):
    exit_code: ClassVar[int] = 2

class PreconditionError(LivespecError):
    exit_code: ClassVar[int] = 3

class ValidationError(LivespecError):
    exit_code: ClassVar[int] = 4

class GitUnavailableError(LivespecError):
    exit_code: ClassVar[int] = 3

class PermissionDeniedError(LivespecError):
    exit_code: ClassVar[int] = 126

class ToolMissingError(LivespecError):
    exit_code: ClassVar[int] = 127


class HelpRequested(Exception):
    exit_code: ClassVar[int] = 0

    def __init__(self, *, text: str) -> None:
        super().__init__(text)
        self.text = text
```

`HelpRequested` is NOT a `LivespecError` — it is an informational early-exit category (user asked for help; not a domain error). The supervisor pattern-matches `HelpRequested` via keyword destructure and returns exit 0 after emitting the help text to stdout.

`sys.exit(err.exit_code)` MUST appear ONLY in `bin/*.py` shebang wrappers and `bin/_bootstrap.py`. Everywhere else stays on the railway.

### Doctor static-phase exit-code derivation

The `livespec.doctor.run_static.main()` supervisor derives exit code from the final `IOResult`:

- `IOFailure(err)` where `err` is a `LivespecError` subclass: emit a structured-error JSON line on stderr via structlog, then exit `err.exit_code`.
- `IOSuccess(report)`: emit `{"findings": [...]}` to stdout, then exit `3` if any finding has `status: "fail"`, else exit `0`. `status: "skipped"` does NOT trigger a fail exit.
- Uncaught exception (bug): the supervisor's `try/except Exception` logs via structlog with traceback and returns `1`.

Enforced by `check-supervisor-discipline` (AST).

## Structured logging

Logging uses vendored **`structlog`**. Configuration:

- **JSON output to stderr only.** No console renderer, no format switch.
- **Standard fields every line carries:** `timestamp` (RFC 3339), `level`, `logger` (module name), `message` (human-readable text), `run_id` (UUID bound at executable startup via `structlog.contextvars.bind_contextvars`), plus arbitrary kwargs.
- **Level control:** `LIVESPEC_LOG_LEVEL` env var + `-v` / `-vv` CLI flag (CLI wins over env). Default level `WARNING`.
- **Style rules:** kwargs only — `log.error("parse failed", path=str(p), error=repr(exc))`. Never f-strings in log messages; the message MUST be a stable literal. Errors MUST include the `LivespecError` subclass name and structured context dict.
- **stdout is reserved** for documented contracts (doctor static-phase findings JSON; `HelpRequested` text path). Mechanical enforcement: ruff `T20` bans `print` and `pprint`; AST check `check-no-write-direct` bans `sys.stdout.write` and `sys.stderr.write` everywhere EXCEPT three designated surfaces: (1) `bin/_bootstrap.py` — pre-livespec-import version-check error message; (2) supervisor `main()` functions in `livespec/commands/**.py` — `sys.stdout.write` permitted for documented stdout contracts; (3) `livespec/doctor/run_static.py::main()` — writes `{"findings": [...]}` JSON to stdout.

**Bootstrap.** `livespec/__init__.py` MUST call `structlog.configure(...)` exactly once and bind `run_id` (UUID) via `structlog.contextvars.bind_contextvars(run_id=str(uuid.uuid4()))` in the same block, on first import. The following calls are **exempt** from `check-global-writes`: `structlog.configure(...)` in `livespec/__init__.py`; `structlog.contextvars.bind_contextvars(run_id=...)` in `livespec/__init__.py`; the module-level `_COMPILED: dict[str, Callable]` cache in `livespec/io/fastjsonschema_facade.py`.

The `log` logger is obtained via `structlog.get_logger(__name__)` in each module that logs, routed through `livespec/io/structlog_facade.py`.


## File naming and invocation

- Python module and script filenames MUST use snake_case + `.py`, including `bin/*.py` shebang wrappers and `bin/_bootstrap.py`.
- Hyphens appear only in JSON wire contracts (`check_id` values like `"doctor-out-of-band-edits"`) and in PROPOSAL.md prose (`propose-change` sub-command name).
- The slug↔module-name mapping for doctor-static checks is recorded literally in `.claude-plugin/scripts/livespec/doctor/static/__init__.py`'s static registry.
- Executables (`bin/*.py`) MUST carry the shebang `#!/usr/bin/env python3`, the executable bit, and conform to the 6-statement wrapper shape.

### Shebang-wrapper contract

Each file under `bin/*.py` (except `_bootstrap.py`) MUST consist of exactly 6 statements plus an optional single blank line between the import block and the `raise SystemExit(main())` statement:

```python
#!/usr/bin/env python3
"""Shebang wrapper for <sub-command>. No logic; see livespec.<module>."""
from _bootstrap import bootstrap
bootstrap()
from livespec.<module>.<submodule> import main

raise SystemExit(main())
```

Shape conformance is enforced by `check-wrapper-shape` (AST-lite) and `tests/bin/test_wrappers.py`. The optional blank line does NOT count as a statement; `check-wrapper-shape` explicitly permits its presence (v016 P5).

### bin/_bootstrap.py contract

The shared bootstrap module MUST live under `bin/` so its `raise SystemExit(127)` is allowed by `check-supervisor-discipline`. Body shape:

```python
"""Pre-livespec-import bootstrap: sys.path setup + Python version check."""
import sys
from pathlib import Path


def bootstrap() -> None:
    if sys.version_info < (3, 10):
        sys.stderr.write("livespec requires Python 3.10+; install via your package manager.\n")
        raise SystemExit(127)
    bundle_scripts = Path(__file__).resolve().parent.parent
    bundle_vendor = bundle_scripts / "_vendor"
    for path in (bundle_scripts, bundle_vendor):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
```


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
