# Plan: Bootstrap the `livespec` specification and repo

**Status:** Pre-execution. This document captures everything required
to exit the brainstorming phase and stand up a working `livespec`
repo whose own `SPECIFICATION/` tree is seeded from the brainstorming
artifacts and whose skill bundle implements the PROPOSAL.

**Version basis.** The plan body below is written against
PROPOSAL.md v018, which has now been produced by the
continuation interview pass that landed Q1-Option-A (template
sub-specifications) alongside Q2-Q6:
- Q2: explicit bootstrap-exception clause in §"Self-
  application" (the loop becomes operable from first seed
  onward).
- Q3: one-time initial-vendoring procedure in §"Vendoring
  discipline" (applies at Phase 2 of this plan).
- Q4: closures for `returns-pyright-plugin-disposition`
  (vendor the plugin as sixth vendored lib) and
  `basedpyright-vs-pyright` (stay on pyright). Both land at
  Phase 1 via `pyproject.toml` pinning per the
  post-commit-b041d19 plan revision.
- Q5: new prompt-QA tier at `tests/prompts/<template>/` +
  `just check-prompts` recipe in Phase 5 test-suite phase.
- Q6: Companion-documents migration-class policy + per-doc
  assignment table in PROPOSAL.md §"Self-application"
  (Phase 6 / Phase 8 consumption).

PROPOSAL.md v018 is now the frozen basis for every phase
below; Phase 0 freezes at v018.

Execution is performed by the prompt at the end of this file. The
prompt is self-contained; it can be pasted into a fresh Claude Code
session in the `livespec` repo.

---

## 1. Inputs (authoritative sources)

The plan operates on these files. They are the single source of
truth for every decision encoded below; the plan itself does not
restate their content.

Working proposal + embedded grounding:

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md` (frozen at
  the latest post-interview version; see "Version basis" above)
- `brainstorming/approach-2-nlspec-based/livespec-nlspec-spec.md`
- `prior-art/nlspec-spec.md`

Companion documents (all under
`brainstorming/approach-2-nlspec-based/`):

- `python-skill-script-style-requirements.md`
- `deferred-items.md`
- `goals-and-non-goals.md`
- `subdomains-and-unsolved-routing.md`
- `prior-art.md`
- `2026-04-19-nlspec-lifecycle-diagram.md`
- `2026-04-19-nlspec-lifecycle-diagram-detailed.md`
- `2026-04-19-nlspec-lifecycle-legend.md`
- `2026-04-19-nlspec-terminology-and-structure-summary.md`

History:

- `brainstorming/approach-2-nlspec-based/history/README.md`
- `brainstorming/approach-2-nlspec-based/history/v001/` through
  the latest `history/vNNN/` directory (every `PROPOSAL.md`,
  `proposed_changes/`, `conversation.json`,
  `retired-documents/`)

Anything NOT in the list above MUST NOT influence the plan's
output. Files under `history/vNNN/retired-documents/` are
reference-only.

---

## 2. Preconditions

- Repo root is `/data/projects/livespec/` with `master` branch
  clean.
- No `.claude-plugin/`, `.claude/`, `.mise.toml`, `justfile`,
  `lefthook.yml`, `pyproject.toml`, `dev-tooling/`, `tests/`,
  `SPECIFICATION/`, `SPECIFICATION.md`, `NOTICES.md`, or
  `.vendor.jsonc` exist yet at repo root.
- `brainstorming/` and `prior-art/` persist AS-IS — they are
  historical reference material and are not rewritten or moved by
  this plan.
- The brainstorming interview pass producing v018 HAS RUN and
  been frozen. Its revision file (at
  `brainstorming/approach-2-nlspec-based/history/v018/
  proposed_changes/proposal-critique-v17-revision.md`) records
  six accepted decisions (Q1-Q6 all accepted at option A):
  Q1-Option-A (template sub-specifications under
  `SPECIFICATION/templates/<name>/`), Q2 (bootstrap-exception
  clause), Q3 (initial-vendoring procedure), Q4 (returns
  pyright plugin vendored + pyright stays), Q5 (prompt-QA
  tier at `tests/prompts/`), Q6 (companion-documents migration-
  class policy + assignment table). The resulting frozen
  `PROPOSAL.md` v018, plus touched companion docs
  (`deferred-items.md`;
  `python-skill-script-style-requirements.md`), is the
  authority for Phases 0-10 below.
- PROPOSAL.md is treated as frozen from Phase 0 onward. No
  further brainstorming revisions are produced; all subsequent
  refinement happens inside the seeded `SPECIFICATION/` via
  `propose-change` / `revise`.

---

## 3. Cutover principle

Brainstorming artifacts → immutable. The first real
`SPECIFICATION/` tree is produced by `livespec seed` run against
this repo; from that moment on, every change flows through the
governed loop (propose-change → critique → revise). The
brainstorming folder becomes archival.

The skill implementation is bootstrapped by hand only to the
minimum shape required to run `seed` against this repo; the
remaining scope lands through `propose-change` / `revise` cycles
authored by the skill itself (dogfooding, per PROPOSAL.md
§"Self-application"). **PROPOSAL.md v018 Q2 codifies the
bootstrap exception**: the bootstrap ordering in §"Self-
application" steps 1-4 (this plan's Phases 0-5, up through
the first seed in Phase 6) lands imperatively; the governed
loop becomes MANDATORY from Phase 6 onward. Hand-editing any
file under any spec tree or under
`.claude-plugin/specification-templates/<name>/` after Phase 6
is a bug in execution per that clause.

The SPECIFICATION tree is NOT flat: it contains the main spec
files AND a nested sub-spec per built-in template under
`SPECIFICATION/templates/<name>/` (per v018 Q1-Option-A). Each
sub-spec is a first-class livespec-managed spec tree with its
own `proposed_changes/` and `history/`. `seed` produces main +
two template sub-specs atomically; later `propose-change` /
`revise` invocations target a specific spec tree via
`--spec-target <path>`. The agentic generation of each built-in
template's shipped content (its `template.json`,
`prompts/*.md`, and `specification-template/`) flows from
that template's sub-spec.

---

## 4. Phases

Each phase has a clear exit criterion. Phases are sequential;
sub-steps within a phase MAY run in parallel where noted.

### Phase 0 — Freeze the brainstorming folder

1. Confirm `brainstorming/approach-2-nlspec-based/PROPOSAL.md` is
   byte-identical to the latest `history/vNNN/PROPOSAL.md`
   snapshot (the version that adopts Q1-Option-A per the
   Preconditions section).
2. Add a top-of-file note to
   `brainstorming/approach-2-nlspec-based/PROPOSAL.md`:
   > **Status:** Frozen at vNNN. Further evolution happens in
   > `SPECIFICATION/` via `propose-change` / `revise`. This file
   > and the rest of the `brainstorming/` tree are historical
   > reference only.
3. `tmp/` is deleted (empty; was working directory for earlier
   passes).
4. Nothing else in `brainstorming/` is modified.

**Exit criterion:** a single commit `freeze: vNNN brainstorming`
containing only the header-note addition and `tmp/` removal.

### Phase 1 — Repo-root developer tooling

Create at repo root (outside the plugin bundle), exactly as
specified in PROPOSAL.md §"Developer tooling layout" and the
style doc §"Dev tooling and task runner":

- `.mise.toml` pinning `python@3.10.x`, `just`, `lefthook`,
  `ruff`, `pyright`, `pytest`, `pytest-cov`, `pytest-icdiff`,
  `hypothesis`, `hypothesis-jsonschema`, `mutmut`,
  `import-linter` to exact versions. (`typing_extensions` is
  vendored, NOT mise-pinned.)
- `pyproject.toml` containing:
  - `[tool.ruff]` per style doc §"Linter and formatter"
    (27 categories; pylint thresholds; TID banned imports).
  - `[tool.pyright]` strict + the six strict-plus diagnostics
    (`reportUnusedCallResult`, `reportImplicitOverride`,
    `reportUninitializedInstanceVariable`,
    `reportUnnecessaryTypeIgnoreComment`,
    `reportUnnecessaryCast`, `reportUnnecessaryIsInstance`,
    `reportImplicitStringConcatenation`), plus (per v018 Q4)
    `pluginPaths = ["_vendor/returns_pyright_plugin"]` pointing
    at the sixth vendored lib that Phase 2 will land. The
    `returns-pyright-plugin-disposition` and
    `basedpyright-vs-pyright` deferred items are CLOSED in
    v018 with concrete decisions: **returns pyright plugin is
    vendored alongside the library** (PROPOSAL.md §"Runtime
    dependencies — Vendored pure-Python libraries"); **pyright
    is the chosen typechecker, NOT basedpyright** (PROPOSAL.md
    §"Runtime dependencies — Developer-time dependencies →
    Typechecker decision (v018 Q4)"). Rationale is captured
    in a leading `#` comment block in `pyproject.toml`
    cross-referencing those PROPOSAL.md sections. Phase 6
    migrates the rationale into
    `SPECIFICATION/constraints.md`; Phase 8 items 8 and 9
    become bookkeeping closes pointing at the Phase-1 commit.
  - `[tool.pytest.ini_options]` wiring `pytest-cov` +
    `pytest-icdiff`.
  - `[tool.coverage.run]` / `[tool.coverage.report]` with
    100% line+branch, `source` covering `livespec` package and
    `.claude-plugin/scripts/bin`, `fail_under = 100`.
  - `[tool.importlinter]` with the two authoritative contracts
    (`parse-and-validate-are-pure`, `layered-architecture`) per
    v013 M7 as narrowed by v017 Q3.
  - `[tool.mutmut]` for mutmut runtime config ONLY; NO
    `threshold` key. The ratchet-with-ceiling semantics
    (floor = current baseline, capped at 80%) live entirely
    in the `just check-mutation` recipe: it reads
    `.mutmut-baseline.json`, computes
    `min(baseline_kill_rate, 80)`, and fails if the run's
    kill-rate is below that. A static `threshold = 80` in
    pyproject would misstate the spec (DoD 10).
  - NO build-system section (livespec is not a published PyPI
    package; it ships via Claude Code plugin bundling).
- `justfile` with the canonical target list from the style doc
  §"Enforcement suite — Canonical target list". All recipes
  delegate to their underlying tool or to
  `python3 dev-tooling/checks/<name>.py`. Includes
  `just bootstrap`, `just check`, every `just check-*`,
  `just e2e-test-claude-code-mock`,
  `just e2e-test-claude-code-real`,
  `just check-prompts` (v018 Q5; recipe body
  `pytest tests/prompts/`),
  `just check-mutation`,
  `just check-no-todo-registry`, `just fmt`, `just lint-fix`,
  `just vendor-update <lib>`. At this phase, `just bootstrap`
  contains ONLY `lefthook install`; the
  `.claude/skills → ../.claude-plugin/skills` symlink-recreation
  step is added by Phase 2, after the target directory exists.
- `lefthook.yml` with pre-commit and pre-push hooks; every
  `run:` is `just check`.
- `.github/workflows/ci.yml` — per-target matrix with
  `fail-fast: false` invoking `just <target>`; installs pinned
  tools via `jdx/mise-action@v2`.
- `.github/workflows/release-tag.yml` — runs
  `just check-mutation` and `just check-no-todo-registry` on
  tag push.
- `.github/workflows/e2e-real.yml` — invokes
  `just e2e-test-claude-code-real` on `merge_group`, `push` to
  `master`, and `workflow_dispatch`; gated on
  `ANTHROPIC_API_KEY`.
- `.vendor.jsonc` — JSONC with an entry per vendored library
  (`returns`, `returns_pyright_plugin` per v018 Q4,
  `fastjsonschema`, `structlog`, `jsoncomment`,
  `typing_extensions` — six entries total). Each entry records
  `upstream_url`, `upstream_ref`, `vendored_at`;
  `typing_extensions` also records `shim: true`. For the shim,
  `upstream_ref` is the upstream `typing_extensions` release
  whose `override` / `assert_never` semantics the shim
  faithfully replicates (e.g., `"4.12.2"`) — giving reviewers
  a concrete comparison target. Widening the shim later
  updates `upstream_ref` to the then-matching upstream
  version. Phase 1 authors all six entries with placeholder
  `upstream_ref` and `vendored_at` values; Phase 2's
  initial-vendoring procedure (per v018 Q3) populates the
  real values during the manual git-clone-and-copy step.
- `.mutmut-baseline.json` — placeholder recording
  `baseline_reason: "pre-implementation placeholder; real
  baseline captured on first release-tag run"`, `kill_rate_percent: 0`,
  `mutants_surviving: 0`, `mutants_total: 0`,
  `measured_at: "<UTC>"`. Replaced on first release-tag run.
- `NOTICES.md` listing every vendored library with its
  upstream project, license name, and a verbatim license
  reference.
- `.gitignore` amendments (ignore `__pycache__/`, `.pytest_cache/`,
  `.coverage`, `.ruff_cache/`, `.pyright/`, `.mutmut-cache/`,
  `htmlcov/`). `.mypy_cache/` is intentionally NOT listed:
  mypy compatibility is a style-doc non-goal, so its cache
  path is not a tolerated artifact.

**Exit criterion:** `mise install` succeeds; `just bootstrap`
(which at this stage just runs `lefthook install`) succeeds;
`just --list` shows every target from the canonical table.

### Phase 2 — Plugin bundle skeleton

Create the plugin bundle under `.claude-plugin/` exactly matching
PROPOSAL.md §"Skill layout inside the plugin":

- `.claude-plugin/plugin.json` populated per the current Claude
  Code plugin format.
- `.claude/skills/` → relative symlink to `../.claude-plugin/skills/`;
  committed as a tracked symlink.
- `.claude-plugin/skills/<sub-command>/SKILL.md` for each of:
  `help`, `seed`, `propose-change`, `critique`, `revise`,
  `doctor`, `prune-history`. At this stage each SKILL.md carries
  the required frontmatter (`name`, `description`,
  `allowed-tools`, plus `disable-model-invocation: true` on
  `prune-history`) and a placeholder body marked "authoring
  deferred to `skill-md-prose-authoring`".
- `.claude-plugin/scripts/bin/` — shebang wrappers per
  §"Shebang-wrapper contract":
  - `_bootstrap.py` — full body per the style doc's
    `bin/_bootstrap.py` contract.
  - `seed.py`, `propose_change.py`, `critique.py`, `revise.py`,
    `doctor_static.py`, `resolve_template.py`,
    `prune_history.py` — each is the exact 6-statement form
    (`check-wrapper-shape` passes).
  - `chmod +x` applied to every wrapper.
- `.claude-plugin/scripts/_vendor/<lib>/` — vendored pure-Python
  libraries, each with its upstream `LICENSE`, at the exact
  upstream ref recorded in `.vendor.jsonc`. **Per v018 Q3, the
  initial population of each upstream-sourced lib follows the
  one-time manual procedure documented in PROPOSAL.md
  §"Vendoring discipline — Initial-vendoring exception"**
  (git clone + checkout + cp + LICENSE capture + record in
  `.vendor.jsonc` + smoke-test import); after `jsoncomment` is
  in place, subsequent re-vendoring of any upstream-sourced lib
  flows through `just vendor-update <lib>`.
  - `returns/` (dry-python/returns, BSD-2)
  - `returns_pyright_plugin/` (dry-python/returns pyright
    plugin, BSD-2; v018 Q4 — configures pyright strict-mode
    `Result` / `IOResult` inference; referenced via
    `[tool.pyright]`'s `pluginPaths` entry added to
    `pyproject.toml` in Phase 1)
  - `fastjsonschema/` (MIT)
  - `structlog/` (BSD-2 / MIT dual)
  - `jsoncomment/` (MIT)
  - `typing_extensions/` — the ~15-line shim per v013 M1
    exporting exactly `override` and `assert_never`, with a
    verbatim PSF-2.0 `LICENSE`. (Initial-vendoring exception
    does NOT apply to shim libraries — shims are livespec-
    authored by hand per v013 M1.)
- `.claude-plugin/scripts/livespec/` — Python package with the
  subdirectories enumerated in the PROPOSAL tree
  (§"Skill layout"): `commands/`, `doctor/` (with
  `run_static.py` + `static/__init__.py` registry +
  per-check modules), `io/`, `parse/`, `validate/`,
  `schemas/` (plus `schemas/dataclasses/`), `context.py`,
  `types.py`, `errors.py`, `__init__.py`. **`errors.py` is
  authored fully at Phase 2, NOT stubbed** — it carries the
  full `LivespecError` hierarchy + `HelpRequested` per the
  style doc §"Exit code contract". Justification: Phase 2's
  stub contract requires `IOFailure(<DomainError>(...))` /
  `Failure(<DomainError>(...))` return statements that
  reference `LivespecError` subclasses defined in
  `errors.py`. Phase 2 must therefore land `errors.py` in
  full so the stubs can reference real domain-error classes.
  `livespec/__init__.py` (structlog configuration + `run_id`
  bind) is also full at Phase 2.
- `.claude-plugin/specification-templates/livespec/` and
  `.claude-plugin/specification-templates/minimal/` — both
  built-in templates, at **bootstrap-minimum scaffolding
  only** (per v018 Q1-Option-A). Each has:
  - `template.json` with required fields
    (`template_format_version: 1`, `spec_root`, optional
    doctor-hook paths populated per PROPOSAL.md's template
    schema).
  - `prompts/{seed,propose-change,revise,critique}.md` each
    authored at a minimum-viable level — just enough for the
    Phase 3 / Phase 6 bootstrap seed to succeed against this
    repo. Their full authoring lands in Phase 7 as agent-
    generated output against each template's sub-spec (which
    itself is seeded in Phase 6).
  - `specification-template/…` as an empty skeleton
    (directory tree only, no starter content files). Starter
    content is generated agentically in Phase 7 from the
    template's sub-spec.
  The `livespec` template also ships `livespec-nlspec-spec.md`
  at its root (copied verbatim from
  `brainstorming/approach-2-nlspec-based/livespec-nlspec-spec.md`)
  and carries a stub `prompts/doctor-llm-subjective-checks.md`.
  The `minimal` template's stub prompts carry placeholder
  delimiter-comment markers; the final delimiter-comment
  format and its codification in the `minimal` template
  sub-spec (`SPECIFICATION/templates/minimal/contracts.md`)
  are Phase 7 work.

All code in this phase is stub-level EXCEPT the wrapper shapes,
`_bootstrap.py`, `livespec/__init__.py` (structlog
configuration + `run_id` bind), and `livespec/errors.py` (full
`LivespecError` hierarchy + `HelpRequested` — required by the
stub contract below so stub bodies can reference real
domain-error classes).

**Stub contract (authoritative for Phases 2–3 stubs).** Every
stubbed module under `.claude-plugin/scripts/livespec/**`
satisfies the following from the moment it lands:

- A module-top `__all__: list[str]` is declared and enumerates
  every public name the module exposes (required by
  `check-all-declared`).
- Every public function carries complete type annotations
  including the `Result[...]` or `IOResult[...]` return type
  (required by `check-public-api-result-typed`).
- Every stubbed function body is exactly one statement returning
  a single, stable value:
  - `IOResult`-returning functions: `return
    IOFailure(<DomainError>("<module>: not yet implemented"))`
    where `<DomainError>` is a `LivespecError` subclass already
    defined in `livespec/errors.py`.
  - Pure `Result`-returning functions: `return
    Failure(<DomainError>("<module>: not yet implemented"))`.
- Phase 5 tests assert that single return path; one test per
  stubbed public function is sufficient for 100% line+branch
  coverage of the stub.

Also, Phase 2 amends `just bootstrap` authored in Phase 1 to
append the defensive symlink step:
`ln -sfn ../.claude-plugin/skills .claude/skills` — safe to run
now that `.claude-plugin/skills/` exists. `lefthook install`
remains the first step of the recipe.

Every directory under `.claude-plugin/scripts/` (excluding the
entire `_vendor/` subtree) MUST carry a `CLAUDE.md` describing
its local constraints.

**Exit criterion:** `just check-wrapper-shape`,
`just check-claude-md-coverage`, `just check-main-guard`, and
`ruff check` all pass on the skeleton. `pyright` may still
report errors against the stub bodies (acceptable at this phase;
`check-types` is a Phase-5 gate). **Plugin-loading smoke
check**: `readlink .claude/skills` resolves to
`../.claude-plugin/skills`; `ls .claude/skills/` enumerates
exactly the seven sub-command directories (`help`, `seed`,
`propose-change`, `critique`, `revise`, `doctor`,
`prune-history`); and a fresh `claude` session rooted at the
repo lists seven `/livespec:*` slash commands in its autocomplete
menu.

### Phase 3 — Minimum viable `livespec seed`

Flesh out exactly the code path required to run `livespec seed`
successfully against this repo. This is the bootstrap moment;
everything else is downstream of it.

Required implementation surface (everything else stays stubbed):

- `livespec/errors.py` — landed in Phase 2 (full
  `LivespecError` hierarchy + `HelpRequested` per the style
  doc §"Exit code contract"). Phase 3 verifies Phase 2's
  errors.py covers every domain-error class the seed
  implementation uses; widens the hierarchy if Phase 3
  surfaces new classes that weren't anticipated at Phase 2.
- `livespec/types.py` — every canonical `NewType` alias listed in
  the style doc §"Domain primitives via `NewType`".
- `livespec/context.py` — `DoctorContext`, `SeedContext`, and
  the other context dataclasses with the exact fields named in
  the style doc §"Context dataclasses", including v014 N3's
  `config_load_status` / `template_load_status` AND v018 Q1's
  `template_scope: Literal["main", "sub-spec"]` (used by
  `run_static.py` for per-tree applicability dispatch — see the
  `APPLIES_TO` constant rule below in this phase's
  `livespec/doctor/static/` enumeration).
- `livespec/io/`:
  - `fs.py` — `@impure_safe` filesystem primitives; shared
    upward-walk helper per v017 Q9.
  - `git.py` — `get_git_user() -> IOResult[str, GitUnavailableError]`
    with the three-branch semantics (full success / partial /
    absent) from PROPOSAL.md §"Git".
  - `cli.py` — argparse-with-`exit_on_error=False` wrapped per
    the style doc §"CLI argument parsing seam".
  - `fastjsonschema_facade.py` — cached compile keyed on `$id`.
  - `structlog_facade.py` — typed logging wrapper.
  - `returns_facade.py` — typed re-exports (pending
    `returns-pyright-plugin-disposition`).
- `livespec/parse/jsonc.py` — thin pure wrapper over the
  vendored `jsoncomment`.
- `livespec/validate/` — factory-shape validators for the
  schemas seed actually needs in Phase 3:
  `livespec_config.py`, `template_config.py`, `seed_input.py`,
  `finding.py`, `doctor_findings.py`.
- `livespec/schemas/*.schema.json` + paired
  `schemas/dataclasses/*.py` for the same set. Three-way
  pairing passes `check-schema-dataclass-pairing`.
- `livespec/commands/resolve_template.py` — full implementation
  per PROPOSAL.md §"Template resolution contract": supports
  `--project-root`, `--template`, upward-walk on `.livespec.jsonc`,
  built-in-name-vs-path resolution, stdout contract, exit-code
  table.
- `livespec/commands/seed.py` — full implementation per
  PROPOSAL.md §"`seed`": `--seed-json` intake, pre-seed
  `.livespec.jsonc` bootstrap per v016 P2 + v017 Q5/Q6,
  idempotency refusal, v001 history materialization,
  auto-capture of `seed.md` proposed-change +
  `seed-revision.md`. Per v018 Q1-Option-A, the
  implementation ALSO produces the two template sub-spec
  trees under `SPECIFICATION/templates/<name>/` atomically
  with the main tree — each sub-spec gets its own
  `spec.md`/`contracts.md`/`constraints.md`/`scenarios.md`,
  its own `proposed_changes/` with `README.md`, and its own
  `history/v001/` materialized from the payload.
  `seed_input.schema.json` widens to carry a
  `sub_specs: list[SubSpecPayload]` field; Phase 3 authors
  the schema + dataclass + validator triple for
  `SubSpecPayload`.
- `livespec/doctor/run_static.py` — orchestrator per PROPOSAL.md
  §"Static-phase structure" + v014 N3 bootstrap lenience + v018
  Q1 per-tree iteration. The orchestrator enumerates
  `(spec_root, template_name)` pairs at startup (main tree
  first; then each sub-spec tree under
  `<main-spec-root>/templates/<sub-name>/`); per pair it builds
  a per-tree `DoctorContext` (with `template_scope` set
  appropriately) and runs the applicable check subset.
- `livespec/doctor/static/__init__.py` — static registry. Per
  v018 Q1, each entry exposes the triple `(SLUG, run, APPLIES_TO)`
  (extending the prior `(SLUG, run)` shape).
- `livespec/doctor/static/` — each check module declares an
  `APPLIES_TO: frozenset[Literal["main", "sub-spec"]]`
  module-top constant alongside `SLUG` and `run`. The
  orchestrator inspects this constant per-tree to decide
  whether to invoke the check. Default value: `frozenset({
  "main", "sub-spec"})` (the check runs on every tree). The
  three v1 narrowings:
  - `template_exists`: `APPLIES_TO = frozenset({"main"})`
    (sub-spec trees are spec trees, not template payloads).
  - `template_files_present`: `APPLIES_TO = frozenset({
    "main"})` (same reason).
  - `gherkin_blank_line_format`: `APPLIES_TO = frozenset({
    "main", "sub-spec"})` BUT the check itself emits a
    `status: "skipped"` Finding when the tree's template
    convention is the `minimal` template's no-Gherkin
    convention (the conditional applicability is content-
    aware; runtime skip is cleaner than a more elaborate
    constant). The exact dispatch is codified in
    `static-check-semantics`.
  Phase-3 minimum subset of checks the seed post-step
  exercises: `livespec_jsonc_valid`, `template_exists`,
  `template_files_present`, `proposed_changes_and_history_dirs`,
  `version_directories_complete`, `version_contiguity`,
  `revision_to_proposed_change_pairing`,
  `proposed_change_topic_format`. (Remaining checks —
  `out_of_band_edits`, `bcp14_keyword_wellformedness`,
  `gherkin_blank_line_format`, `anchor_reference_resolution` —
  stubbed to return a `skipped` finding with message
  "not-yet-implemented"; they're fleshed out in Phase 7.)
- `seed/SKILL.md` — **bootstrap prose** covering the pre-seed
  template dialogue, the two-step `resolve_template.py` →
  Read(`prompts/seed.md`) dispatch, payload assembly, wrapper
  invocation, post-wrapper narration, and exit-code handling
  with retry-on-4. This is intentionally narrower than the full
  per-sub-command body structure in PROPOSAL.md; Phase 7 brings
  it to final per `skill-md-prose-authoring`.
- `doctor/SKILL.md`, `help/SKILL.md` — **bootstrap prose**
  (enough to run the LLM-driven phase orchestration during
  Phase 6). Phase 7 brings both to final alongside the four
  remaining SKILL.md bodies.
- The `livespec` template's `prompts/seed.md` — **bootstrap-
  minimum authoring** sufficient for the Phase 6 seed LLM
  round-trip to produce a schema-valid
  `seed_input.schema.json` payload covering the main spec AND
  the two template sub-specs (per v018 Q1-Option-A). This is
  intentionally narrower than the full template-controlled
  seed interview; the full `prompts/seed.md` is regenerated
  from the `livespec` template's sub-spec in Phase 7.
  The `minimal` template's `prompts/seed.md` stays stubbed at
  this phase — Phase 6 uses only the `livespec` template. All
  four `minimal`-template prompts and the three remaining
  `livespec`-template prompts (`propose-change`, `revise`,
  `critique`) are Phase 7 work.

**Exit criterion (narrow Phase-3 gate).** `just check-lint`,
`just check-wrapper-shape`, `just check-main-guard`, and
`just check-schema-dataclass-pairing` all succeed. Running
`/livespec:seed` against a throwaway `tmp_path` fixture produces
a valid `.livespec.jsonc`, spec tree, and `history/v001/`.

Full `just check` is NOT a Phase-3 gate. The following targets
are deliberately deferred to Phase 5's exit criterion, once
tests and remaining enforcement scripts exist: `check-tests`,
`check-coverage`, `check-pbt-coverage-pure-modules`,
`check-claude-md-coverage` (tests/ branch), `check-types`
(pyright strict against Phase-2/3 stubs), and every target
backed by a Phase-4 `dev-tooling/checks/*.py` script. Phase-2/3
stubs conform to the Phase-2 stub contract so they pass Phase-5
gates without refactor.

### Phase 4 — Developer tooling enforcement scripts

Author every enforcement check under `dev-tooling/checks/` per
the canonical `just` target list. Each script is a standalone
Python module conforming to the same style rules as the shipped
code (`just check` includes `dev-tooling/**` in scope). Scripts:

- `file_lloc.py` — file ≤ 200 logical lines.
- `private_calls.py`, `global_writes.py`,
  `supervisor_discipline.py`, `no_raise_outside_io.py` (raise-site
  only per v017 Q3), `no_except_outside_io.py`,
  `public_api_result_typed.py` (`__all__`-based per v012 L9),
  `main_guard.py`, `wrapper_shape.py` (permits the optional blank
  line per v016 P5), `schema_dataclass_pairing.py` (three-way per
  v013 M6), `keyword_only_args.py` (also verifies
  `frozen=True`+`kw_only=True`+`slots=True` on `@dataclass`),
  `match_keyword_only.py`, `no_inheritance.py` (direct-parent
  allowlist per v013 M5), `assert_never_exhaustiveness.py`,
  `newtype_domain_primitives.py`, `all_declared.py`,
  `no_write_direct.py`, `pbt_coverage_pure_modules.py`,
  `claude_md_coverage.py`, `no_direct_tool_invocation.py`
  (grep-level), `no_todo_registry.py` (release-gate only).

Each script has a paired `tests/dev-tooling/checks/test_<name>.py`.

Every `dev-tooling/` directory carries a `CLAUDE.md`.

**Exit criterion:** `just check` passes against the current code
base. Every check listed in the canonical table is invokable and
non-trivial (tests cover both pass and fail cases).

### Phase 5 — Test suite

Build out the test tree per PROPOSAL.md §"Testing approach":

- `tests/` mirrors `.claude-plugin/scripts/livespec/`,
  `.claude-plugin/scripts/bin/`, and `<repo-root>/dev-tooling/`
  one-to-one.
- `tests/bin/test_wrappers.py` — meta-test: every wrapper matches
  the 6-statement shape.
- `tests/bin/test_<cmd>.py` — per-wrapper coverage test that
  imports the wrapper under `monkeypatch`-stubbed `main`,
  catches `SystemExit` via `pytest.raises`.
- `tests/bin/test_bootstrap.py` — covers `_bootstrap.bootstrap()`.
  Covers BOTH sides of the `sys.version_info` check via
  `monkeypatch.setattr(sys, "version_info", (3, 9, 0, "final", 0))`
  (and its 3.10+ counterpart). Pragma exclusions on `bin/*.py`
  are forbidden by v011 K3, so branch coverage of the
  exit-127 path is achieved exclusively through monkeypatching.
- `tests/e2e/` — skeleton directory, `CLAUDE.md`, placeholder
  `fake_claude.py`. Real E2E content is fleshed out in Phase 8
  (tied to the `end-to-end-integration-test` deferred item).
- `tests/prompts/` — (v018 Q5) skeleton directory with
  `CLAUDE.md` describing the prompt-QA harness conventions
  (distinct from `tests/e2e/fake_claude.py`), plus
  `tests/prompts/<template>/` subdirectories for each
  built-in template (`livespec`, `minimal`). Each
  per-template subdirectory carries its own `CLAUDE.md`
  per the strict DoD-13 rule (every directory under
  `tests/` has a `CLAUDE.md`); the per-template
  `CLAUDE.md` MAY be a brief one-paragraph cross-reference
  to `tests/prompts/CLAUDE.md` when conventions don't
  diverge. Each per-template subdirectory carries placeholder
  `test_{seed,propose_change,revise,critique}.py` per
  PROPOSAL.md §"Testing approach — Prompt-QA tier". Real
  prompt-QA content (harness + fixtures + semantic-property
  assertions) is fleshed out in Phase 7 (as part of each
  built-in template's sub-spec-driven content generation)
  and closed by Phase 8's `prompt-qa-harness` deferred-items
  revision. `just check-prompts` is authored in Phase 1's
  justfile alongside the rest of the canonical target list
  (recipe body: `pytest tests/prompts/`); at Phase 1 time
  `tests/prompts/` doesn't exist yet so the target fails on
  invocation, but Phase 1's exit criterion is that
  `just --list` shows every target — failing-but-defined is
  fine and consistent with how `check-tests` and
  `check-coverage` are listed in Phase 1's justfile but rely
  on Phase-5 test code to actually pass.
- `tests/fixtures/` — empty at this phase; grows through Phases
  6–9.
- `tests/heading-coverage.json` — initially empty array `[]`
  (populated alongside the seeded spec in Phase 6 and after each
  deferred-item-driven revise). Entry shape per v018
  Q1-Option-A carries a `spec_root` field discriminating the
  main spec from each template sub-spec tree.
- `tests/test_meta_section_drift_prevention.py` — covers the
  registry.
- Every `tests/` directory (with `fixtures/` subtrees excluded at
  any depth) carries a `CLAUDE.md`.

`just check-coverage` MUST pass at 100% line+branch.

**Exit criterion:** `just check` passes end-to-end including
`check-tests`, `check-coverage`, `check-pbt-coverage-pure-modules`,
and `check-claude-md-coverage`.

### Phase 6 — First self-application seed

Run `/livespec:seed` against `/data/projects/livespec` itself,
producing the real `SPECIFICATION/` tree — main spec + the two
built-in-template sub-specs atomically, per v018 Q1-Option-A.

Seed scope is deliberately NARROW for the MAIN spec: Phase 6
seeds the main spec from PROPOSAL.md + `goals-and-non-goals.md`
ONLY. The companion docs
(`python-skill-script-style-requirements.md`,
`livespec-nlspec-spec.md`, `subdomains-and-unsolved-routing.md`,
lifecycle/terminology docs, prior-art survey) are migrated
individually in Phase 8 via dedicated propose-change/revise
cycles (items 2 and 3). This preserves the seed as a clean
PROPOSAL.md-grounded first cut and lets each companion-doc
migration be auditable as its own revision, rather than relying
on a single 295KB-context seed pass that risks lossy
compression.

For the two TEMPLATE SUB-SPECS, Phase 6 seeds from the
PROPOSAL.md sections describing each built-in template plus
the `livespec-nlspec-spec.md` shipped alongside the `livespec`
template. The sub-specs land bootstrap-minimum at this phase;
they are widened in Phase 7 via propose-change/revise when the
full template content (prompts, starter content, delimiter-
comment format) is authored.

Seed intent fed to the prompt:

> Seed this project's `SPECIFICATION/` tree from the frozen
> `PROPOSAL.md` and `goals-and-non-goals.md` in
> `brainstorming/approach-2-nlspec-based/`. Use the `livespec`
> built-in template (multi-file). The
> `livespec-nlspec-spec.md` the template's prompts use at
> seed-time comes from the template's own copy, NOT from the
> brainstorming folder.
>
> MAIN SPEC:
> `spec.md` carries the core PROPOSAL material (runtime and
> packaging, specification model, sub-command lifecycle,
> versioning, pruning, sub-commands, proposed-change /
> revision file formats, testing approach, developer-tooling
> layout, Definition of Done, non-goals, self-application).
> `contracts.md` carries the skill↔template JSON contracts
> (input/output schemas; wrapper CLI shapes), the
> lifecycle exit-code table, and the sub-spec structural
> mechanism (propose-change/revise `--spec-target` flag;
> `seed_input.schema.json`'s `sub_specs` field; per-sub-spec
> doctor parameterization).
> `constraints.md` carries the architecture-level
> constraints PROPOSAL.md states directly (Python 3.10+ pin,
> vendored-lib discipline, pure/IO boundary, ROP composition,
> supervisor discipline) plus the typechecker decisions
> pinned in Phase 1. The bulk of
> `python-skill-script-style-requirements.md` lands via a
> Phase 8 propose-change (item 2), NOT here.
> `scenarios.md` carries the happy-path seed/propose-change/
> revise/doctor scenario plus the three error paths v014 N9
> enumerates and the recovery paths from §"seed", §"doctor",
> and §"Pruning history" in PROPOSAL.md.
>
> TEMPLATE SUB-SPEC `SPECIFICATION/templates/livespec/`:
> `spec.md` carries the `livespec` template's user-visible
> behavior: the seed interview flow's intent, the
> propose-change/revise/critique prompt interview intents,
> how `livespec-nlspec-spec.md` is internalized by each
> prompt, and the starter-content policy (what headings get
> derived, what BCP14 placement looks like, the scenarios.md
> literal stub). **`spec.md` MUST also explicitly specify
> that the `livespec` template's `prompts/seed.md` emits the
> full `seed_input.schema.json` payload INCLUDING
> `sub_specs: list[SubSpecPayload]` entries for every v1
> built-in template's sub-spec tree (`livespec` AND
> `minimal`)** — this is what makes the multi-tree atomic
> seed (per v018 Q1) work; the seed prompt regenerated from
> this sub-spec in Phase 7 must preserve this behavior.
> `contracts.md` carries the template-internal JSON contracts
> (what `seed_input.schema.json` payload fields this template
> populates, what `proposal_findings.schema.json` fields the
> critique prompt populates) AND a "Per-prompt
> semantic-property catalogue" subsection enumerating the
> testable semantic properties for each REQUIRED prompt
> (`seed`, `propose-change`, `revise`, `critique`) — at
> Phase 6 this is bootstrap-minimum (1-2 properties per
> prompt; e.g., for `seed`: "MUST derive top-level headings
> from intent nouns, not from a fixed taxonomy"); Phase 7's
> first propose-change against this sub-spec widens the
> catalogue to the full assertion surface that the v018 Q5
> prompt-QA harness asserts against.
> `constraints.md` carries the NLSpec discipline constraints
> (Gherkin blank-line convention, BCP14 keyword well-
> formedness, heading taxonomy conventions).
> `scenarios.md` carries a happy-path seed-interview scenario
> plus one edge-case per prompt.
>
> TEMPLATE SUB-SPEC `SPECIFICATION/templates/minimal/`:
> `spec.md` carries the `minimal` template's single-file
> positioning (reference-minimum for custom-template authors;
> canonical fixture for the end-to-end integration test) and
> its prompt interview intents (reduced vs. `livespec`).
> `contracts.md` carries the delimiter-comment format
> contract (format is itself Phase 7 work; at Phase 6 this
> section is a placeholder with a "TBD in Phase 7" note) AND
> a "Per-prompt semantic-property catalogue" subsection
> bootstrap-minimum the same way the `livespec` sub-spec's
> contracts.md is, scoped to `minimal`'s reduced prompt
> contracts.
> `constraints.md` carries the single-file-only constraint,
> the `spec_root: "./"` convention, and the
> `gherkin-blank-line-format` doctor-check exemption.
> `scenarios.md` carries the end-to-end-integration-test
> scenarios' structural outline (retry-on-exit-4, doctor-
> static-fail-then-fix, prune-history-no-op).

After seed, the working tree contains:

- `.livespec.jsonc` at repo root.
- **Main spec** (per the `livespec` template's multi-file
  convention):
  - `SPECIFICATION/{README.md, spec.md, contracts.md,
    constraints.md, scenarios.md}`.
  - `SPECIFICATION/proposed_changes/` containing only the
    skill-owned `README.md`.
  - `SPECIFICATION/history/README.md` (skill-owned;
    directory-description paragraph per PROPOSAL.md
    §"SPECIFICATION directory structure").
  - `SPECIFICATION/history/v001/` containing frozen copies
    of every main-spec file (`README.md`, `spec.md`,
    `contracts.md`, `constraints.md`, `scenarios.md`) +
    `proposed_changes/seed.md` +
    `proposed_changes/seed-revision.md`.
- **`livespec` template sub-spec** (follows the `livespec`
  template's own convention — multi-file with sub-spec-root
  README and per-version README):
  - `SPECIFICATION/templates/livespec/{README.md, spec.md,
    contracts.md, constraints.md, scenarios.md}`.
  - `SPECIFICATION/templates/livespec/proposed_changes/`
    containing only the skill-owned `README.md`.
  - `SPECIFICATION/templates/livespec/history/README.md`
    (skill-owned).
  - `SPECIFICATION/templates/livespec/history/v001/`
    containing frozen copies of every sub-spec file
    (`README.md`, `spec.md`, `contracts.md`, `constraints.md`,
    `scenarios.md`) + an EMPTY `proposed_changes/` subdir
    (sub-specs do NOT receive auto-captured seed proposals
    per v018 Q1 — the main-spec `seed.md` + `seed-revision.md`
    documents the whole multi-tree creation).
- **`minimal` template sub-spec** (follows the `minimal`
  template's own convention — multi-file but with no
  sub-spec-root README and no per-version README):
  - `SPECIFICATION/templates/minimal/{spec.md, contracts.md,
    constraints.md, scenarios.md}` — note: NO top-level
    `README.md` for this sub-spec.
  - `SPECIFICATION/templates/minimal/proposed_changes/`
    containing only the skill-owned `README.md`.
  - `SPECIFICATION/templates/minimal/history/README.md`
    (skill-owned).
  - `SPECIFICATION/templates/minimal/history/v001/`
    containing frozen copies of every sub-spec file
    (`spec.md`, `contracts.md`, `constraints.md`,
    `scenarios.md` — no `README.md`) + an EMPTY
    `proposed_changes/` subdir.

The seed wrapper writes the skill-owned `proposed_changes/
README.md` AND `history/README.md` per-tree (same content
across trees; only the `<spec-root>/` base differs). The
asymmetry between sub-spec README presence (`livespec`
sub-spec has top-level + per-version README; `minimal`
sub-spec has neither) follows each sub-spec's OWN template
convention, NOT the main-spec template's convention.

Running `/livespec:doctor` against this newly-seeded state
passes its STATIC phase per-tree (main + each sub-spec).
**LLM-driven phases (objective + subjective checks) do NOT run
at Phase 6** — they require `critique` (Phase-7 work) to file
critique-authored proposals against the surfaced findings, and
the full LLM-driven phase orchestration in `doctor/SKILL.md`
is itself Phase-7 work per `skill-md-prose-authoring`. Phase 3's
`doctor/SKILL.md` bootstrap prose covers static-phase invocation
only; it explicitly does NOT invoke an LLM-driven phase. Phase 7
brings doctor's LLM-driven phase to operability AND lands the
first round of critique proposals against the seeded trees.

Every `##` heading in every seeded spec file (main + both
sub-specs) gets a corresponding entry in
`tests/heading-coverage.json` (each entry carries a
`spec_root` field naming its tree; entries with
`test: "TODO"` + non-empty `reason` are acceptable at this
point; Phase 7–8 work replaces TODOs with real test IDs).

**Exit criterion:** `just check` passes; `/livespec:doctor`'s
static phase runs cleanly against every spec tree (exit `0`
per tree). LLM-driven phases are Phase-7 scope; they are NOT
invoked at Phase 6 and consequently NOT part of Phase 6's
exit criterion.

### Phase 7 — Remaining sub-commands + full doctor coverage

With `SPECIFICATION/` in place, implement every sub-command left
stubbed from Phase 3 and flesh out the remaining doctor checks.
Every implementation lands via a `propose-change` → `revise`
cycle against the seeded spec, so SPECIFICATION/ revisions and
code implementation land atomically per the dogfooding rule.
PROPOSAL.md stays frozen — from Phase 6 onward, SPECIFICATION/
is the living oracle.

Work items (each is one or more propose-change files filed
against the seeded `SPECIFICATION/`):

- `livespec/commands/propose_change.py` — full implementation
  including topic canonicalization (v015 O3), reserve-suffix
  canonicalization (v016 P3; v017 Q1), unified author precedence,
  schema validation, collision disambiguation (v014 N6), single-
  canonicalization invariant routing (v016 P4), AND the
  `--spec-target <path>` flag selecting which spec tree's
  `proposed_changes/` is written to (per v018 Q1-Option-A).
- `livespec/commands/critique.py` — full implementation with
  internal delegation to `propose_change` via `-critique`
  reserve-suffix; accepts `--spec-target` and routes
  delegation with the same target.
- `livespec/commands/revise.py` — full implementation including
  per-proposal LLM decision flow (skill-prose-side), delegation
  toggle, version cut, history materialization, rejection flow
  preserving audit trail, AND `--spec-target <path>` targeting
  per v018 Q1-Option-A.
- `livespec/commands/prune_history.py` — full pruning logic with
  `PRUNED_HISTORY.json` marker, no-op short-circuit, numeric
  contiguity.
- `livespec/doctor/static/` — the four remaining checks
  (`out_of_band_edits`, `bcp14_keyword_wellformedness`,
  `gherkin_blank_line_format`, `anchor_reference_resolution`)
  implemented in full with the semantics from PROPOSAL.md
  §"Static-phase checks" and codified in the
  `static-check-semantics` deferred item. `out_of_band_edits`
  honors the pre-backfill guard + auto-backfill semantics
  including author identifier `livespec-doctor`. All doctor-
  static checks are parameterized per-spec-tree per v018
  Q1-Option-A: `run_static.py` iterates over the main spec
  root + each sub-spec root discovered under
  `<main-spec-root>/templates/<name>/`, running the
  appropriate check subset per tree (e.g.,
  `gherkin_blank_line_format` applies to the main spec and
  the `livespec` sub-spec but NOT the `minimal` sub-spec).
- `livespec/doctor/` — LLM-driven phase orchestration in
  `doctor/SKILL.md` including both objective and subjective
  checks + template-extension hooks.
- `parse/front_matter.py` — restricted-YAML parser (tracked by
  the `front-matter-parser` deferred item).
- The full `livespec` template content — its
  `prompts/seed.md` (replacing the Phase 3 bootstrap-minimum
  version), `prompts/propose-change.md`,
  `prompts/revise.md`, `prompts/critique.md`,
  `prompts/doctor-llm-subjective-checks.md` (plus optional
  `doctor-llm-objective-checks.md`), and the
  `specification-template/SPECIFICATION/` starter content —
  is **agent-generated from
  `SPECIFICATION/templates/livespec/`** (the sub-spec seeded
  in Phase 6). Each prompt's authoring lands via a
  `propose-change --spec-target SPECIFICATION/templates/livespec`
  → `revise --spec-target ...` cycle against that sub-spec,
  and the generated template files are committed alongside
  the sub-spec revision. No hand-authoring.
  **Verification (v018 Q1).** The regenerated
  `prompts/seed.md` MUST emit the full
  `seed_input.schema.json` payload INCLUDING
  `sub_specs: list[SubSpecPayload]` entries for every v1
  built-in template's sub-spec tree. Phase 7's revise step
  for `prompts/seed.md` MUST run a smoke-check against the
  regenerated prompt that exercises this behavior (the
  prompt-QA harness from v018 Q5 covers this in tests/prompts/livespec/test_seed.py).
  If the regenerated prompt omits sub_specs[] emission,
  Phase 7's revise rejects the modification.
- The full `minimal` template content — its four prompts
  with their delimiter comments and its single-file starter
  `specification-template/SPECIFICATION.md` — is
  agent-generated from
  `SPECIFICATION/templates/minimal/` sub-spec via the same
  `--spec-target` mechanism. The delimiter-comment format
  is CHOSEN here (not at Phase 9); the choice is codified in
  `SPECIFICATION/templates/minimal/contracts.md` under a
  "Template↔mock delimiter-comment format" section, and THAT
  is what Phase 9's `fake_claude.py` parses against. Future
  custom-template authors can replicate the mock harness
  without reading the parser source.
- All seven SKILL.md prose bodies brought to final per the
  deferred item `skill-md-prose-authoring` — including
  replacing the Phase-3 bootstrap prose for `seed`, `doctor`,
  and `help` with the full per-sub-command body structure
  from PROPOSAL.md (opening, when-to-invoke, inputs, steps,
  post-wrapper, failure handling).

**Exit criterion:** every wrapper in `bin/` has a real
implementation path; every doctor-static check runs in full;
`just check` + `/livespec:doctor` pass on the project's own
`SPECIFICATION/`; every `test: "TODO"` in
`heading-coverage.json` has been resolved to a real test id.

### Phase 8 — Process every deferred-items entry

Walk `brainstorming/approach-2-nlspec-based/deferred-items.md` in
order, filing one or more `propose-change` files for each entry
and running `revise` against them. Each entry's revision either
fully incorporates the content into `SPECIFICATION/` (primary
case) or explains why the entry is superseded / moot / deferred
further (secondary case, with a paired revision explaining the
deferral).

**Default `--spec-target` for Phase 8 (v018 Q1).** Every Phase
8 propose-change uses `--spec-target SPECIFICATION` (the main
spec tree) by default UNLESS the per-item entry below names a
different target. Justification: most deferred items target
spec content in `SPECIFICATION/spec.md` /
`SPECIFICATION/contracts.md` /
`SPECIFICATION/constraints.md` (main); the actual
implementation files (`dev-tooling/checks/`, `pyproject.toml`,
`.claude-plugin/scripts/`, etc.) are committed alongside the
revise but are described BY the main-spec content. The two
v018 NEW entries (`sub-spec-structural-formalization`,
`prompt-qa-harness`) and the three v018 CLOSED entries
(`template-prompt-authoring`,
`returns-pyright-plugin-disposition`,
`basedpyright-vs-pyright`) are bookkeeping closures pointing
at PROPOSAL.md / Phase-1 / Phase-3 / Phase-6 / Phase-7
decisions; their Phase 8 revises are also `--spec-target
SPECIFICATION` (main) — the closure record lives in main's
`history/`, not in any sub-spec's history.

Canonical deferred items — 17 items after v018 (the `### <id>`
schema-example heading at `deferred-items.md` line 29 is not an
item): 15 carried forward from v017 plus 2 new in v018
(`sub-spec-structural-formalization`, `prompt-qa-harness`); 3
closed in v018 (`template-prompt-authoring`,
`returns-pyright-plugin-disposition`,
`basedpyright-vs-pyright`) land as bookkeeping revisions
pointing at PROPOSAL.md / Phase-1 / Phase-7 decisions:

1. `template-prompt-authoring` — CLOSED in v018 Q1. Content
   already landed in Phase 7, generated agentically from
   each template's sub-spec under
   `SPECIFICATION/templates/<name>/` per v018 Q1-Option-A.
   The Phase-7 propose-change that landed the `minimal`
   template's delimiter comments also codified the delimiter-
   comment format contract in
   `SPECIFICATION/templates/minimal/contracts.md` (under a
   "Template↔mock delimiter-comment format" section).
   Phase 8's revise records the closure, pointing at the
   relevant Phase-7 sub-spec revisions and PROPOSAL.md
   §"SPECIFICATION directory structure — Template
   sub-specifications".
2. `python-style-doc-into-constraints` — verifies the style-doc
   migration into `constraints.md` happened cleanly in Phase 6.
3. `companion-docs-mapping` — (v018 Q6) processes every
   companion doc according to its pre-assigned migration class
   (MIGRATED-to-SPEC-file / SUPERSEDED-by-section /
   ARCHIVE-ONLY) per PROPOSAL.md §"Companion documents and
   migration classes". The deferred entry's body is a pointer
   to that section; each Phase-8 propose-change targets one
   companion doc; the paired revise records the migration
   outcome (what was migrated, into which section, or why the
   doc is ARCHIVE-ONLY). Phase 6 has already migrated
   `goals-and-non-goals.md`; Phase 8 processes the remaining
   assignments.
4. `enforcement-check-scripts` — verifies every Phase-4 check
   script matches the canonical list and that `pyproject.toml`'s
   `[tool.importlinter]` carries the narrowed-to-two contracts
   per v017 Q3.
5. `claude-md-prose` — verifies every `CLAUDE.md` exists and
   carries real content (not lorem-ipsum stubs).
6. `task-runner-and-ci-config` — verifies `justfile`,
   `lefthook.yml`, `.github/workflows/*.yml` match the
   configuration codified in `SPECIFICATION/` (the seeded and
   Phase-8-migrated oracle; PROPOSAL.md is frozen reference
   material only).
7. `static-check-semantics` — materializes the
   semantics-codification paragraph for every check touched by
   v006–v017 widenings (bootstrap lenience, GFM anchor rules,
   reserve-suffix algorithm, wrapper-shape blank-line tolerance,
   etc.) into `constraints.md` or `spec.md` as appropriate.
8. `returns-pyright-plugin-disposition` — CLOSED in v018 Q4.
   Plugin vendored at
   `.claude-plugin/scripts/_vendor/returns_pyright_plugin/`
   in Phase 2; `pluginPaths` pinned in `pyproject.toml` in
   Phase 1; rationale migrated to
   `SPECIFICATION/constraints.md` in Phase 6. Bookkeeping
   close pointing at PROPOSAL.md §"Runtime dependencies —
   Vendored pure-Python libraries".
9. `basedpyright-vs-pyright` — CLOSED in v018 Q4. pyright is
   the chosen typechecker; basedpyright is NOT used.
   Rationale in PROPOSAL.md §"Runtime dependencies —
   Developer-time dependencies → Typechecker decision
   (v018 Q4)"; migrated to `SPECIFICATION/constraints.md` in
   Phase 6. Bookkeeping close pointing at the Phase-1 commit.
10. `front-matter-parser` — landed in Phase 7.
11. `skill-md-prose-authoring` — landed in Phase 7.
12. `wrapper-input-schemas` — every input schema authored
    (`seed_input` including v018 Q1's `sub_specs: list[
    SubSpecPayload]` field; new standalone
    `sub_spec_payload.schema.json` + paired dataclass +
    validator per v018 Q1; `proposal_findings`,
    `revise_input`, `proposed_change_front_matter`,
    `revision_front_matter`, plus `doctor_findings`,
    `livespec_config`, `template_config`, `finding` as
    already done).
13. `user-hosted-custom-templates` — documented as v2 scope;
    revise closes the entry with a pointer to the v2 tracking
    (extended in v018 Q1 with the sub-spec-mechanism note —
    v2+ template-discovery extensions MAY declare their own
    sub-spec structure; the `--spec-target` flag surface is
    v1-frozen).
14. `end-to-end-integration-test` — see Phase 9.
15. `local-bundled-model-e2e` — documented as v2 scope; revise
    closes.
16. `sub-spec-structural-formalization` — (v018 Q1 NEW)
    materialized across Phase 3 (seed's multi-tree
    file-shaping work; `--spec-target` flag implementation on
    propose-change / critique / revise; `SubSpecPayload`
    schema + dataclass + validator; `DoctorContext`
    `template_scope` field), Phase 6 (sub-spec tree seeding
    atomically with main tree), Phase 7 (each built-in
    template's sub-spec contents authored via
    `propose-change --spec-target` cycles), and confirmed
    clean by Phase 8. Bookkeeping close pointing at the
    relevant phase commits.
17. `prompt-qa-harness` — (v018 Q5 NEW) materialized in
    Phase 5 (`tests/prompts/` skeleton), Phase 7 (per-prompt
    test content + harness implementation + fixture format —
    joint-resolved with `sub-spec-structural-formalization`
    for the per-prompt semantic-property catalogue authored
    in each sub-spec's `scenarios.md` or `contracts.md`),
    and confirmed green by Phase 8. Bookkeeping close.

**Exit criterion:** every deferred-item entry has a paired
revision under `SPECIFICATION/history/vNNN/proposed_changes/`.
`brainstorming/approach-2-nlspec-based/deferred-items.md` is
left AS-IS (brainstorming is frozen); the authoritative list of
future work now lives in `SPECIFICATION/` itself if any remains.

### Phase 9 — End-to-end integration test

Per v014 N9 and the `end-to-end-integration-test` deferred item:

- `tests/e2e/fake_claude.py` — the livespec-authored API-
  compatible mock of the Claude Agent SDK's query-interface
  surface. Parses the `minimal` template's prompt delimiter
  comments (format codified by Phase 7 in
  `SPECIFICATION/templates/minimal/contracts.md` under the
  "Template↔mock delimiter-comment format" section per v018
  Q1; the v014-N9-era joint-resolution between
  `template-prompt-authoring` and `end-to-end-integration-test`
  is superseded by v018 Q1's sub-spec codification, and
  `template-prompt-authoring` is closed) and drives wrappers
  deterministically.
- `tests/e2e/fixtures/` — `tmp_path`-template fixtures for the
  happy path + three error paths (retry-on-exit-4, doctor-
  static-fail-then-fix, prune-history-no-op).
- `tests/e2e/test_*.py` — common pytest suite; mode selected
  by `LIVESPEC_E2E_HARNESS=mock|real`. Mock-only tests carry
  explicit pytest markers / `skipif` annotations.
- `.github/workflows/e2e-real.yml` — NOT modified in Phase 9.
  Phase 1 already authored the complete workflow (triggers,
  `just e2e-test-claude-code-real` invocation, secret gating).
  Phase 9 verifies the workflow runs green now that
  `fake_claude.py`, fixtures, and the pytest suite exist.

**Exit criterion:**
`just e2e-test-claude-code-mock` passes locally and in CI as part
of `just check`. `just e2e-test-claude-code-real` passes in the
dedicated workflow (manual or merge-queue trigger).

### Phase 10 — Verify the v1 Definition of Done

Run through the "Definition of Done (v1)" section as it lives
in `SPECIFICATION/spec.md` (migrated from PROPOSAL.md during
Phase 6) item-by-item (DoD 1–15), and produce a checklist
revision in `SPECIFICATION/history/vNNN/` confirming each
item. Any gaps become `propose-change` inputs and are revised.
PROPOSAL.md is reference material only; the verification is
against SPECIFICATION/'s version of DoD. When every DoD item
is marked done, tag the commit `v1.0.0`.

**Exit criterion:** `v1.0.0` tag exists; release-tag CI workflow
runs `just check-mutation` (first real baseline captured in
`.mutmut-baseline.json`) and `just check-no-todo-registry`;
both pass.

---

## 5. Out of scope for this plan

- Any change to `brainstorming/`, `prior-art/`, or
  `history/vNNN/` — those are immutable archives from this point
  forward.
- Publishing the plugin to a Claude Code plugin marketplace
  (v2 non-goal per PROPOSAL.md).
- `opencode` / `pi-mono` agent-runtime packaging (v2 non-goal).
- Windows native support (non-goal).
- Async or concurrency (non-goal).

---

## 6. Risks and mitigations

- **Phase 3 is the tightest bottleneck.** If the minimum-viable
  `seed` path has a bug, Phase 6 produces an unreviewable spec.
  Mitigation: Phase 5's tests cover the seed code path at 100%
  line+branch AND include a property-based test over
  `seed_input.schema.json` via `hypothesis-jsonschema` before
  Phase 6 runs.
- **Dogfooding amplifies mistakes.** A bug in `revise` while
  processing deferred-items in Phase 8 corrupts the audit trail.
  Mitigation: each Phase-8 revise is a separate git commit; any
  corruption is recoverable by `git revert` + re-file the
  propose-change.
- **Vendoring drift.** Re-running `just vendor-update <lib>`
  after the baseline is in place can silently widen the
  supported-version window. Mitigation: `.vendor.jsonc` records
  the exact ref; PR review explicitly diffs `_vendor/` + the
  vendor manifest.
- **E2E-real CI cost.** Every `master` commit invokes the real
  Anthropic API. Mitigation: the mock tier is the default for
  `just check`; `e2e-real.yml` runs only on merge-queue + master
  + manual dispatch. A future deferred item
  (`local-bundled-model-e2e`) tracks removing the API-key
  dependency.
- **Under-specified template sub-specs at Phase 6 seed time.**
  The Phase 6 seed intent for each template sub-spec is the
  only input shaping that template's eventual prompt interview
  flow and starter-content policies. A shallow sub-spec seed
  produces a sub-spec that passes doctor-static but gives
  Phase 7's agent-generation step weak guidance, yielding
  templates whose prompt behavior is inconsistent or thin.
  Mitigation: the Phase 6 seed intent enumerates every
  sub-spec file's required content explicitly (see the
  intent block in Phase 6); Phase 7's first propose-change
  against each sub-spec is a critique-driven widening pass
  that exposes and fills under-specified sections before any
  template content generation happens.

---

## 7. Execution prompt

Paste the block below into a fresh Claude Code session rooted at
`/data/projects/livespec/` to execute the plan. The prompt is
self-contained; it does not require the plan document itself as
context, but it assumes every file listed in §1 is readable.

---

```
Execute the livespec bootstrap plan documented at
`/data/projects/livespec/brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`.

## Required reading

Load every file listed in that plan's §1 "Inputs (authoritative
sources)" section before doing any work:

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md` (frozen at
  the latest history/vNNN snapshot — per the plan's "Version
  basis" note, this is v018, which adopts Q1-Option-A through
  Q6: template sub-specifications, bootstrap exception,
  initial-vendoring exception, returns-pyright-plugin
  vendored + pyright stays, prompt-QA tier, companion-doc
  migration classes)
- `brainstorming/approach-2-nlspec-based/livespec-nlspec-spec.md`
- `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`
- `brainstorming/approach-2-nlspec-based/goals-and-non-goals.md`
- `brainstorming/approach-2-nlspec-based/subdomains-and-unsolved-routing.md`
- `brainstorming/approach-2-nlspec-based/prior-art.md`
- All four `2026-04-19-nlspec-*.md` lifecycle / terminology docs
- `prior-art/nlspec-spec.md`
- `brainstorming/approach-2-nlspec-based/history/README.md`
- Every `history/vNNN/PROPOSAL.md`, every
  `history/vNNN/proposed_changes/*.md`, and every
  `history/vNNN/conversation.json` that exists. Skim
  `history/vNNN/retired-documents/` READMEs to understand what was
  retired and why, but do NOT load retired docs themselves.

Treat PROPOSAL.md v018 as authoritative. Do not propose any
modification to it, to any companion doc under `brainstorming/`,
or to any file under `brainstorming/history/` during this
execution. Those are frozen.

## Execution rules

1. Work phase by phase, in order: Phase 0 → Phase 10. Do not
   skip forward. Each phase's exit criterion MUST be demonstrably
   met before starting the next. Demonstrate the exit criterion
   by running the relevant `just` target or the explicit check
   the plan names.

2. Every phase of work lands as one or more git commits. Commit
   messages follow the form `<phase>: <summary>` (e.g.,
   `phase-1: repo-root developer tooling`).

3. `brainstorming/` is immutable from Phase 0 onward EXCEPT the
   one-time header-note addition in Phase 0 Step 2. Any other
   edit under `brainstorming/` is a bug in execution; stop and
   ask.

4. From Phase 6 onward, every change to any spec tree —
   main `SPECIFICATION/` OR any template sub-spec under
   `SPECIFICATION/templates/<name>/` — MUST flow through
   `propose-change` → `revise` against the specific tree,
   selected via the `--spec-target <path>` flag (use the skill
   bundle's own sub-commands; dogfooding is mandatory per
   PROPOSAL.md §"Self-application"). Do not hand-edit
   any `.md` file under any spec tree after Phase 6. Template
   content files (`.claude-plugin/specification-templates/
   <name>/prompts/*.md`, `template.json`,
   `specification-template/`) are ALSO not hand-edited after
   Phase 6: they are agent-generated alongside the
   corresponding sub-spec revision.

5. Confirm with the user before:
   - Adding a dependency not already listed in the authority
     for the current phase: PROPOSAL.md's runtime /
     developer-tooling sections during Phases 0–5;
     `SPECIFICATION/` (spec.md / constraints.md) from Phase 6
     onward.
   - Deviating from the directory layout declared by the
     same phase-keyed authority (PROPOSAL.md pre-Phase-6,
     `SPECIFICATION/` post-Phase-6).
   - Resolving a `static-check-semantics` sub-question in a way
     that's not already codified in `deferred-items.md`.

6. Do NOT run `git push`, `git tag`, `git reset --hard`,
   `git commit --amend`, or any destructive git operation
   without explicit confirmation. The only tag operation
   (creating `v1.0.0` in Phase 10) requires explicit approval.

7. Do NOT add hooks, CI triggers, or automations beyond what
   PROPOSAL.md and the style doc already specify. The
   enforcement suite is defined; implement it, do not extend it.

8. If any phase's exit criterion fails, surface the failure with
   the exact `just` target output or check message and ask the
   user before proceeding.

## Tracking

Use TaskCreate / TaskUpdate to track phase-level and
sub-step-level progress. Surface the phase you're working on and
what's next at each meaningful turn. Keep responses focused on
the work; do not narrate internal deliberation.

Start at Phase 0. Proceed when I say "go".
```

---
