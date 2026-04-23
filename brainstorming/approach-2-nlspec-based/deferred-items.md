# Deferred Items

Canonical tracking list for implementation work that PROPOSAL.md
intentionally defers to first-batch propose-changes after `livespec
seed`. Each entry is the source-of-truth that future revisions must
update; PROPOSAL.md's `Self-application` section references this
file rather than duplicating its contents.

## Discipline

- **Each brainstorming revision MUST enumerate every deferred item
  carried forward from the previous version, plus any new items
  surfaced by the revision.** Removed items require an explicit
  explanation in the revision (i.e., "resolved by item X" or
  "no longer applicable because Y").
- **Items are addressed via post-seed `livespec propose-change`
  invocations.** When `livespec` itself is seeded against this
  brainstorming directory, this file's entries become the first
  batch of work to file as proposed changes.
- **Items have stable ids** (`kebab-case`), which serve as
  the topic/filename for the eventual propose-change file
  (`SPECIFICATION/proposed_changes/<id>.md`).

## Item schema

Each entry uses this shape:

```
### <id>

- **Source:** <which version surfaced this item, e.g. v002 / v003 /
  v004 / v005 / v006 / v007 / v008 / v009 / v010 / v011 / v012>
- **Target spec file(s):** <repo-root-relative path(s)>
- **How to resolve:** <one paragraph describing what the eventual
  propose-change must produce>
```

## Items

### template-prompt-authoring

- **Source:** v001 (carried forward through every version; scope widened in v011 per K5)
- **Target spec file(s):** `SPECIFICATION/spec.md`,
  `SPECIFICATION/contracts.md` (skill↔template I/O contracts),
  `specification-templates/livespec/prompts/*.md`
- **How to resolve:** Author each template prompt's input/output
  JSON Schemas (in `.claude-plugin/scripts/livespec/schemas/`) and the prompt
  bodies themselves under
  `specification-templates/livespec/prompts/{seed,propose-change,
  revise,critique}.md`. Cover: variables the skill provides as
  input, the JSON contract the prompt MUST emit, retry semantics
  on schema-validation failure. Each `livespec`-template prompt
  MUST Read `../livespec-nlspec-spec.md` (template-root-relative)
  at the start of its execution as NLSpec reference context; this
  is template-internal (the skill no longer injects it per v011 K5).
  v011 K5 adds two more prompts for the built-in livespec template:
  `specification-templates/livespec/prompts/doctor-llm-objective-checks.md`
  (skill-configurable via `doctor_llm_objective_checks_prompt` in
  `template.json`; OPTIONAL — livespec template MAY leave it unset
  in v1) and
  `specification-templates/livespec/prompts/doctor-llm-subjective-checks.md`
  (skill-configurable via `doctor_llm_subjective_checks_prompt`;
  REQUIRED for the built-in template because it hosts the NLSpec-
  conformance evaluation + template-compliance semantic judgments
  that v010 had as skill-baked "subjective checks"). The
  doctor-subjective prompt MUST Read `../livespec-nlspec-spec.md`
  template-internally.

### python-style-doc-into-constraints

- **Source:** v005 (carried forward through every version since)
- **Target spec file(s):** `SPECIFICATION/constraints.md`
- **How to resolve:** Migrate
  `python-skill-script-style-requirements.md` into
  `SPECIFICATION/constraints.md` at seed time, restructured for the
  spec's heading conventions and BCP 14 requirement language.

### companion-docs-mapping

- **Source:** v001 (carried forward through every version)
- **Target spec file(s):** various within `SPECIFICATION/`
- **How to resolve:** Map brainstorming-folder companion documents
  to their destinations in the seeded spec:
  - `subdomains-and-unsolved-routing.md` → spec.md "Non-goals"
    appendix or similar.
  - `prior-art.md` → spec.md "Prior Art" appendix.
  - `goals-and-non-goals.md` → spec.md introduction + non-goals.
  - The four 2026-04-19 lifecycle / terminology docs → spec.md
    "Lifecycle" section + diagram references.

### enforcement-check-scripts

- **Source:** v005 (carried forward; scope widened in v011 per K4; scope widened in v012 per L4, L5, L7, L8, L9, L10, L12, L15a; scope widened in v013 per M6)
- **Target spec file(s):** `SPECIFICATION/constraints.md` +
  `<repo-root>/dev-tooling/checks/` + `<repo-root>/pyproject.toml`
  (`[tool.importlinter]` section per v012 L15a)
- **How to resolve:** Author each enforcement-check Python script
  per the canonical `just` target list in
  `python-skill-script-style-requirements.md`. The v012 list
  reflects L15a's adoption of Import-Linter at the dev-tooling
  layer (replacing v011's planned `check-purity`,
  `check-import-graph`, and the import-surface portion of
  `check-no-raise-outside-io`):
  - **Hand-written AST checks (still required in v012):**
    `check-private-calls`, `check-global-writes`,
    `check-supervisor-discipline`,
    `check-no-raise-outside-io` (raise-site portion only;
    import-surface portion delegated to
    `check-imports-architecture`),
    `check-no-except-outside-io`,
    `check-public-api-result-typed` (rescoped per L9 to use
    `__all__`-based public detection rather than underscore
    convention),
    `check-main-guard`, `check-wrapper-shape`,
    `check-schema-dataclass-pairing` (widened to three-way
    walker per v013 M6 — validates schema ↔ dataclass ↔
    validator),
    `check-claude-md-coverage`,
    `check-no-direct-tool-invocation`, `file_lloc`,
    `check-keyword-only-args` (v011 K4 + v012 L4: AST-walks
    `@dataclass` decorators; verifies `frozen=True`,
    `kw_only=True`, AND `slots=True` are all present; verifies
    every `def` has `*` separator),
    `check-match-keyword-only` (v011 K4).
  - **New AST checks (v012):**
    - `check-no-inheritance` (L5; AST: rejects `class X(Y):`
      where `Y` not in allowlist).
    - `check-assert-never-exhaustiveness` (L7; AST: every
      `match` ends in `case _: assert_never(<subject>)`;
      conservative scope).
    - `check-newtype-domain-primitives` (L8; AST: walks
      `schemas/dataclasses/*.py` and function signatures;
      verifies role-named fields use the corresponding
      `livespec/types.py` NewType).
    - `check-all-declared` (L9; AST: every module under
      `livespec/**` declares module-top `__all__: list[str]`;
      verifies every name in `__all__` resolves in the module).
    - `check-no-write-direct` (L10; AST: bans
      `sys.stdout.write` and `sys.stderr.write` calls outside
      `bin/_bootstrap.py`).
    - `check-pbt-coverage-pure-modules` (L12; AST: every test
      module under `tests/livespec/parse/` and
      `tests/livespec/validate/` declares ≥1 `@given(...)`-
      decorated test).
  - **New AST / grep-level checks (v013):**
    - `check-no-todo-registry` (M8; grep-level:
      `dev-tooling/checks/no_todo_registry.py` walks
      `tests/heading-coverage.json` and rejects any
      `test: "TODO"` entry regardless of `reason`;
      release-gate only, NOT included in `just check`).
  - **Import-Linter target (v012 L15a):**
    `check-imports-architecture` invokes `lint-imports` against
    declarative `[tool.importlinter]` contracts in
    `pyproject.toml`. Three contracts replace the planned
    hand-written checks:
    - `forbidden` contract for `parse/` + `validate/` (no
      imports from `io/` or effectful APIs) — replaces planned
      `check-purity`.
    - `layers` contract (no circular imports; layered
      architecture) — replaces planned `check-import-graph`.
    - `forbidden` contract for `LivespecError` subclass imports
      outside `io/**` and `errors.py` (raise-discipline import
      surface) — replaces import-surface portion of planned
      `check-no-raise-outside-io`. Raise-site AST portion
      remains hand-written.
  - **Release-gate target (v012 L13):** `check-mutation`
    invokes `mutmut run` against `livespec/parse/` and
    `livespec/validate/`; threshold ≥80% kill rate; NOT in
    `just check`; runs only on release-tag CI workflow.
  - Includes: test fixtures, edge-case parameterizations,
    exit-code mapping.

### claude-md-prose

- **Source:** v006 (carried forward through every version since)
- **Target spec file(s):** `<bundle>/scripts/**/CLAUDE.md`,
  `<repo-root>/tests/**/CLAUDE.md` (with `tests/fixtures/` excluded
  per H15),
  `<repo-root>/dev-tooling/**/CLAUDE.md` (excluding `_vendor/`
  subtree per G7)
- **How to resolve:** Author each per-directory `CLAUDE.md` with
  directory-local constraints an agent working there must satisfy.
  Concise (typically <50 lines); links to
  `python-skill-script-style-requirements.md` for global rules.
  v012-relevant directory-local notes worth including:
  `livespec/parse/CLAUDE.md` and `livespec/validate/CLAUDE.md`
  note the L12 Hypothesis PBT requirement (each test module
  here MUST have ≥1 `@given(...)`-decorated function);
  `livespec/types.py` (single file; no CLAUDE.md required) is
  the canonical NewType-aliases location per L8;
  `livespec/io/CLAUDE.md` notes that supervisor-stdout-write
  exemptions (per L10) apply to `commands/<cmd>.py::main()`
  and `doctor/run_static.py::main()` only, not to `io/`
  helpers.

### task-runner-and-ci-config

- **Source:** v006 (widened v009 I3; widened v010 per J8, J9, J10; widened v011 per K3, K4; widened v012 per L1, L2, L3, L6, L10, L11, L12, L13, L15a; widened v013 per M1, M3, M7, M8)
- **Target spec file(s):** `<repo-root>/justfile`,
  `<repo-root>/lefthook.yml`,
  `<repo-root>/.github/workflows/ci.yml`,
  `<repo-root>/.mise.toml`,
  `<repo-root>/pyproject.toml`,
  `<repo-root>/.vendor.jsonc` (v010 J9: renamed from `.vendor.toml`
  to avoid requiring a new `tomli` vendored dep; the already-
  vendored `jsoncomment` parses it).
- **How to resolve:** Author the actual config files per the
  patterns in `python-skill-script-style-requirements.md`.
  Includes: `just bootstrap` target (G16; also creates the
  `.claude/skills/ → ../.claude-plugin/skills/` dogfood symlink
  per I11 — and v010 J12 made that symlink a committed tracked
  symbolic link, so `just bootstrap` is defensive rather than
  mandatory), `just check` aggregation behavior (G15), CI matrix
  with `fail-fast: false`, pinned tool versions,
  ruff/pyright/pytest/coverage configuration (including
  `max-args=6` + `max-positional-args=6` per H5, AND coverage
  `source` extended to include `.claude-plugin/scripts/bin/` per v010 J8 so
  `_bootstrap.py` lands in the 100% line+branch surface), the
  recorded vendored-lib versions (including `jsoncomment` per
  H2), AND the new `check-schema-dataclass-pairing` target (I3).
  Also pick up the narrowed `check-no-raise-outside-io` and
  `check-no-except-outside-io` targets per I10, AND the
  mutually-exclusive `--skip-pre-check` / `--run-pre-check` flag
  pair in pre-step-having sub-command wrappers per v010 J10
  (lefthook pre-commit/pre-push hook invocations of those
  sub-commands must pass one of the two flags OR neither,
  defaulting to the config value), AND the new
  `check-keyword-only-args` + `check-match-keyword-only` just
  targets per v011 K4, AND the removal of any `[tool.coverage.run]
  omit` entry for `bin/*.py` wrapper bodies per v011 K3 (wrappers
  are now covered by per-wrapper tests at `tests/bin/test_<cmd>.py`
  rather than pragma-excluded). `pyproject.toml`'s coverage
  `source` list covers `.claude-plugin/scripts/bin/**` uniformly; no special-case
  omit for wrapper files. If the pyproject-generating recipe writes
  any per-wrapper pragma application, remove it.

  **v012 additions:**
  - **`[tool.pyright]` strict-plus diagnostics (L1 + L2):**
    set `reportUnusedCallResult = "error"`,
    `reportImplicitOverride = "error"`,
    `reportUninitializedInstanceVariable = "error"`,
    `reportUnnecessaryTypeIgnoreComment = "error"`,
    `reportUnnecessaryCast = "error"`,
    `reportUnnecessaryIsInstance = "error"`,
    `reportImplicitStringConcatenation = "error"`.
  - **`typing_extensions` resolution (v013 M1 CLOSED):** the
    v012-era open follow-up is closed. `typing_extensions` is
    vendored as a minimal shim at
    `.claude-plugin/scripts/_vendor/typing_extensions/__init__.py`
    exporting exactly `override` and `assert_never`, retaining
    the `typing_extensions` module name so pyright's
    `reportImplicitOverride` (L2) and
    `check-assert-never-exhaustiveness` (L7) recognize the
    import path. Vendored-libs license policy extended to admit
    PSF-2.0 narrowly for this one library (see style doc
    §"Vendored third-party libraries"). Uniform import
    discipline: `from typing_extensions import override,
    assert_never` everywhere in `livespec/**`. Future widening
    of the shim to re-export additional symbols is a one-line
    edit; re-vendoring full upstream is a scope-widening
    decision. NO mise-pinning of `typing_extensions` (it's
    vendored, not dev-only).
  - **Ruff rule selection expansion (L3 + L10 + L11):** the
    v012 selection is `E F I B UP SIM C90 N RUF PL PTH TRY FBT
    PIE SLF LOG G TID ERA ARG RSE PT FURB SLOT ISC T20 S` (16
    categories added above v011's 11; 27 total). Per-category
    configuration tuning is implementer choice.
  - **TID banned-imports config (L6 + L11):**
    `[tool.ruff.lint.flake8-tidy-imports]` sets
    `ban-relative-imports = "all"` and a banned-imports list
    containing `abc.ABC`, `abc.ABCMeta`, `abc.abstractmethod`,
    `pickle`, `marshal`, `shelve`.
  - **Hypothesis + hypothesis-jsonschema mise pins (L12):**
    `.mise.toml` adds `hypothesis` (HypothesisWorks/hypothesis,
    MPL-2.0) and `hypothesis-jsonschema` (MIT) as test-time
    dev deps. NOT vendored in bundle; mise-pinned only. The
    MPL-2.0 license-policy expansion is NOT needed (vendored-
    libs license policy applies only to bundle-vendored libs).
  - **mutmut mise pin + release-gate workflow (L13):**
    `.mise.toml` adds `mutmut` (MIT). `just check-mutation`
    target added; release-tag CI workflow runs it; per-commit
    CI does NOT.
  - **Import-Linter mise pin + pyproject config (L15a):**
    `.mise.toml` adds `import-linter` (BSD-2).
    `pyproject.toml` adds `[tool.importlinter]` section with
    three contracts (`forbidden` for purity; `layers` for
    architecture; `forbidden` for raise-discipline imports).
    `just check-imports-architecture` target added; replaces
    planned `check-purity` + `check-import-graph` + import-
    surface portion of `check-no-raise-outside-io`.
  - **L15b principle (no bundle vendoring of dev tools).**
    Hypothesis, hypothesis-jsonschema, mutmut, and Import-
    Linter are mise-pinned only. The bundle's vendored libs
    (returns, fastjsonschema, structlog, jsoncomment) are
    unchanged in v012.

  **v013 additions:**
  - **`typing_extensions` vendored as minimal shim (M1).**
    `.claude-plugin/scripts/_vendor/typing_extensions/__init__.py`
    exports `override` + `assert_never` with upstream attribution
    and PSF-2.0 `LICENSE` copied verbatim. `.mise.toml` does NOT
    pin `typing_extensions` (it's vendored, not dev-only).
    Vendored-libs license policy extended to admit PSF-2.0
    (style doc §"Vendored third-party libraries").
  - **`.mutmut-baseline.json` tracked at repo root (M3).** New
    tracked file recording initial mutation-kill-rate
    measurement; ratchet comparison bounded by absolute 80%
    ceiling. `just check-mutation` emits structured JSON
    surviving-mutants report on failure. See style doc
    §"Mutation testing as release-gate" for the schema and
    ratchet rule.
  - **Import-Linter minimum concrete configuration (M7).**
    Style doc §"Import-Linter contracts (minimum configuration)"
    codifies a canonical 25-line `[tool.importlinter]` TOML
    example with three contracts + architecture-vs-mechanism
    illustrative caveat. Deferred-entry `static-check-semantics`
    subsection now references the style-doc codified example
    rather than re-describing the three contracts.
  - **`check-no-todo-registry` release-gate target (M8).**
    New `just check-no-todo-registry` target rejects any
    `test: "TODO"` entry in `tests/heading-coverage.json`.
    Release-tag CI workflow runs it alongside `just
    check-mutation`; NOT included in `just check`; NOT run
    per-commit. Livespec-repo-internal enforcement; NOT
    shipped in the `.claude-plugin/` bundle.

### static-check-semantics

- **Source:** v007 (renamed in v008 from `ast-check-semantics`;
  scope widened per H3, H11, H13, H14; scope widened in v009 per
  I1, I4, I5, I7, I10, I3; scope widened in v010 per J4, J5, J7,
  J10, J11, J14; scope widened in v011 per K3, K4, K5, K10;
  scope widened in v012 per L4, L5, L7, L8, L9, L10, L12, L15a;
  scope widened in v013 per M1, M4, M5, M6, M7)
- **Target spec file(s):** `SPECIFICATION/constraints.md`
  (`python-skill-script-style-requirements.md` companion) and
  `SPECIFICATION/spec.md` (doctor static-check sections)
- **How to resolve:** Author the precise semantics of every
  enforcement and doctor static check, covering:
  - **AST enforcement checks** (v007 G6 scope, preserved):
    exact `ast` node types inspected (`ast.Import`,
    `ast.ImportFrom`, `ast.Call`, `ast.Raise`, `ast.FunctionDef`,
    `ast.Assert`, etc.), scope globs (file patterns the check
    applies to / excludes), edge-case dispositions (deferred
    imports inside function bodies, `__all__` re-exports,
    `assert` statements, `raise StopIteration` in generators,
    `raise X from None` re-raises, `if TYPE_CHECKING:` guards,
    `# noqa` interactions) for each of the hand-written AST
    checks: `check-private-calls`, `check-global-writes`,
    `check-supervisor-discipline`, `check-no-raise-outside-io`
    (raise-site portion only per v012 L15a; import-surface
    portion delegated to `check-imports-architecture`),
    `check-no-except-outside-io`, `check-public-api-result-typed`
    (rescoped per v012 L9 to use `__all__` rather than
    underscore convention), `check-main-guard`,
    `check-wrapper-shape`, `check-schema-dataclass-pairing`,
    `check-no-inheritance` (v012 L5),
    `check-assert-never-exhaustiveness` (v012 L7),
    `check-newtype-domain-primitives` (v012 L8),
    `check-all-declared` (v012 L9),
    `check-no-write-direct` (v012 L10),
    `check-pbt-coverage-pure-modules` (v012 L12). The v011-
    planned `check-purity` and `check-import-graph` are NOT
    in this list — they were replaced in v012 L15a by the
    Import-Linter `check-imports-architecture` target.
  - **Narrowed raise / except discipline** (v009 I10):
    `check-no-raise-outside-io` accepts raising of bug-class
    exceptions (`TypeError`, `NotImplementedError`,
    `AssertionError`, `RuntimeError`, etc.) anywhere;
    forbids raising `LivespecError` subclasses (domain
    errors) outside `io/**` and `errors.py`. Mirror
    semantics for `check-no-except-outside-io`:
    catching bug-class exceptions is permitted only in the
    supervisor bug-catcher; catching domain errors outside
    `io/**` is forbidden. The AST check distinguishes
    domain-error classes from bug-class by subclass
    relationship to `LivespecError`.
  - **Supervisor bug-catcher exemption** (v009 I10):
    `check-supervisor-discipline` permits one top-level
    `try/except Exception` in each supervisor (`main()` in
    `commands/<cmd>.py` and `bin/doctor_static.py`) whose
    body logs via structlog and returns the bug-class exit
    code. This is the ONLY catch-all permitted.
  - **Supervisor public-API exemption** (v009 I4):
    `check-public-api-result-typed` exempts supervisor
    functions (by name `main` in `commands/**.py` and in
    `doctor/run_static.py`) from the Result/IOResult return
    requirement; supervisors may return `int` or `None`
    per style doc §"Type safety."
  - **`check-schema-dataclass-pairing` semantics** (v009 I3;
    widened to three-way in v013 M6):
    walks `.claude-plugin/scripts/livespec/schemas/*.schema.json`,
    `.claude-plugin/scripts/livespec/schemas/dataclasses/*.py`,
    AND `.claude-plugin/scripts/livespec/validate/*.py`. For
    each schema, asserts a paired dataclass exists at
    `schemas/dataclasses/<name>.py` (by `$id`-derived name)
    with every listed field in matching Python type, AND a
    paired validator exists at `validate/<name>.py` exporting
    `validate_<name>(payload: dict, schema: dict) ->
    Result[<Dataclass>, ValidationError]`. The walker checks
    drift in all three directions: schema without dataclass
    or validator; dataclass without schema or validator;
    validator without schema or dataclass. Any direction of
    drift fails.
  - **`check-global-writes` exemption list** (v007 G14 +
    v008 H9): `structlog.configure` in `__init__.py`,
    `structlog.contextvars.bind_contextvars` in `__init__.py`,
    and the `_COMPILED` cache mutation in
    `livespec/io/fastjsonschema_facade.py`.
  - **`check-supervisor-discipline` scope** (v008 H3):
    `livespec/**` in scope; `bin/*.py` (including
    `_bootstrap.py`) as sole exempt subtree; argparse
    `SystemExit` path impossible under `exit_on_error=False`.
    Under v009 I14: `bin/doctor_static.py`'s argparse does
    not accept `--skip-pre-check`.
  - **Markdown-parsing checks** (v008 H13, H14):
    `bcp14-keyword-wellformedness`'s enumeration of detected
    misspellings and mixed-case standalone-word rules;
    `gherkin-blank-line-format`'s fenced-block detection
    algorithm; `anchor-reference-resolution`'s GFM slug
    algorithm edge cases (case variations, non-ASCII
    headings, duplicate-heading disambiguation suffixes,
    fenced-block exclusion specifics).
  - **Doctor-cycle semantics** (v008 H11 + v009 I1, I7):
    `out-of-band-edits` pre-backfill guard glob details (exact
    file/directory patterns that trigger the guard; behavior
    when only one of the guard predicates matches; ordering of
    the guard vs the comparison), `git_head_available`
    detection logic, the skipped-check finding shape on
    non-git repos, AND the seed-exempt-from-pre-step
    semantics (I1; how the sub-command lifecycle ROP chain
    knows to elide pre-step for seed), AND `<spec-root>/`
    path parameterization from `DoctorContext.spec_root`
    applied to every path reference in every check
    (I7; includes the edge case spec_root = "./" for
    repo-root templates).
  - **`io/git.get_git_user()` semantics** (v009 I5):
    fallback behavior on missing git binary, missing config,
    unset `user.name` or `user.email`; always returns
    success with literal `"unknown"` rather than failure for
    the missing-config case; failure only on unexpected
    `git`-binary absence (domain error
    `GitUnavailableError`, exit 3).
  - **Exit code 4 for ValidationError** (v010 J4): the
    supervisor's `derive_exit_code` maps
    `IOFailure(ValidationError)` to exit `4` (retryable by
    template re-prompt), distinct from exit `3`
    (`PreconditionError` / `GitUnavailableError`;
    non-retryable). Other `LivespecError` subclasses map to
    their class-attribute `exit_code`. `bin/doctor_static.py`
    never emits `4` because it takes no JSON input.
    `HelpRequested` (not a `LivespecError`) maps to exit `0`
    after emitting help text to stdout.
  - **`build_parser` exemption in
    `check-public-api-result-typed`** (v010 J5): exempt
    functions named `build_parser` in `commands/**.py`
    alongside `main` in `commands/**.py` and
    `doctor/run_static.py`. Pure argparse factory; no effects;
    cannot fail; returns `ArgumentParser` (a framework type).
  - **Supervisor three-way pattern match for
    `HelpRequested` / `UsageError` / other
    `LivespecError`** (v010 J7): `check-supervisor-discipline`
    allows the supervisor's `derive_exit_code` to pattern-match
    three classes distinctly. `HelpRequested` is NOT a
    `LivespecError` subclass; emits text to stdout; exits 0.
    `UsageError` (a `LivespecError`) emits to stderr; exits 2.
    Other `LivespecError` subclasses emit to stderr; exit
    `err.exit_code`. Uncaught exception → supervisor's
    `try/except Exception` bug-catcher → exit 1.
  - **Mutually-exclusive pre-step flag pair** (v010 J10):
    argparse-level mutually exclusive group for
    `--skip-pre-check` / `--run-pre-check` on pre-step-having
    sub-commands (`propose-change`, `critique`, `revise`,
    `prune-history`); both flags set → `UsageError` (exit 2);
    neither → config default. `bin/doctor_static.py` rejects
    BOTH flags (supersedes v009 I14's "rejects
    `--skip-pre-check`" — now rejects both).
  - **`check-schema-dataclass-pairing` walker scope**
    (v010 J11; widened to three-way in v013 M6): walks
    `.claude-plugin/scripts/livespec/schemas/*.schema.json`,
    `.claude-plugin/scripts/livespec/schemas/dataclasses/*.py`,
    AND `.claude-plugin/scripts/livespec/validate/*.py`.
    `Finding` moved from `doctor/finding.py` to
    `schemas/dataclasses/finding.py` so both `Finding` and
    `DoctorFindings` live in the pairing-walked tree.
    Implementer choice whether `finding.schema.json` is a
    standalone schema OR the `Finding` shape is embedded as
    the `items` schema of `doctor_findings.schema.json`'s
    `findings` array (either is acceptable; check must pass
    either way).
  - **`prune-history` already-pruned precondition**
    (v010 J14): `prune-history` detects the
    "oldest-surviving-is-already-`PRUNED_HISTORY.json`"
    state before step 4 and short-circuits with an
    informational `status: "skipped"` finding; no marker
    re-write.
  - **Wrapper coverage via per-wrapper tests**
    (v011 K3): No `# pragma: no cover` is applied to any
    `bin/*.py` wrapper body. Each wrapper has
    `tests/bin/test_<cmd>.py` that imports it and catches
    `SystemExit` via `pytest.raises`, with `monkeypatch` stubbing
    the target `main` to a no-op. Coverage.py's tracer registers
    every line of the 6-line body under test. Wrapper-shape rule
    preserved unchanged; `check-wrapper-shape` + `test_wrappers.py`
    meta-test verify shape in parallel to per-wrapper coverage
    tests.
  - **`check-keyword-only-args` semantics**
    (v011 K4): AST walker over `.claude-plugin/scripts/livespec/**`,
    `.claude-plugin/scripts/bin/**`, and `<repo-root>/dev-tooling/**`. For every
    `ast.FunctionDef` / `ast.AsyncFunctionDef`, `args.args` MUST
    be empty after `self`/`cls` (all declared params in
    `args.kwonlyargs`). For every `@dataclass` decorator, the
    invocation MUST include `kw_only=True` as a keyword arg.
    **Exemptions:** dunder methods with Python-mandated positional
    signatures (`__eq__(self, other)`, `__hash__(self)`,
    `__getitem__(self, key)`, `__iter__(self)`, `__next__(self)`,
    `__contains__(self, item)`, etc.; enumeration codified in
    this deferred entry); `__init__` of Exception subclasses when
    the body does `super().__init__(<single-positional>)` and no
    other effects; `__post_init__(self)` on dataclasses.
  - **`check-match-keyword-only` semantics**
    (v011 K4): AST walker over every `ast.Match` statement in
    livespec scope. Each `ast.MatchClass` whose class name
    resolves (by AST-level name resolution, walking `import` /
    `from ... import` statements in the containing module) to
    a livespec-authored class MUST bind attributes via
    `kwd_patterns` (keyword sub-patterns). `patterns` (positional
    sub-patterns) MUST be empty for livespec-authored classes.
    **Exemption:** classes whose resolution names come from
    third-party libraries (notably `dry-python/returns`'s
    `IOFailure`, `IOSuccess`, `Result.Success`, `Result.Failure`)
    — positional destructure permitted since those libraries
    define `__match_args__` idiomatically.
  - **Doctor-static domain-failure-to-fail-Finding discipline**
    (v011 K10): doctor-static checks MUST map domain-meaningful
    failure modes to `IOSuccess(Finding(status="fail", ...))`, not
    `IOFailure(err)`. `IOFailure` reserved for boundary errors
    where the check cannot continue (I/O read failure on the
    target file itself, not validation-against-content). Preserves
    the invariant "`bin/doctor_static.py` never emits exit 4."
  - **Template-extension doctor-static check loading**
    (v011 K5): `template.json`'s
    `doctor_static_check_modules: list[str]` names paths relative
    to the template root. `livespec/doctor/run_static.py` loads
    each via `importlib.util.spec_from_file_location(...)` +
    `module_from_spec(...)` + `loader.exec_module(...)`. Each
    loaded module MUST export
    `TEMPLATE_CHECKS: list[tuple[str, CheckRunFn]]`
    (same shape as the skill-internal static registry's exported
    `CHECKS`). Template-extension checks compose after skill-baked
    checks in the ROP chain; SLUGs MUST NOT collide with skill-
    baked SLUGs (the orchestrator rejects duplicates at registry-
    assembly time with an IOFailure). **Extension-loaded modules
    are out of scope for the enforcement suite** per v012's user-
    provided-extensions principle (no pyright / ruff / AST-check /
    Import-Linter / Hypothesis / mutmut application to them; only
    the `TEMPLATE_CHECKS` export shape and `CheckRunFn` /
    `Finding` contract apply).
  - **Extended `check-keyword-only-args` semantics**
    (v012 L4): walker additionally verifies each `@dataclass`
    decorator's call expression includes ALL THREE keyword
    arguments `frozen=True`, `kw_only=True`, AND `slots=True`.
    Missing any one fails. Existing v011 K4 exemptions
    (Python-mandated dunders; Exception `__init__` forwarding;
    `__post_init__`) still apply at the function-signature
    layer; do not apply to the dataclass decorator.
  - **`check-no-inheritance` semantics**
    (v012 L5; TIGHTENED in v013 M5): AST walker over
    `.claude-plugin/scripts/livespec/**`,
    `.claude-plugin/scripts/bin/**`,
    `<repo-root>/dev-tooling/**`. For every `ast.ClassDef`
    with non-empty `bases`, inspect each base; reject unless
    base name resolves (by AST-level name resolution; imports
    walked) to a class in the **direct-parent allowlist**:
    `{Exception, BaseException, LivespecError, Protocol,
    NamedTuple, TypedDict}`. The v013 M5 tightening removes
    the v012-era transitive-subclass acceptance: `LivespecError`
    subclasses (`UsageError`, `ValidationError`, etc.) are NOT
    acceptable bases. `class RateLimitError(UsageError):` is
    rejected even though `UsageError` is itself a
    `LivespecError` subclass; `class RateLimitError(LivespecError):`
    is accepted. This enforces the v012 revision-file leaf-
    closed intent mechanically. Exemptions: vendored libs
    (out of scope by §"Scope"); `_vendor/**` (excluded).
  - **`check-assert-never-exhaustiveness` semantics**
    (v012 L7): AST walker over every `ast.Match` node in scope.
    The final `case_block` MUST have its pattern be
    `MatchAs(pattern=None, name=None)` (the bare `case _:` form)
    AND its body MUST consist of exactly one statement: an
    `ast.Expr` containing an `ast.Call` whose function name
    resolves to `assert_never` imported from `typing_extensions`
    (per v013 M1 uniform-import discipline; the check MUST
    match the `typing_extensions` module-named import path
    specifically so a stray `from typing import assert_never`
    is itself a failure at this check). The call's single
    argument is an `ast.Name` matching the match-statement's
    subject name. Any deviation fails. Conservative scope
    (every `match`, regardless of subject type) is the
    load-bearing decision per v012 L7's recommendation.
  - **`check-newtype-domain-primitives` semantics**
    (v012 L8): AST walker over
    `livespec/schemas/dataclasses/*.py` and `livespec/**.py`
    function signatures. The check source enumerates the
    canonical field-name → NewType mapping. The mapping accepts
    the field names actually used in PROPOSAL.md / context
    dataclasses (which precede v012 L8 and don't all match the
    NewType base name): `check_id` → `CheckId`, `run_id` →
    `RunId`, `topic` → `TopicSlug` (note: field name is `topic`
    not `topic_slug`; NewType name carries the disambiguating
    suffix), `spec_root` → `SpecRoot`, `schema_id` → `SchemaId`,
    `template` → `TemplateName` (note: field name is `template`,
    matching `.livespec.jsonc`'s `template` field; NewType name
    uses `Name` suffix to disambiguate from the
    `template_root: Path` field which uses raw `Path`),
    `author` / `author_human` / `author_llm` → `Author` (per
    K7 rename; all three field-name variants map to the same
    NewType), `version_tag` → `VersionTag`. For every dataclass
    field
    whose name matches a canonical mapping entry, the
    annotation MUST resolve to the corresponding NewType
    (imported from `livespec.types`). For every function
    parameter whose name matches a canonical entry, the
    annotation MUST resolve to the corresponding NewType.
    Mismatches in either direction (right NewType wrong field
    name; right field name wrong NewType; right field name no
    annotation) fail with the expected vs actual NewType name
    in the error.
  - **`check-all-declared` semantics**
    (v012 L9): AST walker over every `*.py` module under
    `livespec/**`. The module-top must contain an
    `ast.Assign(targets=[Name(id='__all__')],
    value=List(elts=[Constant(str), ...]))` statement (a
    module-level `__all__: list[str] = [...]` assignment).
    Each name in the list MUST resolve in the module's
    namespace (defined via `def`, `class`, top-level
    assignment, `NewType(...)` call, or imported via
    `from ... import`). Stale entries (in `__all__` but no
    matching definition) fail. The
    `check-public-api-result-typed` rule is rescoped: instead
    of inferring "public" from underscore convention, it
    inspects each name listed in `__all__` and verifies its
    return annotation is `Result[_, _]` or `IOResult[_, _]`
    per the existing exemption list. `__init__.py` files MAY
    declare `__all__` for re-exports; the check applies the
    same rule (every listed name resolves in the namespace).
  - **`check-no-write-direct` semantics**
    (v012 L10): AST walker over `livespec/**`, `bin/**`,
    `dev-tooling/**`. For every `ast.Call` whose function is an
    `ast.Attribute` resolving to `sys.stdout.write` or
    `sys.stderr.write` (after walking imports for `import sys` /
    `from sys import stdout, stderr` / aliases), reject —
    EXCEPT in three documented surfaces:
    1. File `bin/_bootstrap.py` — pre-livespec-import version-
       check stderr (structlog has not been configured at this
       point; the only legitimate `sys.stderr.write` site).
    2. Supervisor `main()` functions in
       `livespec/commands/**.py` — `sys.stdout.write` permitted
       for any documented stdout contract owned by the
       supervisor (`HelpRequested.text` per K7 / J7;
       `bin/resolve_template.py`'s single-line resolved-path
       output per K2; any future supervisor-owned stdout
       contract added to PROPOSAL.md). The exemption is
       function-scoped (only the `main` function at module
       top-level), NOT module-scoped (helpers inside the
       same `commands/<cmd>.py` module are NOT exempt).
    3. `livespec/doctor/run_static.py::main()` —
       `sys.stdout.write` of the `{"findings": [...]}` JSON
       per the doctor static-phase output contract.
    The exemption is determined by file path AND function name
    (the supervisor exemption applies only inside the
    function named `main` at module top-level, not in
    helpers). Pairs with ruff `T20` (which bans `print` /
    `pprint`); together they cover the stdout-discipline
    surface.
  - **`check-pbt-coverage-pure-modules` semantics**
    (v012 L12): AST walker over `tests/livespec/parse/*.py`
    and `tests/livespec/validate/*.py`. For each test module,
    inspect every `ast.FunctionDef` decorator list; the module
    PASSES if at least one function in the module is decorated
    with `@given(...)` (where `given` resolves to
    `hypothesis.given`). Modules with zero `@given(...)`
    decorations fail. Test modules outside `tests/livespec/
    parse/` and `tests/livespec/validate/` are out of scope.
  - **Import-Linter contract semantics** (v012 L15a; minimum
    concrete configuration codified in v013 M7): see style doc
    §"Import-Linter contracts (minimum configuration)" for the
    canonical `[tool.importlinter]` TOML example with three
    contracts:
    - **Purity contract** (`type = "forbidden"`): forbids
      imports from `livespec.parse.*` and `livespec.validate.*`
      to `livespec.io`, `subprocess`, filesystem APIs
      (`pathlib`, `open`), `returns.io`, `socket`, `http`,
      `urllib`. Replaces planned `check-purity`.
    - **Layered architecture contract** (`type = "layers"`):
      layer stack `livespec.parse` < `livespec.validate` <
      `livespec.io` < `livespec.commands | livespec.doctor`.
      Replaces planned `check-import-graph` (no circular
      imports follows by construction).
    - **Raise-discipline import contract** (`type =
      "forbidden"`): forbids `from livespec.errors import
      LivespecError | <subclass>` outside `livespec.io.*` and
      `livespec.errors`. Catches the import-side surface.
      Raise-site AST discipline (the actual `raise` statements)
      remains the responsibility of hand-written
      `check-no-raise-outside-io`, which now covers ONLY the
      raise-site portion and is correspondingly narrower.
    Architecture-vs-mechanism caveat (v009 I0): the minimum
    example in the style doc is illustrative; contract names,
    layer names, and ignore-import globs MAY be restructured so
    long as the three English-language rules (codified in the
    style doc) are enforced. Configuration tuning (root
    packages, includes/excludes) is implementer choice during
    the `enforcement-check-scripts` deferred entry's resolution.

### returns-pyright-plugin-disposition

- **Source:** v007 (carried forward through every version since)
- **Target spec file(s):** `SPECIFICATION/constraints.md`
  (`python-skill-script-style-requirements.md` companion)
- **How to resolve:** Determine and document whether the
  `dry-python/returns` pyright plugin is vendored alongside the
  library (and how it's configured in `pyrightconfig.json` or
  `[tool.pyright]`), or whether returns' own native types are
  sufficient for livespec's usage. Because `Result` and `IOResult`
  are used pervasively (not just at boundaries), the typed-facade
  pattern from G10 doesn't apply uniformly to returns; this item
  resolves the gap.

### basedpyright-vs-pyright

- **Source:** v012 (L14; new)
- **Target spec file(s):** `SPECIFICATION/constraints.md`
  (`python-skill-script-style-requirements.md` companion);
  `<repo-root>/.mise.toml`; `<repo-root>/pyproject.toml`
- **How to resolve:** Determine whether to switch from `pyright`
  to `basedpyright` (DetachHead/basedpyright, a community fork
  of pyright with ~30 stricter diagnostics enabled by default).
  basedpyright is drop-in compatible with pyright (same CLI, same
  config); switching would let several v012 L1 + L2 manual flag
  selections collapse into "use defaults," and would unlock the
  baselining system for incremental adoption.

  Tradeoffs to evaluate:
  - **+** L1's `reportUnusedCallResult` and most of L2's strict-
    plus diagnostics become defaults; less manual flag config
    in `[tool.pyright]`.
  - **+** Baselining system accepts current diagnostics as a
    baseline; only fails on regressions. Useful during initial
    adoption.
  - **−** Smaller maintainer pool than upstream pyright (a
    community fork of a Microsoft project).
  - **−** Diagnostic semantics could drift from upstream over
    time.
  - **−** v012 already accepted L1 + L2 as manual flag config;
    the marginal value of switching now is reduced.

  This is a STANDALONE deferred entry (NOT bundled with
  `returns-pyright-plugin-disposition`, which is a separate
  concern about the dry-python/returns pyright plugin's
  vendoring + configuration).

### front-matter-parser

- **Source:** v007 (carried forward; scope widened in v009 per I9/I12; scope widened in v011 per K7 and K9; scope widened in v012 per L4 and L8; scope widened in v013 per M6)
- **Target spec file(s):**
  `<bundle>/scripts/livespec/parse/front_matter.py`,
  `<bundle>/scripts/livespec/schemas/proposed_change_front_matter.schema.json`,
  `<bundle>/scripts/livespec/schemas/revision_front_matter.schema.json`
- **How to resolve:** Implement the restricted-YAML parser per the
  format restrictions codified in PROPOSAL.md "Proposed-change file
  format" and "Revision file format" (scalar-only,
  JSON-compatible, no nesting). Author two distinct JSON Schemas:
  `proposed_change_front_matter.schema.json` (fields:
  `topic`, `author`, `created_at`) and
  `revision_front_matter.schema.json` (fields: `proposal`,
  `decision`, `revised_at`, `author_human`, `author_llm` — fields
  renamed in v011 K7 from `reviser_human` / `reviser_llm` to
  eliminate the domain-term mismatch; the revision front-matter
  captures authorship of the revision decision, and propose-change
  / critique payload field names also unified to `author`).
  **No `^livespec-` pattern validation on author fields** — the
  `livespec-` prefix is a SHOULD-NOT convention per v011 K9, not
  a mechanical reservation. Schemas do not reject `livespec-`-
  prefixed user-supplied values; wrappers also do not reject them.
  Validators in `validate/` consume the parsed dict via the
  factory shape, routed through the dataclass pairing
  (`ProposedChangeFrontMatter`, `RevisionFrontMatter` dataclasses
  with correspondingly renamed fields). Per v013 M6, paired
  validators at `validate/proposed_change_front_matter.py` and
  `validate/revision_front_matter.py` are mandatory; the
  three-way `check-schema-dataclass-pairing` walker catches
  validator drift symmetrically with dataclass drift. **Both
  dataclasses use the v012 L4 strict triple
  `@dataclass(frozen=True, kw_only=True, slots=True)`** and
  **the v012 L8 NewType aliases** for `topic` (`TopicSlug`)
  and `author_human` / `author_llm`
  (`Author`).

### skill-md-prose-authoring

- **Source:** v008 (H4; widened v009 I8; widened v010 per J3, J4, J7, J10; widened v011 per K5, K6, K7; widened v013 per M4)
- **Target spec file(s):**
  `.claude-plugin/skills/<sub-command>/SKILL.md` (one per
  sub-command: `seed`, `propose-change`, `critique`, `revise`,
  `doctor`, `prune-history`, `help`)
- **How to resolve:** Author each SKILL.md body per the canonical
  body shape codified in PROPOSAL.md §"Per-sub-command SKILL.md
  body structure" (opening statement; when to invoke; inputs;
  ordered LLM-driven steps; post-wrapper behavior; failure
  handling). Cover:
  - sub-command trigger phrases;
  - Bash invocations of `bin/<cmd>.py` with explicit argv;
  - **template prompt dispatch via `bin/resolve_template.py`**
    (v010 J3): two-step flow — invoke `bin/resolve_template.py`
    via Bash, capture stdout (the resolved template directory
    path), then use Read to fetch `<path>/prompts/<name>.md`.
    Replaces v009's literal `@`-reference approach; works
    uniformly for built-in and custom templates;
  - **retry-on-wrapper-exit-4** prose (v010 J4; renamed from
    v009 I8's retry-on-exit-3; count semantics updated v013 M4):
    on exit 4 re-invoke the template prompt with error context
    from stderr and re-assemble the JSON payload, up to 2
    retries (3 attempts total: 1 initial invocation + 2
    retries). Abort on the third failing attempt. Exit 3 is
    NOT retryable (pre-step / precondition failure — surface
    findings and abort); wrappers validate internally; no
    separate validator CLI wrappers;
  - **exit 0 on `--help`** (v010 J7): help text goes to stdout
    via the `HelpRequested` supervisor path; not an error;
  - per-proposal confirmation dialogue (`revise` only);
  - **mutually-exclusive `--skip-pre-check` / `--run-pre-check`
    flag pair** (v010 J10): Inputs section for every pre-step-
    having sub-command lists both; narration for both flags
    (skip warning when `--skip-pre-check` is set or config
    default is skip=true; neutral when `--run-pre-check`
    overrides config default skip=true);
  - **two symmetric LLM-driven flag pairs** (v011 K5 +
    K6): `--skip-doctor-llm-objective-checks` /
    `--run-doctor-llm-objective-checks` and
    `--skip-doctor-llm-subjective-checks` /
    `--run-doctor-llm-subjective-checks`; both pairs LLM-layer
    only (never passed to Python wrappers); mutually exclusive
    within each pair (both set → argparse usage error exit 2);
    narration rule identical to pre-step (warn on silent skips
    only; explicit flag → self-evident, no narration). Replaces
    the v010 single `--skip-subjective-checks` flag.
  - **uniform `--author <id>` CLI flag** (v011 K7) listed
    in Inputs section of propose-change, critique, and revise
    bodies (identical precedence across all three:
    CLI → env var `LIVESPEC_AUTHOR_LLM` → payload `author` field
    → `"unknown-llm"` fallback). Critique body changes from
    v010's positional `<author>` to `--author` flag; topic
    still derived as `<resolved-author>-critique`.
  - exit-code narration (exit 0 on help; exit 2 on usage error
    including both-flags-set; exit 3 on precondition /
    doctor-static; exit 4 on schema validation; exit 1 on
    bug / unexpected exception; exit 126 / 127 on permission /
    missing tool).

- **Strictly NO skill-level injection of `livespec-nlspec-spec.md`**
  (v011 K5): SKILL.md prose MUST NOT name `livespec-nlspec-spec.md`
  or any other template-internal reference file. Template
  prompts handle their own discipline-doc injection internally
  (see `template-prompt-authoring`). Skill-level template
  interaction is limited to: reading `template.json` via
  `bin/resolve_template.py`, reading `prompts/<name>.md` via the
  two-step Bash+Read dispatch (v010 J3), reading
  `specification-template/` at seed time, and reading the two
  `doctor_llm_*_checks_prompt` paths (if `template.json` declares
  them) as additional Read-then-invoke steps during the LLM-
  driven phases.

### wrapper-input-schemas

- **Source:** v008 (H6 + H10; widened v009 per I3; widened v010 per J6; widened v011 per K2 and K7; widened v012 per L4 and L8; widened v013 per M6)
- **Target spec file(s):**
  `<bundle>/scripts/livespec/schemas/proposal_findings.schema.json`
  (renamed from `critique_findings.schema.json`),
  `<bundle>/scripts/livespec/schemas/doctor_findings.schema.json`,
  `<bundle>/scripts/livespec/schemas/seed_input.schema.json`,
  `<bundle>/scripts/livespec/schemas/revise_input.schema.json`,
  `<bundle>/scripts/livespec/schemas/template_config.schema.json`
  (NEW per v011 K5 — validates `template.json` fields including
  the three new `doctor_*_checks*` extension fields),
  AND the paired hand-authored dataclasses under
  `<bundle>/scripts/livespec/schemas/dataclasses/*.py` per I3.
- **How to resolve:** Author the five JSON Schema Draft-7 files:
  - `proposal_findings.schema.json` — propose-change / critique
    template-prompt output. Each finding has `name`,
    `target_spec_files[]`, `summary`, `motivation`,
    `proposed_changes`. Optional file-level `author` field
    (string) so the LLM can self-declare the author per the
    unified precedence (CLI `--author` → env var
    `LIVESPEC_AUTHOR_LLM` → payload `author` field →
    `"unknown-llm"` fallback; v011 K7 rename of env var from
    `LIVESPEC_REVISER_LLM`). No `^livespec-` pattern on the
    `author` field (v011 K9 — convention-only, not enforced).
  - `doctor_findings.schema.json` — doctor static-phase JSON
    output. Each finding has `check_id`, `status` (one of
    `pass`/`fail`/`skipped`), `message`, `path`, `line`.
  - `seed_input.schema.json` — seed wrapper input. Shape:
    `{files: [{path, content}], intent}`.
  - `revise_input.schema.json` — revise wrapper input. Shape:
    `{decisions: [{proposal_topic, decision, rationale,
    modifications, resulting_files: [{path, content}]}],
    author}`. File-level optional `author` field (renamed from
    `reviser_llm` per v011 K7) carries the LLM's best-effort
    self-identification; the resolved author value becomes the
    `author_llm` field on the generated revision front-matter.
  - `template_config.schema.json` (v011 K5 NEW) — validates the
    `template.json` file shipped by every template. Fields:
    `template_format_version: integer (const: 1 in v1)`,
    `spec_root: string (OPTIONAL, default "SPECIFICATION/")`,
    `doctor_static_check_modules: list[string] (OPTIONAL,
    default [])`,
    `doctor_llm_objective_checks_prompt: string | null
    (OPTIONAL, default null)`,
    `doctor_llm_subjective_checks_prompt: string | null
    (OPTIONAL, default null)`. Loaded by the `template-exists`
    doctor-static check and by `bin/resolve_template.py` (v011 K2).

  `bin/resolve_template.py` does NOT take a JSON input payload — it
  accepts only `--project-root <path>` (optional; default
  `Path.cwd()`) and emits the resolved template absolute POSIX
  path to stdout per the v011 K2 wrapper contract in PROPOSAL.md
  §"Template resolution contract."

  Also author the paired hand-authored dataclasses per I3:
  `ProposalFindings`, `DoctorFindings`, `SeedInput`,
  `ReviseInput`, `TemplateConfig` (v011 K5 new), and
  `LivespecConfig`. Each dataclass lives at
  `.claude-plugin/scripts/livespec/schemas/dataclasses/<name>.py` with fields
  matching the schema. **All dataclasses use the v012 L4 strict
  triple `@dataclass(frozen=True, kw_only=True, slots=True)`**
  (extension of K4's pre-v012 `frozen=True, kw_only=True`
  pair). **Domain-meaningful fields use the v012 L8 NewType
  aliases from `livespec/types.py`** — relevant to these
  dataclasses: `topic` → `TopicSlug`, `author` /
  `author_human` / `author_llm` → `Author`, `template`
  → `TemplateName`, `check_id` → `CheckId`. Other fields use
  underlying primitives. `check-schema-dataclass-pairing`
  (widened to three-way in v013 M6) enforces drift-free pairing
  in all three directions (schema ↔ dataclass ↔ validator);
  `check-newtype-domain-primitives` (v012 L8) enforces the
  NewType usage at the field-annotation layer.

  Validators in `.claude-plugin/scripts/livespec/validate/<name>.py` return
  `Result[<Dataclass>, ValidationError]` from the factory
  shape per v007 G4. Per v013 M6, every schema listed above
  MUST have a paired validator at `validate/<name>.py`:
  `validate/proposal_findings.py`,
  `validate/doctor_findings.py`,
  `validate/seed_input.py`,
  `validate/revise_input.py`,
  `validate/template_config.py`,
  `validate/livespec_config.py`.
  `check-schema-dataclass-pairing`'s three-way walker catches
  validator drift (missing validator file, rename, stale
  signature) symmetrically with dataclass drift.

### user-hosted-custom-templates

- **Source:** v010 (J3; new)
- **Target spec file(s):** `SPECIFICATION/spec.md` (v2+ scope
  note and future template-discovery section); potentially
  `SPECIFICATION/contracts.md` (for the resolved-template-path
  output contract of `bin/resolve_template.py` if that contract
  needs versioning).
- **How to resolve:** Codify in v2 scope (post-v1) that
  `bin/resolve_template.py` is the extensibility seam for
  future template-discovery mechanisms. v1 accepts only built-in
  names (`"livespec"`) or project-root-relative directory paths
  for `.livespec.jsonc`'s `template` field. v2+ may extend the
  resolution algorithm to support additional sources without
  breaking the wrapper's output contract (stdout = resolved
  absolute template directory path; exit 0 on success; exit 3
  on invalid template config). Candidate v2+ sources include:
  - **Remote URLs**: `https://example.com/templates/my-template`
    (fetch + cache locally; integrity-verify).
  - **Template registries**: a named registry entry resolved
    through a trust-anchored catalogue file.
  - **Plugin-path hints**: templates shipped by other Claude
    Code plugins / skills, resolved via a plugin-discovery
    mechanism.
  - **Per-environment overrides**: env var
    `LIVESPEC_TEMPLATE_OVERRIDE` pointing at an absolute
    directory path, letting users test alternate templates
    without editing `.livespec.jsonc`.

  The v1 wrapper MUST keep its output contract stable so v2
  extensions land as additive functionality. The
  `template-exists` doctor check continues to validate the
  resolved path regardless of its source.
