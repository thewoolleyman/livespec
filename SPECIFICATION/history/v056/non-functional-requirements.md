# Non-functional requirements — `livespec`

This document MUST be read alongside `spec.md`, `contracts.md`, `constraints.md`, and `scenarios.md`. It enumerates the project's non-functional requirements: invariants on the development environment, repository tooling, build and test discipline, contributor workflow, and any other internal-facing concerns that are NOT visible at the user-facing CLI/API surface. The five top-level `##` sections below mirror the same four-file boundary the user-facing spec uses (`Spec` / `Contracts` / `Constraints` / `Scenarios`) plus a `Boundary` preamble, so contributors and agents apply the same categorization rule when landing new content.

## Boundary

`non-functional-requirements.md` covers concerns of the form "how the project is built, tested, and maintained". The top-level sections below mirror the user-facing spec files. The decision rule for each section:

- `## Spec` — process *intent and behavior*: what testing means in this project, what TDD means here, what "done" means, how `livespec` applies to itself. Mirrors `spec.md`'s role.
- `## Contracts` — *external interfaces and contributor-facing toolchain*: the specific tools the project depends on, the contributor-facing invocation surface (`just check`), and any wire-level test/coverage data file shapes. Mirrors `contracts.md`'s role.
- `## Constraints` — *architectural invariants on the implementation*: code patterns, layout rules, thresholds, style rules. Mirrors `constraints.md`'s role.
- `## Scenarios` — *Gherkin-style scenarios for contributor-facing workflows*. Mirrors `scenarios.md`'s role. Empty initially; populated when specific contributor flows need to be pinned.

The boundary against the user-facing spec files:

- User-facing intent or behavior MUST stay in `spec.md`.
- User-facing wire contracts MUST stay in `contracts.md`.
- Constraints whose violation an end user could observe MUST stay in `constraints.md` (runtime versions, exit-code contracts, dependency envelopes, structured-logging schemas, vendored-library discipline, NLSpec discipline including BCP14 and heading-taxonomy rules).
- User-facing scenarios MUST stay in `scenarios.md`.

The trickiest boundary is `constraints.md` ↔ `non-functional-requirements.md`: constraints whose violation an end user could observe MUST stay in `constraints.md`; constraints that bind only the project's contributors MUST move here.

## Spec

This section's sub-sections enumerate the project's contributor-facing process intent and behavior — the analogue of `spec.md`'s role for the user-facing surface.

### Test-Driven Development discipline

This section codifies how the Test-Driven Development discipline is applied at the keyboard, day to day, in Python.

**Authoring rhythm.** Red and Green happen in the editor; only the cohesive unit of value (Red+Green together for a feature/bugfix; or a behavior-preserving structural change for a refactor) commits. `just check` runs as the pre-commit hook and a failing test rejects the commit — the discipline aligns with that: keep the Red phase in the editor, run it, observe it fail for the right reason, then write Green and commit the pair.

**Running a Red test in isolation.** Use pytest's `-k` or test-id syntax to run exactly the new test: `uv run pytest tests/livespec/<area>/test_<module>.py::<test_name>`. Confirm the failure message names the missing behavior. Unhelpful Reds (`ImportError`, `ModuleNotFoundError`, `NameError`, `TypeError` on call shape) MUST be fixed before proceeding to Green.

**Writing Green: the minimum that turns Red green.** A stub that returns `Failure(<error>)` for the specific inputs the test exercises is often enough. Resist anticipating downstream tests. Once Green, run `just check-coverage` (full suite + 100% line+branch in one pass per v039 D1).

**Per v039 D4 (proactive coverage discipline).** Before staging the Green amend, run `just check-coverage-incremental --paths <impl_path>`. The incremental tool finishes in seconds and surfaces coverage gaps (including defensive branches) BEFORE the Green amend triggers the full pre-commit aggregate. The full `check-coverage` aggregate runs at pre-commit as the load-bearing safety net; the incremental tool exists to make the failure mode rare.

**Refactor cycle (independent, structure-only).** A refactor commit is reviewable on its own terms: (1) confirm the suite is green pre-refactor; (2) identify and characterize any coverage gaps in the area; (3) apply the structural change, running `just check` after each meaningful step — tests MUST stay green throughout; (4) commit with a `refactor:` message prefix. If a test goes red mid-refactor, behavior changed — stop and reapply as a Red-Green-driven feature or restart with better characterization.

**Exception clauses (exhaustive list):**

| Change | Exception category |
|---|---|
| Rename a file via grep (no behavior change; existing tests follow) | Mechanical migration |
| Add `# noqa: E501` to a long line | Configuration-only |
| Add `__all__: list[str] = []` to a module | Type-only / convention |
| Update `CLAUDE.md` text | Documentation-only |
| Bump `pytest` minor version in `pyproject.toml` | Configuration-only (version pin)* |
| Introduce a `NewType` alias and propagate annotations | Type-only |
| Extract a helper function with no behavior change | Pure refactor |

\* If a config bump surfaces a new lint violation in covered code, the violation IS a behavior change and test-first reapplies — the failing-rule output is the Red signal. "I couldn't think of a failing test smaller than the implementation" is NOT an exception.

### Testing approach

Every Python source file under `livespec/`, `bin/`, and `dev-tooling/checks/` MUST have a paired test file at the mirrored path under `tests/`, except: (a) **private-helper modules** — `.py` files whose filename starts with `_` and is NOT `__init__.py` (e.g., `_seed_railway_emits.py`); these are covered transitively through the public function that imports them. (b) **Pure-declaration modules** — files whose AST contains no `FunctionDef` / `AsyncFunctionDef` anywhere (no module-level or class-level functions); covers boilerplate `__init__.py`, pure dataclass declarations, value-object modules, and the `LivespecError` hierarchy — none have testable behavior independent of their consumers. The `bin/_bootstrap.py` shebang preamble has its own special-cased test at `tests/bin/test_bootstrap.py`. The `dev-tooling/checks/tests_mirror_pairing.py` script enforces the binding mechanically and runs in the `just check` aggregate. Per-file line+branch coverage MUST be 100% (enforced by `dev-tooling/checks/per_file_coverage.py`). Coverage is computed under `pytest --cov` with `pyproject.toml`'s `[tool.coverage.run]` settings active.

The v034 D2-D3 Red→Green replay contract gates every `feat:` / `fix:` commit: the Red commit stages exactly one new test file and zero impl files; the Green amend stages the impl that turns the test green; the commit-msg hook verifies the temporal Red→Green order via reflog inspection plus test-file SHA-256 checksum.

**Prompt-QA tier.** Above the unit-test layer (which gates 100% per-file line+branch coverage on `livespec/`, `bin/`, `dev-tooling/checks/`), every built-in template's REQUIRED prompts (`prompts/seed.md`, `prompts/propose-change.md`, `prompts/revise.md`, `prompts/critique.md`) are exercised by per-prompt tests under `tests/prompts/<template>/`. Each test loads one or more fixture files capturing a prompt-input + canonical-LLM-response pair, validates the canonical response against its named JSON Schema (`seed_input.schema.json`, `proposal_findings.schema.json`, `revise_input.schema.json`), and asserts every declared semantic-property name in the fixture against per-template assertion functions. The prompt-QA tier is invoked via `just check-prompts` (included in `just check`); each built-in template MUST ship at least one prompt-QA test per REQUIRED prompt (4 prompts × 2 built-in templates = 8 minimum cases). The prompt-QA tier is scope-distinct from the v014 N9 end-to-end harness at `tests/e2e/` (which drives wrappers via the Claude Agent SDK surface) — the prompt-QA harness performs no LLM round-trip and no wrapper invocation, only deterministic replay-and-assert against canonical fixtures. Per the unit-tier coverage scope codified above, `tests/prompts/` is NOT measured for line+branch coverage; the prompt-QA tier provides additional confidence but does not contribute to the 100% gate.

Tests MUST NOT mutate files under `tests/fixtures/`; test-local filesystem state MUST use pytest's `tmp_path` fixture. Tests MUST NOT require network access; impure wrappers are stubbed via `monkeypatch.setattr`. Tests MUST be independent of execution order; no module-level mutable state that a prior test could leave behind. `@pytest.mark.parametrize` is the preferred idiom for tabulated inputs. Assertions use pytest's default assertion-introspection; no third-party assertion library is used. `pytest-icdiff` is enabled via `pyproject.toml`; it produces structured diffs on failure, aiding LLM consumption of test output.

The meta-test `tests/test_meta_section_drift_prevention.py` verifies every top-level (`##`) heading in each specification file has at least one corresponding entry in `tests/heading-coverage.json`. The meta-test `tests/bin/test_wrappers.py` verifies every `bin/*.py` wrapper (excluding `_bootstrap.py`) matches the canonical 5-statement shebang-wrapper shape.

#### Property-based testing for pure modules

Pure `Result`-returning modules (`livespec/parse/` and `livespec/validate/`) are mandatory targets for property-based testing via `hypothesis` (uv-managed per v024, NOT vendored). PBT generates many input shapes and checks invariants the test author may not have imagined.

- `hypothesis` and `hypothesis-jsonschema` (MIT) MUST be uv-managed via `pyproject.toml` `[dependency-groups.dev]`. They are NOT vendored in `_vendor/`.
- Each test module under `tests/livespec/parse/` and `tests/livespec/validate/` MUST declare at least one `@given(...)`-decorated test function.
- For schema-driven validators, `hypothesis-jsonschema` provides auto-generated strategies from the schema's JSON Schema definition; tests SHOULD use this rather than hand-authoring `@composite` strategies.

Enforced by AST check `check-pbt-coverage-pure-modules`.

#### Mutation testing as release-gate

Mutation testing via `mutmut` (MIT; uv-managed per v024, NOT vendored) runs on a release-gate schedule (CI release branch only; not per-commit; NOT part of `just check`).

- `just check-mutation` runs `mutmut run` against `livespec/parse/` and `livespec/validate/` and reports kill rate.
- **Threshold:** ≥80% mutation kill rate. The 80% figure is initial guidance; first real measurement against shipping code may surface a different appropriate value, updated via a new propose-change cycle.
- Before first release-tag run, a `.mutmut-baseline.json` file MUST be committed at the repo root recording the kill-rate measurement at initial adoption. Subsequent tag runs compare against `min(baseline.kill_rate_percent - 5, 80)`.
- `just check-mutation` MUST emit to stderr a structured JSON summary when the threshold fails, containing `threshold_percent`, `kill_rate_percent`, and a `surviving_mutants` array with `file`, `line`, and `mutation_kind` fields.

### Definition of Done

A `livespec` change MUST satisfy the Definition of Done (above) before merge. Bootstrap-minimum: `just check` aggregate passes, paired tests exist for every new source file, the CLAUDE.md coverage check passes, the heading-coverage check passes against `tests/heading-coverage.json`, and the v034 D3 replay-hook trailers are present on `feat:` / `fix:` commits.

The full DoD widens via Phase 7 dogfooded propose-change cycles when individual DoD items surface as needing more rigorous specification.

### Self-application bootstrap exception

The Phase 0–6 imperative window closed at the Phase 6 seed commit and remains closed. Every mutation to this `SPECIFICATION/` MUST flow through `/livespec:propose-change` → `/livespec:revise` against the appropriate spec target. Hand-edits to spec files outside the propose-change/revise loop are forbidden and would be caught by `dev-tooling/checks` plus the doctor static phase.
## Contracts

This section's sub-sections enumerate the project's contributor-facing external interfaces and toolchain — the analogue of `contracts.md`'s role for the user-facing surface.

### Toolchain pins

The project's contributor-facing toolchain MUST be pinned via the version managers below. End users install only the shipped plugin runtime; per `constraints.md` §"End-user runtime dependencies", end users do NOT need any of these tools.

Non-Python binary tools — `uv`, `just`, `lefthook`, and any other binary the dev workflow requires — MUST pin via `.mise.toml`. Python itself and Python dev dependencies MUST pin via `uv` against `pyproject.toml`'s `[dependency-groups.dev]` (lockfile: `uv.lock`).

The contributor toolchain's roles:

- `mise` — manages versions of `uv`, `just`, `lefthook`, and any future binary additions.
- `uv` — manages Python + Python dev dependencies.
- `just` — task runner; the canonical entry point for every dev-tooling invocation. See §"Enforcement-suite invocation" below.
- `lefthook` — git hook manager registering pre-commit, commit-msg, and pre-push behaviors.
- `pytest` (+ `pytest-cov`, `pytest-xdist`, `pytest-icdiff`) — test runner.
- `hypothesis` (+ `hypothesis-jsonschema`) — property-based testing for pure modules.
- `ruff` — linter and formatter; rule set codified under §"Linter rule set".
- `pyright` — type checker (configured strict); rule set codified under §"Typechecker rule set".
- `mutmut` — release-gate mutation testing (NOT part of `just check`).

The `dev-tooling/checks/no_direct_tool_invocation.py` AST check enforces that `lefthook.yml` and CI workflows MUST delegate to `just <target>` and MUST NOT shell out to underlying tools directly.

### Enforcement-suite invocation

The enforcement suite is **invocation-surface-agnostic**. Every check is a `just` target; pre-commit, pre-push, CI, and manual invocation are consumers. Linux is the primary platform; macOS is a supported developer platform. No Windows support.

The canonical target list is maintained in the justfile. Key groupings:

- **Per-commit aggregate (`just check`):** runs every check below sequentially, continues on failure, exits non-zero if any failed.
- **Standard per-commit checks:** `check-lint`, `check-format`, `check-types`, `check-complexity`, `check-imports-architecture`, `check-private-calls`, `check-global-writes`, `check-rop-pipeline-shape`, `check-supervisor-discipline`, `check-no-raise-outside-io`, `check-no-except-outside-io`, `check-public-api-result-typed`, `check-schema-dataclass-pairing`, `check-main-guard`, `check-wrapper-shape`, `check-keyword-only-args`, `check-match-keyword-only`, `check-no-inheritance`, `check-assert-never-exhaustiveness`, `check-newtype-domain-primitives`, `check-all-declared`, `check-no-write-direct`, `check-pbt-coverage-pure-modules`, `check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`, `check-coverage`, `e2e-test-claude-code-mock`, `check-prompts`.
- **Alternate-cadence targets (NOT in `just check`):** `e2e-test-claude-code-real` (requires `ANTHROPIC_API_KEY`; runs on merge-queue, master push, and `workflow_dispatch`).
- **Release-gate targets (release-tag CI only; NOT in `just check`):** `check-mutation` (mutmut; ≥80% kill rate on `parse/` + `validate/`); `check-no-todo-registry` (rejects any `test: "TODO"` entry in `tests/heading-coverage.json`).
- **Mutating targets (opt-in, not in CI):** `just fmt` (`ruff format`), `just lint-fix` (`ruff check --fix`), `just vendor-update <lib>`.

**Invocation surfaces:**

- **Pre-commit and pre-push (local):** `lefthook.yml` runs `just check`.
- **CI (GitHub Actions):** one job per check via a matrix strategy with `fail-fast: false`, each calling `just <target>`. The `jdx/mise-action@v2` step installs pinned tools.
- **Manual (developer at the shell):** `just <target>` — same targets hooks and CI use.


## Constraints

This section's sub-sections enumerate the architectural invariants on the project's implementation — the analogue of `constraints.md`'s role for the user-facing surface, but bound to contributor-facing concerns.

### Developer-tooling layout

`justfile` is the single source of truth for every dev-tooling invocation. `lefthook.yml` and CI workflows MUST delegate to `just <target>` and MUST NOT shell out to underlying tools directly (enforced by `dev-tooling/checks/no_direct_tool_invocation.py`). Tool versions for non-Python binaries (`uv`, `just`, `lefthook`) pin via `.mise.toml`; Python and Python packages pin via `uv` against `pyproject.toml`'s `[dependency-groups.dev]`. Lefthook pre-commit runs `just lint-autofix-staged` as its first step, which applies `ruff check --fix` + `ruff format` to the staged Python files only and re-stages them in place; this lets auto-fixable lint trivia (import ordering, formatting) get fixed without forcing a full pre-commit retry. The autofix step runs BEFORE the v034 D3 commit-msg replay hook computes the Red commit's test-file SHA-256 checksum, so the recorded checksum reflects post-autofix bytes; the Green amend stages impl files only (not the test), preserving the test-file-byte-identical invariant the replay hook enforces.

The canonical `just check` aggregate is enumerated in the justfile recipe. The aggregate runs sequentially with continue-on-failure semantics and exits non-zero if any target fails. This matches CI's `fail-fast: false` matrix; one local run reproduces full CI feedback.

**First-time bootstrap:** `mise install`, then `uv sync --all-groups` (resolves Python dev deps into a project-local `.venv` and commits `uv.lock`), then `just bootstrap`. The `bootstrap` target runs `lefthook install` (registers the pre-commit and pre-push hooks with git) and any other one-time setup. Without `just bootstrap`, lefthook hooks do not fire on commit.

### Package layout

The plugin's Python surface lives under `.claude-plugin/scripts/`. The canonical directory tree is the directory itself; this file does not duplicate it.

The top-level layout has three roots:

- **`bin/`** — executable shebang-wrappers plus the shared `_bootstrap.py`. Each wrapper file MUST match the canonical 5-statement wrapper shape (plus an optional single blank line between the imports and `raise SystemExit(main())` per v016 P5). No logic. `chmod +x` MUST be applied.
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

#### Dataclass authorship

Each JSON Schema under `schemas/*.schema.json` MUST have a paired hand-authored `@dataclass(frozen=True, kw_only=True, slots=True)` at `schemas/dataclasses/<name>.py`. The dataclass and the schema are co-authoritative: the schema is the wire contract (validated at the boundary by `fastjsonschema`); the dataclass is the Python type threaded through the railway (`Result[<Dataclass>, ValidationError]` from each validator per the factory shape). Domain-meaningful field types MUST use the canonical `NewType` aliases from `livespec/types.py`.

- The file name MUST match the `$id`-derived snake_case dataclass name (e.g., `LivespecConfig` → `livespec_config.py`).
- Fields MUST match the schema one-to-one in name and Python type.
- `schemas/__init__.py` MUST re-export every dataclass name for convenient import.
- No codegen toolchain. No generator. Drift between schema, dataclass, and validator MUST be caught mechanically by `check-schema-dataclass-pairing` (three-way AST walker per v013 M6: schema ↔ dataclass ↔ validator).

#### Context dataclasses

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

#### CLI argument parsing seam

`argparse` MUST be the sole CLI parser and MUST live in `livespec/io/cli.py`. Rationale: `ArgumentParser.parse_args()` raises `SystemExit` on usage errors and `--help`; the 5-statement wrapper shape leaves no room for it; `check-supervisor-discipline` forbids `SystemExit` outside `bin/*.py`. Routing argparse through the impure boundary keeps the railway intact.

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

### Pure / IO boundary

Purity is enforced **structurally** by directory, not by per-file markers:

- **`livespec/parse/**` and `livespec/validate/**` are PURE.** Modules here MUST NOT import from: `livespec.io.*`, `subprocess`, filesystem APIs (`open`, `pathlib.Path.read_text`, `.read_bytes`, `.write_text`, `.write_bytes`, any `os.*` I/O function), `returns.io.*` (pure code uses `Result`, not `IOResult`), or `socket`/`http.*`/`urllib.*` (no network).
- **`livespec/io/**` is IMPURE.** Every function MUST be decorated with `@impure_safe` from `dry-python/returns`. Functions here are thin wrappers over one side-effecting operation each. `io/` also hosts thin typed facades over vendored libs whose surface types are not strict-pyright-clean.
- **Everything else** (`commands/`, `doctor/**`, `context.py`, `errors.py`) MAY call both pure and impure layers; these are composition layers.

`LivespecError` raise-sites are restricted to `livespec/io/` and `errors.py`. The `dev-tooling/checks/no_raise_outside_io.py` AST check enforces the raise-site discipline mechanically.

Validators MUST stay pure by accepting their schema as a parameter (factory shape). The schema dict is read from disk by an `io/` wrapper and passed in by the caller; `fastjsonschema.compile` is cached in the impure `io/fastjsonschema_facade.py` module-level cache keyed on the schema's `$id`. This separates "reading" (impure) from "checking" (pure).

Enforced by `check-imports-architecture` (Import-Linter contracts over `parse/` and `validate/` imports) and `check-no-raise-outside-io` (AST raise-site check).

#### Import-Linter contracts (minimum configuration)

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

### ROP composition

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

#### ROP pipeline shape

A class decorated with `@rop_pipeline` MUST carry exactly ONE public method (the entry point). Every other method MUST be `_`-prefixed (private). Dunder methods (`__init__`, `__call__`, etc., matching `^__.+__$`) are not counted toward the public-method quota.

The decorator is a runtime no-op (returns the decorated class unchanged) declared in `livespec.types`. AST enforcement lives in `dev-tooling/checks/rop_pipeline_shape.py`. The decorator serves as an AST marker for the static check and as documentation at the def-site.

Each pipeline class encapsulates one cohesive railway chain. Enforcing the shape prevents the public surface from drifting as new chain steps are added — agent-authored code that grows a second public method is caught at check time. Helper classes and helper modules (anything NOT carrying `@rop_pipeline`) are exempt and MAY export multiple public names.

The marker is a decorator rather than a base class because the `check-no-inheritance` allowlist is intentionally small (`{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict}`); adding `RopPipeline` to the allowlist would expand the open-extension-point set for an application pattern.

Enforced by `just check-rop-pipeline-shape`.

### Supervisor discipline

Each command's `main()` function MUST be the only place outside `livespec/io/` where `sys.exit` (or its `raise SystemExit(...)` shape inside `bin/`) MAY appear. The supervisor pattern-matches the final railway `IOResult` onto an exit code via `unsafe_perform_io` plus a `match` statement that ends in `case _: assert_never(unwrapped)` for exhaustiveness. The `dev-tooling/checks/supervisor_discipline.py` AST check enforces this shape.

The shebang-wrapper layer at `bin/<sub-command>.py` MUST conform to the canonical 5-statement shape: shebang → docstring → `from _bootstrap import bootstrap` → `bootstrap()` → `from livespec.<...> import main` → `raise SystemExit(main())`. The optional blank line between statements 4 and 5 is permitted per v016 P5.

Every supervisor MUST wrap its ROP chain body in one `try/except Exception` bug-catcher whose exclusive job is: (1) log the exception via `structlog` with full traceback and structured context (module, function, `run_id`); (2) return the bug-class exit code (`1`). This is the ONLY catch-all `except Exception` permitted in the codebase. `check-supervisor-discipline` enforces the scope: exactly one catch-all per supervisor; no catch-alls outside supervisors; no catch-alls swallow exceptions without logging and exit-1 return.

### Typechecker rule set

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

#### @override and assert_never import source

Both symbols MUST be imported uniformly from `typing_extensions`, not from stdlib `typing`, regardless of Python version. `typing_extensions` is vendored full upstream verbatim at tag `4.12.2` per v027 D1 at `.claude-plugin/scripts/_vendor/typing_extensions/__init__.py`. The upstream-canonical module name is retained so pyright's `reportImplicitOverride` recognizes the import path and `check-assert-never-exhaustiveness` recognizes the `Never`-narrowing signature. Uniform import discipline (`from typing_extensions import override, assert_never`) eliminates per-version conditionals.

#### Module API surface

Every module in `.claude-plugin/scripts/livespec/**` MUST declare a module-top `__all__: list[str]` listing the public API names. Public functions, public classes, and public `NewType` aliases belong in `__all__`; private helpers (single-leading-underscore prefix) MUST NOT appear in `__all__`. `__init__.py` files MAY declare `__all__` for re-export composition; every name listed MUST resolve in the module's namespace, including imported names.

Enforced by AST check `check-all-declared`: walks every module under `.claude-plugin/scripts/livespec/**`; verifies a module-level `__all__: list[str]` assignment exists; verifies every name in `__all__` is actually defined in the module (catches stale entries after a rename).

#### Domain primitives via NewType

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

#### Inheritance and structural typing

Class inheritance in `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**` is RESTRICTED. The AST check `check-no-inheritance` rejects any `class X(Y):` definition where `Y` is not in the **direct-parent allowlist**: `{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict}`. The rule is DIRECT-PARENT only; `LivespecError` subclasses (e.g., `UsageError`, `ValidationError`) are NOT acceptable bases for further subclassing (v013 M5). This enforces the flat-composition direction: `class RateLimitError(UsageError):` is rejected; `class RateLimitError(LivespecError):` is permitted.

Structural interfaces MUST be declared via `typing.Protocol`. `abc.ABC`, `abc.ABCMeta`, and `abc.abstractmethod` imports are banned via the ruff TID rule configuration.

The `@final` decorator (imported from `typing_extensions`) is OPTIONAL; the AST check is the source of truth. Authors MAY use `@final` as documentation-by-decorator for clarity.

#### Exhaustiveness

Every `match` statement in `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**` MUST terminate with `case _: assert_never(<subject>)` regardless of subject type. `assert_never` MUST be imported from `typing_extensions`.

When all variants of a closed-union subject are handled by preceding `case` arms, the residual type at the default arm is `Never` and pyright accepts the call. When a new variant is added without updating the dispatch site, the residual type narrows to the unhandled variant and `assert_never` becomes a type error. The conservative scope (every `match`, regardless of subject type) is preferred over a precise scope (only closed-union subjects) because false positives are cheap and the simpler check is more maintainable.

Enforced by AST check `check-assert-never-exhaustiveness`.

#### Vendored-lib type-safety integration

- **`fastjsonschema`** exposes generated callables typed as `Callable[[Any], Any]`. The thin facade at `livespec/io/fastjsonschema_facade.py` MUST expose a fully-typed surface: `compile_schema(schema_id: str, schema: dict) -> Callable[[dict], Result[dict, ValidationError]]`. The facade holds a module-level `_COMPILED: dict[str, Callable] = {}` keyed on `$id` to dedupe compiles across calls. `functools.lru_cache` cannot be used directly (dicts are unhashable), and a module-level cache would trip `check-global-writes` in pure code — the cache lives in the impure facade layer and is explicitly exempted.
- **`structlog`** logger calls are dynamically typed. The thin facade at `livespec/io/structlog_facade.py` MUST expose typed logging functions: `info(message: str, **kwargs: object) -> None`, etc.
- **`dry-python/returns`**: `Result` and `IOResult` types are used pervasively. The facade pattern does not apply uniformly; pyright strict plus the seven strict-plus diagnostics (especially `reportUnusedCallResult`) are the guardrails.

### Linter rule set

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

### Comment discipline

Comments in first-party trees (`justfile`, `lefthook.yml`, `.github/workflows/*.yml`, `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, `dev-tooling/**`, `tests/**`) MUST follow two rules:

**Rule 1 — WHY-not-WHAT.** A comment MUST explain WHY a section, recipe, or block exists when the WHY is non-obvious to a future reader: a hidden constraint, a subtle invariant, a workaround for a specific tooling bug, or behavior that would surprise a reader. A comment MUST NOT explain WHAT the code does — well-named identifiers, BCP14 normative prose, and the surrounding spec already convey WHAT. If removing the comment would not confuse a future reader who can read the code, the comment MUST be deleted.

**Rule 2 — No historical-bookkeeping references.** Comments MUST NOT cite version numbers (`v033`, `v034 D2`), decision IDs (`Per v036 D1`, `v037 D1`), phase numbers (`Phase 4`), cycle numbers (`cycle 117`), commit references (`this commit`, `the previous PR`), or any other temporal/historical bookkeeping marker. The audit trail of decisions lives in `SPECIFICATION/history/vNNN/`, `git log`, the v034 D3 replay-hook trailers, and per-revision proposed-change files; duplicating it in source-file comments creates bit-rot risk and reader-archeology cost. Comments MUST state the live constraint in present tense without reference to when, why-historically, or by-which-decision the constraint was adopted.

**Scope exemptions.** The two rules DO NOT apply to: (a) `_vendor/**` (vendored upstream code; comments are inherited as-is); (b) the YAML front-matter and Markdown body of files under `SPECIFICATION/` (the spec IS the historical record; cross-references to other spec sections are acceptable); (c) `SPECIFICATION/history/vNNN/` snapshots (immutable); (d) `archive/` (frozen historical artifacts). Inside in-scope trees, the per-line escapes `# noqa: <CODE> — <reason>` (per §"Linter and formatter") and `# type: ignore[<code>] — <reason>` (per §"Typechecker constraints") are already WHY-formed and remain compliant.

**Retroactive cleanup.** As part of accepting this proposal, every comment in the in-scope trees that violates Rule 1 or Rule 2 MUST be either rewritten to a WHY-form (when the comment carries a still-relevant non-obvious WHY) or deleted (when the comment is pure historical bookkeeping or pure WHAT). Reference checklist for the cleanup pass: every match for the regex `(?i)\b(v\d{3}\s*[A-Z]\d|per v\d{3}|phase\s+\d+|cycle\s+\d+|this commit|the previous (commit|PR))\b` in the in-scope trees MUST be reviewed and either rewritten or deleted.

**Enforcement.** A new `dev-tooling/checks/comment_no_historical_refs.py` script MUST be added to the `just check` aggregate (alongside `check-comment-line-anchors`) that greps every in-scope file for the historical-reference regex above and exits non-zero with structured findings naming each violation site. The check is categorized as a python-code check per §"Pre-commit step ordering" so it is skipped when zero `.py` files change. Rule 1 (WHY-not-WHAT) is judgment-based and MUST NOT be mechanically enforced — code review is the gate. Rule 2 is mechanically grep-able and MUST be enforced by the new check.

### Complexity thresholds

The following complexity thresholds MUST be satisfied by all first-party `.py` files under `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**`. **Waivers are not permitted.** A function or file that cannot meet a threshold MUST be decomposed; no escape hatch exists.

- **Cyclomatic complexity ≤ 10** per function (ruff `C901`).
- **Function body ≤ 30 logical lines** (ruff `PLR0915`).
- **File ≤ 200 LLOC (SOFT) / ≤ 250 LLOC (HARD).** LLOC excludes blank lines, comment-only lines, and docstrings. Files at 201-250 LLOC pass the per-commit `check-complexity` target with a structured warning emitted to stderr; `just check` stays green but the file is flagged for refactoring. Files above 250 LLOC fail the check (exit 1). The `dev-tooling/checks/file_lloc.py` script enforces both tiers. The `check-no-lloc-soft-warnings` release-gate (NOT in `just check`; fires on release-tag CI only) rejects any file in the 201-250 LLOC soft band before a release tag.
- **Max nesting depth ≤ 4** (ruff PLR rule).
- **Arguments ≤ 6** per function, counted TWO ways, both enforced: total args (ruff `PLR0913`, `max-args = 6`) AND positional args (ruff `PLR0917`, `max-positional-args = 6`). Functions needing more parameters MUST be refactored to accept a dataclass.

Enforced by `just check-complexity`.

### Code coverage thresholds

**100% line + branch coverage** is mandatory across the whole Python surface in `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**`. No tier split. `_vendor/` is excluded. `bin/` is included because `_bootstrap.py` carries real logic (version check + sys.path setup) AND the 5-statement wrapper bodies carry the `bootstrap()` call + `raise SystemExit(main())` dispatch — all executable lines covered by dedicated `tests/bin/test_<cmd>.py` files. NO `# pragma: no cover` is applied to wrapper bodies; NO `[tool.coverage.run].omit` for `bin/`.

`pyproject.toml`'s `[tool.coverage.run]` MUST set `branch = true` and `source` to include both the `livespec` package and the `bin/` directory. `[tool.coverage.report]` MUST set `fail_under = 100`, `show_missing = true`, `skip_covered = false`. Enforced by `just check-coverage`.

**No line-level pragma escape hatch.** `# pragma: no cover` comments are forbidden anywhere in covered trees. The ONLY coverage exclusions permitted are the four structural patterns in `[tool.coverage.report].exclude_also`: `if TYPE_CHECKING:`, `raise NotImplementedError`, `@overload`, and `case _:` (the assert_never exhaustiveness arm). These are block-level patterns recognized by coverage.py without per-instance annotation:

- `if TYPE_CHECKING:` guards are matched by the `exclude_also` pattern.
- `sys.version_info` gates in `bin/_bootstrap.py` are covered by dedicated `tests/bin/test_bootstrap.py` tests that monkeypatch `sys.version_info` to exercise both branches.
- `case _: assert_never(<subject>)` arms are structurally unreachable by the spec mandate (every `match` MUST terminate with the pattern; `check-assert-never-exhaustiveness` enforces the body shape). The `case _:` exclude_also pattern catches the entire arm.

A targeted check (`# pragma: no cover` literal match) in `dev-tooling/checks/` rejects any commit that introduces the comment in covered code.

**Wrapper coverage.** Each wrapper has a matching `tests/bin/test_<cmd>.py` that imports the wrapper and catches `SystemExit` via `pytest.raises`, with `monkeypatch` stubbing the target `main` to a no-op returning exit `0`. The import triggers the 5-statement wrapper body under coverage.py's tracer.

### Keyword-only arguments

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

### Structural pattern matching

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

### CLAUDE.md coverage

Every directory under:

- `.claude-plugin/scripts/` (with the entire `_vendor/` subtree explicitly excluded), AND
- `<repo-root>/tests/` (with the entire `fixtures/` subtree explicitly excluded at any depth — e.g., `tests/fixtures/` AND `tests/e2e/fixtures/` per v014 N9), AND
- `<repo-root>/dev-tooling/`

MUST contain a `CLAUDE.md` file describing the local constraints an agent working in that directory must satisfy.

Each `CLAUDE.md`:

- States the directory's purpose in one sentence.
- Lists directory-local rules (e.g., "this directory is pure; no imports from `io/`").
- Links to the global style doc for global rules rather than duplicating.
- Is kept short (typically under 50 lines); it's a local crib sheet, not a full reference.

One optional `tests/fixtures/CLAUDE.md` (and `tests/e2e/fixtures/CLAUDE.md`) is permitted but not required; subdirectories under any `fixtures/` tree are never required to carry `CLAUDE.md`. The `_vendor/` carve-out prevents forcing `CLAUDE.md` inside vendored libs.

Enforced by `just check-claude-md-coverage`.


### Commit and merge discipline

Every commit on every branch and every commit landing on `master` MUST conform to Conventional Commits 1.0:

```
<type>[(scope)][!]: <subject>

[optional body]

[optional footers]
```

Valid types: `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `revert`. Breaking changes MUST be indicated by `!` after the type/scope OR a `BREAKING CHANGE:` footer (or both).

`master` accepts only **rebase-merge**. Squash-merge and merge-commit strategies are forbidden at the GitHub repo-settings level (`allow_squash_merge: false`, `allow_merge_commit: false`, `allow_rebase_merge: true`). Combined with `required_linear_history: true`, every commit on `master` is a per-cycle commit landed individually with its own Conventional Commits subject — including `!` breaking-change markers — intact. release-please reads each commit's type directly without squash flattening or PR-title cross-check.

The local commit-msg hook MUST validate the Conventional Commits subject prefix as the FIRST step, BEFORE the v034 D3 Red→Green replay dispatch. Non-conformant subjects MUST exit non-zero regardless of staged shape. The validation regex pins the canonical type set: `^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)(\([^)]+\))?!?: .+`. The hook MUST emit a structured diagnostic naming the canonical type set when rejecting.

A CI workflow validating PR titles for Conventional Commits conformance is OPTIONAL and advisory only (PR titles are NOT load-bearing under rebase-merge since per-commit subjects land on `master`). The OPTIONAL workflow MAY be added separately if the open-PR list becomes noisy with non-Conventional titles.

The plugin's release versioning is auto-managed via `release-please` from per-commit Conventional Commits per `contracts.md` §"Plugin versioning". The Conventional Commits mandate is the load-bearing input that makes release-please's auto-bump mechanism deterministic.

## Scenarios

Contributor-facing Gherkin scenarios — the analogue of `scenarios.md`'s role for the user-facing surface. Empty initially; populated via propose-change cycles when specific contributor flows need to be pinned (e.g., first-time-contributor onboarding, post-`/livespec:revise` cleanup).
