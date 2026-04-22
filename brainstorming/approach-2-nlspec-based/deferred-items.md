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
  v004 / v005 / v006 / v007 / v008 / v009 / v010>
- **Target spec file(s):** <repo-root-relative path(s)>
- **How to resolve:** <one paragraph describing what the eventual
  propose-change must produce>
```

## Items

### template-prompt-authoring

- **Source:** v001 (carried forward through every version)
- **Target spec file(s):** `SPECIFICATION/spec.md`,
  `SPECIFICATION/contracts.md` (skill↔template I/O contracts)
- **How to resolve:** Author each template prompt's input/output
  JSON Schemas (in `scripts/livespec/schemas/`) and the prompt
  bodies themselves under
  `specification-templates/livespec/prompts/{seed,propose-change,
  revise,critique}.md`. Cover: variables the skill provides as
  input, the JSON contract the prompt MUST emit, retry semantics
  on schema-validation failure.

### python-style-doc-into-constraints

- **Source:** v005 (carried forward to v008)
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

- **Source:** v005 (carried forward to v008)
- **Target spec file(s):** `SPECIFICATION/constraints.md` +
  `<repo-root>/dev-tooling/checks/`
- **How to resolve:** Author each enforcement-check Python script
  per the canonical `just` target list in
  `python-skill-script-style-requirements.md` (`check-purity`,
  `check-private-calls`, `check-import-graph`, `check-global-writes`,
  `check-supervisor-discipline`, `check-no-raise-outside-io`,
  `check-public-api-result-typed`, `check-main-guard`,
  `check-wrapper-shape`, `check-claude-md-coverage`,
  `check-no-direct-tool-invocation`, `file_lloc`). Includes:
  test fixtures, edge-case parameterizations, exit-code mapping.

### claude-md-prose

- **Source:** v006 (carried forward to v008)
- **Target spec file(s):** `<bundle>/scripts/**/CLAUDE.md`,
  `<repo-root>/tests/**/CLAUDE.md` (with `tests/fixtures/` excluded
  per H15),
  `<repo-root>/dev-tooling/**/CLAUDE.md` (excluding `_vendor/`
  subtree per G7)
- **How to resolve:** Author each per-directory `CLAUDE.md` with
  directory-local constraints an agent working there must satisfy.
  Concise (typically <50 lines); links to
  `python-skill-script-style-requirements.md` for global rules.

### task-runner-and-ci-config

- **Source:** v006 (carried forward to v010; scope widened in v009 per I3; scope widened in v010 per J8, J9, J10)
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
  `source` extended to include `scripts/bin/` per v010 J8 so
  `_bootstrap.py` lands in the 100% line+branch surface), the
  recorded vendored-lib versions (including `jsoncomment` per
  H2), AND the new `check-schema-dataclass-pairing` target (I3).
  Also pick up the narrowed `check-no-raise-outside-io` and
  `check-no-except-outside-io` targets per I10, AND the
  mutually-exclusive `--skip-pre-check` / `--run-pre-check` flag
  pair in pre-step-having sub-command wrappers per v010 J10
  (lefthook pre-commit/pre-push hook invocations of those
  sub-commands must pass one of the two flags OR neither,
  defaulting to the config value).

### static-check-semantics

- **Source:** v007 (renamed in v008 from `ast-check-semantics`;
  scope widened per H3, H11, H13, H14; scope widened in v009 per
  I1, I4, I5, I7, I10, I3; scope widened in v010 per J4, J5, J7,
  J10, J11, J14)
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
    `# noqa` interactions) for each of `check-purity`,
    `check-private-calls`, `check-import-graph`,
    `check-global-writes`, `check-supervisor-discipline`,
    `check-no-raise-outside-io`, `check-no-except-outside-io`,
    `check-public-api-result-typed`, `check-main-guard`,
    `check-wrapper-shape`, `check-schema-dataclass-pairing`.
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
  - **`check-schema-dataclass-pairing` semantics** (v009 I3):
    walks `scripts/livespec/schemas/*.schema.json` and
    `scripts/livespec/schemas/dataclasses/*.py`; for each
    schema, asserts a paired dataclass exists (by
    `$id`-derived name) with every listed field in matching
    Python type; and vice versa. Drift in either direction
    fails.
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
    (v010 J11): still walks only
    `scripts/livespec/schemas/dataclasses/*.py`. `Finding`
    moved from `doctor/finding.py` to
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

### returns-pyright-plugin-disposition

- **Source:** v007 (carried forward to v008)
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

### front-matter-parser

- **Source:** v007 (carried forward to v009; scope widened in v009 per I9 and I12)
- **Target spec file(s):**
  `<bundle>/scripts/livespec/parse/front_matter.py`,
  `<bundle>/scripts/livespec/schemas/proposed_change_front_matter.schema.json`,
  `<bundle>/scripts/livespec/schemas/revision_front_matter.schema.json`
- **How to resolve:** Implement the restricted-YAML parser per the
  format restrictions codified in PROPOSAL.md "Proposed-change file
  format" and "Revision file format" (scalar-only,
  JSON-compatible, no nesting). Author two distinct JSON Schemas
  (I12): `proposed_change_front_matter.schema.json` (fields:
  `topic`, `author`, `created_at`) and
  `revision_front_matter.schema.json` (fields: `proposal`,
  `decision`, `revised_at`, `reviser_human`, `reviser_llm`). Each
  schema pattern-validates the reserved `livespec-` prefix
  namespace convention from I9: identifiers matching the
  `^livespec-` pattern are reserved for automated skill-tool
  authorship (e.g., `livespec-seed`, `livespec-doctor`); fields
  accepting human-or-LLM identifiers MUST NOT accept
  user-supplied `livespec-`-prefixed values from non-skill
  callers (enforced at parse time on the proposed-change /
  revision file format, not at the front-matter schema layer).
  Validators in `validate/` consume the parsed dict via the
  factory shape from G4, routed through the dataclass pairing
  from I3 (`ProposedChangeFrontMatter`, `RevisionFrontMatter`
  dataclasses).

### skill-md-prose-authoring

- **Source:** v008 (H4; carried forward to v010 with I8 reshape; scope widened in v010 per J3, J4, J7, J10)
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
    v009 I8's retry-on-exit-3): on exit 4 re-invoke the
    template prompt with error context from stderr and retry,
    up to 3 retries; exit 3 is NOT retryable (pre-step /
    precondition failure — surface findings and abort);
    wrappers validate internally; no separate validator CLI
    wrappers;
  - **exit 0 on `--help`** (v010 J7): help text goes to stdout
    via the `HelpRequested` supervisor path; not an error;
  - per-proposal confirmation dialogue (`revise` only);
  - **mutually-exclusive `--skip-pre-check` / `--run-pre-check`
    flag pair** (v010 J10): Inputs section for every pre-step-
    having sub-command lists both; narration for both flags
    (skip warning when `--skip-pre-check` is set or config
    default is skip=true; neutral when `--run-pre-check`
    overrides config default skip=true);
    `--skip-subjective-checks` (LLM-layer only; never passed
    to Python) handling;
  - exit-code narration (exit 0 on help; exit 2 on usage error
    including both-flags-set; exit 3 on precondition /
    doctor-static; exit 4 on schema validation; exit 1 on
    bug / unexpected exception; exit 126 / 127 on permission /
    missing tool).

### wrapper-input-schemas

- **Source:** v008 (H6 + H10; carried forward to v010 with I3 widening; scope widened in v010 per J6)
- **Target spec file(s):**
  `<bundle>/scripts/livespec/schemas/proposal_findings.schema.json`
  (renamed from `critique_findings.schema.json`),
  `<bundle>/scripts/livespec/schemas/doctor_findings.schema.json`,
  `<bundle>/scripts/livespec/schemas/seed_input.schema.json`,
  `<bundle>/scripts/livespec/schemas/revise_input.schema.json`,
  AND the paired hand-authored dataclasses under
  `<bundle>/scripts/livespec/schemas/dataclasses/*.py` per I3.
- **How to resolve:** Author the four JSON Schema Draft-7 files:
  - `proposal_findings.schema.json` — propose-change / critique
    template-prompt output. Each finding has `name`,
    `target_spec_files[]`, `summary`, `motivation`,
    `proposed_changes`. v010 J6 adds an optional file-level
    `author` field (string) so the LLM can self-declare the
    propose-change author per the precedence rule documented
    in PROPOSAL.md §"propose-change → Author identifier
    resolution" (CLI `--author` → env var
    `LIVESPEC_REVISER_LLM` → payload `author` field →
    `"unknown-llm"` fallback).
  - `doctor_findings.schema.json` — doctor static-phase JSON
    output. Each finding has `check_id`, `status` (one of
    `pass`/`fail`/`skipped`), `message`, `path`, `line`.
  - `seed_input.schema.json` — seed wrapper input. Shape:
    `{files: [{path, content}], intent}`.
  - `revise_input.schema.json` — revise wrapper input. Shape:
    `{decisions: [{proposal_topic, decision, rationale,
    modifications, resulting_files: [{path, content}], reviser_llm}]}`.
    Note: optional `reviser_llm` field carries the LLM's
    best-effort self-identification per I13 precedence.

  Also author the paired hand-authored dataclasses per I3:
  `ProposalFindings`, `DoctorFindings`, `SeedInput`,
  `ReviseInput`, and `LivespecConfig` (for `.livespec.jsonc`).
  Each dataclass lives at
  `scripts/livespec/schemas/dataclasses/<name>.py` with fields
  matching the schema. `check-schema-dataclass-pairing`
  enforces drift-free pairing in both directions (every schema
  has a dataclass; every dataclass has a schema).

  Also: rename every reference to the old
  `critique_findings.schema.json` → `proposal_findings.schema.json`
  in PROPOSAL.md, the style doc, and any layout diagrams.

  Validators in `scripts/livespec/validate/<name>.py` return
  `Result[<Dataclass>, ValidationError]` from the factory
  shape per v007 G4.

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
