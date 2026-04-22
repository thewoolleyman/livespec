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
  v004 / v005 / v006 / v007 / v008>
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

- **Source:** v006 (carried forward to v008)
- **Target spec file(s):** `<repo-root>/justfile`,
  `<repo-root>/lefthook.yml`,
  `<repo-root>/.github/workflows/ci.yml`,
  `<repo-root>/.mise.toml`,
  `<repo-root>/pyproject.toml`,
  `<repo-root>/.vendor.toml` (or per-lib VERSION files per G12)
- **How to resolve:** Author the actual config files per the
  patterns in `python-skill-script-style-requirements.md`.
  Includes: `just bootstrap` target (G16), `just check`
  aggregation behavior (G15), CI matrix with `fail-fast: false`,
  pinned tool versions, ruff/pyright/pytest/coverage configuration
  (including `max-args=6` + `max-positional-args=6` per H5), and
  the recorded vendored-lib versions (including `jsoncomment` per
  H2).

### static-check-semantics

- **Source:** v007 (renamed in v008 from `ast-check-semantics`;
  scope widened per H3, H11, H13, H14)
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
    `check-no-raise-outside-io`, `check-public-api-result-typed`,
    `check-main-guard`, `check-wrapper-shape`.
  - **`check-global-writes` exemption list** (v007 G14 +
    v008 H9): `structlog.configure` in `__init__.py`,
    `structlog.contextvars.bind_contextvars` in `__init__.py`,
    and the `_COMPILED` cache mutation in
    `livespec/io/fastjsonschema_facade.py`.
  - **`check-supervisor-discipline` scope** (v008 H3):
    `livespec/**` in scope; `bin/*.py` (including
    `_bootstrap.py`) as sole exempt subtree; argparse
    `SystemExit` path impossible under `exit_on_error=False`.
  - **Markdown-parsing checks** (v008 H13, H14):
    `bcp14-keyword-wellformedness`'s enumeration of detected
    misspellings and mixed-case standalone-word rules;
    `gherkin-blank-line-format`'s fenced-block detection
    algorithm; `anchor-reference-resolution`'s GFM slug
    algorithm edge cases (case variations, non-ASCII
    headings, duplicate-heading disambiguation suffixes,
    fenced-block exclusion specifics).
  - **Doctor-cycle semantics** (v008 H11):
    `out-of-band-edits` pre-backfill guard glob details (exact
    file/directory patterns that trigger the guard; behavior
    when only one of the guard predicates matches; ordering of
    the guard vs the comparison), `git_head_available`
    detection logic, and the skipped-check finding shape on
    non-git repos.

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

- **Source:** v007 (carried forward to v008)
- **Target spec file(s):**
  `<bundle>/scripts/livespec/parse/front_matter.py`,
  `<bundle>/scripts/livespec/schemas/front_matter.schema.json`
- **How to resolve:** Implement the restricted-YAML parser per the
  format restrictions codified in PROPOSAL.md "Proposed-change file
  format" and "Revision file format" (scalar-only,
  JSON-compatible, no nesting). Author the JSON Schema for
  proposed-change front-matter and revision front-matter.
  Validators in `validate/` consume the parsed dict via the
  factory shape from G4.

### skill-md-prose-authoring

- **Source:** v008 (NEW, H4)
- **Target spec file(s):**
  `.claude-plugin/skills/<sub-command>/SKILL.md` (one per
  sub-command: `seed`, `propose-change`, `critique`, `revise`,
  `doctor`, `prune-history`, `help`)
- **How to resolve:** Author each SKILL.md body per the canonical
  body shape codified in PROPOSAL.md §"Per-sub-command SKILL.md
  body structure" (opening statement; when to invoke; inputs;
  ordered LLM-driven steps; post-wrapper behavior; failure
  handling). Cover: sub-command trigger phrases, Bash invocations
  of `bin/<cmd>.py` with explicit argv, template prompt
  `@`-references, schema validation routing via
  `livespec.validate.<name>.validate`, per-proposal confirmation
  dialogue (`revise` only), `--skip-pre-check` /
  `--skip-subjective-checks` handling, exit-code narration.

### wrapper-input-schemas

- **Source:** v008 (NEW, H6 + H10)
- **Target spec file(s):**
  `<bundle>/scripts/livespec/schemas/proposal_findings.schema.json`
  (renamed from `critique_findings.schema.json`),
  `<bundle>/scripts/livespec/schemas/doctor_findings.schema.json`,
  `<bundle>/scripts/livespec/schemas/seed_input.schema.json`,
  `<bundle>/scripts/livespec/schemas/revise_input.schema.json`
- **How to resolve:** Author the four JSON Schema Draft-7 files:
  - `proposal_findings.schema.json` — propose-change / critique
    template-prompt output. Each finding has `name`,
    `target_spec_files[]`, `summary`, `motivation`,
    `proposed_changes`.
  - `doctor_findings.schema.json` — doctor static-phase JSON
    output. Each finding has `check_id`, `status` (one of
    `pass`/`fail`/`skipped`), `message`, `path`, `line`.
  - `seed_input.schema.json` — seed wrapper input. Shape:
    `{files: [{path, content}], intent}`.
  - `revise_input.schema.json` — revise wrapper input. Shape:
    `{decisions: [{proposal_topic, decision, rationale,
    modifications, resulting_files: [{path, content}]}]}`.

  Also: rename every reference to the old
  `critique_findings.schema.json` → `proposal_findings.schema.json`
  in PROPOSAL.md, the style doc, and any layout diagrams.
