# Constraints — `livespec`

This file enumerates the architecture-level constraints `livespec` MUST satisfy.

## Constraint scope

The constraints in this file MUST be satisfied by:

- Every Python module bundled with the plugin under `.claude-plugin/scripts/livespec/**`.
- Every Python shebang-wrapper executable under `.claude-plugin/scripts/bin/*.py`, including the shared `_bootstrap.py` module.
- Every Python module or script under `<repo-root>/dev-tooling/**`.

The constraints DO NOT apply to:

- Vendored third-party code under `.claude-plugin/scripts/_vendor/**`. Vendored libs ship at pinned upstream versions per the v018 Q3 / v026 D1 vendoring procedure and are EXEMPT from livespec's own style rules.
- User-provided Python modules loaded via custom-template extension hooks (e.g., `template.json`'s `doctor_static_check_modules`). Extension code is the extension author's responsibility; livespec's enforcement suite MUST NOT scope to it. Extension authors MUST satisfy only the calling-API contract — the `TEMPLATE_CHECKS` export shape, the `CheckRunFn` signature, and the `Finding` payload shape, all defined inside `livespec/`. Inside an extension module, the author MAY use any library, architecture, and patterns of their choosing; livespec MUST NOT impose requirements beyond invocability per the contract.

Tests under `<repo-root>/tests/` MUST comply unless a test explicitly exercises a non-conforming input, in which case the non-conformance MUST be declared in a docstring at the top of the fixture.

Constraints in this file MUST be those whose violation an end user could observe — runtime versions, exit-code contracts, dependency envelopes, structured-logging schemas, vendored-library discipline, and NLSpec discipline (BCP14 + heading taxonomy). Contributor-facing invariants — code patterns, layout rules, coverage thresholds, linter/typechecker rule sets, and dev-toolchain pins — MUST live in `non-functional-requirements.md` instead.

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

- **`returns`** (dry-python/returns, BSD-3-Clause) — ROP primitives: `Result`, `IOResult`, `@safe`, `@impure_safe`, `flow`, `bind`, `Fold.collect`, `lash`. NO pyright plugin is vendored: pyright has no plugin system by design (microsoft/pyright#607) and dry-python/returns explicitly does not support pyright (dry-python/returns#1513). The seven strict-plus diagnostics in `[tool.pyright]` (especially `reportUnusedCallResult = "error"`) are the load-bearing guardrails against silent `Result` / `IOResult` discards.
- **`fastjsonschema`** (horejsek/python-fastjsonschema, MIT) — JSON Schema Draft-7 validator.
- **`structlog`** (hynek/structlog, BSD-2 / MIT dual) — structured JSON logging.
- **`jsoncomment`** (MIT, derivative work) — vendored as a minimal hand-authored shim per v026 D1. The shim at `.claude-plugin/scripts/_vendor/jsoncomment/__init__.py` faithfully replicates jsoncomment 0.4.2's `//` line-comment and `/* */` block-comment stripping semantics. The canonical upstream (`bitbucket.org/Dando_Real_ITA/json-comment`) was sunset by Atlassian and no live git mirror exists; the shim's `LICENSE` carries verbatim MIT attribution to Gaspare Iengo (citing jsoncomment 0.4.2's `COPYING` file). Used by `livespec/parse/jsonc.py` as a comment-stripping pre-pass over stdlib `json.loads`.
- **`typing_extensions`** (python/typing_extensions, PSF-2.0) — vendored full upstream verbatim at tag `4.12.2` per v027 D1. Provides `override`, `assert_never`, `Self`, `Never`, `TypedDict`, `ParamSpec`, `TypeVarTuple`, `Unpack` plus the variadic-generics symbols transitively required at import time by `returns`, `structlog`, `fastjsonschema` on Python 3.10. The verbatim PSF-2.0 `LICENSE` is shipped at `_vendor/typing_extensions/LICENSE`.

The cross-repo work-item dependency machinery (`livespec_runtime.cross_repo`) is deliberately absent from this set: the orchestrator that uses `livespec_runtime.cross_repo` owns its own vendoring or dependency declaration per its own specification (physical removal of the still-present vendored tree and its `.vendor.jsonc` entry is Phase-2 implementation work).

The shared `bin/_bootstrap.py:bootstrap()` function MUST insert BOTH the bundle's `scripts/` directory AND the bundle's `scripts/_vendor/` directory into `sys.path`. Adding `scripts/` makes the `livespec` package resolvable (`from livespec.commands.seed import main`); adding `scripts/_vendor/` makes each vendored top-level package resolvable under its natural name (`from returns.io import IOResult`, `import structlog`, etc.).

### Vendoring procedure

Source-tree population is governed by two paths:

- **Re-vendoring** of upstream-sourced libs (`returns`, `fastjsonschema`, `structlog`, `typing_extensions`) MUST go through `just vendor-update <lib>` — the only blessed mutation path. The recipe fetches the upstream ref, copies it under `_vendor/<lib>/`, preserves `LICENSE`, and updates `.vendor.jsonc`'s recorded ref.
- **Initial vendoring** is a one-time MANUAL procedure (the v018 Q3 exception, executed once per livespec repo when the vendored tree is first established): `git clone` the upstream repo at a working ref into a throwaway directory, `git checkout <ref>` matching `.vendor.jsonc`'s `upstream_ref`, copy the library's source tree under `_vendor/<lib>/`, copy the upstream `LICENSE` verbatim to `_vendor/<lib>/LICENSE`, record the lib's provenance (`upstream_url`, `upstream_ref`, `vendored_at` ISO-8601 UTC), delete the throwaway clone, and smoke-test that the wrapper bootstrap imports the vendored lib successfully. The exception resolves the circularity that `just vendor-update` invokes Python through `livespec.parse.jsonc` (which imports `jsoncomment`); the recipe cannot run before `jsoncomment` exists.
- **Shim libs** are livespec-authored and DO NOT go through `just vendor-update`. The `jsoncomment` shim is the sole shim post-v027; it is widened (one-line edit per added feature) or replaced with a full upstream vendoring via a new propose-change cycle. `.vendor.jsonc` records the shim's upstream attribution ref (for provenance) and a `shim: true` flag.

Direct edits to `_vendor/` files are forbidden for upstream-sourced libs — any such edit is treated as drift and caught at code review. The "never edit `_vendor/`" rule applies only to upstream-sourced libs; shim updates go through normal code-review.

`.vendor.jsonc` records `{upstream_url, upstream_ref, vendored_at}` per lib; for shims, additionally `shim: true` and the provenance ref from which the shim's `LICENSE` was derived.

`_vendor/` is EXEMPT from livespec's own style rules, type-checking strictness, coverage measurement, and CLAUDE.md coverage enforcement per `## Constraint scope` above.
## Renderer non-vendoring

Livespec MUST NOT vendor rendering binaries or runtimes for any diagram language (no bundled `plantuml.jar`, no Java-runtime detection, no Graphviz dependency, no Mermaid CLI bundle), AND MUST NOT itself invoke any diagram renderer. Mermaid — livespec's standard and default diagram format — renders natively wherever markdown is viewed (GitHub, IDEs, previewers), so it needs no livespec-side rendering at all.

An author who needs a diagram type Mermaid lacks (per `spec.md` §"Template manifest") renders it with an alternate tool such as PlantUML or Graphviz OUTSIDE livespec and commits the resulting image as an opaque asset. Livespec MUST NOT detect, recommend, install, or invoke any such renderer; the project owns that tool entirely.

This non-vendoring-and-non-invoking constraint preserves the "Python 3.10 is the sole end-user runtime dependency" invariant in §"End-user runtime dependencies": no diagram tool is ever a livespec dependency — any alternate renderer is the author's own choice, exercised outside livespec.

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
- Hyphens appear only in JSON wire contracts (`check_id` values like `"doctor-out-of-band-edits"`) and in sub-command names in prose (e.g., `propose-change`, `prune-history`).
- The slug↔module-name mapping for doctor-static checks is recorded literally in `.claude-plugin/scripts/livespec/doctor/static/__init__.py`'s static registry.
- Executables (`bin/*.py`) MUST carry the shebang `#!/usr/bin/env python3`, the executable bit, and conform to the 5-statement wrapper shape.

### Shebang-wrapper contract

Each file under `bin/*.py` (except `_bootstrap.py`) MUST consist of exactly 5 top-level AST statements (the shebang is a comment, not a statement) plus an optional single blank line between the import block and the `raise SystemExit(main())` statement:

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

Every `##` heading in a **template-declared NLSpec file at a spec-tree root** MUST have a corresponding entry in `tests/heading-coverage.json`. The registry maps `(spec_root, spec_file, heading)` triples to pytest test identifiers. The `spec_root` field is the repo-root-relative path to the spec tree's root (main spec = `SPECIFICATION`; sub-specs = `SPECIFICATION/templates/<name>`). The `spec_file` field is the `spec_root`-relative path to the spec file containing the heading (e.g., `spec.md`, `contracts.md`). The `heading` field is the exact `##` heading text. Each entry's `test` field is a pytest node identifier (`<path>::<function>`) OR the literal `"TODO"`; `"TODO"` entries MUST also carry a non-empty `reason` field.

A registry entry MAY additionally carry an OPTIONAL `clauses` array binding individual behavior clauses under its heading to the scenarios that exercise them. Each `clauses[]` element is an object `{"gap_id": "<gap-id>", "scenario": "<scenarios.md H2 section name>"}`. The `gap_id` field MUST hold the stable identifier the shared `dev-tooling/spec_clauses.py` extractor derives for the clause (the first 8 lowercase-base32 characters of `sha256(spec_file \x1f heading_path \x1f rule_text)`). The `scenario` field MUST name a live `scenarios.md` `##` (H2) section heading, written with or without the leading `## `; a `scenario` that does not resolve to a live `scenarios.md` H2 section does NOT count as a link. The `clauses` array is OPTIONAL and backward-compatible: an entry without it is unchanged, and the `heading_coverage` check ignores the key. The `clauses[]` link is consumed by the `behavior_scenario_link` check (see `non-functional-requirements.md` §"Behavior-clause-to-scenario link check") and is maintained under the §"Self-application" co-edit discipline in `spec.md`.

The `dev-tooling/checks/heading_coverage.py` script enforces the binding mechanically at `just check` time. Per tree, the check walks **only the template-declared NLSpec files at the tree root** — for the `livespec` template, the four files `spec.md`, `contracts.md`, `constraints.md`, and `scenarios.md`. The check does NOT recurse into `proposed_changes/`, `history/`, `templates/<name>/history/`, or any other subdirectory; it does NOT include the skill-owned `README.md` at the tree root. Boilerplate headings such as `## Proposal: ...` in propose-change files, `## Decision and Rationale` in revision records, and per-version snapshot headings under `history/v*/` are out of scope for the registry and are NOT counted by the check.

The check fails in three directions:

1. **Uncovered heading** — a `(spec_root, spec_file, heading)` triple appears in some template-declared spec file but no matching registry entry exists. Diagnostic: `spec heading missing coverage entry`.
2. **Orphan registry entry** — a registry entry's `(spec_root, spec_file, heading)` triple does not match any heading in any template-declared spec file (heading was renamed or removed without updating the registry). Diagnostic: `registry entry orphaned — no matching spec heading`.
3. **Missing `reason` on a `TODO` entry** — entry carries `test: "TODO"` but no non-empty `reason` field. Diagnostic: `TODO registry entry missing reason`.

Within `scenarios.md`, every `##` heading — including those beginning with the `Scenario:` prefix — MUST have its own registry entry; scenarios are tracked **granularly**, one entry per scenario. Multiple scenario entries MAY map to the **same** test node id — a many-to-one mapping is expected, since one integration-tier test commonly exercises several related scenarios. The per-spec-file rule test that validates scenario *format* does NOT substitute for these per-scenario coverage entries. (`Scenario:`-prefixed headings outside `scenarios.md`, if any, remain out of registry scope.)

An empty `[]` array is a failure if any spec tree exists.

**Scenario headings require integration-tier-or-above coverage.** For a `tests/heading-coverage.json` entry whose `spec_file` is `scenarios.md`, the mapped `test` node id MUST resolve to a test at the **integration tier or above** (middle or top of the test pyramid), never a unit-tier test — a scenario describes user-observable behavior, which a unit test does not exercise. Operationally, one of the following MUST hold: (a) the node-id path component begins with one of the integration-tier prefixes enumerated in the per-repo `[tool.livespec_dev_tooling.scenario_tiers]` allowlist (e.g., `tests.e2e.…`, `tests.integration.…`, `tests.consumer.…`, `tests.prompts.…`); OR (b) the resolved test function carries an explicit `pytest.mark.integration` (or stronger) marker. A `TODO` entry remains allowed during transition, but its `reason` MUST explicitly acknowledge the tier requirement. This sub-rule applies ONLY to `scenarios.md`; headings in `spec.md`, `contracts.md`, and `constraints.md` MAY be exercised by unit-tier tests. The `heading_coverage` check enforces this with a distinct `scenario heading mapped to unit-tier test` diagnostic; the `[tool.livespec_dev_tooling.scenario_tiers]` allowlist is read per consumer repo so each declares its own integration-test directory convention without amending the shared check.

## Reference discipline

Two paired invariants govern how `SPECIFICATION/` files reference other content and how source code references spec content. Both invariants exist to keep references stable under heading renames, file moves, and revise-pass content reshuffling; both ROT SILENTLY without the static-phase check codified below.

### `SPECIFICATION/`-to-`SPECIFICATION/` references

Within a single `SPECIFICATION/` tree, files MAY cite peer files and peer headings via the canonical `<filename>.md §"<Heading text>"` form. Same-file anchor references using Markdown link syntax (link text plus a `#<heading-slug>` URL fragment) remain governed by `doctor-anchor-reference-resolution`.

### Forbidden: references OUTSIDE the same `SPECIFICATION/` tree

A `SPECIFICATION/<file>.md` MUST NOT reference any of the following EXCEPT via the allowlist mechanism in §"Allowlist mechanism":

- Sibling-repo spec files (e.g., `livespec/SPECIFICATION/contracts.md` from a non-livespec tree, or `livespec-dev-tooling/SPECIFICATION/...` from a non-dev-tooling tree).
- Implementation-tree files (`livespec/doctor/`, `livespec_dev_tooling/checks/`, etc.).
- Work-item identifiers (`li-fgqgnk`, `li-tvi7lm`, etc.) — these live in the orchestrator's work-item store, not in the spec.
- Epic phase identifiers (`Phase G.2`, `Phase G.4`, etc.) — these are external work-tracking terminology.
- GitHub PR numbers, branch names, commit SHAs, or other version-control identifiers.
- URLs pointing to GitHub, Slack, Notion, or any other external system that may go stale.

The invariant exists because a `SPECIFICATION/` tree MUST be readable standalone — a reader with only the tree's files in hand MUST be able to resolve every reference. Cross-repo coordination contracts inherently need to name parent-spec content; the allowlist mechanism is the supported escape hatch, NOT an open license to scatter cross-repo citations through prose.

### Forbidden: `§"…"` citations from source code

Source code (Python modules under the implementation tree, test modules under `tests/`, skill prose under `skills/<name>/SKILL.md`) MUST NOT cite spec sections via the `§"…"` form or any analogous formal anchor reference. The static-phase `doctor-no-spec-section-citations-in-code` check (codified at §"Doctor static-phase enforcement" below) scans the implementation tree for the pattern and fails on any match.

Source code MAY reference spec files at the FILE level (e.g., `Per SPECIFICATION/contracts.md, this module implements the runtime contract`), but MUST NOT name specific headings within those files. The file-level reference is stable across heading renames; the heading-level reference is not.

### Allowlist mechanism

Cross-repo coordination requires that sibling-spec trees reference parent-spec content (e.g., a consuming library's spec references a heading in a parent repo's `SPECIFICATION/` tree). The allowlist mechanism MUST be declared as a typed block in `.livespec.jsonc` under a top-level `external_references` key. The block below is ILLUSTRATIVE of the general shape, not a fixed roster:

```jsonc
{
  "external_references": {
    "parent-repo": [
      "SPECIFICATION/non-functional-requirements.md §\"Cross-repo coordination — pin-and-bump\"",
      "SPECIFICATION/non-functional-requirements.md §\"Shared code sync — livespec-dev-tooling\""
    ],
    "sibling-library": [
      "SPECIFICATION/contracts.md §\"DependsOnEntry union\""
    ]
  }
}
```

The top-level key under `external_references` is a sibling-repo short name (per the §"Sibling discovery" convention in `livespec-dev-tooling/SPECIFICATION/contracts.md`, once that contract is itself promoted into `livespec`'s spec or remains a cross-reference under this allowlist). The value is an array of `<file> §"<heading>"` strings. Any `§"…"` reference to a sibling-repo spec heading MUST appear in the allowlist; references to non-`SPECIFICATION/` paths in sibling repos remain absolutely forbidden.

### Doctor static-phase enforcement

Two new static-phase doctor checks MUST land alongside this invariant:

- `doctor-no-cross-spec-reference` — scans every `SPECIFICATION/<file>.md` for the `§"…"` pattern; for each match, resolves the target heading. Same-tree matches pass; allowlist-declared external matches pass; everything else fires `fail` with the file path, line number, and the suggested allowlist entry.

- `doctor-no-spec-section-citation-in-code` — scans every source file under the implementation tree (Python modules under `livespec/`, `livespec_dev_tooling/`, etc., and Markdown files under `skills/`) for the `§"…"` pattern. Any match fires `fail` with the file path, line number, and the offending citation.

Both checks MUST short-circuit on the first violation per the existing static-check discipline. The wrapper exit code follows the standard `3 = at least one fail Finding` mapping.

## BCP14 normative language

Spec-file prose MUST use BCP 14 (RFC 2119 + RFC 8174) requirement language: `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`, `OPTIONAL`. The keywords MUST be uppercase to be normative; lowercase use is non-normative descriptive prose. The `livespec`-template's NLSpec discipline doc enumerates BCP14 well-formedness rules in detail; this constraints file states only the meta-rule.

**Static-phase enforcement scope.** Doctor's static-phase `bcp14_keyword_wellformedness` check MUST detect the mixed-case form of `SHALL` (uppercase-S followed by lowercase characters) as the unambiguous-mismatch case — no descriptive English usage of the mixed-case form is realistic at sentence boundaries. Mixed-case `Must`, `Should`, and `May` MUST be deferred to the LLM-driven phase, where sentence-level context discriminates normative misuse from descriptive English (e.g., "May be empty" as data-shape description vs. a malformed normative "May implementations support X"). The static rule's first-violation short-circuit behavior MUST be preserved within the narrowed keyword set. The static rule's exemption from sub-trees (`history/`, `proposed_changes/`, `templates/`) and its single-top-level-`.md`-files-only walk MUST be preserved.


## Sub-command lifecycle mechanics

The deterministic file-shaping mechanics each sub-command's wrapper performs after the skill-prose layer assembles its payload. Wire-level CLI contracts (payload validation, exit-code semantics, path-relativity guards) live in `contracts.md` §"Sub-command wire contracts".

### `revise` file-shaping mechanics

After the skill assembles a `revise_input.schema.json`-conforming payload, the `bin/revise.py` wrapper performs deterministic file-shaping:

- (a) It MUST fail hard with `PreconditionError` (exit 3) when `<spec-target>/proposed_changes/` contains no in-flight proposal files (the skill-owned `proposed_changes/README.md` does not count).
- (b) It MUST fail hard with `UsageError` (exit 2) when the inbound `--revise-json` payload's `decisions[]` array is empty — a revise pass with zero decisions would produce a no-op cut and is forbidden; the schema `revise_input.schema.json` MUST encode this precondition with `minItems: 1` on `decisions[]` (paired with the corresponding dataclass under `livespec/schemas/dataclasses/` per the schema-dataclass-pairing invariant); together with clause (a), this ensures every successful revise cut represents at least one processed proposal.
- (c) Proposals are processed in YAML front-matter `created_at` creation-time order (oldest first), with lexicographic filename as tiebreaker; within each file, `## Proposal` sections are processed in document order.
- (d) Per v038 D1 (Statement B), a new `<spec-target>/history/vNNN/` is cut on every successful revise invocation — when at least one decision is `accept` or `modify`, the working-spec files named in those decisions' `resulting_files[]` are updated in place before the snapshot. Every resolved `resulting_files[].path` target MUST already exist as a regular file at `<spec-target>/<resulting_files[i].path>` before the wrapper writes to it; a non-existent target is a `PreconditionError` (exit 3) and the wrapper MUST emit a structured finding naming the missing target and abort before any write occurs. Creating new spec files via `resulting_files[]` is forbidden — new template-declared spec files are added through a future template-revision mechanism, not through revise; new sub-spec trees are added through a future seed-extension mechanism, not through revise. When every decision is `reject`, the new version's spec files are byte-identical copies of the prior version's spec files (rejection-flow audit trail).
- (e) On every cut, `<spec-target>/history/vNNN/` snapshots every template-declared spec file byte-identically as it stands post-update (or post-no-update, on all-reject).
- (f) Every processed proposal moves byte-identically from `<spec-target>/proposed_changes/<stem>.md` to `<spec-target>/history/vNNN/proposed_changes/<stem>.md` — the filename stem is preserved including any `-N` collision-disambiguation suffix per `spec.md` §"Proposed-change and revision file formats" filename-stem rule (v017 Q7).
- (g) Every processed proposal gets a paired `<stem>-revision.md` written to the same `history/vNNN/proposed_changes/` directory using the same stem.
- (h) After successful completion `<spec-target>/proposed_changes/` MUST contain exactly the in-flight proposal files whose canonical topic is NOT named in `decisions[]`; every proposal whose canonical topic IS named in `decisions[]` MUST have been moved to `<spec-target>/history/vNNN/proposed_changes/` per clauses (f) and (g). The skill-owned `proposed_changes/README.md` persists across all cases. When `decisions[]` covers every in-flight proposal, this collapses to the empty-of-in-flight-proposals state (the historical behavior); when `decisions[]` covers a strict subset, the unprocessed proposals remain in place for a future revise pass.

The author identifier for the revision-file `author_llm` field follows the unified precedence codified in `spec.md` §"Author identifier resolution".

### `prune-history` file-shaping mechanics

The `bin/prune_history.py` wrapper resolves the spec root from `--project-root` and `.livespec.jsonc` via the shared upward-walk helper (the main spec tree only — there is no `--spec-target` flag for prune-history in v1) and performs deterministic file-shaping:

- (a) It identifies the current highest version `vN` under `<spec-root>/history/`.
- (b) It resolves the carry-forward `first` field — if `<spec-root>/history/v(N-1)/PRUNED_HISTORY.json` exists, it reads that file's `pruned_range[0]` and uses it as `first`; otherwise `first` is the smallest-numbered v-directory currently under `<spec-root>/history/` (typically `1`).
- (c) It deletes every `<spec-root>/history/vK/` where `K < N-1`.
- (d) It replaces the contents of `<spec-root>/history/v(N-1)/` with a single file `<spec-root>/history/v(N-1)/PRUNED_HISTORY.json` containing exactly `{"pruned_range": [first, N-1]}` — no timestamps, git SHAs, or identity fields (per the no-metadata invariant; git commit metadata already provides that audit context).
- (e) `<spec-root>/history/vN/` is left fully intact.

The version counter never resets — `PRUNED_HISTORY.json`'s `pruned_range[0]` carries the original-earliest version number forward across multiple prune cycles.

Two no-op short-circuits MUST be detected before reaching step (c):

- (i) Only `v001` exists under `<spec-root>/history/` (nothing to prune).
- (ii) The oldest surviving v-directory under `<spec-root>/history/vK/` (smallest `K < N`) already contains a `PRUNED_HISTORY.json` marker (no full versions remain to prune below the prior marker).

On either no-op, the wrapper emits a single-finding `{"findings": [{"check_id": "prune-history-no-op", "status": "skipped", "message": "nothing to prune; oldest surviving history is already PRUNED_HISTORY.json"}]}` JSON document to stdout and exits 0; the existing marker is NOT re-written, no new commit-worthy diff is produced.

### `accept-decision-snapshot-consistency` doctor static check

A static check MUST run against every `<spec-target>/history/vNNN/` directory where `NNN >= 2`. For every `<stem>-revision.md` in `vNNN/proposed_changes/` with YAML front-matter `decision` in `{accept, modify}` AND a non-empty `## Resulting Changes` section: every spec-target-relative file path listed under `## Resulting Changes` MUST exist in both `vNNN/` and `v(NNN-1)/`, AND `vNNN/<file>` MUST NOT be byte-identical to `v(NNN-1)/<file>`. A byte-identical pair indicates the `resulting_files[]` write silently failed during the revise that cut `vNNN`. The check emits a `fail` Finding naming the inconsistent `(vNNN, file)` pair and lifts the wrapper exit to non-zero; the user is directed to roll back the cut and re-run revise. The check is exempt for `vNNN` directories that contain a `PRUNED_HISTORY.json` marker (per the existing pruned-marker exemption convention).

### Cross-boundary doctor static checks

The single cross-boundary invariant codified in `contracts.md` §"Doctor cross-boundary invariants" (`config-named-cli-callability`) is a cross-boundary check in the wiring sense only: it reads `.livespec.jsonc` and resolves the config-named CLIs (spec-side and orchestrator-side); it never reads the orchestrator's work-item store, prompts, or any other orchestrator-private state. The check's exit-code derivation MUST surface a missing or non-executable resolution as a `fail` Finding (lifting the wrapper exit to non-zero) rather than as a silent skip, naming the offending config key and value. The check ID MUST follow the existing slug convention (lowercase-hyphenated, per §"File naming and invocation"): `config-named-cli-callability`.

The doctor static invariant catalog MUST be enumerable from a single named registry inside `livespec.doctor.static` so contributors and tools can list all checks programmatically; the registry contract follows the existing slug↔module-name mapping pattern stated in §"File naming and invocation". Every check ID covered by `contracts.md` §"Doctor cross-boundary invariants" — currently the single `config-named-cli-callability` invariant — MUST appear in this registry.
