# Python skill script style requirements

This section constrains how Python scripts bundled with a Claude Code
skill governed by this specification are authored, tested, and enforced.
It applies to every Python module under the shipped skill bundle
(`.claude-plugin/scripts/`) and to every Python module under the
dev-tooling tree at `<repo-root>/dev-tooling/`. It does not
apply to scripts written in other languages; livespec v008 ships no
scripts in any language other than Python.

Scripts governed by this section are invoked by Claude as tools via the
bash tool. They execute **non-interactively**: no TTY, no user prompts,
stdin is not a terminal. Interactive-shell affordances are forbidden.

The normative source of truth for Python practice in this document is
the [Python language reference](https://docs.python.org/3/reference/),
PEP 8 (style), PEP 484 / PEP 604 / PEP 695 (typing), and the tooling
conventions baked in by `ruff` (astral-sh/ruff) and `pyright`
(microsoft/pyright). Where a rule below cites a specific PEP or tool,
that citation is authoritative; where a rule below is silent on a
question the tooling covers, the tooling default applies.

This document extends — and defers to — `livespec-nlspec-spec.md`
§"Architecture-Level Constraints (Implementation Discipline)" and its
"Error Handling Discipline" subsection. Rules below are architecture-
level (language deps, code-quality tooling, type-level public-API
guarantees, structural boundaries enforced by checks, externally-
visible invariants, inspected directory layouts). Internal composition
details (specific ROP primitives used, exact return annotations of
private helpers, illustrative code held as normative) are OUT of scope
— the enforcement suite carries the guardrail work. An implementation
that passes the behavioral contracts in `PROPOSAL.md`, the
type/purity/import/coverage checks, and the AST-enforcement suite
satisfies this document regardless of the exact internal mechanism
chosen.

This section uses BCP 14 / RFC 2119 / RFC 8174 keywords (`MUST`,
`MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`, `SHOULD NOT`, `MAY`,
`OPTIONAL`) for normative requirements.

---

## Scope

- Every Python module bundled with the skill under
  `.claude-plugin/scripts/livespec/**`.
- Every Python shebang-wrapper executable under
  `.claude-plugin/scripts/bin/*.py`, including the shared
  `_bootstrap.py` module.
- Every Python module or script under `<repo-root>/dev-tooling/**`.
- **Exempt:** vendored third-party code under
  `.claude-plugin/scripts/_vendor/**` — vendored libs ship at pinned
  upstream versions and are not subjected to livespec's own style
  rules. See "Vendored third-party libraries" below.

Tests under `<repo-root>/tests/` MUST comply unless a test explicitly
exercises a non-conforming input, in which case the non-conformance MUST
be declared in a docstring at the top of the fixture.

---

## Non-interactive execution

- Scripts MUST NOT read from a terminal. `input()`, `getpass.getpass()`,
  and any prompt-and-wait construct are forbidden.
- Scripts MUST NOT manipulate terminal modes or open `/dev/tty`.
- Scripts MUST NOT rely on `sys.stdout.isatty()` or `os.isatty(...)` to
  gate **interactive** behavior. They MAY use these checks to select
  between stdin-piped and stdin-file-redirect handling, provided neither
  branch prompts the user.
- A script that needs a human-confirmation step MUST fail with an
  actionable message and exit code `3` (precondition failed), leaving
  the decision to the caller.
- All configuration and input MUST arrive through one of: positional
  arguments, flags via `argparse`, environment variables, files named
  by the above, or stdin pipe when documented.

---

## Interpreter and Python version

- Every Python file MUST target **Python 3.10 or newer**. Python 3.10's
  `X | Y` union syntax, `match` statements, `ParamSpec`, `TypeAlias`,
  and improved typing syntax are expected idioms.
- Bundled executables MUST use the shebang `#!/usr/bin/env python3`.
  No other interpreter path is valid.
- The shared `bin/_bootstrap.py:bootstrap()` function asserts
  `sys.version_info >= (3, 10)` and exits `127` with an actionable
  install instruction if older. `bin/_bootstrap.py` is the canonical
  location for the version check; `scripts/livespec/__init__.py` does
  NOT raise (it cannot — see "Railway-Oriented Programming" below).
- The `.mise.toml` at the repo root pins the developer and CI Python
  version to an exact 3.10+ release; developers use `mise install` to
  match.
- Features from Python 3.11+ (e.g., `Self`, `tomllib`, `ExceptionGroup`)
  MUST NOT be used.

---

## Runtime dependencies

### End-user install

- **`python3` >= 3.10** is the sole runtime dependency the skill imposes
  on end-user machines. Preinstalled on Debian ≥ 12, Ubuntu ≥ 22.04,
  Fedora, Arch, RHEL ≥ 9; one-command install on macOS via Homebrew or
  Xcode CLT.
- No other runtime deps. No PyPI install step required of end users.
- `jq` is NOT a runtime dep (contrast v005); stdlib `json` covers every
  use.
- No bash is invoked anywhere in the bundle.

### Vendored third-party libraries

The bundle ships a curated set of pure-Python third-party libraries
under `.claude-plugin/scripts/_vendor/<lib>/`. All vendored libs MUST be:

- Pure Python (no compiled wheels; no C / Rust extensions).
- Permissively licensed (MIT, BSD-2-Clause, BSD-3-Clause, or
  Apache-2.0).
- Actively maintained by a reputable upstream.
- Zero-transitive-dep or all-transitive-deps-also-vendored.

Locked vendored libs for v008 (each pinned to an exact upstream ref
recorded in `<repo-root>/.vendor.jsonc`):

- **`returns`** (dry-python/returns, BSD-2) — ROP primitives: `Result`,
  `IOResult`, `@safe`, `@impure_safe`, `flow`, `bind`, `Fold.collect`,
  `lash`. Whether to vendor returns' pyright plugin is a deferred
  decision tracked in `deferred-items.md` (`returns-pyright-plugin-
  disposition`).
- **`fastjsonschema`** (horejsek/python-fastjsonschema, MIT) — JSON
  Schema Draft-7 validator.
- **`structlog`** (hynek/structlog, BSD-2 / MIT dual) — structured JSON
  logging.
- **`jsoncomment`** (MIT) — JSONC (JSON-with-comments) parser. A
  comment-stripping pre-pass over stdlib `json.loads`; used by
  `livespec/parse/jsonc.py` for `.livespec.jsonc` parsing and any
  other JSONC input.

Each vendored lib's `LICENSE` file MUST be preserved at
`_vendor/<lib>/LICENSE`. A `NOTICES.md` at the repo root MUST list every
vendored lib with its license and copyright.

The shared `bin/_bootstrap.py:bootstrap()` function inserts BOTH the
bundle's `scripts/` directory AND the bundle's `scripts/_vendor/`
directory into `sys.path`. Adding `scripts/` makes the `livespec`
package resolvable (`from livespec.commands.seed import main`).
Adding `scripts/_vendor/` makes each vendored top-level package
resolvable under its natural name (`from returns.io import IOResult`,
`from fastjsonschema import compile`, `import structlog`,
`import jsoncomment`). Adding only `scripts/` is insufficient —
vendored libraries live one level deeper under `_vendor/` and Python
would not find them on `import`.

### Vendoring discipline

- **Never edit `_vendor/` files directly.** Any edit is treated as
  drift; code review and git diff visibility are the catching
  mechanisms.
- **Re-vendoring goes through `just vendor-update <lib>`** — the only
  blessed mutation path. The recipe fetches the upstream ref, copies
  it under `_vendor/<lib>/`, preserves `LICENSE`, and updates
  `.vendor.jsonc`'s recorded ref.
- **`.vendor.jsonc`** records `{upstream_url, upstream_ref, vendored_at}`
  per lib. No hashes; no automated drift-detection check (`check-
  vendor-audit` was removed in v007 as over-engineered for the threat
  model).
- `_vendor/` is **excluded** from livespec's own style rules, type
  checking strictness, coverage measurement, and CLAUDE.md coverage
  enforcement.

---

## Package layout

See **PROPOSAL.md §"Skill layout inside the plugin"** for the
canonical directory tree (`.claude-plugin/scripts/bin/`,
`.claude-plugin/scripts/_vendor/`, `.claude-plugin/scripts/livespec/`
and every subpackage within it). This document does not duplicate
the tree — the layout is maintained in exactly one place.

- **`bin/`** — executable shebang-wrappers + the shared `_bootstrap.py`.
  Each wrapper file is exactly 6 lines matching the shape below. No
  logic. `chmod +x` applied.
- **`_vendor/`** — vendored third-party libs, exempt from livespec
  rules.
- **`livespec/`** — the Python package. Every other file here follows
  the rules in this document.

Per sub-package conventions:

- **`commands/<cmd>.py`** — one module per sub-command. Exports `run()`
  (ROP-returning) and `main()` (supervisor that unwraps to exit code).
- **`doctor/run_static.py`** — static-phase orchestrator. Composes all
  check modules via a single ROP chain. The specific composition
  primitive is implementer choice under the architecture-level
  constraints (see `livespec-nlspec-spec.md` §"Architecture-Level
  Constraints" and §"Railway-Oriented Programming" below).
- **`doctor/static/__init__.py`** — **static registry.** Imports every
  check module by name and re-exports a tuple of `(SLUG, run)` pairs.
  Adding or removing a check is one explicit edit to the registry.
  No dynamic discovery. Pyright strict can fully type-check the
  composition through this registry.
- **`doctor/static/<check>.py`** — one module per static check. Exports
  `SLUG` constant and `run(ctx) -> IOResult[Finding, E]` where `E` is
  any `LivespecError` subclass (see §"Exit code contract" for the
  retirement of the v008-era `DoctorInternalError` and the domain-
  error-only discipline that replaces it).
- **`io/`** — impure boundary. Every function wraps a side-effecting
  operation (filesystem, subprocess, git) with `@impure_safe`. Also
  hosts thin typed facades over vendored libs whose surface types are
  not strict-pyright-clean (`fastjsonschema`, `structlog`); see "Type
  safety" below.
- **`parse/`** — pure parsers. Every function takes a string/bytes/dict
  and returns `Result[T, ParseError]`. Includes the restricted-YAML
  parser at `parse/front_matter.py`.
- **`validate/`** — pure validators using the **factory shape**: each
  validator takes `(payload: dict, schema: dict)` and returns
  `Result[T, ValidationError]`. Callers in `commands/` or `doctor/`
  read schemas from disk via `io/` wrappers and pass the parsed dict.
  Validators invoke `livespec.io.fastjsonschema_facade.compile_schema`
  for the actual compile; the facade owns the compile cache (see
  "Vendored-lib type-safety integration" below). `validate/` stays
  strictly pure (no module-level mutable state, no filesystem I/O).
- **`schemas/`** — JSON Schema Draft-7 files plus the
  `dataclasses/` subdirectory that holds the paired hand-authored
  dataclasses. Filename matches the dataclass: `LivespecConfig` →
  `livespec_config.schema.json` paired with
  `schemas/dataclasses/livespec_config.py`. `check-schema-dataclass-
  pairing` enforces drift-free pairing in both directions (every
  schema has a matching dataclass; every dataclass has a matching
  schema). See "Dataclass authorship" below.
- **`context.py`** — immutable context dataclasses (`DoctorContext`,
  `SeedContext`, etc.) — the railway payload. See "Context
  dataclasses" below for field sets.
- **`errors.py`** — `LivespecError` hierarchy with per-subclass
  `exit_code` class attribute. The hierarchy holds ONLY expected-
  failure (domain error) classes per the Error Handling Discipline
  below; bugs are NOT represented as `LivespecError` subclasses.

### Dataclass authorship

Each JSON Schema under `schemas/*.schema.json` has a paired
hand-authored `@dataclass(frozen=True)` at
`schemas/dataclasses/<name>.py`. The dataclass and the schema are
co-authoritative: the schema is the wire contract (validated at
boundary by `fastjsonschema`); the dataclass is the Python type
threaded through the railway (`Result[<Dataclass>,
ValidationError]` from each validator per the factory shape).

- The file name matches the `$id`-derived snake_case dataclass
  name (`LivespecConfig` → `livespec_config.py`).
- Fields MUST match the schema one-to-one in name and Python type.
- `schemas/__init__.py` re-exports every dataclass name for
  convenient import.
- No codegen toolchain. No generator. Drift between schema and
  dataclass is caught mechanically by
  `check-schema-dataclass-pairing` (AST walker over both sides).

### Context dataclasses

Every context dataclass MUST be `@dataclass(frozen=True)` and carry
exactly the fields below at minimum. Sub-command contexts embed
`DoctorContext` rather than inheriting so the type checker can
narrow each sub-command's payload independently.

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DoctorContext:
    project_root: Path          # repo root containing the spec tree
    spec_root: Path             # resolved template.json spec_root, repo-relative (default: Path("SPECIFICATION/"))
    config: LivespecConfig      # parsed .livespec.jsonc (dataclass; see validate/livespec_config.py)
    template_root: Path         # resolved template directory (built-in path or custom)
    run_id: str                 # uuid4 string bound at wrapper startup
    git_head_available: bool    # false when not a git repo or no HEAD commit

@dataclass(frozen=True)
class SeedContext:
    doctor: DoctorContext
    seed_input: SeedInput       # parsed seed_input.schema.json payload

@dataclass(frozen=True)
class ProposeChangeContext:
    doctor: DoctorContext
    findings: ProposalFindings  # parsed proposal_findings.schema.json payload
    topic: str

@dataclass(frozen=True)
class CritiqueContext:
    doctor: DoctorContext
    findings: ProposalFindings
    author: str

@dataclass(frozen=True)
class ReviseContext:
    doctor: DoctorContext
    revise_input: ReviseInput   # parsed revise_input.schema.json payload
    steering_intent: str | None

@dataclass(frozen=True)
class PruneHistoryContext:
    doctor: DoctorContext
```

`LivespecConfig`, `SeedInput`, `ProposalFindings`, and `ReviseInput`
are dataclasses generated from the corresponding `*.schema.json`
files; each schema carries a `$id` naming the dataclass. Fields are
filled at validation time (via the factory-shape validators under
`livespec/validate/`).

### CLI argument parsing seam

argparse is the sole CLI parser and lives in `livespec/io/cli.py`.
Rationale: `ArgumentParser.parse_args()` raises `SystemExit` on
usage errors and `--help`; the 6-line wrapper shape leaves no room
for it; `check-supervisor-discipline` forbids `SystemExit` outside
`bin/*.py`. Routing argparse through the impure boundary keeps the
railway intact.

Contract:

- **`livespec/io/cli.py`** exposes `@impure_safe`-wrapped functions
  that construct argparse invocations with `exit_on_error=False`
  (Python 3.9+), returning `IOResult[Namespace, UsageError |
  HelpRequested]`. `-h`/`--help` is detected explicitly before
  `parse_args` runs; on detection, the function returns
  `IOFailure(HelpRequested("<help text>"))` (NOT `UsageError`).
  The supervisor pattern-matches `HelpRequested` into an exit-0
  path (help text to stdout), distinct from `UsageError`'s exit-2
  path (bad flag / wrong arg count to stderr). Avoids argparse's
  implicit `SystemExit(0)` without conflating help requests with
  usage errors.
- **`livespec/commands/<cmd>.py`** exposes a pure
  `build_parser() -> ArgumentParser` factory. This factory
  constructs the parser (subparsers, flags, help strings) but does
  NOT parse. Keeping construction pure lets tests introspect the
  parser shape without effectful invocation.
- `livespec.commands.<cmd>.main()` threads argv through the
  railway:
  Supervisor pattern-match derives the exit code from the final
  `IOResult` payload:
  - `IOFailure(HelpRequested(text))`: emit `text` to stdout; exit 0.
  - `IOFailure(err)` where `err` is a `LivespecError` subclass:
    emit structured-error JSON line to stderr via structlog; exit
    `err.exit_code` (which is `2` for `UsageError`, `3` for
    `PreconditionError` / `GitUnavailableError`, `4` for
    `ValidationError`, `126` for `PermissionDeniedError`, `127`
    for `ToolMissingError`).
  - `IOSuccess(...)` with any `status: "fail"` finding: exit `3`.
  - `IOSuccess(...)` otherwise: exit `0`.
  - Uncaught exception (bug): supervisor's top-level
    `try/except Exception` logs via structlog with traceback and
    returns `1`.
- `check-supervisor-discipline` scope: `livespec/**` is in scope;
  `bin/*.py` (including `_bootstrap.py`) is the sole exempt
  subtree. `argparse`'s `SystemExit` path is impossible under
  `exit_on_error=False`; the AST check has no special case for it.

---

## Railway-Oriented Programming (ROP)

Every public function in `livespec/` MUST compose via ROP using
`dry-python/returns` primitives:

- **Pure functions** (in `parse/`, `validate/`) return `Result[T, E]`.
- **Impure functions** (in `io/`) return `IOResult[T, E]`.
- **Composition code** (`commands/`, `doctor/`) threads steps
  together using the library's composition primitives
  (`flow`, `bind`, `bind_result`, `bind_ioresult`, `Fold.collect`,
  `.map`, `.lash`, etc.). The specific primitives chosen to compose
  a given chain are **implementer choice** under the architecture-
  level constraints. Mixed-monad chains (e.g., `IOResult`-returning
  I/O steps followed by `Result`-returning pure steps) MUST use the
  appropriate lifting primitive from `dry-python/returns` (such as
  `bind_result` on an `IOResult` chain, or explicit
  `IOResult.from_result(...)`); pyright strict and
  `check-public-api-result-typed` are the guardrails that catch
  mis-composition.

Error-handling routing (see `livespec-nlspec-spec.md`
§"Architecture-Level Constraints — Error Handling Discipline" for
the underlying principle):

- **Expected failure modes** — user input, environment, infra,
  timing — flow through the Result track as `LivespecError`
  subclass payloads. They are *domain errors*.
- **Unrecoverable bugs** — type mismatches, unreachable-branch
  assertions, broken invariants, dependency misuse — propagate
  as raised exceptions. They are NOT on the Result track.
- **Third-party code that raises DOMAIN-meaningful exceptions**
  (`FileNotFoundError`, `PermissionError`, `JSONDecodeError`,
  etc.) is wrapped at the `io/` boundary using
  `@safe(exceptions=(ExcType1, ExcType2, ...))` or
  `@impure_safe(exceptions=(...))` with **explicit enumeration
  of the expected exception types**. A blanket `@safe` or
  `@impure_safe` with NO exception enumeration is forbidden —
  it would swallow bugs as if they were domain failures.
- **Raising `LivespecError` subclasses** (domain errors) is
  restricted to `io/**` and `errors.py`. Enforced by
  `check-no-raise-outside-io` (AST). Raising bug-class
  exceptions (`TypeError`, `NotImplementedError`,
  `AssertionError`, `RuntimeError` for unreachable branches,
  etc.) is **permitted anywhere**; the AST check distinguishes
  the two by subclass relationship to `LivespecError`.
- **Catching exceptions** outside `io/**` is restricted to ONE
  call site: the outermost supervisor's top-level
  `try/except Exception` bug-catcher (see "Supervisor
  discipline" below). `check-no-except-outside-io` enforces.
- **`assert` statements are first-class.** Use them for
  invariants the implementer believes always hold. An
  `AssertionError` is a bug; it propagates to the supervisor
  bug-catcher.
- **`sys.exit` and `raise SystemExit`** appear ONLY in `bin/*.py`
  files (including `bin/_bootstrap.py`). Not in any `livespec/**`
  module. Enforced by `check-supervisor-discipline`.

Every public function's `return` annotation MUST be `Result[_, _]` or
`IOResult[_, _]`, unless the function is a supervisor at a
deliberate side-effect boundary (e.g., `main() -> int` in
`commands/*.py` and `doctor/run_static.py`, or any function
returning `None`). The rule exempts only such supervisors. Enforced
by `check-public-api-result-typed` (AST); the exemption scope is
documented in the `static-check-semantics` deferred item.

### Supervisor discipline (bug-catcher)

Every supervisor (the outermost entry-point function that owns
exit-code emission — `main()` in every `commands/<cmd>.py` and in
`doctor/run_static.py`) MUST wrap its ROP chain body in one
`try/except Exception` bug-catcher whose exclusive job is:

1. Log the exception via structlog with full traceback and
   structured context (module, function, `run_id`).
2. Return the bug-class exit code (`1`).

This is the ONLY catch-all `except Exception` permitted in the
codebase. `check-supervisor-discipline` enforces the scope:
exactly one catch-all per supervisor; no catch-alls outside
supervisors; no catch-alls swallow exceptions without logging and
exit-1 return.

The behavioral contract of the deterministic lifecycle (pre-step
doctor static + sub-command logic + post-step doctor static) is
described in `PROPOSAL.md` §"Sub-command lifecycle orchestration."
The specific Python composition used to express that lifecycle is
implementer choice under the above constraints.

---

## Sub-command lifecycle composition

The wrapper (in `livespec.commands.<cmd>.main()`) owns the
deterministic lifecycle: pre-step doctor static + sub-command logic
+ post-step doctor static. Fail-fast on any `status: "fail"`
finding from pre-step or post-step per the behavioral contract in
PROPOSAL.md §"Sub-command lifecycle orchestration." The post-step
LLM-driven phase, where applicable, runs from skill prose **after**
the wrapper exits (Python doesn't invoke the LLM).

Applicability and flags:

- **`seed` is exempt from pre-step doctor static** (see
  PROPOSAL.md). Seed's wrapper runs sub-command logic +
  post-step only.
- **`help` and `doctor`** have no pre-step and no post-step
  wrapper-side static.
- **`prune-history`** has pre-step and post-step static but no
  post-step LLM-driven phase.
- **`propose-change`, `critique`, `revise`** have both pre-step
  and post-step static.
- **`--skip-pre-check` and `--run-pre-check`** are a mutually-
  exclusive wrapper-parsed flag pair for sub-commands that have a
  pre-step (propose-change, critique, revise, prune-history):
  - `--skip-pre-check` → skip pre-step (skip = true).
  - `--run-pre-check` → run pre-step (skip = false), overriding
    `.livespec.jsonc`'s `pre_step_skip_static_checks: true` for
    the current invocation.
  - Neither flag → use config's `pre_step_skip_static_checks`
    value.
  - Both flags → argparse usage error (exit 2 via
    `IOFailure(UsageError)`).

  `bin/doctor_static.py` rejects BOTH flags (exit 2 via
  `IOFailure(UsageError)`); it IS the static phase and has no
  pre/post wrap.
- The two LLM-driven flag pairs
  (`--skip-doctor-llm-objective-checks` /
  `--run-doctor-llm-objective-checks` and
  `--skip-doctor-llm-subjective-checks` /
  `--run-doctor-llm-subjective-checks`) are LLM-layer only —
  they gate the two post-step LLM-driven phases (both skill prose)
  and never reach Python wrappers.

Python composition mechanism for the lifecycle chain is implementer
choice under the architecture-level constraints (see §"Railway-
Oriented Programming" above; see `livespec-nlspec-spec.md`
§"Architecture-Level Constraints" for the underlying principle
permitting mechanism freedom where enforcement checks already
constrain the outcome).

---

## Purity and I/O isolation

Purity is enforced **structurally** by directory, not by per-file
markers:

- **`livespec/parse/**` and `livespec/validate/**` are PURE.** Modules
  here MUST NOT import from:
  - `livespec.io.*`
  - `subprocess`
  - Filesystem APIs (`open`, `pathlib.Path.read_text`, `.read_bytes`,
    `.write_text`, `.write_bytes`, any `os.*` I/O function).
  - `returns.io.*` (pure code uses `Result`, not `IOResult`).
  - `socket`, `http.*`, `urllib.*` (no network).
- **`livespec/io/**` is IMPURE.** Every function there MUST be decorated
  with `@impure_safe` from dry-python/returns. Functions here are
  thin wrappers over one side-effecting operation each. `io/` also
  hosts thin typed facades over vendored libs whose surface types are
  not strict-pyright-clean.
- **Everything else** (`commands/`, `doctor/**`, `context.py`,
  `errors.py`) may call both pure and impure layers; these are
  composition layers.

**Validators stay pure** by accepting their schema as a parameter
(factory shape). The schema dict is read from disk by an `io/` wrapper
and passed in by the caller. `fastjsonschema.compile` is cached via
`functools.lru_cache` keyed on the schema's `$id`. This separates
"reading" (impure) from "checking" (pure).

Enforced by `check-purity` (AST walker over `parse/` and `validate/`
imports).

---

## Type safety

- **pyright strict mode** is mandatory. `pyproject.toml`'s
  `[tool.pyright]` sets `typeCheckingMode = "strict"` and excludes
  `_vendor/**` from strict scope while keeping
  `useLibraryCodeForTypes = true` so vendored libs' inferable types
  reach the type checker. Enforced by `just check-types` — any pyright
  diagnostic in non-vendored code fails the gate.
- Every public function and every dataclass field MUST have type
  annotations. Private (single-leading-underscore) helpers SHOULD be
  annotated.
- Every public function's return annotation MUST be `Result[_, _]` or
  `IOResult[_, _]`, UNLESS the function is:
  - a supervisor at a deliberate side-effect boundary (e.g.,
    `main() -> int` in `commands/*.py` and `doctor/run_static.py`,
    or any function returning `None`), OR
  - the `build_parser() -> ArgumentParser` factory in
    `commands/**.py`: a pure argparse constructor that produces a
    framework type, has no effects, and cannot fail.

  The rule exempts only those two cases; the precise AST scope is
  documented in the `static-check-semantics` deferred item
  (`check-public-api-result-typed` exempts functions named `main`
  in `commands/**.py` and `doctor/run_static.py`, PLUS functions
  named `build_parser` in `commands/**.py`).
- **`Any` is forbidden outside `io/` boundary wrappers and vendored-lib
  facades.** The thin facades under `livespec/io/<lib>_facade.py` are
  the ONLY place `Any` may appear, and they exist precisely to confine
  `Any` to a small audited surface. An AST check rejects `Any`
  annotations elsewhere.
- **`# type: ignore` is forbidden without a narrow justification
  comment** of the form `# type: ignore[<specific-code>] — <reason>`.
  Vendored-lib facades MAY use `# type: ignore` for vendored-lib types
  pyright cannot see; livespec code outside the facades MUST NOT.
- Implicit `Optional` via `None` default without `| None` annotation is
  forbidden (pyright strict flags this).
- mypy is not used; there is no mypy configuration file.

### Vendored-lib type-safety integration

- **`fastjsonschema`** exposes generated callables typed as
  `Callable[[Any], Any]`. The thin facade at
  `livespec/io/fastjsonschema_facade.py` exposes a fully-typed
  surface: `compile_schema(schema_id: str, schema: dict) ->
  Callable[[dict], Result[dict, ValidationError]]`. The facade
  holds a module-level `_COMPILED: dict[str, Callable] = {}`
  keyed on `$id` to dedupe compiles across calls. `functools.lru_cache`
  can't be used directly (dicts are unhashable), and a module-level
  cache would trip `check-global-writes` in pure code — so the cache
  lives in the impure facade layer and is explicitly exempted. See
  "Structured logging → Bootstrap" for the exemption list.
- **`structlog`** logger calls are dynamically typed. The thin facade
  at `livespec/io/structlog_facade.py` exposes typed logging functions:
  `info(message: str, **kwargs: object) -> None`, etc.
- **`dry-python/returns`**: its types (`Result`, `IOResult`) are used
  pervasively throughout the codebase, not just at boundaries. The
  facade pattern doesn't apply uniformly. Whether the returns pyright
  plugin is vendored alongside the lib (and how it's configured) is
  deferred: see `deferred-items.md` (`returns-pyright-plugin-
  disposition`). If the plugin is not vendored, the thin
  `livespec/io/returns_facade.py` MAY hold typed re-exports of the
  primitives we use.

---

## Linter and formatter

`ruff` (astral-sh/ruff) is the sole linter, formatter, import-sorter,
and complexity checker. Pinned via mise.

- `pyproject.toml`'s `[tool.ruff]` configures:
  - `target-version = "py310"`.
  - `line-length = 100`.
  - Rule selection: `E F I B UP SIM C90 N RUF PL PTH`.
  - `[tool.ruff.lint.pylint]` sets `max-args = 6`,
    `max-positional-args = 6`, `max-branches = 10`,
    `max-statements = 30`. Both arg-count gates are enforced; see
    "Complexity thresholds".
- `just check-lint` runs `ruff check .`. Any finding fails the gate.
- `just check-format` runs `ruff format --check .`. Any diff fails.
- Mutating targets for developers: `just fmt` (`ruff format`),
  `just lint-fix` (`ruff check --fix`).
- `# noqa: <CODE> — <reason>` is the only permitted per-line escape.
  Bare `# noqa` without a code and reason is forbidden; the
  `check-lint` enforcement inspects the comment shape.

---

## Testing

Tests use **`pytest`** with mandatory plugins `pytest-cov` and
`pytest-icdiff`. Pinned via mise.

See **PROPOSAL.md §"Testing approach"** for the canonical test-tree
layout (mirroring `scripts/livespec/`, `scripts/bin/`, and
`<repo-root>/dev-tooling/` one-to-one, plus per-spec-file rule-
coverage tests and `heading-coverage.json`). This document does
not duplicate the tree — the layout is maintained in exactly one
place.

Rules:

- **Per-module tests** at `tests/livespec/<mirror>.py` and
  `tests/dev-tooling/<mirror>.py` exercise each module's contract.
- **Per-spec-file tests** at `tests/test_<spec-file>.py` exercise rules
  stated in a specification file end-to-end. These are the tests
  referenced by `heading-coverage.json`.
- Tests MUST NOT mutate files under `tests/fixtures/`. Test-local
  filesystem state uses pytest's `tmp_path` fixture.
- Tests MUST NOT require network access. Impure wrappers are stubbed
  via `monkeypatch.setattr(livespec.io.fs, "read_file", fake_read_file)`
  or equivalent.
- Tests MUST be independent of execution order. Use `tmp_path`-scoped
  state only; no module-level mutable state that a prior test could
  leave behind.
- `@pytest.mark.parametrize` is the preferred idiom for tabulated
  inputs.
- Assertions use `pytest`'s default assertion-introspection. No
  third-party assertion library is used.
- `pytest-icdiff` is enabled via `pyproject.toml`; produces structured
  diffs on failure, aiding LLM consumption of test output.
- The meta-test `tests/test_meta_section_drift_prevention.py` verifies
  every top-level (`##`) heading in each specification file has at
  least one corresponding per-spec-file test case in
  `heading-coverage.json`.
- The meta-test `tests/bin/test_wrappers.py` verifies every
  `scripts/bin/*.py` wrapper (excluding `_bootstrap.py`) matches the
  exact 6-line shape (see "Shebang-wrapper contract" below).

---

## Code coverage

Coverage is measured by `coverage.py` via `pytest-cov`:

- **100% line + branch coverage** is mandatory across the whole Python
  surface in `scripts/livespec/**`, `scripts/bin/**`, and
  `<repo-root>/dev-tooling/**`. No tier split. `_vendor/` is excluded.
  `scripts/bin/` is included because `_bootstrap.py` carries real logic
  (Python-version check + sys.path setup) that warrants enforcement;
  the 6-line wrapper bodies are pragma-excluded per the rules below
  (trivial pass-throughs covered by the wrapper-shape meta-test).
- `pyproject.toml`'s `[tool.coverage.run]` sets `source` to include
  both the `livespec` package and the `bin/` directory (the exact path
  form is implementer choice; e.g., an additional `source` entry for
  `scripts/bin` or a `run_also` directive) and `branch = true`.
- `[tool.coverage.report]` sets `fail_under = 100`, `show_missing = true`,
  `skip_covered = false`.
- Enforced by `just check-coverage`.
- **Escape hatch:** `# pragma: no cover — <reason>` on a single line or
  a bounded block; cap ≤ 3 pragma-lines per file. Bare `# pragma: no cover`
  without a reason is rejected by a targeted regex check. Legitimate
  uses: `if TYPE_CHECKING:` guards; `sys.version_info` gates in
  `bin/_bootstrap.py`.
- **Wrapper coverage (`bin/*.py` except `_bootstrap.py`).** Wrapper
  bodies are NOT pragma-excluded. Each wrapper has a matching
  `tests/bin/test_<cmd>.py` that imports the wrapper and catches
  `SystemExit` via `pytest.raises`, with `monkeypatch` stubbing
  `livespec.commands.<cmd>.main` (or the relevant module's `main`)
  to a no-op returning exit `0`. The import triggers the 6-line
  wrapper body (version check via `_bootstrap.bootstrap()`, package
  import, `raise SystemExit(main())`) under coverage.py's tracer,
  registering every line as covered. The wrapper-shape 6-line rule
  is preserved unchanged; the meta-test `tests/bin/test_wrappers.py`
  continues to verify that shape in parallel to the per-wrapper
  coverage tests.

---

## Keyword-only arguments

All user-defined callables in livespec's scope (`scripts/livespec/**`,
`scripts/bin/**`, `<repo-root>/dev-tooling/**`) MUST accept every
parameter as keyword-only. Call-site ambiguity over positional
order is eliminated by construction: reading `foo(name="alice",
age=30)` unambiguously tells the reader which value is which,
without cross-referencing the function signature.

Rules:

- Every `def` MUST place a lone `*` as its first parameter (or,
  for methods, immediately after `self` / `cls`) so that every
  subsequent parameter is in `kwonlyargs`.
- Every `@dataclass` decorator MUST include `kw_only=True`
  (Python 3.10+). The generated `__init__` is keyword-only.
- Callers MUST pass arguments by keyword wherever the callee
  permits it. Positional invocation is allowed only where the
  callee cannot be changed (stdlib, third-party, dunder methods
  with Python-mandated signatures).
- **Exempt from the `*`-separator rule:**
  - Dunder methods whose signatures are fixed by Python
    (`__eq__(self, other)`, `__hash__(self)`, `__getitem__(self,
    key)`, `__iter__(self)`, `__next__(self)`, etc.).
  - `__init__` of `Exception` subclasses when the only positional
    argument is the message forwarded to `super().__init__(msg)`;
    downstream callers of such classes SHOULD use keyword-only
    form (`MyError(text="...")` with `__match_args__` not
    required for livespec code per §"Structural pattern matching").
  - `__post_init__(self)` on dataclasses.
  - Call-sites into stdlib / third-party / vendored-lib APIs that
    require positional arguments (e.g., `super().__init__(msg)`,
    `Path("/some/path")`, `sys.exit(code)`). These are call-sites,
    not livespec-authored function definitions; the rule binds
    only definitions.

Enforced by `just check-keyword-only-args` (AST): every
`ast.FunctionDef` and `ast.AsyncFunctionDef` under scope MUST have
`args.args` empty after `self` / `cls` (all declared parameters in
`args.kwonlyargs`); every `@dataclass` MUST carry `kw_only=True`.

## Structural pattern matching

`match` statements destructuring livespec-authored classes MUST
use keyword patterns, not positional patterns. Concrete form:
`case Foo(x=x, y=y)` (keyword) rather than `case Foo(x, y)`
(positional). This eliminates the need for `__match_args__` on
any livespec class — the class pattern binds attributes by name,
reading directly from the instance's `.x` / `.y`.

Rules:

- Livespec-authored classes (anything under `scripts/livespec/**`,
  `dev-tooling/**`, or `scripts/bin/**`) MUST NOT declare
  `__match_args__` at class scope.
- Class patterns in `match` statements whose class resolves to a
  livespec-authored class MUST use keyword sub-patterns.
- Class patterns resolving to third-party types (e.g.,
  `dry-python/returns`'s `IOFailure`, `IOSuccess`, `Result.Success`,
  `Result.Failure`) MAY use positional destructure, because those
  libraries define `__match_args__` idiomatically for sum-type
  wrappers and keyword-only patterns would be unnecessarily
  verbose at the library boundary.

Enforced by `just check-match-keyword-only` (AST): every
`ast.Match` with an `ast.MatchClass` whose name resolves (by AST
name resolution; imports walked) to a livespec-authored class MUST
bind via `kwd_patterns`, not `patterns`.

**HelpRequested example.** Under the keyword-only rules, the
supervisor's three-way match dispatch reads:

```python
match result:
    case IOFailure(HelpRequested(text=text)):
        sys.stdout.write(text)
        return 0
    case IOFailure(err):
        log.error("livespec failed", error=err)
        return err.exit_code
    case IOSuccess(report):
        # ... handle success per sub-command
        return 0
```

The outer `IOFailure(...)` uses positional destructure (permitted —
`IOFailure` is from `dry-python/returns`). The inner
`HelpRequested(text=text)` uses keyword destructure. `HelpRequested`
declares no `__match_args__`.

---

## Complexity thresholds

Adapted from language-agnostic research (McCabe, Martin) and tightened
for Python's density:

- **Cyclomatic complexity ≤ 10** per function (ruff `C901`).
- **Function body ≤ 30 logical lines** (ruff `PLR0915`).
- **File ≤ 200 logical lines** (custom check at
  `<repo-root>/dev-tooling/checks/file_lloc.py`).
- **Max nesting depth ≤ 4** (ruff PLR rule).
- **Arguments ≤ 6** per function, counted two ways, both enforced:
  total args (ruff `PLR0913`, `max-args = 6`) AND positional args
  (ruff `PLR0917`, `max-positional-args = 6`). Functions needing
  more parameters MUST be refactored to accept a dataclass (or an
  equivalent struct). This reverses v006 P9's "no positional-arg
  limit" decision: the refactor-to-dataclass discipline is
  load-bearing and requires mechanical enforcement, not voluntary
  compliance.
- **Waivers not permitted.** A function that can't meet the thresholds
  MUST be decomposed; the gate has no escape hatch. Refactor is the
  answer.

Enforced by `just check-complexity`.

---

## Structured logging

Logging uses vendored **`structlog`**. Configuration:

- **JSON output to stderr only.** No console renderer, no format
  switch. Humans pipe to `jq` or similar for visualization.
- **Standard fields every line carries:**
  - `timestamp` (RFC 3339).
  - `level` (`debug` / `info` / `warning` / `error` / `critical`).
  - `logger` (module name).
  - `message` (human-readable text).
  - `run_id` (UUID, bound at executable startup via
    `structlog.contextvars.bind_contextvars`; correlates all logs from
    one invocation).
  - Arbitrary kwargs provided at the call site.
- **Level control:** `LIVESPEC_LOG_LEVEL` env var + `-v` / `-vv` CLI
  flag (CLI wins over env). Default level `WARNING`.
- **Style rules:**
  - **Kwargs only** — `log.error("parse failed", path=str(p),
    error=repr(exc))`. Never f-strings in log messages; the message is
    a stable literal.
  - **Errors include structured fields** — `LivespecError` subclass
    name and structured context dict, not just `str(exc)`.
  - **stdout is reserved** for the structured-findings contract (per
    PROPOSAL.md's doctor static-phase stdout contract).

### Bootstrap

`scripts/livespec/__init__.py` calls `structlog.configure(...)` exactly
once and then binds `run_id` (UUID) via
`structlog.contextvars.bind_contextvars(run_id=str(uuid.uuid4()))` in
the same block. This happens on first import, which is per-process
(each wrapper invocation is its own process; one bind per invocation).

The following calls are **exempt** from `check-global-writes`
because they configure or cache third-party library state, not
livespec module-level state mutated from a function body:

- `structlog.configure(...)` in `livespec/__init__.py`.
- `structlog.contextvars.bind_contextvars(run_id=...)` in
  `livespec/__init__.py`.
- The module-level `_COMPILED: dict[str, Callable]` cache in
  `livespec/io/fastjsonschema_facade.py` and its mutation via
  `compile_schema`.

The complete exemption list, its AST semantics, and the scope of
`check-global-writes` are documented in the
`static-check-semantics` deferred-items entry (renamed from the
v007 `ast-check-semantics` entry and widened to cover
markdown-parsing checks, doctor-cycle semantics, and the argparse
`SystemExit` disposition under supervisor-discipline).

The `log` logger is obtained via `structlog.get_logger(__name__)` in
each module that logs, routed through `livespec/io/structlog_facade.py`.

---

## Exit code contract

Scripts bundled with the skill MUST use the following exit codes,
preserved from v005/v006:

| Code | Meaning |
|---|---|
| `0` | Success. Also covers intentional `--help` output: a `-h` / `--help` request is not an error and exits with `0` via the `HelpRequested` supervisor pattern-match path (see §"HelpRequested disposition" below). |
| `1` | Script-internal failure (unexpected runtime error; likely a bug). |
| `2` | Usage error: bad flag, wrong argument count, malformed invocation. |
| `3` | Input or precondition failed: referenced file/path/value missing, malformed, or in an incompatible state. |
| `4` | Schema validation failed (retryable): LLM-provided JSON payload does not conform to the wrapper's input schema. Per-sub-command SKILL.md prose retries the template prompt with error context, up to 3 retries. Distinct from exit `3` (precondition failure) so the LLM can classify failures deterministically without parsing stderr. |
| `126` | Permission denied: a required file exists but is not executable/readable/writable. |
| `127` | Required external tool not on PATH, or Python version too old. |

Implementation:

- `livespec/errors.py` defines the hierarchy. It holds ONLY
  expected-failure (domain error) classes per the Error Handling
  Discipline in `livespec-nlspec-spec.md`. Bugs are NOT represented
  as `LivespecError` subclasses:
  ```python
  from typing import ClassVar

  class LivespecError(Exception):
      """Base class for expected-failure (domain error) classes.

      A LivespecError represents a domain-meaningful failure that a
      retry, corrected input, or environment fix could resolve. It
      is ROP-track failure-payload material. Bugs (unrecoverable
      programming errors) are NOT LivespecError subclasses; they
      propagate as raised exceptions to the outermost supervisor's
      bug-catcher.
      """
      exit_code: ClassVar[int] = 1

  class UsageError(LivespecError):
      exit_code: ClassVar[int] = 2

  class PreconditionError(LivespecError):
      exit_code: ClassVar[int] = 3

  class ValidationError(LivespecError):
      """Schema validation failure on LLM-provided JSON payload.

      Retryable: the sub-command's SKILL.md prose re-invokes the
      template prompt with error context and retries (up to 3).
      Exit code 4 (distinct from PreconditionError's exit 3) so the
      LLM can deterministically classify retryable vs non-retryable
      exit-3-class failures without parsing stderr.
      """
      exit_code: ClassVar[int] = 4

  class GitUnavailableError(LivespecError):
      exit_code: ClassVar[int] = 3

  class PermissionDeniedError(LivespecError):
      exit_code: ClassVar[int] = 126

  class ToolMissingError(LivespecError):
      exit_code: ClassVar[int] = 127


  class HelpRequested(Exception):
      """User requested help (`-h` or `--help`); NOT a LivespecError.

      A HelpRequested is an informational early-exit category — not a
      domain error (no retry / fix improves it) and not a bug (user
      asked for help). Does not subclass LivespecError. The supervisor
      pattern-matches HelpRequested via keyword destructure (per
      §"Structural pattern matching") and returns exit 0 after
      emitting the help text to stdout.
      """
      exit_code: ClassVar[int] = 0

      def __init__(self, *, text: str) -> None:
          super().__init__(text)
          self.text = text
  ```
- `IOFailure(err)` payloads are `LivespecError` subclasses. Doctor
  static check signatures are `run(ctx) -> IOResult[Finding, E]`
  where `E` is any `LivespecError` subclass (NOT the retired
  `DoctorInternalError` from prior revisions; bugs in a check
  propagate as raised exceptions to the supervisor's bug-catcher
  and result in exit `1`).
- Supervisors (`main()` in `commands/<cmd>.py` and
  `doctor/run_static.py`) pattern-match on the final `IOResult`:
  - `IOFailure(HelpRequested(text))`: emit `text` to stdout; return
    `0`. HelpRequested is NOT a `LivespecError` — it's an
    informational early-exit category.
  - `IOFailure(err)` where `err` is a `LivespecError` subclass: emit
    structured-error JSON line to stderr via structlog; return
    `err.exit_code`.
  - `IOSuccess(...)` with any `status: "fail"` finding: return `3`.
  - `IOSuccess(...)` otherwise: return `0`.

  Supervisors ALSO wrap their body in a top-level
  `try/except Exception` bug-catcher that logs via structlog and
  returns `1` on any uncaught exception (see "Supervisor discipline"
  under §"Railway-Oriented Programming" above).
- `sys.exit(err.exit_code)` appears only in `bin/*.py` shebang
  wrappers and `bin/_bootstrap.py`. Everywhere else stays on the
  railway.

### Doctor static-phase exit-code derivation

The `bin/doctor_static.py` supervisor (in
`livespec.doctor.run_static.main()`) derives exit code from the
final `IOResult` payload:

- On `IOFailure(err)` (`err` is a `LivespecError` subclass — a
  domain error): emit a structured-error JSON line on stderr via
  structlog, then exit `err.exit_code`.
- On `IOSuccess(report)`: emit `{"findings": [...]}` to stdout,
  then exit `3` if any finding has `status: "fail"`, else exit `0`.
  `status: "skipped"` does NOT trigger a fail exit.
- On any uncaught exception (a bug): the supervisor's
  `try/except Exception` logs via structlog with traceback and
  returns `1`.

Enforced by `check-supervisor-discipline` (AST).

---

## File naming and invocation

- Python module and script filenames MUST use snake_case + `.py`.
  Including `bin/*.py` shebang wrappers and `bin/_bootstrap.py`.
- Hyphens appear only in JSON wire contracts (`check_id` values like
  `"doctor-out-of-band-edits"`) and in PROPOSAL.md prose
  (`propose-change` sub-command name).
- The slug↔module-name mapping for doctor-static checks is recorded
  literally in `scripts/livespec/doctor/static/__init__.py`'s static
  registry. JSON slug `out-of-band-edits` ↔ module filename
  `out_of_band_edits.py` ↔ check_id `doctor-out-of-band-edits`. There
  is no conversion loop; the registry's import statements name both
  forms.
- Executables (`bin/*.py`) carry the shebang `#!/usr/bin/env python3`,
  the executable bit, and conform to the shape below.

### Shebang-wrapper contract

Each file under `bin/*.py` (except `_bootstrap.py`) MUST consist of
exactly the following 6-line shape (no other lines, no other
statements):

```python
#!/usr/bin/env python3
"""Shebang wrapper for <description>. No logic; see livespec.<module> for implementation."""
from _bootstrap import bootstrap
bootstrap()
from livespec.<module>.<submodule> import main

raise SystemExit(main())
```

Each wrapper is covered by a dedicated per-wrapper test at
`tests/bin/test_<cmd>.py` that imports the wrapper and catches
`SystemExit` via `pytest.raises`, with `monkeypatch` stubbing the
target `main` to a no-op (see §"Code coverage — Wrapper coverage").
Coverage.py's tracer records every line of the 6-line body as
covered without any `# pragma: no cover` application; the wrapper-
shape 6-line rule is preserved strictly. Shape conformance is
enforced by `check-wrapper-shape` (AST-lite) and verified in parallel
by the `test_wrappers.py` meta-test.

### `bin/_bootstrap.py` contract

The shared bootstrap module is the canonical location for sys.path
setup and the Python-version check. It lives under `bin/` so its
`raise SystemExit(127)` is allowed by `check-supervisor-discipline`.
Body shape:

```python
"""Pre-livespec-import bootstrap: sys.path setup + Python version check.

Imported by every bin/*.py wrapper before any livespec import. Lives under
bin/ so raise SystemExit is permitted by check-supervisor-discipline.
"""
import sys
from pathlib import Path


def bootstrap() -> None:
    if sys.version_info < (3, 10):
        sys.stderr.write(
            "livespec requires Python 3.10+; install via your package manager.\n"
        )
        raise SystemExit(127)
    bundle_scripts = Path(__file__).resolve().parent.parent
    bundle_vendor = bundle_scripts / "_vendor"
    for path in (bundle_scripts, bundle_vendor):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
```

The 6-line wrapper shape and `_bootstrap.py`'s body are jointly
covered by:

- `check-wrapper-shape`: every file under `bin/` matching `*.py`
  except `_bootstrap.py` MUST match the 6-line template.
- `tests/bin/test_wrappers.py`: meta-test asserts the same.
- `tests/bin/test_bootstrap.py`: covers `bootstrap()`'s version
  check and sys.path insertion behaviors.

---

## Dev tooling and task runner

The **`just`** task runner is the single source of truth for every
dev-tooling invocation.

- `justfile` at repo root owns every check, test, build, lint, format,
  coverage, bootstrap, and vendor-management recipe.
- `lefthook.yml` owns when hooks fire (pre-commit, pre-push). Every
  `run:` field is `just <target>`; no direct tool invocations.
- `.github/workflows/*.yml` owns CI triggers and parallelism. Every
  step's `run:` field is `just <target>`; no direct tool invocations.
- `.mise.toml` pins tool versions (Python, just, lefthook, pyright,
  ruff, pytest, pytest-cov, pytest-icdiff).

This eliminates drift across invocation surfaces. A developer
reproduces CI locally by running `just check`.

`just check` runs every check target sequentially, **continues on
failure**, and exits non-zero if any target failed (listing which
targets failed at the end). This matches CI's `fail-fast: false`
matrix; one local run reproduces full CI feedback.

**First-time bootstrap:** `mise install` then `just bootstrap`. The
`bootstrap` target runs `lefthook install` (registers the pre-commit
and pre-push hooks with git) and any other one-time setup. Without
`just bootstrap`, lefthook hooks do not fire on commit.

Enforced by `check-no-direct-tool-invocation` (grep-level): any
`ruff`/`pytest`/`pyright`/`python3` in `lefthook.yml` or any
`.github/workflows/*.yml` `run:` line (other than `just <target>`) is
rejected.

---

## Enforcement suite

The enforcement suite is **invocation-surface-agnostic** (carried over
from v005). Every check is a `just` target; pre-commit, pre-push, CI,
and manual invocation are consumers. Linux is the primary platform;
macOS is a supported developer platform (everything but platform-
specific native code works). No Windows support.

### Canonical target list

| Target | Purpose |
|---|---|
| `just bootstrap` | First-time setup: `lefthook install` + any other one-time setup. |
| `just check` | Run every check below sequentially; continue on failure; non-zero exit if any failed. |
| `just check-lint` | `ruff check .` |
| `just check-format` | `ruff format --check .` |
| `just check-types` | `pyright` (strict, with `_vendor/` excluded). |
| `just check-complexity` | ruff C901 + PLR + file-LLOC custom check. |
| `just check-purity` | AST: `parse/` + `validate/` don't import `io/` or effectful APIs. |
| `just check-private-calls` | AST: no cross-module calls to `_`-prefixed functions defined elsewhere. |
| `just check-import-graph` | AST: no circular imports in `livespec/**`. |
| `just check-global-writes` | AST: no module-level mutable state writes from functions. |
| `just check-supervisor-discipline` | AST: `sys.exit` / `raise SystemExit` only in `bin/*.py` (incl. `_bootstrap.py`). |
| `just check-no-raise-outside-io` | AST: raising of `LivespecError` subclasses (domain errors) restricted to `io/**` and `errors.py`. Raising bug-class exceptions (TypeError, NotImplementedError, AssertionError, etc.) permitted anywhere. |
| `just check-no-except-outside-io` | AST: catching exceptions outside `io/**` permitted only in supervisor bug-catchers (top-level `try/except Exception` in `main()` of `commands/*.py` and `doctor/run_static.py`). |
| `just check-public-api-result-typed` | AST: every public function returns `Result` or `IOResult` per annotation, except supervisors at the side-effect boundary (`main()` in `commands/**.py` and `doctor/run_static.py`). |
| `just check-schema-dataclass-pairing` | AST: every `schemas/*.schema.json` has a paired dataclass at `schemas/dataclasses/<name>.py` with the `$id`-derived name and every listed field in matching Python type; and vice versa. Drift in either direction fails. |
| `just check-main-guard` | AST: no `if __name__ == "__main__":` in `livespec/**`. |
| `just check-wrapper-shape` | AST-lite: `bin/*.py` (except `_bootstrap.py`) conforms to the 6-line shebang-wrapper contract. |
| `just check-keyword-only-args` | AST: every `def` in livespec scope uses `*` as first separator (all params keyword-only); every `@dataclass` declares `kw_only=True`. Exempts Python-mandated dunder signatures and `__init__` of Exception subclasses that forward to `super().__init__(msg)`. |
| `just check-match-keyword-only` | AST: every `match` statement's class pattern resolving to a livespec-authored class binds via keyword sub-patterns (`Foo(x=x)`), not positional (`Foo(x)`). Third-party library class destructures (`returns`-package types) are permitted positionally. |
| `just check-claude-md-coverage` | Every directory under `scripts/` (excluding `_vendor/` subtree), `tests/`, and `dev-tooling/` contains a `CLAUDE.md`. |
| `just check-no-direct-tool-invocation` | grep: `lefthook.yml` and `.github/workflows/*.yml` only invoke `just <target>`. |
| `just check-tools` | Verify every mise-pinned tool is installed at the pinned version. |
| `just check-tests` | `pytest`. |
| `just check-coverage` | `pytest --cov` with 100% line+branch threshold. |

Mutating targets (opt-in, not run in CI):

| Target | Purpose |
|---|---|
| `just fmt` | `ruff format .` |
| `just lint-fix` | `ruff check --fix .` |
| `just vendor-update <lib>` | Re-vendor a library, updating `.vendor.jsonc`. |

Note: `check-vendor-audit` was removed in v007. Vendored libs are
version-pinned in `.vendor.jsonc`; the no-edit discipline plus code
review and git diff visibility cover the threat model.

### Invocation surfaces

- **Pre-commit (local, staged files):** `lefthook.yml` runs `just check`.
- **Pre-push (local, whole tree):** `lefthook.yml` runs `just check`.
- **CI (GitHub Actions):** one job per check via a matrix strategy with
  `fail-fast: false`, each calling `just <target>`. The `jdx/mise-
  action@v2` step installs pinned tools.
- **Manual (developer at the shell):** `just <target>` — same targets
  hooks and CI use.

---

## Agent-oriented documentation: CLAUDE.md coverage

Every directory under:

- `.claude-plugin/scripts/` (with the entire `_vendor/` subtree
  explicitly excluded), AND
- `<repo-root>/tests/` (with the entire `fixtures/` subtree
  explicitly excluded), AND
- `<repo-root>/dev-tooling/`

MUST contain a `CLAUDE.md` file describing the local constraints an
agent working in that directory must satisfy. One optional
`tests/fixtures/CLAUDE.md` at the fixtures root is permitted (it
can explain the read-only discipline) but is not required, and
subdirectories under `tests/fixtures/` are never required to carry
`CLAUDE.md`.

Each `CLAUDE.md`:

- States the directory's purpose in one sentence.
- Lists directory-local rules (e.g., "this directory is pure; no
  imports from `io/`").
- Links to this style doc for global rules rather than duplicating.
- Is kept short (typically under 50 lines); it's a local crib sheet,
  not a full reference.

Enforced by `just check-claude-md-coverage`. The `_vendor/` carve-out
prevents `check-claude-md-coverage` from forcing CLAUDE.md inside
vendored libs (which would itself constitute a local edit). The
`tests/fixtures/` carve-out prevents CLAUDE.md files from
inadvertently landing in read-only fixture trees.

---

## Non-goals

- **Interactive CLI.** Python scripts bundled with the skill are
  non-interactive by design.
- **Windows native support.** Not a v008 target; Linux + macOS only.
- **Async / concurrency.** livespec's workload is synchronous and
  deterministic. No `asyncio`, no threading, no multiprocessing.
- **Performance tuning.** livespec is a CLI-scale tool; no hot-path
  work.
- **Runtime dependency resolution.** Missing `python3` or too-old
  Python → exit 127 from `bin/_bootstrap.py`; installing Python is the
  user's concern.
- **LLM integration from Python.** Python scripts handle only
  deterministic work; LLM-driven behavior stays at the skill-markdown
  layer (per-sub-command `SKILL.md`, template prompts).
- **Mypy compatibility.** Pyright is the sole type checker.
- **Ruby / Node / other language hooks.** No non-Python dev-tooling
  scripts.
- **Automated vendored-lib drift detection.** Pinned versions in
  `.vendor.jsonc` + the no-edit discipline + code review are the
  controls; no `check-vendor-audit` script exists.
