---
proposal: proposal-critique-v05.md
decision: modify
revised_at: 2026-04-22T00:00:00Z
reviser_human: thewoolleyman
reviser_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v05

## Provenance

- **Proposed change:** `proposal-critique-v05.md` (in this directory) — a
  conversion plan, not a defect critique.
- **Revised by:** thewoolleyman (human) in dialogue with Claude Opus 4.7
  (1M context).
- **Revised at:** 2026-04-22 (UTC).
- **Scope:** v005 PROPOSAL.md + `bash-skill-script-style-requirements.md`
  → v006 PROPOSAL.md + new `python-skill-script-style-requirements.md`.
  Bash replaced by Python 3.10+ as the implementation language for every
  skill-bundled script and every dev-tooling enforcement script.

## Pass framing

This pass was a **language migration**, not a defect critique. The v005
bash surface (≈24 pages of style rules compensating for bash's missing
abstractions, plus the enforcement suite of 6 external tools) is replaced
by a Python surface (Python 3.10+, single-package layout, ruff + pyright
+ pytest + coverage.py, ROP via vendored dry-python/returns) that
collapses style rules to a shorter doc and shrinks the enforcement
toolchain.

The pass did NOT re-open any v005 decision about WHAT the skill does
(sub-commands, template architecture, lifecycle, history shape,
proposed-change / revision file formats, doctor static-check contract,
runtime / dev-time split, mise-pinned tooling, enforcement-suite
invocation-agnostic framing). It only changed HOW scripts are
implemented.

Failure-mode labels from prior critiques (ambiguity / malformation /
incompleteness / incorrectness) did NOT apply. Each proposal was
labelled by **axis** (language-floor, dependency-strategy, tooling,
layout, rule-simplification, enforcement-suite-shape,
backwards-compatibility, architecture-pattern, agent-documentation).

## Summary of dispositions

| Axis | Count | Accepted as proposed | Modified-on-accept | Mid-interview additions |
|---|---|---|---|---|
| language-floor | 1 | 1 | 0 | 0 |
| dependency-strategy | 2 | 1 | 1 | 0 |
| layout | 4 | 2 | 2 | 0 |
| tooling | 4 | 4 | 0 | 0 |
| rule-simplification | 6 | 4 | 2 | 0 |
| enforcement-suite-shape | 1 | 0 | 1 | 0 |
| backwards-compatibility | 4 | 4 | 0 | 0 |
| architecture-pattern | 1 | 1 | 0 | 0 |
| agent-documentation (new) | 0 | 0 | 0 | 1 (P22) |

P22 was added mid-interview after the user mandated per-directory
CLAUDE.md coverage across `scripts/` and `tests/`. P10 was split and
substantially reshaped during the interview after the user pointed out
that the initial target-list framing conflated orchestration with
what-gets-run.

## Governing principles established during this pass

Three cross-cutting principles emerged from the interview that govern
the entire v006 Python surface. They apply to every individual
disposition below and are captured as feedback memories for future
Python-skill work.

### Strongest-possible guardrails for agent-authored Python

User stated: *"strongest guardrails on the code possible, in terms of
type safety and the loose coupling and high cohesion forced by ROP
pattern. This gives agentic implementors minimal room to do horrible
things."*

Applied concretely:
- **Type safety:** pyright strict, gating (P6).
- **Error flow:** ROP via vendored dry-python/returns; Result for pure
  code, IOResult for effectful code (P21).
- **Coupling / cohesion:** mechanical AST enforcement of private-call,
  import-graph acyclicity, global-write prohibition, purity discipline,
  ROP-typed public APIs.
- **Linter strictness:** ruff with broad rule selection (E F I B UP SIM
  C90 N RUF + PL + PTH) (P5).
- **Complexity:** CCN ≤ 10, func ≤ 30 LLOC, file ≤ 200 LLOC, nesting
  ≤ 4, no waivers (P9).
- **Coverage:** 100% line+branch everywhere with pragma-only escape
  (P8).

### Task runner is the single source of truth

User stated: *"The justfile should be the single source of truth for
invoking any dev tooling. Any glue code to invoke Python or anything
else should be encapsulated there. And lefthook and CI should just
invoke justfile so we don't have duplication or leakage of any glue
code."*

Applied concretely:
- `justfile` at repo root owns every dev-tooling invocation.
- `lefthook.yml` contains only `just <target>` in `run:` fields.
- `.github/workflows/*.yml` contains only `run: just <target>` steps,
  split into parallel jobs for clarity (not for scope reduction).
- New check `check-no-direct-tool-invocation` grep-verifies this.
- `.mise.toml` owns tool versions only; justfile owns invocation logic.

### Prefer exploring standardized, well-maintained libraries

User authorized vendoring small pure-Python permissively-licensed libs
as precedent for future Python-skill work. Libraries locked in for
v006:

- **dry-python/returns** (BSD-2) — Result / IOResult / `@safe` /
  `@impure_safe` / `flow` / `bind` / `Fold.collect` for ROP.
- **fastjsonschema** (MIT) — JSON Schema Draft-7 validator; pyright
  strict-compatible via thin typed wrappers; publishable `.schema.json`
  files.
- **structlog** (BSD-2 / MIT dual) — structured JSON logging;
  `bind_contextvars` for run_id correlation; modern observability best
  practices; deterministic LLM-parseable output.

All three vendored under `.claude-plugin/skills/livespec/scripts/
_vendor/<lib>/`. A `check-vendor-audit` target diffs vendored sources
against pinned upstream versions and fails on drift.

---

## Disposition by item

### P1. Python version floor (language-floor)

Decision: **Accepted as recommended.** Python 3.10 floor. Unlocks
`X | Y` union syntax, `match` statements, modern typing, `ParamSpec`,
`TypeAlias`. Preinstalled on Ubuntu 22.04 LTS (the common 2026 dev
baseline). Homebrew/Xcode CLT on macOS cover it. The style doc mandates
3.10+ and the `__main__` / entry points assert version at startup.

### P2. Runtime dependency set (dependency-strategy)

Decision: **Accepted with later modification (revised via P3).**
Initial disposition was stdlib-only + drop jq. During the interview the
user authorized vendoring small pure-Python libs, which extended P2 to:
**python3 >= 3.10** plus **vendored pure-Python libraries** listed
under P3. Still drops jq entirely.

### P3. Dependency shipping mechanism (dependency-strategy)

Decision: **Modified-on-accept.** Originally scoped to stdlib-only.
After user authorization ("I'm fine with vendoring... small libraries
should have minimal security exposure... set precedent for how I use
Python and other skills"), expanded to:

- Vendored under `.claude-plugin/skills/livespec/scripts/_vendor/<lib>/`.
- Vendored libs limited to permissively-licensed (MIT / BSD-2 / BSD-3)
  pure-Python (no compiled wheels) actively-maintained libraries.
- `check-vendor-audit` target diffs vendored sources against upstream
  pinned versions (pinned in a `.vendor.toml` or equivalent manifest);
  fails on drift.
- Re-vendoring via `just vendor-update <lib>` — deliberate maintainer
  action, not automated.
- Vendored libs retain their upstream `LICENSE` at
  `_vendor/<lib>/LICENSE`; `NOTICES.md` at repo root lists every
  vendored lib with its license and copyright.
- Sys.path insertion at `scripts/livespec/__init__.py` makes
  `_vendor/*` importable by name inside the livespec package.

Locked-in vendored libs:
- **dry-python/returns** (BSD-2) for ROP (see P21).
- **fastjsonschema** (MIT) for JSON Schema validation (validators use
  `.schema.json` files under `scripts/livespec/schemas/`).
- **structlog** (BSD-2 / MIT dual) for structured JSON logging (see P14).

### P4. Package layout inside the bundle (layout)

Decision: **Accepted as recommended** with one mid-interview addition.
Single `livespec/` package with sub-packages:

```
.claude-plugin/skills/livespec/scripts/
├── bin/                                 # shebang-wrapper executables
│   ├── seed.py
│   ├── propose_change.py
│   ├── critique.py
│   ├── revise.py
│   ├── doctor_static.py                 # static-phase only; LLM-driven phase is skill-level
│   └── prune_history.py
├── _vendor/
│   ├── returns/
│   ├── fastjsonschema/
│   └── structlog/
└── livespec/
    ├── __init__.py
    ├── commands/                        # one module per sub-command: run() + main()
    ├── doctor/
    │   ├── run_static.py                # orchestrator: single ROP chain, Fold.collect
    │   ├── finding.py
    │   └── static/                      # per-check MODULES (not executables)
    ├── io/                              # impure boundary: @impure_safe wrappers
    ├── parse/                           # pure parsers: Result-returning
    ├── validate/                        # pure validators: Result-returning
    ├── schemas/                         # JSON Schema Draft-7 files
    ├── context.py                       # DoctorContext, SeedContext, etc.
    └── errors.py                        # LivespecError hierarchy
```

Mid-interview addition (P22): `CLAUDE.md` at every directory level.

### P5. Linter and formatter (tooling)

Decision: **Accepted as recommended.** `ruff` is the sole linter +
formatter + import-sorter + complexity checker. Pinned via `mise`.
`pyproject.toml`'s `[tool.ruff]` configures:

- Rule selection: `E F I B UP SIM C90 N RUF PL PTH`.
- `ruff format` replaces shfmt / black.
- `C901` provides McCabe complexity gating at default 10 (matches P9).
- `# noqa: <CODE> — <reason>` escapes allowed; AST check rejects bare
  `# noqa` without a code and reason.

Retires: `shellcheck`, `shfmt`, `shellharden`, `shellmetrics`.

### P6. Type checker (tooling)

Decision: **Accepted as recommended.** `pyright` strict mode. Pinned
via `mise`. `pyproject.toml`'s `[tool.pyright]` sets
`typeCheckingMode = "strict"`. Enforcement: `just check-types` fails on
any pyright diagnostic. Strictness is non-negotiable per the guardrails
principle; mypy is not a fallback we plan to invoke (pyright's
control-flow narrowing is tighter and faster).

### P7. Test framework and fixtures (tooling)

Decision: **Accepted as recommended.** `pytest` with `tmp_path`,
`monkeypatch`, and `parametrize`. Required plugins: `pytest-cov`
(coverage) and `pytest-icdiff` (richer failure diffs for the LLM's
context window). No other plugins. No `pytest-asyncio` — livespec is
synchronous.

Fixture discipline:
- Test files live at `tests/livespec/<mirror>.py` (per-module) and
  `tests/test_<spec-file>.py` (per-spec-file, continuing v005's B13
  dual-naming resolution).
- `tests/fixtures/` is read-only; tests MUST NOT mutate fixtures.
- Test-local state uses `tmp_path` (pytest-provided, per-test).
- Stubbing via `monkeypatch.setattr()` on impure `io/` wrappers.

Retires: `bats-core`, `bats-assert`, `bats-support`.

### P8. Coverage tool and threshold (tooling)

Decision: **Accepted as recommended.** `coverage.py` via `pytest-cov`.
**100% line + branch coverage everywhere** — no pure/impure tier split
(the tooling artifact that forced 95% for pure code with kcov is gone
with coverage.py).

Escape hatch: `# pragma: no cover — <reason>` on a single line or
`# pragma: no cover (start|end) — <reason>` for a bounded block. An
AST-lite check rejects bare `# pragma: no cover` without a reason
comment. Cap: ≤ 3 pragma lines per file.

Retires: `kcov`, `bashcov`, the Linux-only kcov wrapper, the pure/impure
tier split, the 95% / 80% thresholds.

### P9. Complexity thresholds (rule-simplification)

Decision: **Accepted as recommended.** Python-density-adjusted
thresholds:

- CCN ≤ 10 (ruff `C901` default).
- Function body ≤ 30 logical lines (ruff `PLR0915`).
- File ≤ 200 logical lines (custom check under `dev-tooling/checks/
  file_lloc.py`).
- Max nesting depth ≤ 4 (ruff `PLR` rules).
- **Positional-args limit dropped** — Python's keyword-only args +
  dataclasses decompose parameter sets naturally; the v005 args ≤ 6
  rule doesn't translate.
- **Waivers not permitted** — the guardrails principle rejects
  escape hatches; refactor is the answer.

Retires: `shellmetrics`, the args-count rule, the v005-era 50-line /
300-line thresholds.

### P10. Enforcement-suite shape (enforcement-suite-shape)

Decision: **Modified-on-accept** after user clarification that the
initial framing conflated orchestration with what-gets-run.

Resolution has three decoupled layers:

**Task runner:** **`just`** (casey/just). Pinned via mise.
- `justfile` at repo root owns every dev-tooling invocation.
- Individual targets per check; a combined `check` target runs all.
- Mutating targets (`fmt`, `lint-fix`, `vendor-update`) are opt-in.

**Hook framework:** **`lefthook`** (evilmartians/lefthook). Pinned via
mise.
- `lefthook.yml` at repo root. All `run:` fields are `just <target>`;
  no direct ruff/pyright/pytest invocations.
- pre-commit and pre-push both run the full `just check` suite.
- Per-check visibility via per-command entries (optional but
  recommended for readable failure output).

**CI:** **GitHub Actions**.
- `.github/workflows/ci.yml`. All `run:` steps are `just <target>`.
- Matrix strategy with one job per check for parallel execution and
  clear failure output; `fail-fast: false` so every job reports.
- `jdx/mise-action@v2` installs pinned tools from `.mise.toml`.
- No other CI providers supported in v006.

Canonical target list (each a `just` recipe):

- `check-lint` (ruff check)
- `check-format` (ruff format --check)
- `check-types` (pyright strict)
- `check-complexity` (ruff C901 + custom file-LLOC + nesting)
- `check-purity` (AST: `parse/` + `validate/` don't import `io/` etc.)
- `check-private-calls` (AST: no cross-module `_`-prefixed calls)
- `check-import-graph` (AST: no circular imports)
- `check-global-writes` (AST: no module-level mutable state writes)
- `check-supervisor-discipline` (AST: `sys.exit` only in `bin/*.py`)
- `check-no-raise-outside-io` (AST: `raise` only in `io/` and
  `errors.py`)
- `check-public-api-result-typed` (AST: public functions return
  `Result` or `IOResult` per annotation)
- `check-main-guard` (AST: no `if __name__ == "__main__":` in
  `livespec/`)
- `check-wrapper-shape` (AST-lite: `bin/*.py` ≤ 5 lines, exact shape)
- `check-claude-md-coverage` (every dir under `scripts/` and `tests/`
  has `CLAUDE.md`)
- `check-vendor-audit` (diff vendored sources vs pinned upstream)
- `check-no-direct-tool-invocation` (grep: lefthook.yml and
  `.github/workflows/*.yml` only invoke `just <target>`)
- `check-tests` (pytest)
- `check-coverage` (pytest + coverage, 100% line+branch)
- `check-tools` (mise tool-version verification)
- `check` (runs all of the above)

Dropped v005 targets: `check-shellcheck`, `check-shfmt`,
`check-shellharden`, `check-filename-blacklist`,
`check-library-headers`, `check-arg-count`, `check-executable-bit`,
`check-sourceable-guards`, `check-source-graph` (renamed →
`check-import-graph`).

### P11. Doctor-static decomposition (layout)

Decision: **Modified-on-accept** via multiple rounds of user pushback.

Final shape:
- **Single executable:** `bin/doctor_static.py`. Runs only the static
  phase. The LLM-driven phase remains skill-level (in
  `commands/doctor.md` at the skill layer), NOT Python-invoked.
- **No per-check executables.** Each check is a module under
  `livespec/doctor/static/<module>.py` exporting `SLUG` and
  `run(ctx: DoctorContext) -> IOResult[Finding, DoctorInternalError]`.
- **Single ROP chain orchestrator** in `livespec/doctor/run_static.py`.
  Uses `Fold.collect` from dry-python/returns to compose all check
  results into `IOResult[FindingsReport, DoctorInternalError]`. Fail
  findings are `IOSuccess(finding)` data; only internal bugs produce
  `IOFailure` that short-circuits.
- **Within each check:** inner ROP chain via `flow(...)` + `bind(...)`
  short-circuits on the first stage failure; `.lash(...)` converts
  known-domain Err into `IOSuccess(fail_finding(SLUG, err))`.
- **Slug↔module-name mapping:** slugs stay hyphenated in JSON
  `check_id` values (wire contract); module filenames use Python
  snake_case. Mapping: slug `out-of-band-edits` ↔ module
  `out_of_band_edits.py` ↔ check_id `doctor-out-of-band-edits`. The
  hyphen↔underscore conversion happens at one defined point in
  `doctor/run_static.py`'s discovery loop.
- **Insert/delete of checks is a non-event:** add/remove a module file,
  slug list updates at next discovery. v005 invariant preserved.

v005 B20 (decompose-doctor-static) intent carries over: per-check
testability via per-module pytest imports, per-check insertion/deletion
without global renumbering. Python achieves this at the module level
without requiring per-check executables.

### P12. Sourceable-guard equivalent (rule-simplification)

Decision: **Absorbed into P11.** With `bin/*.py` shebang wrappers and
no `if __name__ == "__main__":` anywhere in `livespec/`, Python's
native `__name__` guard pattern is deliberately absent from library
code. Executable-ness is externalized to the `bin/` wrapper layer.

Enforcement: `check-main-guard` AST rejects `if __name__ == "__main__":`
appearing in any file under `scripts/livespec/**`.

### P13. Purity / I/O isolation (rule-simplification)

Decision: **Accepted as recommended.** Structural purity enforced by
directory convention + AST check:

- `livespec/parse/**` and `livespec/validate/**` are **pure**. Modules
  here MUST NOT import from `livespec.io.*`, `subprocess`, filesystem
  APIs (`open`, `pathlib.Path.read_text()`, etc.), or `returns.io.*`.
- `livespec/io/**` is **impure**. Every function here is decorated
  with `@impure_safe` from dry-python/returns; exceptions are caught
  and become `IOFailure(...)`.
- `livespec/commands/**`, `livespec/doctor/**`, `livespec/context.py`,
  `livespec/errors.py` are composition code. They may call both pure
  and impure layers.
- `check-purity` AST walker enforces the import-based rules per dir.

The v005 per-file `__purity__` directive retired — directory-based
discipline is cleaner and matches Python's package idioms better.

### P14. Debug / verbose affordances (rule-simplification)

Decision: **Modified-on-accept.** Replaced v005's `LIVESPEC_XTRACE` /
`LIVESPEC_VERBOSE` env vars with vendored `structlog` (BSD-2 / MIT
dual) for structured JSON logging:

- Output format: **JSON only, to stderr.** No console renderer. No
  `LIVESPEC_LOG_FORMAT` env var. Humans pipe to `jq` / `fx` / `jless`
  when they want visualization; the library owns one output shape.
- Standard fields every line carries: `timestamp` (RFC 3339), `level`,
  `logger`, `message`, `run_id`, plus arbitrary call-site kwargs.
- `run_id` (UUID) generated at each executable's startup; bound via
  `structlog.contextvars.bind_contextvars`. Every log line from one
  invocation carries the same run_id → LLM can correlate.
- Level control: `LIVESPEC_LOG_LEVEL` env var + `-v` / `-vv` CLI flag
  (CLI wins). Default WARNING.
- Style rules: **kwargs only** — `log.error("parse failed", path=str(p),
  error=repr(exc))`; never f-strings in log messages. Errors include
  the `LivespecError` subclass name as a field plus structured context
  dict.
- stdout remains reserved for structured output per the v005 doctor
  contract.

Retires: `LIVESPEC_XTRACE`, `LIVESPEC_VERBOSE`, the bash PS4 trace
setup, the `handle_xtrace` / `handle_verbose` helpers.

Motivation for structlog over stdlib-logging-with-JSON-formatter:
structlog is the modern structured-logging standard with context-
binding ergonomics; vendoring it establishes the precedent the user
authorized for maintained-library adoption. JSON output is
non-negotiable because LLM determinism demands structured
parseability.

### P15. Exit code contract (rule-simplification)

Decision: **Accepted as recommended.** Preserve v005's exit-code
contract via a `LivespecError` exception hierarchy in
`livespec/errors.py`:

```python
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

- ROP integration: `IOFailure(err)` carries a `LivespecError` subclass;
  supervisors pattern-match and read `err.exit_code`.
- No scattered `sys.exit(n)` in library code — enforced by
  `check-supervisor-discipline`. `sys.exit` appears only in
  `bin/*.py` wrappers.
- Enforcement: `check-supervisor-discipline` AST check verifies
  `sys.exit` and `raise SystemExit` appear only in `bin/`.

### P16. File naming and invocation (layout)

Decision: **Modified-on-accept** after user clarification that there is
no human user — only the LLM following SKILL.md paths — so hyphens in
filenames serve no purpose.

Final:
- **All Python filenames use snake_case + `.py`.** Including `bin/*.py`
  shebang wrappers.
- `bin/*.py` files have `#!/usr/bin/env python3` shebang + `chmod +x`.
- Hyphens persist only where they are genuine wire contract: JSON
  `check_id` values (`"doctor-out-of-band-edits"`) and PROPOSAL.md
  prose (the sub-command set `seed`, `propose-change`, `critique`,
  `revise`, `doctor`, `prune-history`).
- SKILL.md references wrappers by exact path:
  `.claude-plugin/skills/livespec/scripts/bin/doctor_static.py` etc.
- Slug↔module mapping rule (from P11) handles the one disconnect
  (hyphenated JSON slug vs snake_case module filename).

v005 "no extension on executables" rule dropped — it was a bash
convention; Python tooling (ruff, pyright, IDEs) benefits from `.py`
extension for semantic recognition.

### P17. Dispatch bash stub (backwards-compatibility)

Decision: **Accepted as recommended.** No bash stub anywhere in the
shipped skill bundle. The v005 `scripts/dispatch` is removed outright;
per-sub-command `bin/*.py` wrappers replace it. SKILL.md references
each wrapper directly.

### P18. Bash style doc fate (backwards-compatibility)

Decision: **Accepted as recommended.** `bash-skill-script-style-
requirements.md` is moved to
`history/v006/retired-documents/bash-skill-script-style-requirements.md`
with a `README.md` alongside noting why it was retired and pointing to
the replacement.

### P19. bash-boilerplate.sh fate (backwards-compatibility)

Decision: **Accepted as recommended.** Delete
`.claude-plugin/skills/livespec/scripts/bash-boilerplate.sh` and its
`dev-tooling/bash-boilerplate.sh` symlink entirely. No replacement
Python module — anything shared lives in ordinary imports from
`livespec.*`.

### P20. Broader bash retention (backwards-compatibility)

Decision: **Accepted as recommended.** No standalone bash scripts
anywhere in the repo (neither in the shipped bundle nor in
`dev-tooling/`). All glue lives in:

- `just` recipes (shell commands inline in recipes are permitted but
  should stay minimal).
- `lefthook.yml` (calls `just <target>`).
- `.github/workflows/*.yml` (calls `just <target>`).

If a Python-worthy task emerges for dev-tooling, it goes under
`dev-tooling/checks/<name>.py` or `dev-tooling/scripts/<name>.py` as a
Python module.

### P21. Railway Oriented Programming (architecture-pattern)

Decision: **Accepted as recommended.** Vendored dry-python/returns
provides the ROP primitives: `Result`, `IOResult`, `@safe`,
`@impure_safe`, `flow`, `bind`, `Fold.collect`, `lash`, `bind_ioresult`.

Applied discipline:
- **Pure code** (under `parse/`, `validate/`) returns `Result[T, E]`.
- **Impure code** (under `io/`) returns `IOResult[T, E]` via
  `@impure_safe` wrappers.
- **Composition code** (`commands/`, `doctor/`, etc.) uses `flow` /
  `bind` to chain steps; `.lash` to convert known-domain errors into
  success-track data where appropriate.
- **Exception handling:** no bare `except:` outside `io/` and
  `errors.py`; third-party code is wrapped with `@impure_safe` at the
  boundary.
- **Supervisors** (`main()` functions in `commands/*.py` and
  `doctor/run_static.py`) are the only place `IOFailure` is unwrapped
  to an exit code; invoked only via `bin/*.py` shebang wrappers.

### P22. CLAUDE.md at every level of scripts/ and tests/ (agent-documentation)

Decision: **Accepted** (user-mandated mid-interview). Every directory
under `scripts/` and `tests/` contains a `CLAUDE.md` explaining the
directory-local constraints an agent working at that level must
satisfy. Files are concise (tens of lines, not prose essays); each
links to `python-skill-script-style-requirements.md` for global rules.

Enforcement: `check-claude-md-coverage` target fails if any directory
under `scripts/` or `tests/` is missing a `CLAUDE.md`.

File list (11 under `scripts/`, analogous tree under `tests/`):

- `scripts/CLAUDE.md`
- `scripts/bin/CLAUDE.md`
- `scripts/_vendor/CLAUDE.md`
- `scripts/livespec/CLAUDE.md`
- `scripts/livespec/commands/CLAUDE.md`
- `scripts/livespec/doctor/CLAUDE.md`
- `scripts/livespec/doctor/static/CLAUDE.md`
- `scripts/livespec/io/CLAUDE.md`
- `scripts/livespec/parse/CLAUDE.md`
- `scripts/livespec/validate/CLAUDE.md`
- `scripts/livespec/schemas/CLAUDE.md`

---

## Self-consistency check

Post-revision invariants rechecked:

- **Python-only runtime surface.** Zero bash in the shipped bundle.
  Zero bash in dev-tooling scripts. Inline shell inside just recipes is
  the only place shell commands appear, and they invoke pinned tools
  only. Bash 3.2 accommodations fully retired; macOS users need only
  Python 3.10+ on PATH.
- **Runtime vs dev-time split preserved** (v005 B10). Shipped bundle
  at `.claude-plugin/` contains only what users need at livespec
  runtime. Dev-tooling at `<repo-root>/dev-tooling/` + `justfile` +
  `lefthook.yml` + `.mise.toml` + `.github/workflows/` stays outside
  the bundle.
- **Doctor static-check slug-based contract preserved.** JSON
  `check_id` values (`"doctor-<slug>"`) remain hyphenated per v005 wire
  contract; module filenames are snake_case per Python convention;
  slug↔module mapping is one-point in `doctor/run_static.py`.
- **Enforcement suite stays invocation-agnostic** (v005 B18). pre-
  commit, pre-push, CI, manual invocation are all consumers of justfile
  targets. New `check-no-direct-tool-invocation` target prevents
  cross-surface duplication.
- **mise-for-tool-versions preserved** (v005 B19). `.mise.toml` pins
  Python (3.10+), just, pyright, ruff, pytest, pytest-cov,
  pytest-icdiff, lefthook, and anything else the enforcement suite
  needs.
- **Recreatability.** A competent implementer can generate the
  livespec plugin + built-in template + sub-commands + enforcement
  suite + dev-tooling from v006 PROPOSAL.md +
  `livespec-nlspec-spec.md` + new
  `python-skill-script-style-requirements.md` alone.
- **Cross-doc consistency.** PROPOSAL.md and Python style doc agree on:
  Python version floor, vendored-libs list, layout tree, ROP
  discipline, purity rule, exit-code contract, enforcement targets,
  per-directory CLAUDE.md mandate.

## Outstanding follow-ups

Filed as first-batch post-seed `propose-change`s for v006:

- Authoring each template prompt's input/output JSON schemas and the
  concrete prompt contents.
- Migrating brainstorming-folder companion documents
  (`subdomains-and-unsolved-routing.md`, `prior-art.md`, etc.) into the
  seeded `SPECIFICATION/`.
- Authoring each enforcement-check script under `dev-tooling/checks/`
  per the target list in P10.
- Authoring the concrete CLAUDE.md contents (v006 locks the coverage
  mandate; exact prose TBD at implementation).
- Authoring the justfile and lefthook.yml and GitHub Actions workflow
  per the shape in P10.

## What was rejected

Nothing was rejected outright. Four classes of reshape occurred during
the interview:

- **Over-engineered initial proposals** that the user simplified:
  P10's target-vs-orchestration conflation; P11's single-supervisor-
  monolith-executable framing (multiple entry points were correct);
  P11's Tier 1 / Tier 2 DSL split (unnecessary for livespec's fixed
  command set); P11's per-check-executables proposal (unnecessary
  given ROP composition); P14's console-renderer option
  (pipe-to-jq supplants the need); P16's hyphenated filenames
  (no human users; snake_case is the standard).
- **Scope creep reversed by user** on P3 (vendoring authorized,
  expanded beyond stdlib-only); P14 (JSON logging mandatory, not
  optional); P21 (Result library vendored, not hand-rolled); P22
  (CLAUDE.md coverage added, not originally in the plan).
- **Premature convergence pulled back** at P11 when the user pointed
  out I had not actually read the reference ROP project the prompt
  named; I re-read the reference and then the user correctly argued
  against blindly adopting its Tier 1 / Tier 2 split because
  livespec's context differs.
- **Retracted recommendations** at P10 (initial Makefile-targets-in-
  isolation framing); P11 (repeated iterations); P16 (hyphenated
  filenames).
