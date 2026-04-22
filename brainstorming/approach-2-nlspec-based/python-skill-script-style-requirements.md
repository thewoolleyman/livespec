# Python skill script style requirements

This section constrains how Python scripts bundled with a Claude Code
skill governed by this specification are authored, tested, and enforced.
It applies to every Python module under the shipped skill bundle
(`.claude-plugin/skills/livespec/scripts/`) and to every Python module
under the dev-tooling tree at `<repo-root>/dev-tooling/`. It does not
apply to scripts written in other languages; livespec v006 ships no
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

This section uses BCP 14 / RFC 2119 / RFC 8174 keywords (`MUST`,
`MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`, `SHOULD NOT`, `MAY`,
`OPTIONAL`) for normative requirements.

---

## Scope

- Every Python module bundled with the skill under
  `.claude-plugin/skills/livespec/scripts/livespec/**`.
- Every Python shebang-wrapper executable under
  `.claude-plugin/skills/livespec/scripts/bin/*.py`.
- Every Python module or script under `<repo-root>/dev-tooling/**`.
- **Exempt:** vendored third-party code under
  `.claude-plugin/skills/livespec/scripts/_vendor/**` — vendored libs
  are audited for drift against upstream (`check-vendor-audit`), not
  subjected to livespec's own style rules.

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
- The package `livespec/__init__.py` MUST assert `sys.version_info >=
  (3, 10)` at import time and raise `ToolMissingError` (exit 127) if
  older.
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
under `.claude-plugin/skills/livespec/scripts/_vendor/<lib>/`. All
vendored libs MUST be:

- Pure Python (no compiled wheels; no C / Rust extensions).
- Permissively licensed (MIT, BSD-2-Clause, BSD-3-Clause, or
  Apache-2.0).
- Actively maintained by a reputable upstream.
- Zero-transitive-dep or all-transitive-deps-also-vendored.

Locked vendored libs for v006:

- **`returns`** (dry-python/returns, BSD-2) — ROP primitives: `Result`,
  `IOResult`, `@safe`, `@impure_safe`, `flow`, `bind`, `Fold.collect`,
  `lash`.
- **`fastjsonschema`** (horejsek/python-fastjsonschema, MIT) — JSON
  Schema Draft-7 validator.
- **`structlog`** (hynek/structlog, BSD-2 / MIT dual) — structured JSON
  logging.

Each vendored lib's `LICENSE` file MUST be preserved at
`_vendor/<lib>/LICENSE`. A `NOTICES.md` at the repo root MUST list every
vendored lib with its license and copyright.

The `scripts/livespec/__init__.py` MUST insert `_vendor/` into
`sys.path` at import time so vendored libs import under their natural
names (`from returns.io import IOResult`).

`check-vendor-audit` (see "Enforcement suite") diffs each vendored lib's
source tree against its upstream pinned version recorded in
`<repo-root>/.vendor.toml` (or equivalent manifest). Any drift fails
the gate. Re-vendoring via `just vendor-update <lib>` is a deliberate
maintainer action.

---

## Package layout

The shipped bundle organizes Python code as:

```
.claude-plugin/skills/livespec/scripts/
├── bin/                                   # shebang-wrapper executables
│   ├── seed.py
│   ├── propose_change.py
│   ├── critique.py
│   ├── revise.py
│   ├── doctor_static.py
│   └── prune_history.py
├── _vendor/
│   ├── returns/
│   ├── fastjsonschema/
│   └── structlog/
└── livespec/
    ├── __init__.py
    ├── commands/                          # one module per sub-command
    ├── doctor/
    │   ├── run_static.py                  # orchestrator (single ROP chain)
    │   ├── finding.py
    │   └── static/                        # per-check modules
    ├── io/                                # impure boundary wrappers
    ├── parse/                             # pure parsers
    ├── validate/                          # pure validators
    ├── schemas/                           # JSON Schema Draft-7 files
    ├── context.py                         # Context dataclasses
    └── errors.py                          # LivespecError hierarchy
```

- **`bin/`** — executable shebang-wrappers. Each file is ≤ 5 lines:
  shebang + import of `main` + `raise SystemExit(main())`. No logic.
  `chmod +x` applied. See "Shebang-wrapper contract" below.
- **`_vendor/`** — vendored third-party libs, exempt from livespec
  rules.
- **`livespec/`** — the Python package. Every other file here follows
  the rules in this document.

Per sub-package conventions:

- **`commands/<cmd>.py`** — one module per sub-command. Exports `run()`
  (ROP-returning) and `main()` (supervisor that unwraps to exit code).
- **`doctor/run_static.py`** — static-phase orchestrator. Composes all
  check modules via a single ROP chain (`Fold.collect`).
- **`doctor/static/<check>.py`** — one module per static check. Exports
  `SLUG` constant and `run(ctx) -> IOResult[Finding, DoctorInternalError]`.
- **`io/`** — impure boundary. Every function wraps a side-effecting
  operation (filesystem, subprocess, git) with `@impure_safe`.
- **`parse/`** — pure parsers. Every function takes a string/bytes/dict
  and returns `Result[T, ParseError]`.
- **`validate/`** — pure validators. Uses `fastjsonschema` loaded from
  `../schemas/*.schema.json`. Returns `Result[T, ValidationError]`.
- **`schemas/`** — JSON Schema Draft-7 files, one per public dataclass.
  Filename matches the dataclass: `LivespecConfig` →
  `livespec_config.schema.json`.
- **`context.py`** — immutable context dataclasses (`DoctorContext`,
  `SeedContext`, etc.) — the railway payload.
- **`errors.py`** — `LivespecError` hierarchy with per-subclass
  `exit_code` class attribute.

---

## Railway-Oriented Programming (ROP)

Every public function in `livespec/` MUST compose via ROP:

- **Pure functions** (in `parse/`, `validate/`) return `Result[T, E]`.
- **Impure functions** (in `io/`) return `IOResult[T, E]`.
- **Composition code** (`commands/`, `doctor/`) uses `flow(...)` +
  `bind(...)` to chain steps; `.lash(...)` to convert known-domain
  errors into success-track data where appropriate.
- **Third-party code that raises** is wrapped at the `io/` boundary
  with `@impure_safe` so exceptions become `IOFailure(...)` on the
  railway.
- **No `raise` statements** outside `io/**` and `errors.py`. Enforced by
  `check-no-raise-outside-io` (AST).
- **No `except:` clauses** outside `io/**` and `errors.py`. Exception
  handling happens at the `io/` boundary; internal code stays on the
  railway.
- **`sys.exit` and `raise SystemExit`** appear ONLY in `bin/*.py`
  shebang wrappers. Not in any `livespec/**` module. Enforced by
  `check-supervisor-discipline`.

Composition idioms this document mandates:

```python
# In a doctor-static check:
def run(ctx: DoctorContext) -> IOResult[Finding, DoctorInternalError]:
    return flow(
        ctx.project_root / ".livespec.jsonc",
        read_file,                 # IOResult[str, IOError]
        bind(parse_jsonc),         # Result[dict, ParseError]
        bind(validate_config),     # Result[Config, ValidationError]
    ).map(lambda _: pass_finding(SLUG)) \
     .lash(lambda err: IOSuccess(fail_finding(SLUG, err)))

# In an orchestrator:
def run_static(ctx: DoctorContext) -> IOResult[FindingsReport, DoctorInternalError]:
    results = [module.run(ctx) for _, module in discover_check_modules()]
    return Fold.collect(results, IOSuccess(())).map(
        lambda findings: FindingsReport(findings=list(findings))
    )
```

Every public function's `return` annotation MUST be `Result[_, _]` or
`IOResult[_, _]`. Enforced by `check-public-api-result-typed` (AST).

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
  thin wrappers over one side-effecting operation each.
- **Everything else** (`commands/`, `doctor/**`, `context.py`,
  `errors.py`) may call both pure and impure layers; these are
  composition layers.

Enforced by `check-purity` (AST walker over `parse/` and `validate/`
imports).

---

## Type safety

- **pyright strict mode** is mandatory. `pyproject.toml`'s
  `[tool.pyright]` sets `typeCheckingMode = "strict"`. Enforced by
  `just check-types` — any pyright diagnostic fails the gate.
- Every public function and every dataclass field MUST have type
  annotations. Private (single-leading-underscore) helpers SHOULD be
  annotated.
- Every public function's return annotation MUST be `Result[_, _]` or
  `IOResult[_, _]` unless it returns `None` for a deliberate side-effect
  boundary (e.g., `main() -> int` supervisors in `commands/*.py`).
- `Any` is forbidden outside `io/` boundary wrappers (and in those
  wrappers only for third-party types pyright cannot see). An AST check
  rejects `Any` annotations elsewhere.
- `# type: ignore` is forbidden without a narrow justification comment
  of the form `# type: ignore[<specific-code>] — <reason>`.
- Implicit `Optional` via `None` default without `| None` annotation is
  forbidden (pyright strict flags this).
- mypy is not used; there is no mypy configuration file.

---

## Linter and formatter

`ruff` (astral-sh/ruff) is the sole linter, formatter, import-sorter,
and complexity checker. Pinned via mise.

- `pyproject.toml`'s `[tool.ruff]` configures:
  - `target-version = "py310"`.
  - `line-length = 100`.
  - Rule selection: `E F I B UP SIM C90 N RUF PL PTH`.
  - `[tool.ruff.lint.pylint]` sets `max-args = 6`, `max-branches = 10`,
    `max-statements = 30`.
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

Test-tree layout mirrors the implementation tree:

```
tests/
├── CLAUDE.md
├── heading-coverage.json
├── fixtures/
├── livespec/                          # mirrors scripts/livespec/
│   ├── commands/test_seed.py
│   ├── doctor/test_run_static.py
│   ├── doctor/static/test_livespec_jsonc_valid.py
│   ├── io/test_fs.py
│   ├── parse/test_jsonc.py
│   ├── validate/test_livespec_config.py
│   └── ...
├── bin/                               # mirrors scripts/bin/
│   └── test_wrappers.py               # meta-test: all wrappers match the shape
├── dev-tooling/                       # mirrors <repo-root>/dev-tooling/
│   └── checks/test_purity.py
└── test_*.py                          # per-spec-file rule-coverage tests
```

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

---

## Code coverage

Coverage is measured by `coverage.py` via `pytest-cov`:

- **100% line + branch coverage** is mandatory across the whole Python
  surface in `scripts/livespec/**` and `<repo-root>/dev-tooling/**`.
  No tier split. `_vendor/` is excluded.
- `pyproject.toml`'s `[tool.coverage.run]` sets `source = ["livespec"]`
  and `branch = true`.
- `[tool.coverage.report]` sets `fail_under = 100`, `show_missing = true`,
  `skip_covered = false`.
- Enforced by `just check-coverage`.
- **Escape hatch:** `# pragma: no cover — <reason>` on a single line or
  a bounded block; cap ≤ 3 pragma-lines per file. Bare `# pragma: no cover`
  without a reason is rejected by a targeted regex check. Common
  legitimate uses: `if TYPE_CHECKING:` guards, `sys.version_info` gates,
  `bin/*.py` wrapper bodies (each is a 3-line trivial pass-through).

---

## Complexity thresholds

Adapted from language-agnostic research (McCabe, Martin) and tightened
for Python's density:

- **Cyclomatic complexity ≤ 10** per function (ruff `C901`).
- **Function body ≤ 30 logical lines** (ruff `PLR0915`).
- **File ≤ 200 logical lines** (custom check at
  `<repo-root>/dev-tooling/checks/file_lloc.py`).
- **Max nesting depth ≤ 4** (ruff PLR rule).
- **No positional-arg limit** — Python's keyword-only args and
  dataclasses decompose large parameter sets naturally.
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
- **Bootstrap:** `scripts/livespec/__init__.py` configures structlog's
  processors pipeline to emit JSON via `structlog.processors.JSONRenderer()`.

The `log` logger is obtained via `structlog.get_logger(__name__)` in
each module that logs.

---

## Exit code contract

Scripts bundled with the skill MUST use the following exit codes,
preserved from v005:

| Code | Meaning |
|---|---|
| `0` | Success. |
| `1` | Script-internal failure (unexpected runtime error; likely a bug). |
| `2` | Usage error: bad flag, wrong argument count, malformed invocation. |
| `3` | Input or precondition failed: referenced file/path/value missing, malformed, or in an incompatible state. |
| `126` | Permission denied: a required file exists but is not executable/readable/writable. |
| `127` | Required external tool not on PATH, or Python version too old. |

Implementation:

- `livespec/errors.py` defines the hierarchy:
  ```python
  from typing import ClassVar

  class LivespecError(Exception):
      exit_code: ClassVar[int] = 1

  class UsageError(LivespecError):
      exit_code: ClassVar[int] = 2

  class PreconditionError(LivespecError):
      exit_code: ClassVar[int] = 3

  class PermissionDeniedError(LivespecError):
      exit_code: ClassVar[int] = 126

  class ToolMissingError(LivespecError):
      exit_code: ClassVar[int] = 127
  ```
- `IOFailure(err)` payloads are `LivespecError` subclasses.
- Supervisors (`main()` in `commands/<cmd>.py` and
  `doctor/run_static.py`) pattern-match on the final `IOResult` and
  return `err.exit_code` on `IOFailure`.
- `sys.exit(err.exit_code)` appears only in `bin/*.py` shebang
  wrappers. Everywhere else stays on the railway.

Enforced by `check-supervisor-discipline` (AST).

---

## File naming and invocation

- Python module and script filenames MUST use snake_case + `.py`.
  Including `bin/*.py` shebang wrappers.
- Hyphens appear only in JSON wire contracts (`check_id` values like
  `"doctor-out-of-band-edits"`) and in PROPOSAL.md prose
  (`propose-change` sub-command name).
- The slug↔module-name mapping for doctor-static checks converts
  hyphens to underscores: JSON slug `out-of-band-edits` ↔ module
  filename `out_of_band_edits.py`. The conversion happens at one
  defined point in `doctor/run_static.py`.
- Executables (`bin/*.py`) carry the shebang `#!/usr/bin/env python3`,
  the executable bit, and conform to the shape below.

### Shebang-wrapper contract

Each file under `bin/*.py` MUST be ≤ 5 lines matching exactly this
shape:

```python
#!/usr/bin/env python3
"""Shebang wrapper for <description>. No logic; see livespec.<module> for implementation."""
from livespec.<module>.<submodule> import main

raise SystemExit(main())
```

No other content. `# pragma: no cover` is applied to each wrapper file
to acknowledge these are trivial pass-throughs. Enforced by
`check-wrapper-shape` (AST-lite).

---

## Dev tooling and task runner

The **`just`** task runner is the single source of truth for every
dev-tooling invocation.

- `justfile` at repo root owns every check, test, build, lint, format,
  coverage, and vendor-management recipe.
- `lefthook.yml` owns when hooks fire (pre-commit, pre-push). Every
  `run:` field is `just <target>`; no direct tool invocations.
- `.github/workflows/*.yml` owns CI triggers and parallelism. Every
  step's `run:` field is `just <target>`; no direct tool invocations.
- `.mise.toml` pins tool versions (Python, just, lefthook, pyright,
  ruff, pytest, pytest-cov, pytest-icdiff).

This eliminates drift across invocation surfaces. A developer
reproduces CI locally by running `just check`.

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
| `just check` | Run every check below. |
| `just check-lint` | `ruff check .` |
| `just check-format` | `ruff format --check .` |
| `just check-types` | `pyright` (strict). |
| `just check-complexity` | ruff C901 + PLR + file-LLOC custom check. |
| `just check-purity` | AST: `parse/` + `validate/` don't import `io/` or effectful APIs. |
| `just check-private-calls` | AST: no cross-module calls to `_`-prefixed functions defined elsewhere. |
| `just check-import-graph` | AST: no circular imports in `livespec/**`. |
| `just check-global-writes` | AST: no module-level mutable state writes from functions. |
| `just check-supervisor-discipline` | AST: `sys.exit` / `raise SystemExit` only in `bin/*.py`. |
| `just check-no-raise-outside-io` | AST: `raise` only in `io/**` and `errors.py`. |
| `just check-public-api-result-typed` | AST: every public function returns `Result` or `IOResult` per annotation. |
| `just check-main-guard` | AST: no `if __name__ == "__main__":` in `livespec/**`. |
| `just check-wrapper-shape` | AST-lite: `bin/*.py` conforms to the shebang-wrapper contract. |
| `just check-claude-md-coverage` | Every directory under `scripts/` and `tests/` contains a `CLAUDE.md`. |
| `just check-vendor-audit` | Diff `_vendor/<lib>/` sources against pinned upstream version in `.vendor.toml`. |
| `just check-no-direct-tool-invocation` | grep: `lefthook.yml` and `.github/workflows/*.yml` only invoke `just <target>`. |
| `just check-tools` | Verify every mise-pinned tool is installed at the pinned version. |
| `just check-tests` | `pytest`. |
| `just check-coverage` | `pytest --cov` with 100% line+branch threshold. |

Mutating targets (opt-in, not run in CI):

| Target | Purpose |
|---|---|
| `just fmt` | `ruff format .` |
| `just lint-fix` | `ruff check --fix .` |
| `just vendor-update <lib>` | Re-vendor a library, updating `.vendor.toml`. |

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

Every directory under `.claude-plugin/skills/livespec/scripts/` and
`<repo-root>/tests/` MUST contain a `CLAUDE.md` file describing the
local constraints an agent working in that directory must satisfy.

Each `CLAUDE.md`:

- States the directory's purpose in one sentence.
- Lists directory-local rules (e.g., "this directory is pure; no
  imports from `io/`").
- Links to this style doc for global rules rather than duplicating.
- Is kept short (typically under 50 lines); it's a local crib sheet,
  not a full reference.

Enforced by `just check-claude-md-coverage`.

---

## Non-goals

- **Interactive CLI.** Python scripts bundled with the skill are
  non-interactive by design.
- **Windows native support.** Not a v006 target; Linux + macOS only.
- **Async / concurrency.** livespec's workload is synchronous and
  deterministic. No `asyncio`, no threading, no multiprocessing.
- **Performance tuning.** livespec is a CLI-scale tool; no hot-path
  work.
- **Runtime dependency resolution.** Missing `python3` or too-old
  Python → exit 127; installing Python is the user's concern.
- **LLM integration from Python.** Python scripts handle only
  deterministic work; LLM-driven behavior stays at the skill-markdown
  layer (`SKILL.md`, `commands/<cmd>.md`, template prompts).
- **Mypy compatibility.** Pyright is the sole type checker.
- **Ruby / Node / other language hooks.** No non-Python dev-tooling
  scripts.
