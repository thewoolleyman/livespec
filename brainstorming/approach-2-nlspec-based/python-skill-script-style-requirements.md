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
- **Exempt:** user-provided Python modules loaded via custom-template
  extension hooks (e.g., `template.json`'s
  `doctor_static_check_modules`). Extension code is the extension
  author's responsibility; livespec's enforcement suite does NOT
  scope to it. The only obligation extension authors carry is the
  calling-API contract (the `TEMPLATE_CHECKS` export shape, the
  `CheckRunFn` signature, the `Finding` payload shape — all defined
  inside `livespec/`). Inside an extension module, the author has
  full freedom over library usage, architecture, and patterns;
  livespec imposes no requirements beyond invocability per the
  contract.

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
  location for the version check; `.claude-plugin/scripts/livespec/__init__.py` does
  NOT raise (it cannot — see "Railway-Oriented Programming" below).
- `.python-version` at the repo root pins the developer and CI Python
  version to an exact 3.10.x release, managed by `uv python pin` per
  v024. `pyproject.toml`'s `[project.requires-python]` declares the
  same constraint. `.mise.toml` pins only the non-Python binaries
  (`uv`, `just`, `lefthook`); developers run `mise install` then
  `uv sync --all-groups` to match.
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
- Permissively licensed (MIT, BSD-2-Clause, BSD-3-Clause,
  Apache-2.0, or PSF-2.0). PSF-2.0 added in v013 M1 to admit
  `typing_extensions`; the narrow extension is deliberate and
  does not generalize to other licenses.
- Actively maintained by a reputable upstream.
- Zero-transitive-dep or all-transitive-deps-also-vendored.

Locked vendored libs (each pinned to an exact upstream ref
recorded in `<repo-root>/.vendor.jsonc`):

- **`returns`** (dry-python/returns, BSD-3-Clause) — ROP
  primitives: `Result`, `IOResult`, `@safe`, `@impure_safe`,
  `flow`, `bind`, `Fold.collect`, `lash`. NO pyright plugin
  is vendored: per v025, pyright has no plugin system
  (microsoft/pyright#607: maintainer rejected plugin support
  in 2020, formalized 2021, reaffirmed 2024) and dry-python/
  returns explicitly does not support pyright (dry-python/
  returns#1513: closed by maintainer 2022). The
  `returns-pyright-plugin-disposition` deferred item was
  originally closed in v018 Q4 by vendoring a hypothetical
  pyright plugin; the closure was rescinded and re-closed in
  v025 D1 with the revised disposition: no plugin vendored.
  The seven strict-plus diagnostics in `[tool.pyright]`
  (especially `reportUnusedCallResult = "error"`) remain the
  load-bearing guardrails against silent `Result` /
  `IOResult` discards. Pyright still type-checks
  `Result[T, E]` generic parameters via standard generic
  inference; flow-narrowing through `bind` chains is lossier
  than under mypy-with-plugin, requiring occasional explicit
  annotations or `cast()` calls at combinator boundaries.
  Unnecessary casts are caught by `reportUnnecessaryCast`
  and unnecessary type-ignores by
  `reportUnnecessaryTypeIgnoreComment` (both enabled), so
  the friction surfaces at call sites rather than hiding in
  opaque `# type: ignore` debt.
- **`fastjsonschema`** (horejsek/python-fastjsonschema, MIT) — JSON
  Schema Draft-7 validator.
- **`structlog`** (hynek/structlog, BSD-2 / MIT dual) — structured JSON
  logging.
- **`jsoncomment`** (MIT, derivative work) — **vendored as a
  minimal shim** per v026 D1. The shim file at
  `.claude-plugin/scripts/_vendor/jsoncomment/__init__.py`
  faithfully replicates jsoncomment 0.4.2's `//` line-comment and
  `/* */` block-comment stripping semantics; multi-line strings
  and trailing-commas support are OPTIONAL (implemented only if
  `livespec/parse/jsonc.py` requires them). Module-named
  `jsoncomment` so existing `import jsoncomment` statements work
  unchanged. The shim's `LICENSE` carries verbatim MIT attribution
  to Gaspare Iengo (citing jsoncomment 0.4.2's `COPYING` file as
  the derivative-work source). Used by `livespec/parse/jsonc.py`
  as a comment-stripping pre-pass over stdlib `json.loads` for
  `.livespec.jsonc` parsing and any other JSONC input. The
  canonical upstream (`bitbucket.org/Dando_Real_ITA/json-comment`)
  was sunset by Atlassian and no live git mirror exists; the PyPI
  sdist is the only surviving source-of-record, and the v018 Q3
  git-based initial-vendoring procedure does not apply.
- **`typing_extensions`** (python/typing_extensions, PSF-2.0) —
  **vendored full upstream verbatim** at tag `4.12.2` per v027
  D1 (was the v013 M1 hand-authored minimal shim pre-v027). The
  upstream lib at
  `.claude-plugin/scripts/_vendor/typing_extensions/__init__.py`
  provides full Python typing-system backports: `override` +
  `assert_never` for livespec's own canonical-import-path needs
  (pyright's `reportImplicitOverride` diagnostic v012 L2 and the
  `check-assert-never-exhaustiveness` check v012 L7), plus the
  variadic-generics + Self + Never + TypedDict + ParamSpec +
  TypeVarTuple + Unpack symbols that the vendored returns +
  structlog + fastjsonschema sources transitively require at
  import time. The module name `typing_extensions` is the
  upstream-canonical path. The verbatim PSF-2.0 `LICENSE` is
  shipped at `_vendor/typing_extensions/LICENSE`. v027 D1
  reclassified typing_extensions from shim to upstream-sourced
  because the v013 M1 minimal-shim approach cannot satisfy
  `Generic[..., Unpack[TypeVarTuple(...)]]` variadic-generics
  usage on Python 3.10 (the dev-env minimum); PROPOSAL.md v013
  M1 explicitly anticipated this scope-widening path.

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
  blessed mutation path for upstream-sourced libs (`returns`,
  `fastjsonschema`, `structlog`, `typing_extensions`). The recipe
  fetches the upstream ref, copies it under `_vendor/<lib>/`,
  preserves `LICENSE`, and updates `.vendor.jsonc`'s recorded
  ref. (The v018 Q4 sixth lib `returns_pyright_plugin` was
  dropped in v025 D1; `jsoncomment` was reclassified from
  upstream-sourced lib to hand-authored shim in v026 D1;
  `typing_extensions` was reclassified from hand-authored shim
  to upstream-sourced lib in v027 D1 — see PROPOSAL.md
  §"Runtime dependencies — Vendored pure-Python libraries".)
- **Initial-vendoring exception (one-time, v018 Q3).** The
  first population of every upstream-sourced vendored lib
  (`returns`, `fastjsonschema`, `structlog`,
  `typing_extensions`) is a one-time MANUAL procedure,
  distinct from the blessed
  `just vendor-update` path above: `git clone` the upstream
  repo at a working ref into a throwaway directory;
  `git checkout <ref>` matching the `upstream_ref` recorded
  in `.vendor.jsonc`; copy the library's source tree under
  `.claude-plugin/scripts/_vendor/<lib>/`; copy the upstream
  `LICENSE` file verbatim to
  `.claude-plugin/scripts/_vendor/<lib>/LICENSE`; record the
  lib's provenance in `.vendor.jsonc` (`upstream_url`,
  `upstream_ref`, `vendored_at` ISO-8601 UTC); delete the
  throwaway clone; smoke-test that the wrapper bootstrap
  imports the vendored lib successfully. Once the
  `jsoncomment` shim is hand-authored at Phase 2 of the
  bootstrap plan, `just vendor-update <lib>` becomes the only
  permitted path for subsequent re-vendoring of upstream-
  sourced libs. The initial procedure applies ONCE per
  livespec repo, at Phase 2 of the bootstrap plan; thereafter
  all upstream-sourced-lib mutations flow through the blessed
  recipe. The circularity the exception resolves:
  `just vendor-update <lib>` invokes Python through
  `livespec.parse.jsonc` to read/write `.vendor.jsonc`, and
  `livespec.parse.jsonc` imports `jsoncomment`; the recipe
  cannot run before `jsoncomment` exists. Pre-v026 the
  satisfying mechanism was "git-clone-and-copy of upstream";
  post-v026 it is "hand-author the shim at Phase 2".
- **Shim libraries are livespec-authored** (v026 D1).
  `_vendor/jsoncomment/` is the only shim post-v027: a JSONC
  parser shim per v026 D1, faithfully replicating jsoncomment
  0.4.2's `//` and `/* */` comment-stripping semantics. The
  shim is not re-vendored via `just vendor-update`; instead it
  is widened (one-line edit per added feature) or replaced
  with a full upstream vendoring via a new propose-change
  cycle. `.vendor.jsonc` records the shim's upstream
  attribution ref (for provenance) and its `shim: true` flag.
  The shim's `LICENSE` is a derivative-work LICENSE with
  attribution to the upstream author (Gaspare Iengo, MIT).
  Shim updates go through normal code-review; the "never edit
  `_vendor/`" rule above applies only to upstream-sourced
  libs. (Pre-v027, `_vendor/typing_extensions/` was also a
  shim per v013 M1; v027 D1 reclassified it to upstream-sourced
  because vendored-lib transitive use of variadic generics
  required full upstream typing_extensions backports that a
  minimal shim cannot synthesize on Python 3.10.)
- **`.vendor.jsonc`** records `{upstream_url, upstream_ref, vendored_at}`
  per lib; for shims, records the additional flag `shim: true`
  and the provenance ref from which the shim's LICENSE was
  copied. No hashes; no automated drift-detection check
  (`check-vendor-audit` was removed in v007 as over-engineered
  for the threat model).
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
  Each wrapper file is exactly 6 statements matching the shape
  below (plus an optional single blank line between the imports
  and `raise SystemExit(main())`). No logic. `chmod +x` applied.
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
  validator at `validate/<name>.py` exports a function
  `validate_<name>(payload: dict, schema: dict) ->
  Result[<Dataclass>, ValidationError]` where `<Dataclass>` is the
  paired dataclass at `schemas/dataclasses/<name>.py`. Callers in
  `commands/` or `doctor/` read schemas from disk via `io/`
  wrappers and pass the parsed dict. Validators invoke
  `livespec.io.fastjsonschema_facade.compile_schema` for the actual
  compile; the facade owns the compile cache (see "Vendored-lib
  type-safety integration" below). `validate/` stays strictly pure
  (no module-level mutable state, no filesystem I/O). **Every
  schema at `schemas/*.schema.json` MUST have a paired validator
  at `validate/<name>.py` in addition to its paired dataclass
  (v013 M6); three-way drift is caught by
  `check-schema-dataclass-pairing`.** Per v014 N2, this includes
  `validate/finding.py` paired with `schemas/finding.schema.json`
  and `schemas/dataclasses/finding.py` — the v010 J11 implementer
  choice (standalone-vs-embedded `finding.schema.json`) is closed
  in favor of standalone, so the three-way symmetry holds without
  a by-name exemption.
- **`schemas/`** — JSON Schema Draft-7 files plus the
  `dataclasses/` subdirectory that holds the paired hand-authored
  dataclasses. Filename matches the dataclass: `LivespecConfig` →
  `livespec_config.schema.json` paired with
  `schemas/dataclasses/livespec_config.py` AND
  `validate/livespec_config.py`. `check-schema-dataclass-pairing`
  enforces drift-free pairing in all three directions (v013 M6):
  every schema has matching dataclass + validator; every dataclass
  has matching schema + validator; every validator has matching
  schema + dataclass. See "Dataclass authorship" below.
- **`context.py`** — immutable context dataclasses (`DoctorContext`,
  `SeedContext`, etc.) — the railway payload. See "Context
  dataclasses" below for field sets.
- **`errors.py`** — `LivespecError` hierarchy with per-subclass
  `exit_code` class attribute. The hierarchy holds ONLY expected-
  failure (domain error) classes per the Error Handling Discipline
  below; bugs are NOT represented as `LivespecError` subclasses.

### Dataclass authorship

Each JSON Schema under `schemas/*.schema.json` has a paired
hand-authored `@dataclass(frozen=True, kw_only=True, slots=True)`
at `schemas/dataclasses/<name>.py`. The dataclass and the schema
are co-authoritative: the schema is the wire contract (validated
at boundary by `fastjsonschema`); the dataclass is the Python
type threaded through the railway (`Result[<Dataclass>,
ValidationError]` from each validator per the factory shape).
Domain-meaningful field types use the canonical NewType aliases
from `livespec/types.py` (see §"Type safety — Domain primitives
via `NewType`").

- The file name matches the `$id`-derived snake_case dataclass
  name (`LivespecConfig` → `livespec_config.py`).
- Fields MUST match the schema one-to-one in name and Python type.
- `schemas/__init__.py` re-exports every dataclass name for
  convenient import.
- No codegen toolchain. No generator. Drift between schema,
  dataclass, and validator is caught mechanically by
  `check-schema-dataclass-pairing` (three-way AST walker per
  v013 M6: schema ↔ dataclass ↔ validator).

### Context dataclasses

Every context dataclass MUST be
`@dataclass(frozen=True, kw_only=True, slots=True)` and carry
exactly the fields below at minimum. Sub-command contexts embed
`DoctorContext` rather than inheriting so the type checker can
narrow each sub-command's payload independently. Domain-meaningful
fields use NewType aliases from `livespec/types.py`.

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
    config_load_status: Literal["ok", "absent", "malformed", "schema_invalid"]  # v014 N3: bootstrap-lenience status for livespec-jsonc-valid check
    template_root: Path         # resolved template directory (built-in path or custom)
    template_load_status: Literal["ok", "absent", "malformed", "schema_invalid"]  # v014 N3: bootstrap-lenience status for template-exists check
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

`LivespecConfig`, `SeedInput`, `ProposalFindings`, and `ReviseInput`
are dataclasses generated from the corresponding `*.schema.json`
files; each schema carries a `$id` naming the dataclass. Fields are
filled at validation time (via the factory-shape validators under
`livespec/validate/`).

### CLI argument parsing seam

argparse is the sole CLI parser and lives in `livespec/io/cli.py`.
Rationale: `ArgumentParser.parse_args()` raises `SystemExit` on
usage errors and `--help`; the 6-statement wrapper shape leaves no
room for it; `check-supervisor-discipline` forbids `SystemExit` outside
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
- `check-supervisor-discipline` scope: `.claude-plugin/scripts/livespec/**` is in scope;
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
  files (including `bin/_bootstrap.py`). Not in any `.claude-plugin/scripts/livespec/**`
  module. Enforced by `check-supervisor-discipline`.

Every public function's `return` annotation MUST be `Result[_, _]` or
`IOResult[_, _]`, unless the function is a supervisor at a
deliberate side-effect boundary (e.g., `main() -> int` in
`commands/*.py` and `doctor/run_static.py`, or any function
returning `None`). The rule exempts only such supervisors. Enforced
by `check-public-api-result-typed` (AST); the exemption scope is
documented in the `static-check-semantics` deferred item.

### ROP pipeline shape

A class decorated with `@rop_pipeline` MUST carry exactly ONE
public method (the entry point). Every other method MUST be
`_`-prefixed (private). Dunder methods (`__init__`, `__call__`,
etc., name matches `^__.+__$`) are not counted toward the
public-method quota — they are Python-mandated structural
surfaces.

The decorator itself is a runtime no-op (returns the decorated
class unchanged) declared in `livespec.types`. AST enforcement
lives in `dev-tooling/checks/rop_pipeline_shape.py`. The decorator
exists primarily as an AST marker for the static check, plus as
documentation at the def-site.

Rationale: the rule encodes the Command / Use Case Interactor /
Trailblazer Operation lineage. Each pipeline class encapsulates
one cohesive railway chain; the single public method is the entry
point; internal steps are bounded by the class body. Statically
enforcing the shape prevents the public surface from drifting as
new chain steps are added — agent-authored code that grows a
second public method gets caught at check time, not at review.
Helpers stay private (`_`-prefixed) and intra-class, so the
`check-private-calls` cross-module-import rule is moot for them.

Helper classes and helper modules (anything NOT carrying the
`@rop_pipeline` decorator) are exempt from this rule and may
export multiple public names.

The marker is a decorator rather than a base class because the
`check-no-inheritance` direct-parent allowlist is intentionally
small (`{Exception, BaseException, LivespecError, Protocol,
NamedTuple, TypedDict}`) and adding `RopPipeline` to the allowlist
would expand the open-extension-point set for an application
pattern. The decorator approach achieves the same "marker" effect
without inheritance.

Enforced by `just check-rop-pipeline-shape`.

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

Enforced by `check-imports-architecture` (Import-Linter `forbidden`
contract over `parse/` and `validate/` imports; see §"Enforcement
suite" for the full target list and the v012 L15a Import-Linter
adoption that replaces v011's planned hand-written `check-purity`;
see §"Import-Linter contracts (minimum configuration)" below for
the minimum concrete `[tool.importlinter]` shape per v013 M7, as
narrowed in v017 Q3 to two contracts — purity and layered
architecture — with raise-discipline now raise-site-only via
`check-no-raise-outside-io`).

### Import-Linter contracts (minimum configuration)

Per v013 M7 (scope narrowed in v017 Q3), the Import-Linter
contracts in `pyproject.toml`'s `[tool.importlinter]` section
MUST collectively enforce purity and layered architecture. The
minimum concrete configuration below is **illustrative** of the
canonical shape; contract names, layer names, and ignore-import
globs MAY be restructured so long as the two English-language
rules below are enforced. (v012 L15a's third contract covering
the raise-discipline import surface was retracted in v017 Q3;
see §"Exit code contract" and `check-no-raise-outside-io`'s
target description below — raise-site enforcement is the
single enforcement point.)

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

The authoritative rules (enforced by ANY valid Import-Linter
configuration satisfying these two statements):

1. Modules in `livespec.parse` and `livespec.validate` MUST NOT
   import `livespec.io`, `subprocess`, filesystem APIs
   (`pathlib`, `open`), `returns.io`, `socket`, `http`, `urllib`.
2. Higher layers MAY import lower layers but not vice-versa; the
   layer stack is `parse` < `validate` < `io` <
   `commands` | `doctor`. No circular imports follow by
   construction.

**Raise-discipline is NOT an Import-Linter concern (v017 Q3).**
`LivespecError` raise-sites are restricted to `livespec.io.*`
and `livespec.errors` (enforced by the hand-written
`check-no-raise-outside-io` raise-site check; see §"Enforcement
suite" target list below and §"Exit code contract" for the
domain-error/bug-class distinction). `livespec.errors` MAY be
imported from any module that needs to reference
`LivespecError` or a subclass in a type annotation, `match`
pattern, or attribute access (e.g., `err.exit_code`). The v012
L15a claim that Import-Linter "replaces the import-surface
portion of `check-no-raise-outside-io`" is retracted: Import-
Linter operates on import statements and cannot distinguish
import-for-raising from import-for-annotating, so the
discipline collapses to raise-site enforcement only.

Architecture-vs-mechanism principle (see
`livespec-nlspec-spec.md` §"Architecture-Level Constraints"):
the two rules above are the contract; the TOML is one valid
way to express them.

**Implementation overlay (Phase 4 sub-step 26 reconciliation).**
Two of the seven items listed in rule 1 — `returns.io` and
`pathlib` — are intentionally absent from the realized
`pyproject.toml` `forbidden_modules` list. The architecture-
vs-mechanism principle above licenses this reassignment:

- `returns.io` is a subpackage of an external (`returns`)
  package; Import-Linter v2 rejects subpackage forbids on
  externals. The `IOResult` / `IOFailure` ban in pure layers
  is enforced at raise-site by `check-no-raise-outside-io`,
  which catches every site where pure code would actually
  raise into the IO track.
- `pathlib` is required by `livespec.types` (the canonical
  module for `NewType` aliases) because `SpecRoot =
  NewType("SpecRoot", Path)` forces a runtime `pathlib`
  import. That import flows transitively into pure layers
  through the wire dataclasses under
  `livespec.schemas.dataclasses/`. Importing the `Path`
  *class* is not I/O; only its method calls are. The
  no-I/O-at-runtime intent is caught by
  `check-no-write-direct`, `check-supervisor-discipline`,
  and `check-no-raise-outside-io`, none of which fire on
  import-for-typing.

Phase 5+ may revisit this overlay (e.g., split
`livespec.types` into pure + Path-dependent halves with a
location-based exemption in `check-newtype-domain-primitives`)
when the stub-to-implementation widening provides richer
context for choosing among the available IoC patterns.

---

## Type safety

- **pyright strict mode** is mandatory. Livespec uses
  `pyright` (microsoft/pyright), NOT `basedpyright` (per v018
  Q4; the `basedpyright-vs-pyright` deferred item is closed
  in favor of pyright — the v012 L1 + L2 manual strict-plus
  configuration already enables every diagnostic that
  matters, and community-fork maintainer-pool risk outweighs
  basedpyright's incremental defaults-simplification
  benefit). `pyproject.toml`'s `[tool.pyright]` sets
  `typeCheckingMode = "strict"` and excludes `_vendor/**`
  from strict scope while keeping `useLibraryCodeForTypes =
  true` so vendored libs' inferable types reach the type
  checker. NO `pluginPaths` entry: per v025 D1, pyright has
  no plugin system (microsoft/pyright#607) and no upstream
  `returns_pyright_plugin` exists; the v018 Q4 closure of
  `returns-pyright-plugin-disposition` was rescinded and
  re-closed with the revised disposition (no plugin
  vendored). The seven strict-plus diagnostics below remain
  the load-bearing guardrails. Enforced by `just check-types`
  — any pyright diagnostic in non-vendored code fails the
  gate.
- **Pyright strict-plus diagnostics MUST be enabled in
  `[tool.pyright]`.** These seven diagnostics are above the strict
  baseline; each closes a documented LLM-authored-code failure
  pattern with a one-line config change:
  - `reportUnusedCallResult = "error"` — every call to a function
    whose return type is non-`None` MUST be bound or passed on; the
    rare legitimate fire-and-forget pattern uses
    `_ = do_something(ctx)` explicit-discard binding. **This is
    the load-bearing diagnostic for the ROP discipline:** without
    it, an LLM can write `do_something(ctx)` and silently discard
    the entire `Result` / `IOResult` failure track.
  - `reportImplicitOverride = "error"` — every method override MUST
    carry `@override` (imported from `typing_extensions` per v013 M1
    uniform-import discipline; see below). Renaming a base-class
    method without `@override` silently strands the override; this
    catches it.
  - `reportUninitializedInstanceVariable = "error"` — every
    instance attribute MUST be initialized in `__init__` or have a
    class-level default.
  - `reportUnnecessaryTypeIgnoreComment = "error"` — flags
    `# type: ignore` comments that no longer suppress any
    diagnostic.
  - `reportUnnecessaryCast = "error"` — flags `cast(X, value)`
    where `value` is already typed `X`.
  - `reportUnnecessaryIsInstance = "error"` — flags
    `isinstance(x, T)` when the type checker already knows `x: T`.
  - `reportImplicitStringConcatenation = "error"` — catches
    `["foo" "bar"]` (missing comma) bugs in lists / sets / tuples.

- Every public function (per the `__all__` declaration; see
  §"Module API surface" below) and every dataclass field MUST have
  type annotations. Private helpers (single-leading-underscore prefix
  or simply not listed in `__all__`) SHOULD be annotated.
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
  named `build_parser` in `commands/**.py`). The check scopes its
  "public function" detection to names listed in `__all__` (see
  §"Module API surface" below) rather than to the leading-
  underscore convention.
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

### `@override` and `assert_never` import source

Both symbols MUST be imported uniformly from `typing_extensions`,
not from stdlib `typing`, regardless of Python version.
`typing_extensions` is **vendored full upstream verbatim** at
tag `4.12.2` per v027 D1, at
`.claude-plugin/scripts/_vendor/typing_extensions/__init__.py`
(was the v013 M1 hand-authored minimal shim pre-v027). The
upstream-canonical `typing_extensions` module name is retained
so pyright's `reportImplicitOverride` recognizes the import
path and `check-assert-never-exhaustiveness` recognizes the
`Never`-narrowing signature. See §"Vendored third-party
libraries" above for the lib's license + attribution. Uniform
import discipline (`from typing_extensions import override,
assert_never`) eliminates per-version conditionals.

### Module API surface

Every module in `.claude-plugin/scripts/livespec/**` MUST declare a module-top
`__all__: list[str]` listing the public API names. Public functions,
public classes, and public NewType aliases belong in `__all__`;
private helpers (single-leading-underscore prefix) MUST NOT appear in
`__all__`. The `check-public-api-result-typed` rule scopes its
public-function detection to names listed in `__all__` rather than
to the leading-underscore convention.

`__init__.py` files MAY declare `__all__` for re-export composition;
the same rule applies (every name listed must resolve in the module's
namespace, including imported names).

Enforced by AST check `check-all-declared`: walks every module under
`.claude-plugin/scripts/livespec/**`; verifies a module-level `__all__: list[str]`
assignment exists; verifies every name in `__all__` is actually
defined in the module (catches stale entries after a rename).

### Domain primitives via `NewType`

Domain identifiers in `.claude-plugin/scripts/livespec/**` MUST use a `typing.NewType` alias
from the canonical declarations in `livespec/types.py`. `NewType`
creates a zero-runtime-cost type alias that pyright treats as
distinct from the underlying primitive — passing a `RunId` where
a `CheckId` is expected becomes a type error. This eliminates the
classic "right shape, wrong meaning" bug class for raw-string and
raw-`Path` fields.

Canonical roles → NewType mapping (field-name → NewType inferred
by the AST check):

| Field name | NewType | Underlying | Concept |
|---|---|---|---|
| `check_id` | `CheckId` | `str` | doctor-static check slug |
| `run_id` | `RunId` | `str` | per-invocation UUID |
| `topic` | `TopicSlug` | `str` | proposed-change topic (note: field name is `topic`; NewType name uses `Slug` suffix to disambiguate) |
| `spec_root` | `SpecRoot` | `Path` | resolved spec-root path |
| `schema_id` | `SchemaId` | `str` | JSON Schema `$id` |
| `template` | `TemplateName` | `str` | `.livespec.jsonc` `template` field (the user's template selection — built-in name or path-as-string); NewType name uses `Name` suffix to disambiguate from the `template_root: Path` field, which is the resolved directory and uses raw `Path` |
| `author` / `author_human` / `author_llm` | `Author` | `str` | author identifier (per K7 rename) |
| `version_tag` | `VersionTag` | `str` | `vNNN` version identifier |

Dataclass fields and function signatures handling these concepts
MUST use the NewType, not the underlying primitive. Construction
uses the NewType as a callable: `CheckId("doctor-out-of-band-edits")`.

Additions to the canonical list are first-class deferred-items work
(one-line update to `livespec/types.py` plus per-call-site
migrations).

**Note on module name (v013 C4).** The module name `livespec.types`
intentionally echoes the stdlib `types` module name. The TID rule
`ban-relative-imports = "all"` (see §"Linter and formatter") and
absolute-import discipline throughout `.claude-plugin/scripts/livespec/**` preclude any
import-resolution conflict between
`from livespec.types import Author` and
`from types import ModuleType`. Readers encountering the name
re-use for the first time can verify this by grep; no rename is
planned.

Enforced by AST check `check-newtype-domain-primitives`: walks
`livespec/schemas/dataclasses/*.py` and `livespec/**.py` function
signatures; verifies field annotations matching the listed roles
use the corresponding NewType. The role-to-field-name mapping is
enumerated explicitly in the check source; partial mismatches
(right NewType wrong field name; or right field name wrong
NewType) both fail.

### Inheritance and structural typing

Class inheritance in `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `<repo-root>/dev-tooling/**`
is RESTRICTED. The AST check `check-no-inheritance` rejects any
`class X(Y):` definition where `Y` is not in the **direct-parent
allowlist**:
`{Exception, BaseException, LivespecError, Protocol, NamedTuple,
TypedDict}`. The rule is DIRECT-PARENT only; `LivespecError`
subclasses (e.g., `UsageError`, `ValidationError`) are NOT
acceptable bases for further subclassing (v013 M5). This
tightening enforces the v012 revision-file leaf-closed intent
mechanically — an LLM writing `class RateLimitError(UsageError):`
is now rejected at check time, where the v012-era transitive
reading would have accepted it.

This codifies the documented design direction: flat composition
over inheritance; structural typing via `typing.Protocol`; sum-type
dispatch via tagged dataclasses + structural pattern matching.
The `LivespecError` hierarchy is intentionally ONE level deep
below the open base `LivespecError`. Adding a new domain-error
subclass `class RateLimitError(LivespecError):` is permitted by
the rule; `class RateLimitError(UsageError):` is NOT. Authors
who want rate-limit-like-usage-error semantics set
`RateLimitError.exit_code = 2` explicitly on the direct-from-
LivespecError subclass.

Structural interfaces in `.claude-plugin/scripts/livespec/**` MUST be declared via
`typing.Protocol`. `abc.ABC`, `abc.ABCMeta`, and
`abc.abstractmethod` imports are banned via the TID rule
configuration; see §"Linter and formatter."

The `@final` decorator (imported from `typing_extensions` per the
v013 M1 uniform-import discipline) is OPTIONAL throughout
livespec; the AST check is the source of truth. Authors MAY use
`@final` as documentation-by-decorator for clarity but it is not
required. If used, extend the shim at
`_vendor/typing_extensions/__init__.py` to export `final` as well
(one-line addition).

### Exhaustiveness

Every `match` statement in `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and
`<repo-root>/dev-tooling/**` MUST terminate with `case _: assert_never(<subject>)`
regardless of subject type. `assert_never` is imported from
`typing_extensions` per the v013 M1 uniform-import discipline
(see §"Type safety — `@override` and `assert_never` import
source").

Rationale: `assert_never(x)` requires `x` to have type `Never`. When
all variants of a closed-union subject are handled by preceding `case`
arms, the residual type at the default arm is `Never` and pyright
accepts the call. When a new variant is added without updating the
dispatch site, the residual type narrows to the unhandled variant
and `assert_never(x)` becomes a type error at the unhandled dispatch
site. This converts "I added a new variant and forgot to handle it
somewhere" from a silent runtime bug into a compile-time error at
every unhandled site.

The conservative scope (every `match`, regardless of subject type) is
preferred over a precise scope (only closed-union subjects) because
false positives are cheap (just add the line) and the simpler check
is more maintainable.

Enforced by AST check `check-assert-never-exhaustiveness`: walks
every `ast.Match` node in scope; verifies the final case arm is
`case _:` and its body is exactly `assert_never(<subject-name>)`.

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
and complexity checker. Uv-managed per v024 via `pyproject.toml`
`[dependency-groups.dev]`.

- `pyproject.toml`'s `[tool.ruff]` configures:
  - `target-version = "py310"`.
  - `line-length = 100`.
  - **Rule selection** (27 categories total):
    `E F I B UP SIM C90 N RUF PL PTH` (the v011 baseline; 11
    categories) PLUS
    `TRY FBT PIE SLF LOG G TID ERA ARG RSE PT FURB SLOT ISC T20 S`
    (16 categories added in v012). Per-category meaning:
    - `TRY` (tryceratops) — exception-handling discipline; pairs
      with the v011 K10 domain-vs-bugs split.
    - `FBT` — boolean-trap (forbids boolean POSITIONAL arguments);
      reinforces the K4 keyword-only discipline.
    - `PIE` — miscellaneous anti-patterns.
    - `SLF` — forbids accessing `_`-prefixed attributes from outside
      the defining class.
    - `LOG` + `G` — logging discipline (no f-strings in log calls;
      kwargs only); reinforces §"Structured logging".
    - `TID` — tidy imports (no relative imports; supports banning
      specific modules; see banned-imports config below).
    - `ERA` — eradicate commented-out code (a frequent LLM
      artifact).
    - `ARG` — unused function arguments.
    - `RSE` — `raise X` over `raise X()`; enforces `raise ... from
      ...` discipline.
    - `PT` — pytest-style anti-patterns.
    - `FURB` (Refurb) — modern-Python refactor hints.
    - `SLOT` — `__slots__` discipline on tuple/str subclasses.
    - `ISC` — implicit string concatenation (lint-level; complements
      `reportImplicitStringConcatenation`).
    - `T20` (flake8-print) — bans `print` and `pprint` (paired with
      §"Structured logging" and the AST check
      `check-no-write-direct` for `sys.stdout/stderr.write`).
    - `S` (flake8-bandit) — security anti-patterns; catches
      `pickle.loads`, `subprocess` with `shell=True`, `eval`,
      `exec`, etc.

    Note on category arithmetic: 11 (v011 baseline) + 16 (v012
    additions: TRY FBT PIE SLF LOG G TID ERA ARG RSE PT FURB
    SLOT ISC T20 S) = 27 total categories.
  - `[tool.ruff.lint.pylint]` sets `max-args = 6`,
    `max-positional-args = 6`, `max-branches = 10`,
    `max-statements = 30`. Both arg-count gates are enforced; see
    "Complexity thresholds".
  - `[tool.ruff.lint.flake8-tidy-imports]` sets
    `ban-relative-imports = "all"` and a banned-imports list:
    - `abc.ABC`, `abc.ABCMeta`, `abc.abstractmethod` — structural
      interfaces use `typing.Protocol` instead; see §"Type safety —
      Inheritance and structural typing."
    - `pickle`, `marshal`, `shelve` — arbitrary-code-execution
      surface on `load()`; livespec uses JSON / JSONC for all
      serialization.
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
`pytest-icdiff`. Uv-managed per v024 via `pyproject.toml`
`[dependency-groups.dev]`.

See **PROPOSAL.md §"Testing approach"** for the canonical test-tree
layout (mirroring `.claude-plugin/scripts/livespec/`, `.claude-plugin/scripts/bin/`, and
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
  `.claude-plugin/scripts/bin/*.py` wrapper (excluding `_bootstrap.py`) matches the
  exact 6-statement shebang-wrapper shape (see "Shebang-wrapper
  contract" below).

### Property-based testing for pure modules

Pure Result-returning modules (`livespec/parse/` and
`livespec/validate/`) are mandatory targets for property-based
testing via `hypothesis` (HypothesisWorks/hypothesis, MPL-2.0;
uv-managed per v024, NOT vendored). PBT generates many input
shapes and checks invariants the test author may not have
imagined; coverage verifies execution but PBT verifies behavior.

Rules:

- `hypothesis` and `hypothesis-jsonschema` (MIT) are uv-managed
  (per v024) via `pyproject.toml` `[dependency-groups.dev]` as
  test-time deps (same packaging convention as `pytest`,
  `pytest-cov`, `pytest-icdiff`). They are NOT vendored in
  `_vendor/` because they are not imported by
  `.claude-plugin/scripts/livespec/**` at user-runtime.
- Each test module under `tests/livespec/parse/` and
  `tests/livespec/validate/` MUST declare at least one
  `@given(...)`-decorated test function.
- For schema-driven validators, `hypothesis-jsonschema` provides
  auto-generated strategies from the schema's JSON Schema
  definition; tests SHOULD use this rather than hand-authoring
  `@composite` strategies.
- Hand-authored `@composite` strategies are permitted where the
  schema doesn't fully express the input space (e.g., free-form
  text fields).

Enforced by AST check `check-pbt-coverage-pure-modules`: walks
every test module under `tests/livespec/parse/` and
`tests/livespec/validate/`; verifies at least one function in the
module is decorated with `@given(...)` (from `hypothesis`).

### Mutation testing as release-gate

Mutation testing via `mutmut` (MIT; uv-managed per v024, NOT
vendored) runs on a release-gate schedule (CI release branch
only; not per-commit; not part of the `just check` aggregator).

Rules:

- `mutmut` is uv-managed (per v024) via `pyproject.toml`
  `[dependency-groups.dev]` as a release-gate dep.
- `just check-mutation` runs `mutmut run` against
  `livespec/parse/` and `livespec/validate/` (the pure modules
  where mutation testing is most informative); reports kill rate.
- **Threshold:** ≥80% mutation kill rate on `livespec/parse/`
  and `livespec/validate/`. The 80% figure is initial guidance;
  first real measurement against shipping code may surface a
  different appropriate value, in which case the threshold is
  adjusted via a new propose-change cycle.
- Per-commit CI does NOT invoke `just check-mutation` (too slow);
  a dedicated release-tag CI workflow runs it on tagged commits.
- The `just check` aggregator does NOT include `check-mutation`.

**Bootstrap discipline (v013 M3).** Before first release-tag run,
a `.mutmut-baseline.json` file is committed at the repo root
recording the mutation-kill-rate measurement at initial adoption.
Shape:

```json
{
  "measured_at": "<UTC ISO-8601 seconds>",
  "kill_rate_percent": <float>,
  "mutants_surviving": <int>,
  "mutants_total": <int>,
  "baseline_reason": "<one-line explanation of the initial measurement context>"
}
```

`pyproject.toml`'s `[tool.mutmut]` `threshold` is set to 80;
each subsequent release-tag run compares the measured rate
against `min(baseline.kill_rate_percent - 5, 80)` — i.e., the
ratchet accepts at most a 5-point regression relative to
baseline while also enforcing the absolute 80% ceiling once
baseline exceeds it. Once a release-tag run measures sustained
≥80% kill rate, a new propose-change cycle deprecates
`.mutmut-baseline.json` (content retained for history); the
effective threshold collapses to the static 80%.

**Failure output (v013 M3).** `just check-mutation` MUST emit
to stderr a structured JSON summary when the threshold fails,
containing:

```json
{
  "threshold_percent": <float>,
  "kill_rate_percent": <float>,
  "surviving_mutants": [
    {"file": "livespec/parse/jsonc.py", "line": 42, "mutation_kind": "BinOp_replacement"},
    {"...": "..."}
  ]
}
```

The implementation mechanism inside the `just` recipe (mutmut
CLI invocation, output parsing, JSON emission) is implementer
choice under the architecture-level constraints.

---

## Code coverage

Coverage is measured by `coverage.py` via `pytest-cov`:

- **100% line + branch coverage** is mandatory across the whole Python
  surface in `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and
  `<repo-root>/dev-tooling/**`. No tier split. `_vendor/` is excluded.
  `.claude-plugin/scripts/bin/` is included because `_bootstrap.py` carries real logic
  (Python-version check + sys.path setup) AND the 6-statement wrapper bodies
  themselves carry the `bootstrap()` call + the `raise SystemExit(main())`
  dispatch, all of which are real executable lines that v011 K3 brings
  under the same 100% gate via dedicated `tests/bin/test_<cmd>.py`
  files (see "Wrapper coverage" rule below). NO `# pragma: no cover`
  is applied to wrapper bodies; NO `[tool.coverage.run] omit` for
  `.claude-plugin/scripts/bin/`.
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
  to a no-op returning exit `0`. The import triggers the
  6-statement wrapper body (version check via
  `_bootstrap.bootstrap()`, package import,
  `raise SystemExit(main())`) under coverage.py's tracer,
  registering every statement as covered. The wrapper-shape
  6-statement rule is preserved unchanged (the optional blank
  line between the imports and `raise SystemExit(main())` is
  tolerated by `check-wrapper-shape`'s AST-lite walker, which
  operates on the AST module body rather than raw line text;
  see v016 P5 disposition in `deferred-items.md`'s
  `static-check-semantics` entry); the meta-test
  `tests/bin/test_wrappers.py`
  continues to verify that shape in parallel to the per-wrapper
  coverage tests.

---

## Keyword-only arguments

All user-defined callables in livespec's scope (`.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, `<repo-root>/dev-tooling/**`) MUST accept every
parameter as keyword-only. Call-site ambiguity over positional
order is eliminated by construction: reading `foo(name="alice",
age=30)` unambiguously tells the reader which value is which,
without cross-referencing the function signature.

Rules:

- Every `def` MUST place a lone `*` as its first parameter (or,
  for methods, immediately after `self` / `cls`) so that every
  subsequent parameter is in `kwonlyargs`.
- Every `@dataclass` decorator MUST include the full strict-dataclass
  triple: `frozen=True, kw_only=True, slots=True` (Python 3.10+).
  - `frozen=True` — prevents reassigning attributes after
    construction.
  - `kw_only=True` — generated `__init__` is keyword-only; no
    positional construction ambiguity.
  - `slots=True` — uses `__slots__` storage instead of `__dict__`;
    attribute-name typos at access time raise `AttributeError`
    rather than silently creating new attributes; ~30% per-instance
    memory savings.

  No livespec design relies on `__weakref__` (broken by
  `slots=True`) or multiple inheritance with non-slots classes
  (forbidden by §"Type safety — Inheritance and structural typing").
  The triple is therefore a pure win for livespec.
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
  - **ROP-chain DSL callbacks.** Functions whose name appears as a
    positional argument to a Railway-Oriented-Programming chain
    method (`.bind`, `.map`, `.alt`, `.lash`, `.apply`,
    `.bind_result`, `.bind_ioresult`) of a `dry-python/returns`
    container are exempt from the `*`-separator rule. The library
    invokes these callbacks positionally with the unwrapped
    `Success` / `Failure` value, and ROP composition is treated as
    a small DSL: callbacks receive exactly one positional value
    (the unwrapped track payload), so positional-order ambiguity
    — the rule's stated motivation — does not arise. Functions
    qualify only when their name is referenced as an `ast.Name`
    positional argument to one of these methods within the same
    file as the def-site; lambda expressions are unaffected
    (they're not `def`s). The dataclass-triple rule (`frozen=True,
    kw_only=True, slots=True`) stays strict for every dataclass,
    including any used inside a ROP chain.
  - **Protocol method definitions.** Methods declared inside a
    class whose direct-parent base is `Protocol` are exempt from
    the `*`-separator rule. A `Protocol` class is a structural
    type-system surface — it documents the shape of an external
    API (typically third-party) so livespec call-sites can
    type-check against it. The actual implementor is rarely a
    livespec-authored function; `cast("MyProtocol", third_party_obj)`
    is the standard construction pattern. Constraining the
    Protocol's method signatures to keyword-only would force
    livespec call-sites to use kwarg form for parameters whose
    names are dictated by the third-party implementation
    (e.g., structlog's `BoundLogger.<level>` accepts the message
    as the positional `event` parameter; renaming to a livespec-
    chosen kwarg name would break runtime behavior). The exemption
    applies ONLY to methods defined inside `class X(Protocol):`
    (or `class X(Protocol[T])` parametric Protocols); it does NOT
    extend to subclasses of livespec-defined Protocols, helper
    `def`s adjacent to a Protocol class, or factory functions that
    return a Protocol instance.

Enforced by `just check-keyword-only-args` (AST): every
`ast.FunctionDef` and `ast.AsyncFunctionDef` under scope MUST have
`args.args` empty after `self` / `cls` (all declared parameters in
`args.kwonlyargs`), with the per-file ROP-DSL exemption applied to
defs referenced positionally in `.bind` / `.map` / `.alt` /
`.lash` / `.apply` / `.bind_result` / `.bind_ioresult` calls;
every `@dataclass` decorator MUST carry `frozen=True`,
`kw_only=True`, AND `slots=True` keyword arguments.

## Structural pattern matching

`match` statements destructuring livespec-authored classes MUST
use keyword patterns, not positional patterns. Concrete form:
`case Foo(x=x, y=y)` (keyword) rather than `case Foo(x, y)`
(positional). This eliminates the need for `__match_args__` on
any livespec class — the class pattern binds attributes by name,
reading directly from the instance's `.x` / `.y`.

Rules:

- Livespec-authored classes (anything under `.claude-plugin/scripts/livespec/**`,
  `<repo-root>/dev-tooling/**`, or `.claude-plugin/scripts/bin/**`) MUST NOT declare
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
from typing_extensions import assert_never  # per v013 M1 uniform-import discipline

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
    case _:
        assert_never(result)
```

The outer `IOFailure(...)` uses positional destructure (permitted —
`IOFailure` is from `dry-python/returns`). The inner
`HelpRequested(text=text)` uses keyword destructure. `HelpRequested`
declares no `__match_args__`. The trailing `case _: assert_never(result)`
is mandatory per §"Type safety — Exhaustiveness"; if a future variant
of `result` is added but no `case` arm handles it, the
`assert_never` call becomes a type error at this dispatch site.

The `sys.stdout.write(text)` call in the `HelpRequested` arm is
permitted per the `check-no-write-direct` exemption for supervisor
`main()` functions in `livespec/commands/**.py`.

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
  - **stdout is reserved** for documented contracts (the doctor
    static-phase findings JSON per PROPOSAL.md; the
    `HelpRequested` text path per K7 / J7). Mechanical
    enforcement: ruff `T20` (flake8-print) bans `print` and
    `pprint`; AST check `check-no-write-direct` bans
    `sys.stdout.write` and `sys.stderr.write` everywhere
    EXCEPT three designated surfaces:
    1. `bin/_bootstrap.py` — pre-livespec-import version-check
       error message (the only legitimate `sys.stderr.write`
       site outside supervisor scope; structlog has not yet
       been configured at this point).
    2. Supervisor `main()` functions in `livespec/commands/**.py`
       — `sys.stdout.write` permitted for documented stdout
       contracts: `HelpRequested.text` per K7 / J7;
       `bin/resolve_template.py`'s resolved-path single-line
       output per K2; any future supervisor-owned stdout
       contract. The exemption is per-supervisor (the
       function named `main` at module top-level), NOT per-
       helper inside commands/**.
    3. `livespec/doctor/run_static.py::main()` — write the
       `{"findings": [...]}` JSON to stdout per the doctor
       static-phase output contract.

    All other output goes through structlog (which writes JSON
    to stderr).

### Bootstrap

`.claude-plugin/scripts/livespec/__init__.py` calls `structlog.configure(...)` exactly
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
| `0` | Success. Also covers intentional `--help` output: a `-h` / `--help` request is not an error and exits with `0` via the `HelpRequested` supervisor pattern-match path (see the `HelpRequested` class definition later in this §"Exit code contract" section, and §"Structural pattern matching" → "HelpRequested example" for the supervisor's match form). |
| `1` | Script-internal failure (unexpected runtime error; likely a bug). |
| `2` | Usage error: bad flag, wrong argument count, malformed invocation. |
| `3` | Input or precondition failed: referenced file/path/value missing, malformed, or in an incompatible state. |
| `4` | Schema validation failed (retryable): LLM-provided JSON payload does not conform to the wrapper's input schema. Per-sub-command SKILL.md prose SHOULD inspect exit `4`, treat it as a retryable malformed-payload signal, and SHOULD re-invoke the template prompt with error context. v1 intentionally does not specify an exact retry count. Distinct from exit `3` (precondition failure) so the LLM can classify failures deterministically without parsing stderr. |
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

      Retryable: the sub-command's SKILL.md prose SHOULD inspect
      exit code 4, treat it as a malformed-payload signal, and SHOULD
      re-invoke the template prompt with error context. v1 does
      not specify an exact retry count. Exit code 4 (distinct from
      PreconditionError's exit 3) lets the LLM deterministically
      classify retryable vs non-retryable exit-3-class failures
      without parsing stderr.
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
  literally in `.claude-plugin/scripts/livespec/doctor/static/__init__.py`'s static
  registry. JSON slug `out-of-band-edits` ↔ module filename
  `out_of_band_edits.py` ↔ check_id `doctor-out-of-band-edits`. There
  is no conversion loop; the registry's import statements name both
  forms.
- Executables (`bin/*.py`) carry the shebang `#!/usr/bin/env python3`,
  the executable bit, and conform to the shape below.

### Shebang-wrapper contract

Each file under `bin/*.py` (except `_bootstrap.py`) MUST consist of
exactly the following shape, comprising 6 statements (no other
statements, and no other lines beyond the optional single blank
line between the import block and the `raise SystemExit(main())`
statement):

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
Coverage.py's tracer records every statement of the 6-statement
body as covered without any `# pragma: no cover` application; the
wrapper-shape contract is preserved strictly. Shape conformance is
enforced by `check-wrapper-shape` (AST-lite) and verified in parallel
by the `test_wrappers.py` meta-test. The optional blank line
between the import block and `raise SystemExit(main())` does NOT
count as a statement for the 6-statement contract, and
`check-wrapper-shape` explicitly permits its presence (v016 P5);
the algorithm is codified in `deferred-items.md`'s
`static-check-semantics` entry.

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

The 6-statement wrapper shape and `_bootstrap.py`'s body are
jointly covered by:

- `check-wrapper-shape`: every file under `bin/` matching `*.py`
  except `_bootstrap.py` MUST match the 6-statement wrapper
  template (the optional blank line between the import block and
  `raise SystemExit(main())` is permitted; see the
  `static-check-semantics` deferred entry for the exact
  algorithm).
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
- `.mise.toml` pins the non-Python binaries (`uv`, `just`,
  `lefthook`) listed in PROPOSAL.md §"Runtime dependencies —
  Developer-time dependencies." Per v024, the Python dev packages
  in that same PROPOSAL.md section are uv-managed via
  `pyproject.toml` `[dependency-groups.dev]` (single source of
  truth still lives in PROPOSAL.md per v013 C2; this document
  does NOT duplicate the enumeration to eliminate drift risk).

This eliminates drift across invocation surfaces. A developer
reproduces CI locally by running `just check`.

`just check` runs every check target sequentially, **continues on
failure**, and exits non-zero if any target failed (listing which
targets failed at the end). This matches CI's `fail-fast: false`
matrix; one local run reproduces full CI feedback.

**First-time bootstrap:** `mise install`, then `uv sync --all-groups`
(per v024; resolves Python dev deps into a project-local `.venv` and
commits `uv.lock`), then `just bootstrap`. The `bootstrap` target
runs `lefthook install` (registers the pre-commit and pre-push hooks
with git) and any other one-time setup. Without `just bootstrap`,
lefthook hooks do not fire on commit.

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
| `just check-imports-architecture` | Import-Linter: declarative `[tool.importlinter]` contracts in `pyproject.toml` express purity (`parse/` + `validate/` don't import `io/` or effectful APIs) and layered architecture (no circular imports). Replaces v011's planned `check-purity` + `check-import-graph`. The third v012 L15a contract (raise-discipline import surface) was retracted in v017 Q3; raise-discipline is raise-site-enforced only by `check-no-raise-outside-io` below. |
| `just check-private-calls` | AST: no cross-module calls to `_`-prefixed functions defined elsewhere. |
| `just check-global-writes` | AST: no module-level mutable state writes from functions. |
| `just check-rop-pipeline-shape` | AST: every class decorated with `@rop_pipeline` carries exactly one public method (the entry point); other methods are `_`-prefixed; dunders aren't counted. Enforces the Command / Use Case Interactor pattern at the class level. |
| `just check-supervisor-discipline` | AST: `sys.exit` / `raise SystemExit` only in `bin/*.py` (incl. `_bootstrap.py`). |
| `just check-no-raise-outside-io` | AST: raising of `LivespecError` subclasses (domain errors) at runtime restricted to `io/**` and `errors.py`. Raising bug-class exceptions (TypeError, NotImplementedError, AssertionError, etc.) permitted anywhere. **Raise-site enforcement is the sole enforcement point for the raise-discipline (v017 Q3 retraction of the v012 L15a import-surface delegation).** Import-Linter does NOT cover the import surface for `livespec.errors`; type-annotation and `match`-pattern imports of `LivespecError` subclasses are permitted anywhere they are referenced. |
| `just check-no-except-outside-io` | AST: catching exceptions outside `io/**` permitted only in supervisor bug-catchers (top-level `try/except Exception` in `main()` of `commands/*.py` and `doctor/run_static.py`). |
| `just check-public-api-result-typed` | AST: every public function (per `__all__` declaration; see `check-all-declared`) returns `Result` or `IOResult` per annotation, OR carries a railway-lifting decorator that wraps the source-level annotation (`@impure_safe(...)` lifts to `IOResult`, `@safe(...)` lifts to `Result` — both are recognized by their decorator name regardless of whether they appear bare or as a parameterized call). Documented exemptions for functions that legitimately do NOT return a railway carrier because they construct artifacts the railway then composes around: (a) supervisors at the side-effect boundary — `main()` in `commands/**.py` and `doctor/run_static.py`; (b) the `build_parser` argparse factory in `commands/**.py` AND `doctor/run_static.py`; (c) the `make_validator` validator factory in `validate/**.py` (returns `TypedValidator[T]` whose `__call__` returns `Result`); (d) the `get_logger` structlog facade factory in `io/structlog_facade.py`; (e) the `compile_schema` fastjsonschema facade factory in `io/fastjsonschema_facade.py`; (f) the `rop_pipeline` class decorator in `types.py`. Package-private helper modules (filename matching `_*.py`, e.g., `commands/_seed_helpers.py`) are skipped — their public surface is consumed only within the same directory by callers that ARE on the railway, and the helpers themselves are typically pure render/format functions that cannot fail. |
| `just check-schema-dataclass-pairing` | AST (three-way walker per v013 M6): for every `schemas/*.schema.json`, verifies a paired dataclass at `schemas/dataclasses/<name>.py` (the `$id`-derived name) AND a paired validator at `validate/<name>.py` exists; every listed schema field matches the dataclass's Python type; vice versa in all three walks. Drift in any direction fails. |
| `just check-main-guard` | AST: no `if __name__ == "__main__":` in `.claude-plugin/scripts/livespec/**`. |
| `just check-wrapper-shape` | AST-lite: `bin/*.py` (except `_bootstrap.py`) conforms to the 6-statement shebang-wrapper contract (optional blank line between the import block and `raise SystemExit(main())` permitted). |
| `just check-keyword-only-args` | AST: every `def` in livespec scope uses `*` as first separator (all params keyword-only); every `@dataclass` declares the strict-dataclass triple `frozen=True, kw_only=True, slots=True`. Exempts Python-mandated dunder signatures and `__init__` of Exception subclasses that forward to `super().__init__(msg)`. |
| `just check-match-keyword-only` | AST: every `match` statement's class pattern resolving to a livespec-authored class binds via keyword sub-patterns (`Foo(x=x)`), not positional (`Foo(x)`). Third-party library class destructures (`returns`-package types) are permitted positionally. |
| `just check-no-inheritance` | AST: forbids `class X(Y):` in `.claude-plugin/scripts/livespec/**` where `Y` is not in the **direct-parent allowlist** `{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict}`. `LivespecError` subclasses are NOT acceptable bases (v013 M5 tightening enforces leaf-closed intent); `class RateLimitError(UsageError):` is rejected even though `UsageError` is itself a `LivespecError` subclass. Codifies flat-composition direction; `LivespecError` itself remains an open extension point. |
| `just check-assert-never-exhaustiveness` | AST: every `match` statement in scope MUST terminate with `case _: assert_never(<subject>)`. Conservative scope (every match, regardless of subject type). |
| `just check-newtype-domain-primitives` | AST: walks `schemas/dataclasses/*.py` and function signatures; verifies field annotations matching canonical field names (`check_id`, `run_id`, `topic`, `spec_root`, `schema_id`, `template`, `author` / `author_human` / `author_llm`, `version_tag`) use the corresponding `livespec/types.py` NewType (`CheckId`, `RunId`, `TopicSlug`, `SpecRoot`, `SchemaId`, `TemplateName`, `Author`, `VersionTag`). Note: the `template_root` field in DoctorContext is the resolved-directory `Path` and uses raw `Path`, NOT `TemplateName` — the L8 mapping is field-name keyed, and `template_root` doesn't match `template`. |
| `just check-all-declared` | AST: every module under `.claude-plugin/scripts/livespec/**` declares a module-top `__all__: list[str]`; every name in `__all__` is defined in the module. |
| `just check-no-write-direct` | AST: bans `sys.stdout.write` and `sys.stderr.write` calls in `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, `<repo-root>/dev-tooling/**`. Three exemptions: `bin/_bootstrap.py` (pre-import version-check stderr); supervisor `main()` functions in `livespec/commands/**.py` (any documented stdout contract — HelpRequested per K7, resolve_template path per K2, etc.); `livespec/doctor/run_static.py::main()` (findings JSON stdout). Pairs with ruff `T20` which bans `print` / `pprint`. |
| `just check-pbt-coverage-pure-modules` | AST: each test module under `tests/livespec/parse/` and `tests/livespec/validate/` declares at least one `@given(...)`-decorated test function. |
| `just check-claude-md-coverage` | Every directory under `scripts/` (excluding `_vendor/` subtree), `tests/`, and `dev-tooling/` contains a `CLAUDE.md`. |
| `just check-heading-coverage` | Validates that every `##` heading in every spec tree — main + each sub-spec under `SPECIFICATION/templates/<name>/` — has a corresponding entry in `tests/heading-coverage.json` whose `spec_root` field matches the heading's tree. Tolerates an empty `[]` array pre-Phase-6, before any spec tree exists; from Phase 6 onward emptiness is a failure if any spec tree exists. |
| `just check-vendor-manifest` | Validates `.vendor.jsonc` against a schema that forbids placeholder strings — every entry has a non-empty `upstream_url`, a non-empty `upstream_ref`, a parseable-ISO `vendored_at`, and the `shim: true` flag is present on `typing_extensions` and absent on every other entry. |
| `just check-no-direct-tool-invocation` | grep: `lefthook.yml` and `.github/workflows/*.yml` only invoke `just <target>`. |
| `just check-tools` | Verify every pinned tool is installed at the pinned version — both mise-pinned binaries (`uv`, `just`, `lefthook`) and uv-managed Python deps from `pyproject.toml` `[dependency-groups.dev]` per v024. |
| `just check-tests` | `pytest`. |
| `just check-coverage` | `pytest --cov` with 100% line+branch threshold. |
| `just e2e-test-claude-code-mock` | v014 N9: E2E integration test against the `minimal` template via the livespec-authored mock at `<repo-root>/tests/e2e/fake_claude.py`. Deterministic; mock replaces only the Claude Agent SDK / LLM layer (wrappers always run for real). Runs the common pytest suite in mock mode, including the intentionally mock-only deterministic retry-on-exit-4 scenario. Part of `just check`. |
| `just check-prompts` | v018 Q5: per-prompt verification tier. Runs tests under `<repo-root>/tests/prompts/<template>/` using a small deterministic prompt-QA harness scope-distinct from `tests/e2e/fake_claude.py`. Each test case provides a prompt-response pair; harness replays the response; test asserts on structured output at the corresponding input-schema boundary (`seed_input.schema.json`, `proposal_findings.schema.json`, `revise_input.schema.json`) PLUS declared semantic properties per the `prompt-qa-harness` deferred entry. Every built-in template's four REQUIRED prompts ship ≥ 1 prompt-QA test. Part of `just check`. |

Alternate-cadence targets (NOT in `just check`):

| Target | Purpose |
|---|---|
| `just e2e-test-claude-code-real` | v014 N9: E2E integration test against the `minimal` template via the real `claude-agent-sdk`. Requires `ANTHROPIC_API_KEY`. Common pytest suite with the mock target; env var `LIVESPEC_E2E_HARNESS=mock\|real` selects the executable, and pytest markers / `skipif` annotations suppress intentionally mock-only cases such as deterministic retry-on-exit-4 coverage in real mode. CI triggers: `merge_group` (pre-merge via merge queue), `push` to `master` (every master commit), `workflow_dispatch` (manual). Locally invokable. |

Release-gate targets (run on release-tag CI workflow only; NOT
included in `just check`; NOT run per-commit):

| Target | Purpose |
|---|---|
| `just check-mutation` | `mutmut` mutation testing against `livespec/parse/` and `livespec/validate/`. Threshold: ratchet against `.mutmut-baseline.json` (v013 M3) bounded by absolute 80% ceiling; emits structured JSON surviving-mutants report on failure. |
| `just check-no-todo-registry` | Rejects any `test: "TODO"` entry in `tests/heading-coverage.json` (v013 M8). Release-gate only; paired with `check-mutation` on release-tag CI workflow. Ensures every release ships with full rule-test coverage. |

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
  explicitly excluded; the exclusion extends to any `fixtures/`
  subtree at any depth under `tests/` — e.g., `tests/fixtures/`
  AND `tests/e2e/fixtures/` per v014 N9 both fall under this
  rule), AND
- `<repo-root>/dev-tooling/`

MUST contain a `CLAUDE.md` file describing the local constraints an
agent working in that directory must satisfy. One optional
`tests/fixtures/CLAUDE.md` at the fixtures root (and similarly
one optional `tests/e2e/fixtures/CLAUDE.md` per v014 N9) is
permitted (they can explain the read-only discipline) but not
required, and subdirectories under any `fixtures/` tree are
never required to carry `CLAUDE.md`.

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
