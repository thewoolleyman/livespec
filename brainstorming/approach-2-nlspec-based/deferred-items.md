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
  (`<spec-root>/proposed_changes/<id>.md`).

## Item schema

Each entry uses this shape:

```
### <id>

- **Source:** <which version surfaced this item, e.g. v002 / v003 /
  v004 / v005 / v006 / v007 / v008 / v009 / v010 / v011 / v012 /
  v013 / v014 / v015 / v016 / v017>
- **Target spec file(s):** <repo-root-relative path(s)>
- **How to resolve:** <one paragraph describing what the eventual
  propose-change must produce>
```

## Items

### template-prompt-authoring

- **Source:** v001 (carried forward through every version; scope widened in v011 per K5; scope widened in v014 per N1 and N9; scope widened in v015 per O4; scope widened in v016 per P2 — seed prompts for every template MUST emit the new top-level `template` field in their JSON output; scope widened in v017 per Q2 — the pre-seed template-resolution path is now `bin/resolve_template.py --template <chosen>`, so the built-in `minimal` template's `prompts/seed.md` delimiter comments — per v014 N9 — MUST include the pre-seed `resolve_template.py --template` invocation alongside the `bin/seed.py --seed-json` invocation; other templates' prompt-authoring obligations are unchanged)
- **Target spec file(s):** `SPECIFICATION/spec.md`,
  `SPECIFICATION/contracts.md` (skill↔template I/O contracts),
  `specification-templates/livespec/prompts/*.md`,
  `specification-templates/minimal/**` (v014 N1 new built-in
  template)
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

  **v014 N1 additions** (new `minimal` built-in template):
  - Author `specification-templates/minimal/template.json` with
    `template_format_version: 1` and `spec_root: "./"` (repo-root
    placement).
  - Author `specification-templates/minimal/prompts/{seed,
    propose-change,revise,critique}.md` — four REQUIRED prompts;
    minimal shape (single-file output; no Gherkin scenario
    conventions; no NLSpec-conformance Read; `minimal` does NOT
    ship `livespec-nlspec-spec.md` at its template root).
  - Author `specification-templates/minimal/specification-template/
    SPECIFICATION.md` — the single starter file.
  - `doctor_llm_{objective,subjective}_checks_prompt` in
    minimal's `template.json` MAY be null (OPTIONAL; omitting
    leaves the LLM-driven doctor phase running only the
    skill-baked checks).

  **v014 N9 delimiter-comment requirement** (minimal template
  prompts ONLY):
  - Each of `prompts/{seed,propose-change,revise,critique}.md`
    in minimal MUST include **hardcoded delimiter comments** that
    identify the wrapper invocations the v014 N9 mock harness
    performs. The real LLM treats these as inert markdown
    comments (they do not affect natural-language prompt
    interpretation); the mock parses them as directive contracts
    and invokes the wrappers deterministically.
  - The exact format (HTML comment syntax, key=value,
    JSON-in-comment, etc.) is implementer choice settled JOINTLY
    with the `end-to-end-integration-test` deferred entry. Both
    entries MUST agree on a single format.
  - Format considerations when choosing:
    - Must be invisible / inert to the real LLM (a comment
      form the LLM treats as a literal markdown comment).
    - Must be trivially parseable by the mock (simple regex
      or structured extraction).
    - Must accommodate the wrapper-call shapes needed by the
      happy path + 3 error paths in N9-D4.
  - The `livespec` template's prompts are NOT required to
    include delimiter comments — the mock tier doesn't run
    against the `livespec` template.

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

- **Source:** v005 (carried forward; scope widened in v011 per K4; scope widened in v012 per L4, L5, L7, L8, L9, L10, L12, L15a; scope widened in v013 per M6; v014 N2 and N4 affect sibling entries — `wrapper-input-schemas` and `static-check-semantics` — not this entry's scope; v016 P5 widens `check_wrapper_shape.py`'s algorithm to permit the optional blank line per the `static-check-semantics` subsection; v016 P1 and P3 likewise affect `static-check-semantics` sibling subsections without adding a new check script; scope widened in v017 per Q3 — `check-no-raise-outside-io`'s scope expands back to cover the raise-discipline fully (raise-site enforcement is the sole enforcement point; the v012 L15a import-surface delegation to Import-Linter is retracted))
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
  - **Hand-written AST checks (still required in v012; v017 Q3
    restores `check-no-raise-outside-io` to raise-site-only
    full scope for the raise-discipline):**
    `check-private-calls`, `check-global-writes`,
    `check-supervisor-discipline`,
    `check-no-raise-outside-io` (v017 Q3: raise-site
    enforcement is the SOLE enforcement point for the raise-
    discipline; the v012 L15a import-surface delegation to
    `check-imports-architecture` is retracted because
    Import-Linter cannot distinguish import-for-raising from
    import-for-annotating),
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
  - **Import-Linter target (v012 L15a; narrowed in v017 Q3):**
    `check-imports-architecture` invokes `lint-imports` against
    declarative `[tool.importlinter]` contracts in
    `pyproject.toml`. Two contracts (v017 Q3: retracted the
    third) replace a subset of the planned hand-written
    checks:
    - `forbidden` contract for `parse/` + `validate/` (no
      imports from `io/` or effectful APIs) — replaces planned
      `check-purity`.
    - `layers` contract (no circular imports; layered
      architecture) — replaces planned `check-import-graph`.
    **Retracted (v017 Q3):** the third contract (`forbidden`
    for `LivespecError` subclass imports outside `io/**` and
    `errors.py`) is NOT included because Import-Linter cannot
    distinguish import-for-raising from import-for-annotating,
    and blanket-forbidding the imports would block legitimate
    type-annotation and `match`-pattern uses of error types in
    `commands/`, `doctor/`, and `validate/` modules. The full
    raise-discipline lives in hand-written
    `check-no-raise-outside-io` (raise-site only); no import-
    surface Import-Linter contract is defined.
  - **Release-gate target (v012 L13):** `check-mutation`
    invokes `mutmut run` against `livespec/parse/` and
    `livespec/validate/`; threshold ≥80% kill rate; NOT in
    `just check`; runs only on release-tag CI workflow.
  - Includes: test fixtures, edge-case parameterizations,
    exit-code mapping.

### claude-md-prose

- **Source:** v006 (carried forward through every version since; note-only widening in v017 per Q9 — `livespec/io/CLAUDE.md` SHOULD note the shared `upward-walk` helper for `.livespec.jsonc` location lives under `livespec.io.fs`, reused by every wrapper and by `livespec.doctor.run_static`)
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

- **Source:** v006 (widened v009 I3; widened v010 per J8, J9, J10; widened v011 per K3, K4; widened v012 per L1, L2, L3, L6, L10, L11, L12, L13, L15a; widened v013 per M1, M3, M7, M8; widened v014 per N9; widened v017 per Q3 — pyproject.toml `[tool.importlinter]` narrows from three contracts to two; the third L15a-proposed contract covering the raise-discipline import surface is retracted)
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
  - **Import-Linter mise pin + pyproject config (L15a;
    narrowed in v017 Q3):**
    `.mise.toml` adds `import-linter` (BSD-2).
    `pyproject.toml` adds `[tool.importlinter]` section with
    two contracts (`forbidden` for purity; `layers` for
    architecture). The third L15a-proposed contract
    (`forbidden` for raise-discipline imports) is retracted
    in v017 Q3 — see `static-check-semantics` for rationale.
    `just check-imports-architecture` target added; replaces
    planned `check-purity` + `check-import-graph`. The
    import-surface portion of `check-no-raise-outside-io`
    is NOT replaced (v017 Q3 retracted the claim);
    `check-no-raise-outside-io` remains hand-written and
    covers the raise-discipline fully via raise-site
    enforcement.
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
  - **Import-Linter minimum concrete configuration (M7;
    narrowed in v017 Q3 from three contracts to two).**
    Style doc §"Import-Linter contracts (minimum configuration)"
    codifies a canonical `[tool.importlinter]` TOML example
    with two contracts + architecture-vs-mechanism illustrative
    caveat (v013 M7's original configuration was a three-contract
    example; v017 Q3 retracted the third — the raise-discipline
    import-surface contract — leaving purity and layered
    architecture only). Deferred-entry `static-check-semantics`
    subsection now references the style-doc codified example
    rather than re-describing the contracts.
  - **`check-no-todo-registry` release-gate target (M8).**
    New `just check-no-todo-registry` target rejects any
    `test: "TODO"` entry in `tests/heading-coverage.json`.
    Release-tag CI workflow runs it alongside `just
    check-mutation`; NOT included in `just check`; NOT run
    per-commit. Livespec-repo-internal enforcement; NOT
    shipped in the `.claude-plugin/` bundle.

  **v014 additions:**
  - **Two new just targets for E2E integration test (N9).**
    `just e2e-test-claude-code-mock` — part of `just check`,
    per-commit cadence. Shared pytest suite; env var
    `LIVESPEC_E2E_HARNESS=mock` selects the livespec-
    authored API-compatible pass-through mock at
    `<repo-root>/tests/e2e/fake_claude.py`.
    `just e2e-test-claude-code-real` — NOT in `just check`;
    uses `LIVESPEC_E2E_HARNESS=real` to select the real
    `claude-agent-sdk`. Requires `ANTHROPIC_API_KEY`.
    Locally invokable.
  - **Two new GitHub Actions workflows for the real
    E2E target (N9-D3):**
    - `<repo-root>/.github/workflows/e2e-real.yml` (or
      similar name; implementer choice) triggered by THREE
      events:
      - `on: merge_group` — pre-merge check via GitHub
        merge queue. Requires merge queue enabled in
        branch-protection settings for the repo.
      - `on: push` with `branches: [master]` — every
        master-branch commit (covers merged PRs and
        direct pushes).
      - `on: workflow_dispatch` — manual invocation on
        any branch via the GitHub Actions UI (useful for
        developers validating a WIP PR before merging).
    The per-commit CI workflow (existing
    `ci.yml`) runs `just check` which includes the mock
    E2E target; no change required to per-commit CI
    structure.
  - **`claude-agent-sdk` mise-pin (N9-D5).** `.mise.toml`
    pins `claude-agent-sdk` as a test-time dev dep (for
    the real E2E tier). Mise-pinned only; NOT vendored
    (per the v015 L15b test-dep packaging convention).
  - **`ANTHROPIC_API_KEY` env var contract.** CI's real
    E2E workflows mount `ANTHROPIC_API_KEY` from GitHub
    secrets. The mock E2E target does NOT require the
    env var. See `end-to-end-integration-test` deferred
    entry for fixture and assertion details.
  - **Coverage scope clarification.** `tests/e2e/` is
    NOT subject to the 100% line+branch coverage mandate
    (existing rule already excludes `tests/`). The mock
    executable at `tests/e2e/fake_claude.py` is test
    infrastructure, not shipped Python; existing
    coverage carve-out for `tests/` applies.

### static-check-semantics

- **Source:** v007 (renamed in v008 from `ast-check-semantics`;
  scope widened per H3, H11, H13, H14; scope widened in v009 per
  I1, I4, I5, I7, I10, I3; scope widened in v010 per J4, J5, J7,
  J10, J11, J14; scope widened in v011 per K3, K4, K5, K10;
  scope widened in v012 per L4, L5, L7, L8, L9, L10, L12, L15a;
  scope widened in v013 per M1, M4, M5, M6, M7; scope widened in
  v014 per N2, N3, N4, N5, N6, C3; scope widened in v015 per O3;
  scope widened in v016 per P1, P3, P5; scope widened in v017
  per Q1, Q3, Q7, Q9 — Q1 makes this entry the sole source-of-
  truth for the reserve-suffix algorithm; Q3 narrows the
  Import-Linter contract enumeration to two contracts and
  drops the raise-discipline import-surface contract; Q7
  codifies `revision-to-proposed-change-pairing` as a
  filename-stem walk distinct from the front-matter `topic`
  field; Q9 cross-references the uniform `--project-root`
  helper in `livespec.io.fs`)
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
    (v012 L15a delegated the import-surface portion to
    `check-imports-architecture`; v017 Q3 retracted that
    delegation because Import-Linter cannot distinguish
    import-for-raising from import-for-annotating, so
    `check-no-raise-outside-io` covers the raise-site only
    AND is the sole enforcement point for the raise-
    discipline — `livespec.errors` MAY be imported anywhere
    it is referenced),
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
    (v010 J11; widened to three-way in v013 M6; v014 N2
    closes the implementer-choice on `finding.schema.json`):
    walks `.claude-plugin/scripts/livespec/schemas/*.schema.json`,
    `.claude-plugin/scripts/livespec/schemas/dataclasses/*.py`,
    AND `.claude-plugin/scripts/livespec/validate/*.py`.
    `Finding` moved from `doctor/finding.py` to
    `schemas/dataclasses/finding.py` so both `Finding` and
    `DoctorFindings` live in the pairing-walked tree. **Per
    v014 N2, `finding.schema.json` is REQUIRED as a standalone
    schema; the v010 J11 implementer-choice language
    ("standalone schema OR embedded as items of
    doctor_findings.schema.json's findings array") is CLOSED.
    Standalone is the single v1 form.** Paired validator at
    `validate/finding.py` is likewise REQUIRED. Three-way
    symmetry is uniform; no by-name exemption for `Finding`.
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
    every statement of the 6-statement body under test. Wrapper-
    shape rule preserved unchanged; `check-wrapper-shape` +
    `test_wrappers.py` meta-test verify shape in parallel to
    per-wrapper coverage tests.
  - **`check-wrapper-shape` algorithm** (v016 P5): the
    AST-lite check accepts a wrapper file whose AST module
    body consists of EXACTLY the six statements listed in
    PROPOSAL.md §"Shebang-wrapper contract" in order
    (the shebang and docstring count as one each for AST
    purposes; `from _bootstrap import bootstrap`;
    `bootstrap()`; `from livespec.<module>.<submodule> import main`;
    `raise SystemExit(main())`). The check operates on the
    AST module body, which naturally discards whitespace-only
    lines, so the optional blank line between the import
    block and the `raise SystemExit(main())` statement is
    accepted automatically. The `test_wrappers.py` meta-test
    applies the same algorithm. Implementations MUST NOT
    enforce a literal line count on the file text (the v015
    "6-line shape" phrasing was self-contradictory with the
    canonical example and is superseded by the 6-statement
    framing).
  - **`anchor-reference-resolution` walk set** (v016 P1):
    the check's walk is scoped to the active template's
    declared spec artifact set, NOT a `<spec-root>/**` glob.
    The walk set is computed by:
    1. Resolve the active template's declared spec file set
       from its `specification-template/` walk (see v011 K2
       template resolution).
    2. For each template-declared spec file, include it at
       its `<spec-root>`-relative path.
    3. If the template declares a spec-root `README.md` as
       part of its `specification-template/`, include
       `<spec-root>/README.md` (the built-in `livespec`
       template declares one; the built-in `minimal` template
       does not).
    4. Include every file under
       `<spec-root>/proposed_changes/**`.
    5. Include every file under
       `<spec-root>/history/**/proposed_changes/**`.
    6. For each template-declared spec file `<f>`, include
       every file under `<spec-root>/history/**/<f>` (the
       per-version snapshots of that spec file).
    Files outside the walk set are invisible to this check
    even when they exist under `<spec-root>/`. Under the
    built-in `minimal` template's `spec_root: "./"`, the
    check does NOT read the project's top-level `README.md`,
    `CONTRIBUTING.md`, `CHANGELOG.md`, source-tree markdown,
    or `.github/` markdown. This walk-set semantic applies
    uniformly to any future doctor-static check that walks
    `<spec-root>/` recursively; check authors MUST use the
    shared walk-set helper rather than a raw rglob.
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
    concrete configuration codified in v013 M7; narrowed in
    v017 Q3 from three contracts to two): see style doc
    §"Import-Linter contracts (minimum configuration)" for the
    canonical `[tool.importlinter]` TOML example with two
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
    **Retracted (v017 Q3):** the third contract that v012 L15a
    proposed (`forbidden` for `LivespecError` subclass imports
    outside `io/**` and `errors.py`, covering the raise-
    discipline import surface) is NOT part of the
    Import-Linter configuration. Import-Linter operates on
    import statements and cannot distinguish import-for-
    raising from import-for-annotating, so a forbidden-import
    contract on `livespec.errors` would block legitimate
    type-annotation and `match`-pattern uses of `LivespecError`
    subclasses in `commands/`, `doctor/`, and `validate/` modules
    (e.g., `IOResult[Finding, LivespecError]` return
    annotations; `case IOFailure(UsageError(...))` match
    patterns; `err.exit_code` attribute access). The v012 L15a
    claim that Import-Linter "replaces the import-surface
    portion of `check-no-raise-outside-io`" is retracted. The
    full raise-discipline is enforced by hand-written
    `check-no-raise-outside-io` (raise-site only; see below);
    `livespec.errors` MAY be imported from any livespec module
    that needs to reference its types.
    Architecture-vs-mechanism caveat (v009 I0): the minimum
    example in the style doc is illustrative; contract names,
    layer names, and ignore-import globs MAY be restructured so
    long as the two English-language rules (codified in the
    style doc) are enforced. Configuration tuning (root
    packages, includes/excludes) is implementer choice during
    the `enforcement-check-scripts` deferred entry's resolution.
  - **`check-schema-dataclass-pairing` v014 N2 tightening:**
    the v010 J11 implementer-choice language — "Implementer
    choice whether `finding.schema.json` is a standalone
    schema OR the `Finding` shape is embedded as the `items`
    schema of `doctor_findings.schema.json`'s `findings` array
    (either is acceptable; check must pass either way)" — is
    CLOSED in v014 N2. Standalone `finding.schema.json` is
    REQUIRED in v1. The three-way pairing check's symmetry
    stays strict: every dataclass pairs with a schema AND a
    validator; `finding.py` is no exception. The `Finding`
    dataclass at `schemas/dataclasses/finding.py`, the schema
    at `schemas/finding.schema.json`, and the validator at
    `validate/finding.py` all pair together. Closes the
    malformation between J11's implementer choice and M6's
    strict three-way symmetry.
  - **Orchestrator bootstrap lenience** (v014 N3):
    `bin/doctor_static.py` MUST construct `DoctorContext` with
    best-effort defaults when `.livespec.jsonc` is absent,
    malformed, or schema-invalid. `DoctorContext` (see style
    doc §"Context dataclasses") carries two status fields:
    - `config_load_status: Literal["ok", "absent", "malformed",
      "schema_invalid"]`.
    - `template_load_status: Literal["ok", "absent",
      "malformed", "schema_invalid"]`.
    Semantics:
    - `"ok"`: file parsed and schema-validated successfully;
      corresponding check emits pass Finding.
    - `"absent"`: file not found at expected path; corresponding
      check emits skipped Finding with message noting the
      fallback to defaults.
    - `"malformed"`: file found but JSONC parse failed;
      corresponding check emits fail Finding citing the parse
      error (line, column, offending token if available). For
      `.livespec.jsonc`, the orchestrator falls back to
      `LivespecConfig` defaults. For `template.json`, the
      orchestrator falls back to `TemplateConfig` defaults.
    - `"schema_invalid"`: file parsed but schema validation
      failed; corresponding check emits fail Finding citing the
      failing schema path and offending field value. The
      orchestrator falls back to best-effort-partial-parse
      values (fields that validated individually populate;
      others fall to defaults).
    The K10 fail-Finding discipline applies uniformly: the
    `livespec-jsonc-valid` and `template-exists` checks map
    domain-meaningful failures to fail Findings, NOT
    `IOFailure(err)`; `bin/doctor_static.py`'s "never emits
    exit 4" invariant is preserved. The lenient bootstrap
    discipline is doctor-static-only; non-doctor wrappers
    continue to fail-fast on malformed `.livespec.jsonc` (exit
    3 via `PreconditionError`).
  - **`template-exists` widening** (v014 N4): the check's
    existing layout-presence verification (`template.json`,
    `prompts/`, `specification-template/`) plus
    `template_format_version` matching is EXTENDED to verify:
    - All four REQUIRED prompt files exist as files under
      `prompts/`: `seed.md`, `propose-change.md`, `revise.md`,
      `critique.md`.
    - When `template.json` declares
      `doctor_llm_objective_checks_prompt` or
      `doctor_llm_subjective_checks_prompt` as non-null, the
      declared path (resolved relative to the template root)
      exists as a file.
    - When `template.json` declares non-empty
      `doctor_static_check_modules`, each listed path exists
      as a file at the template-root-relative path. (Deeper
      module-load validity — module-loads-cleanly and exports
      `TEMPLATE_CHECKS` — is checked at doctor-static
      orchestrator load-time per the C3 routing below.)
    Every missing-file case emits a fail Finding citing the
    offending `template.json` field (or "REQUIRED prompt
    file"), its value, and the resolved template path.
  - **Author identifier → filename slug transformation**
    (v014 N5): the unified author-resolution precedence
    (CLI `--author` → env var `LIVESPEC_AUTHOR_LLM` → LLM
    self-declared `author` field → `"unknown-llm"` fallback)
    produces an UNCONSTRAINED string (no schema pattern or
    runtime validator applies at the author-field level).
    When the resolved value is used to derive a topic hint or
    filename component (the raw `<resolved-author>` author stem
    passed by `critique` to `propose_change`'s internal
    canonicalization with reserve-suffix `"-critique"` per
    v016 P3; similar positions in future invocations), the
    wrapper transforms the value via this rule:
    1. lowercase.
    2. replace every run of one or more non-[a-z0-9]
       characters with a single hyphen.
    3. strip leading and trailing hyphens.
    4. truncate to 64 characters.
    5. if the result is empty (pathological case: the input
       contained only non-[a-z0-9] characters), fall back to
       the literal `"unknown-llm"`.
    The slug form is used as the filename component; the
    ORIGINAL un-slugged value is preserved in the YAML
    front-matter `author` / `author_human` / `author_llm`
    fields for audit-trail fidelity. The rule matches the GFM
    slug algorithm already used by
    `anchor-reference-resolution`, preserving monotonicity
    across livespec's slug conventions.
  - **Topic canonicalization at the `propose-change` boundary**
    (v015 O3): the CLI `<topic>` argument accepted by
    `bin/propose_change.py` is a user-facing topic hint, not yet
    the canonical artifact identifier. Before any collision
    lookup, filename write, or front-matter population, the
    wrapper canonicalizes the topic via the same slug rule
    family: lowercase → replace runs of non-[a-z0-9] with a
    single hyphen → strip leading/trailing hyphens → truncate to
    64 characters. If the canonicalized result is empty, the
    wrapper raises `UsageError` (exit 2). The canonicalized topic
    is then used uniformly for the output filename, front-matter
    `topic`, and the collision namespace (`foo.md`, `foo-2.md`,
    ...). This rule applies to direct callers and to `critique`'s
    internal delegation path alike.
  - **Reserve-suffix topic canonicalization** (v016 P3):
    `bin/propose_change.py` MAY be invoked with
    `--reserve-suffix <text>` (or called via its Python
    internal API with an equivalent keyword-only parameter,
    which is how `critique`'s internal delegation path
    supplies `-critique`). When `--reserve-suffix` is NOT
    supplied, canonicalization behaves exactly as v015 O3
    defines. When it IS supplied, the algorithm is:
    1. Canonicalize the inbound topic hint with steps 1-3
       (lowercase → non-`[a-z0-9]` runs → single hyphen →
       strip leading/trailing hyphens) — call this
       `<canonical-hint>`.
    2. Canonicalize the `<suffix>` string with the same
       steps 1-3 — call this `<canonical-suffix>`.
    3. If `<canonical-hint>` already ends in `<canonical-suffix>`,
       strip the trailing suffix from `<canonical-hint>`
       before truncation. (This lets callers pass the hint
       either with or without the suffix pre-attached.)
    4. Truncate the resulting non-suffix portion to
       `64 − len(<canonical-suffix>)` characters; strip
       trailing hyphens left behind by the truncation.
    5. Re-append `<canonical-suffix>` verbatim. The result
       is at most 64 characters and the suffix is preserved
       intact.
    6. If the composed result is empty (e.g., the hint
       canonicalizes to nothing and no suffix was supplied),
       the wrapper raises `UsageError` (exit 2).
    Worked examples (suffix = `-critique`; `len(-critique) = 9`;
    non-suffix budget = `64 − 9 = 55` characters):
    - Input `"Claude Opus 4.7 (1M context)"`, suffix
      `"-critique"` → canonical hint
      `claude-opus-4-7-1m-context` (26 chars) → no truncation
      needed → output `claude-opus-4-7-1m-context-critique`
      (35 chars).
    - Input `"An unusually long author identifier that keeps going and going past fifty"`,
      suffix `"-critique"` → canonical hint
      `an-unusually-long-author-identifier-that-keeps-going-and-going-past-fifty`
      (73 chars) → truncated to 55 chars
      `an-unusually-long-author-identifier-that-keeps-going-an` →
      re-appended → `an-unusually-long-author-identifier-that-keeps-going-an-critique`
      (64 chars).
    - Input `"Claude Opus 4.7-critique"`, suffix
      `"-critique"` (suffix was pre-attached by caller) →
      canonical hint strips trailing `-critique` →
      `claude-opus-4-7` (15 chars) → no truncation → output
      `claude-opus-4-7-critique` (24 chars).
  - **Collision-suffix semantics** (v014 N6): when
    `propose-change` or `critique` would write a file at a
    canonicalized topic whose filename already exists, the
    wrapper
    auto-disambiguates by appending a hyphen-separated
    monotonic integer suffix **starting at `2`**:
    - First write at topic `foo`: `foo.md` (no suffix).
    - First collision: `foo-2.md`.
    - Second collision: `foo-3.md`.
    - Nth collision: `foo-<N+1>.md` (no zero-padding).
    Determination: the wrapper enumerates files named
    `<canonical-topic>.md` and `<canonical-topic>-<N>.md` in the
    target directory;
    picks the lowest integer ≥ 2 such that no file with that
    suffix exists. Race: livespec is single-process; no lock
    needed. Alphanumeric sort misordering past 9 duplicates
    (e.g., `foo-10.md` sorts before `foo-2.md` lexically) is
    accepted as an extreme edge case; `revise`'s per-file
    processing already uses `created_at` YAML front-matter as
    the primary ordering, with lexicographic filename as
    tie-breaker only. Scope: this convention applies to
    `propose-change` and `critique` filenames only. The
    `out-of-band-edit-<UTC-seconds>.md` filename form used by
    `doctor-out-of-band-edits` is a SEPARATE always-appended
    UTC-timestamp convention (each backfill is a distinct
    timed event); the two conventions are not unified.
  - **`revision-to-proposed-change-pairing` walks filename
    stems, not front-matter `topic`** (v017 Q7): for every
    `<stem>-revision.md` under
    `<spec-root>/history/vNNN/proposed_changes/`, the check
    verifies `<stem>.md` exists in the same directory.
    `<stem>` is the filename stem of the proposed-change file
    as it was written (including any v014 N6 collision `-N`
    suffix). The front-matter `topic` field is NOT walked for
    pairing because under v014 N6 + v016 P4, multiple files
    may share the same canonical `topic` value, disambiguated
    only at the filename level (`foo.md`, `foo-2.md`,
    `foo-3.md` all carry `topic: foo` in their front-matter).
    Pair failures the check detects: orphan revision
    (revision file with no matching proposed-change stem);
    orphan proposed-change (proposed-change with no matching
    `<stem>-revision.md`). The pairing predicate is a
    literal file-name equality (stem of the revision file
    minus `-revision` suffix equals stem of the proposed-
    change file).

  - **Uniform `--project-root` contract across every wrapper**
    (v017 Q9): every wrapper operating on project state
    (`bin/seed.py`, `bin/propose_change.py`, `bin/critique.py`,
    `bin/revise.py`, `bin/prune_history.py`,
    `bin/doctor_static.py`, `bin/resolve_template.py`) accepts
    `--project-root <path>` with default `Path.cwd()`.
    Upward-walk logic for `.livespec.jsonc` lives as a
    shared helper in `livespec.io.fs` (`@impure_safe` per
    the purity discipline); both the wrapper supervisors and
    `livespec.doctor.run_static` invoke this helper rather
    than re-implementing the upward-walk. `bin/seed.py` is
    the one wrapper that does NOT invoke the upward-walk
    helper for `.livespec.jsonc` location — seed runs
    before `.livespec.jsonc` exists on disk (the normal
    pre-seed case) and the wrapper writes the config itself
    (v016 P2; v017 Q5/Q6 refine the present-but-invalid /
    mismatch branches). `seed`'s `--project-root` therefore
    anchors only the target-file write paths, not an
    existing-config lookup.

  - **Reserve-suffix canonicalization is this entry's sole
    source-of-truth** (v017 Q1 note): PROPOSAL.md §"propose-
    change → Reserve-suffix canonicalization" was trimmed in
    v017 Q1 to invariants-only (≤64 chars, suffix preserved
    intact regardless of pre-attachment or truncation-clip,
    empty → UsageError). The pre-strip + truncate-and-
    hyphen-trim + re-append algorithm defined above (v016 P3
    subsection) remains the only documented algorithm.
    Implementations MUST follow this subsection's steps; the
    PROPOSAL.md bullet is a contract summary, not an
    algorithm specification.

  - **Template-extension doctor-static check loading —
    failure routing** (v014 C3): after the `template-exists`
    widening (v014 N4) catches missing-file at static-check
    time, three remaining failure modes during
    `importlib.util.spec_from_file_location(...)` +
    `module_from_spec(...)` + `loader.exec_module(...)` in
    `livespec/doctor/run_static.py` route as follows:
    - **Syntax error** in the extension module (the file
      exists but contains malformed Python): wrapped as
      `IOFailure(PreconditionError)` → exit 3 with error
      message citing the template path, extension module
      path, and the `SyntaxError` location (line, offset,
      message).
    - **Import error** (the extension module's own imports
      fail, e.g., it imports a package the user's system
      lacks): `IOFailure(PreconditionError)` → exit 3 with
      error message citing the template path, extension
      module path, and the `ImportError` target (module
      name attempted).
    - **Missing `TEMPLATE_CHECKS` export** (the module loads
      cleanly but does not define or exports the required
      symbol): `IOFailure(PreconditionError)` → exit 3 with
      error message citing the template path, extension
      module path, and the expected export shape
      (`TEMPLATE_CHECKS: list[tuple[str, CheckRunFn]]`).
    All three route through the domain-error track because
    from livespec's I/O-boundary perspective, an extension
    author's malformed module is a domain-meaningful failure
    (fixing the extension resolves it; a retry would succeed).
    Bug-class exit 1 remains reserved for livespec's own
    uncaught exceptions via the supervisor bug-catcher.
    Implementation: the `importlib.util` calls are wrapped
    with `@impure_safe(exceptions=(SyntaxError, ImportError,
    AttributeError))` at the `livespec/io/` boundary (the
    extension-loader helper lives in `livespec/io/` per the
    purity/impure split); the exception-type-to-
    `PreconditionError`-message-form mapping lives in
    `livespec/doctor/run_static.py`'s extension-loader path.

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

- **Source:** v008 (H4; widened v009 I8; widened v010 per J3, J4, J7, J10; widened v011 per K5, K6, K7; widened v013 per M4; widened v014 per N1 and N7; widened v015 per O3 and O4; widened v016 per P2 and P3; widened v017 per Q2 and Q4 — Q2 pins the seed pre-seed dialogue's template-resolution step to `bin/resolve_template.py --template <chosen>`; Q4 extends the recovery-flow narration contract to cover propose-change's expected exit-3 during seed-recovery plus the explicit git-commit step)
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
    v009 I8's retry-on-exit-3; retry-count language removed in
    v015 O4): on exit 4, SKILL.md prose SHOULD inspect the
    return code, treat it as a retryable malformed-payload
    signal, and SHOULD re-invoke the template prompt with error
    context from stderr to re-assemble the JSON payload. v1
    intentionally leaves the exact retry count unspecified.
    Exit 3 is NOT retryable (pre-step / precondition failure —
    surface findings and abort); wrappers validate internally;
    no separate validator CLI wrappers;
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
    v010's positional `<author>` to `--author` flag; critique
    passes the raw `<resolved-author>` author stem plus the
    reserve-suffix parameter `"-critique"` (v016 P3) to
    `propose-change`'s internal canonicalization path, which
    canonicalizes the composite topic before filename /
    front-matter / collision handling while preserving the
    `-critique` suffix under truncation.
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

  **v014 additions:**
  - **Seed pre-seed template-choice dialogue** (v014 N1;
    updated by v016 P2; resolution mechanism pinned in v017
    Q2). Seed's SKILL.md prose (`seed/SKILL.md` body Steps
    section) MUST handle the pre-seed state specially:
    BEFORE invoking the wrapper, check whether
    `.livespec.jsonc` exists at the project root. If absent,
    prompt the user in dialogue for template choice with
    these options:
    - `livespec` (default, multi-file SPECIFICATION/ layout
      with `spec.md` + `contracts.md` + `constraints.md` +
      `scenarios.md`). Recommended.
    - `minimal` (single-file `SPECIFICATION.md` at repo
      root; smaller initial surface).
    - custom path (user provides a relative-path-to-
      template-directory; the chosen path must contain a
      valid `template.json`).
    After the user selects, the SKILL.md prose MUST resolve
    the chosen template's directory by invoking
    `bin/resolve_template.py --project-root . --template
    <chosen>` via Bash (per v017 Q2's addition to the
    template-resolution contract — the `--template` flag
    bypasses `.livespec.jsonc` lookup, letting the
    resolution happen BEFORE the wrapper writes the config).
    The wrapper's stdout is the absolute template directory
    path; the SKILL.md prose uses that path with the Read
    tool to fetch `<path>/prompts/seed.md` and proceeds with
    the normal seed template-prompt dispatch. The SKILL.md
    prose MUST ALSO include the chosen value in the seed-
    input JSON payload's required top-level `template`
    field (v016 P2); the wrapper consumes the `template`
    field to bootstrap `.livespec.jsonc` (see PROPOSAL.md
    §"seed" bullet "`.livespec.jsonc` is wrapper-owned").
    When `.livespec.jsonc` IS present, seed's SKILL.md
    prose MAY skip the pre-seed dialogue and instead invoke
    `bin/resolve_template.py --project-root .` WITHOUT
    `--template` (the wrapper walks upward for the
    existing config) to read the existing `template` value;
    the wrapper's `template` ↔ on-disk consistency check
    (v016 P2; exit code refined to 3 per v017 Q6) catches
    any mismatch. The SKILL.md prose MUST NOT write
    `.livespec.jsonc` via the Write tool; wrapper-owned
    file-shaping is the single source of truth for this
    file.
  - **Seed post-step-failure recovery narration** (v014 N7;
    expanded for exit-3-during-recovery + explicit git-commit
    step in v017 Q4). Seed's SKILL.md prose (`seed/SKILL.md`
    body Failure handling section, exit-3 row) MUST surface
    the recovery path concretely when post-step doctor-static
    emits fail Findings:
    > On exit 3 after seed's sub-command logic completed
    > (post-step fail): the specification and history
    > files are on disk but doctor-static rejected them.
    > To correct WITHOUT re-seeding (seed's idempotency
    > blocks re-seed):
    >
    > 1. Review the fail Findings surfaced in stderr /
    >    skill-prose narration.
    > 2. Run `/livespec:propose-change --skip-pre-check
    >    <topic> "<fix description>"` to file a fix
    >    proposal. `--skip-pre-check` bypasses the
    >    pre-step. **Expect propose-change to ALSO exit 3**
    >    (its own post-step doctor-static trips the same
    >    findings), but the proposed-change file IS on
    >    disk (per §"Wrapper-side: deterministic lifecycle").
    > 3. `git commit` the partial state (the seed-written
    >    files plus the new proposed-change file). This is
    >    required before running revise, otherwise the
    >    next invocation's `doctor-out-of-band-edits`
    >    check will trip its pre-backfill guard.
    > 4. Run `/livespec:revise --skip-pre-check` to cut
    >    `v002` with the corrections. Revise's post-step
    >    runs against the now-fixed state and passes.
    No new flags are introduced for this recovery; the
    existing `--skip-pre-check` / `--run-pre-check` flag
    pair (v010 J10) was designed for exactly this emergency-
    recovery case.
    **Propose-change exit-3 narration contract** (v017 Q4):
    `propose-change/SKILL.md` prose MUST narrate the exit-3
    path distinctly when the narrator can detect the
    seed-recovery-in-progress state (heuristic: no `vNNN`
    beyond `v001` exists AND pre-check was skipped). In
    that case, narration says "this exit 3 is expected
    during seed recovery; the proposed-change file is on
    disk; commit the partial state and run
    `/livespec:revise --skip-pre-check`." Otherwise, the
    generic exit-3 narration applies and the user is
    expected to recognize the recovery path from seed's
    earlier narration.

### wrapper-input-schemas

- **Source:** v008 (H6 + H10; widened v009 per I3; widened v010 per J6; widened v011 per K2 and K7; widened v012 per L4 and L8; widened v013 per M6; widened v014 per N2 and N5; widened v016 per P2)
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
    `{template, files: [{path, content}], intent}`. The
    top-level required `template: string` field (v016 P2)
    carries the user-chosen template value from the pre-seed
    SKILL.md-prose dialogue (one of `livespec`, `minimal`, or
    a custom template path). The wrapper uses this value to
    bootstrap `.livespec.jsonc` and to locate the template's
    `prompts/seed.md`.
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

  **v014 additions:**
  - **`finding.schema.json` REQUIRED as standalone schema**
    (v014 N2). Added to the target-spec-file list:
    `<bundle>/scripts/livespec/schemas/finding.schema.json`
    paired with `schemas/dataclasses/finding.py` (existing)
    AND `validate/finding.py` (NEW). Fields: `check_id`,
    `status` (one of `pass`/`fail`/`skipped`), `message`,
    `path`, `line`. The `Finding` dataclass (paired) uses
    the v012 L4 strict triple and v012 L8 NewType aliases
    (`check_id: CheckId`). The paired validator `validate/
    finding.py` returns `Result[Finding, ValidationError]`.
    `check-schema-dataclass-pairing`'s three-way walker
    enforces drift-free pairing (v014 N2 closes the v010
    J11 implementer-choice between standalone and
    embedded; standalone is now REQUIRED).
  - **Author field unconstrained** (v014 N5 note). The
    optional file-level `author` field in
    `proposal_findings.schema.json` and
    `revise_input.schema.json` accepts unconstrained
    strings (no `pattern` constraint beyond type). The
    v014 N5 author→slug transformation applies
    post-validation at the wrapper layer (see
    `static-check-semantics` §"Author identifier →
    filename slug transformation"). This separation keeps
    the schema-validation layer simple and the slug rule
    application consistent across `propose-change`,
    `critique`, and `revise` wrappers.

  **v016 additions:**
  - **`seed_input.schema.json` gains required `template`
    field** (v016 P2). The schema's top-level object adds a
    REQUIRED `template: string` property carrying the user-
    chosen template value (one of `livespec`, `minimal`, or
    a custom template path) from the pre-seed SKILL.md-prose
    dialogue. The paired `SeedInput` dataclass gains a
    matching field `template: TemplateName` (uses the v012
    L8 NewType alias, consistent with how
    `template_config.schema.json`/`TemplateConfig` and
    `.livespec.jsonc`/`LivespecConfig` type their `template`
    values). The paired `validate/seed_input.py` validator
    enforces the required field at schema-validation time;
    `check-schema-dataclass-pairing`'s three-way walker
    catches drift symmetrically across schema, dataclass,
    and validator. The wrapper uses this value (a) to
    bootstrap `.livespec.jsonc` before post-step
    doctor-static (see PROPOSAL.md §"seed" bullets
    "`.livespec.jsonc` is wrapper-owned" and "wrapper
    deterministic file-shaping work order") and (b) to
    resolve the template's `prompts/seed.md` for content
    generation.

### user-hosted-custom-templates

- **Source:** v010 (J3; new; note-only widening in v017 per Q2 — `bin/resolve_template.py`'s v1 surface now includes a `--template <value>` flag alongside `--project-root`; the v2+ extensibility shield covers BOTH the stdout contract AND the flag shape)
- **Target spec file(s):** `SPECIFICATION/spec.md` (v2+ scope
  note and future template-discovery section); potentially
  `SPECIFICATION/contracts.md` (for the resolved-template-path
  output contract of `bin/resolve_template.py` if that contract
  needs versioning).
- **How to resolve:** Codify in v2 scope (post-v1) that
  `bin/resolve_template.py` is the extensibility seam for
  future template-discovery mechanisms. v1 accepts only built-in
  names (`"livespec"` or `"minimal"` per v014 N1) or
  project-root-relative directory paths for `.livespec.jsonc`'s
  `template` field. v2+ may extend the
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
  resolved path regardless of its source. **v017 Q2
  addition**: the `--template <value>` flag (added to support
  the pre-seed template-resolution path; see PROPOSAL.md
  §"Template resolution contract") is part of the v1 frozen
  flag surface. Future v2+ template-discovery extensions MUST
  extend — not replace — the v1 flag set (`--project-root`,
  `--template`), so existing SKILL.md prose and pre-seed
  invocations continue to work unchanged.

### end-to-end-integration-test

- **Source:** v014 (N9; new; widened in v015 per O4)
- **Target spec file(s):**
  - `<repo-root>/tests/e2e/` — fixture tree, mock executable,
    pytest suite.
  - `<repo-root>/justfile` — two new recipes:
    `e2e-test-claude-code-mock` (in `just check`) and
    `e2e-test-claude-code-real` (NOT in `just check`).
  - `<repo-root>/.github/workflows/e2e-real.yml` (or
    equivalent name; implementer choice) — real-tier CI
    workflow with three triggers: `merge_group`, `push` to
    `master`, `workflow_dispatch`.
  - `<repo-root>/.mise.toml` — mise-pin `claude-agent-sdk`.
  - `<repo-root>/pyproject.toml` — if needed for pytest
    configuration of the E2E suite (e.g., a `[tool.pytest.ini_options]`
    marker for E2E tests).
- **How to resolve:** Author the full E2E integration test
  surface per PROPOSAL.md §"Testing approach — End-to-end
  harness-level integration test":

  **Fixture tree** at `<repo-root>/tests/e2e/fixtures/`:
  - A `minimal`-template-shaped fresh-project fixture:
    empty repo root, no `.livespec.jsonc`, no
    `SPECIFICATION.md`. The E2E test copies this into
    `tmp_path`, initializes a git repo there, and drives
    the sub-commands.
  - Pre-seeded fixtures for the three error-path tests (N9
    D4-b): (a) for retry-on-exit-4 — a fixture that triggers
    a schema-invalid LLM payload in the **mock tier only** via a
    specific delimiter comment directive; the mock then returns a
    well-formed payload on the second attempt so the test covers
    exactly one retry cycle. The real tier skips this scenario
    via pytest marker/skipif; (b) for
    doctor-static fail-then-fix — a pre-seeded
    `SPECIFICATION.md` containing a mixed-case `Must` (trips
    `bcp14-keyword-wellformedness`); (c) for prune-history
    no-op — a pre-seeded tree with only `v001` in history.

  **Mock executable** at `<repo-root>/tests/e2e/
  fake_claude.py`:
  - API-compatible with the subset of `claude-agent-sdk`'s
    query interface livespec uses (`query(...)` returning
    an async iterator of SDK message types; `ClaudeAgentOptions`;
    plugin loading via `plugins=[{"type": "local", "path":
    "..."}]`).
  - Reads the `minimal` template's prompts; extracts
    hardcoded delimiter-comment directives identifying
    wrapper invocations; invokes `bin/<cmd>.py` wrappers
    for real (mock does NOT stub wrappers); synthesizes
    SDK-compatible message objects for the test to assert on.
  - The delimiter-comment format is set JOINTLY with the
    `template-prompt-authoring` deferred entry (which
    authors the prompts that carry the delimiters). Both
    entries MUST agree on a single format. Format
    considerations: inert to the real LLM (markdown comment
    form); trivially parseable; accommodates the wrapper-
    call shapes needed by happy path + 3 error paths.
  - Hard-fails (raises a test-harness error) if delimiter
    comments in minimal's prompts are missing or malformed.
  - Mock scope: replaces ONLY the Claude Agent SDK / LLM
    layer. Wrappers always run for real. Doctor-static's
    LLM-driven phase is handled by the mock (LLM-driven by
    construction); doctor-static's Python phase runs for
    real.

  **Pytest suite** at `<repo-root>/tests/e2e/test_*.py`:
  - Parameterized on `LIVESPEC_E2E_HARNESS=mock|real` (env
    var read by a session-scoped fixture that selects
    between `fake_claude` and `claude_agent_sdk`). Shared tests
    run in both modes; intentionally mock-only scenarios use
    pytest marker / `skipif` annotations and are skipped in
    real mode.
  - Happy path test: `test_happy_path_minimal` — runs
    `/livespec:seed` → `propose-change` → `critique` →
    `revise` → `doctor` → `prune-history` in sequence;
    asserts on filesystem state at each step (files
    exist/don't exist; schemas valid; exit codes correct).
  - Error-path tests:
    - `test_retry_on_exit_4` — triggers schema-invalid
      payload in mock mode, then returns well-formed payload on
      the second attempt; verifies the skill/prompt
      orchestration treats exit `4` as a retry signal and the
      sub-command succeeds after exactly one retry. Marked
      mock-only; skipped in real mode.
    - `test_doctor_fail_then_fix` — pre-seed malformed
      state; run doctor → verify fail Finding; apply fix
      via propose-change --skip-pre-check + revise
      --skip-pre-check; verify post-revise doctor-static
      passes.
    - `test_prune_history_noop` — v001-only state; verify
      skipped Finding; verify filesystem unchanged.

  **CI workflows** at `<repo-root>/.github/workflows/`:
  - `e2e-real.yml` (or equivalent) triggered by
    `on: merge_group` + `on: push` with
    `branches: [master]` + `on: workflow_dispatch`.
    Workflow steps: `mise install` → `just bootstrap` →
    `just e2e-test-claude-code-real` (env:
    `ANTHROPIC_API_KEY` mounted from GitHub secrets).
  - Per-commit CI (`ci.yml`) already runs `just check`
    which includes `just e2e-test-claude-code-mock`; no
    change to per-commit CI structure needed.

  **Rate-limiting / retry behavior.** Real tier uses the
  SDK's default retry-on-transient-error behavior; the test
  treats persistent API failures as hard failures (no custom
  retry wrapper). Implementer may add a single at-test-
  fixture-level retry if flakiness becomes operationally
  problematic; not codified in v014.

  **Coverage scope.** `tests/e2e/` is NOT subject to the
  100% line+branch coverage mandate (existing rule already
  excludes `tests/`). The mock executable at
  `tests/e2e/fake_claude.py` is test infrastructure; no
  coverage requirement applies to it.

### local-bundled-model-e2e

- **Source:** v014 (N9-D1 future-scope; new)
- **Target spec file(s):**
  - `<repo-root>/.github/workflows/` — modifications to
    remove the `ANTHROPIC_API_KEY` dependency.
  - `<repo-root>/.mise.toml` — potentially new pins for the
    chosen local-model tooling (e.g., `ollama`, `llama-cpp`).
  - Possibly `<repo-root>/tests/e2e/` — a third harness mode
    (`LIVESPEC_E2E_HARNESS=local`) selecting a local-model-
    backed Claude-Code-API-compatible wrapper.
- **How to resolve:** Investigate replacing the
  `ANTHROPIC_API_KEY`-dependent real E2E tier with a
  local/bundled-model setup that preserves mock↔real parity.
  Candidate approaches:
  - **Ollama + small coding model** (e.g., qwen2.5-coder,
    code-llama). Pros: single binary to install; simple
    integration. Cons: model weights ~2-8 GB; CI startup
    overhead; model-quality ceiling lower than Anthropic's
    frontier models (may produce prompt-authoring-level
    regressions that a Sonnet/Opus would catch).
  - **llama.cpp + GGUF model** bundled or fetched at
    CI-start. Pros: portable, self-contained. Cons: CI
    bandwidth to fetch weights; model-quality ceiling.
  - **MLX + small model on Apple Silicon CI** (if available
    at GitHub Actions' macOS runners). Pros: potentially
    fastest on Apple hardware. Cons: Linux runners can't
    use it; requires dual CI path.

  Evaluate whether a local-model-backed E2E tier actually
  exercises the same coverage as a live-LLM tier (e.g.,
  does the local model produce JSON payloads that stress
  the wrapper's schema-validation retry-signaling path the same
  way?).
  If parity is sufficient, replace the real tier. If not,
  add `local` as a third tier and keep `real` available for
  release-gate or on-demand invocation.

  Scope: v2+. v014 preserves the live-Anthropic-API contract
  for the `real` tier; this entry captures the follow-up
  option to eliminate the API-key CI dependency without
  sacrificing harness-level integration coverage.
