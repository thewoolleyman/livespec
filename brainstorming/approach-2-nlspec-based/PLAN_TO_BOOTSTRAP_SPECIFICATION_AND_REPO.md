# Plan: Bootstrap the `livespec` specification and repo

**Status:** Pre-execution. This document captures everything required
to exit the brainstorming phase (current version **v017**) and stand
up a working `livespec` repo whose own `SPECIFICATION/` is seeded
from the brainstorming artifacts and whose skill bundle implements
the PROPOSAL.

Execution is performed by the prompt at the end of this file. The
prompt is self-contained; it can be pasted into a fresh Claude Code
session in the `livespec` repo.

---

## 1. Inputs (authoritative sources)

The plan operates on these files. They are the single source of
truth for every decision encoded below; the plan itself does not
restate their content.

Working proposal + embedded grounding:

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md` (v017)
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
- `brainstorming/approach-2-nlspec-based/history/v001/` …
  `history/v017/` (every `PROPOSAL.md`, `proposed_changes/`,
  `conversation.json`, `retired-documents/`)

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
- PROPOSAL.md v017 is treated as frozen. No further brainstorming
  revisions are produced; all subsequent refinement happens inside
  the seeded `SPECIFICATION/` via `propose-change` / `revise`.

---

## 3. Cutover principle

Brainstorming artifacts → immutable. The first real
`SPECIFICATION/` is produced by `livespec seed` run against this
repo; from that moment on, every change flows through the governed
loop (propose-change → critique → revise). The brainstorming folder
becomes archival.

The skill implementation is bootstrapped by hand only to the
minimum shape required to run `seed` against this repo; the
remaining scope lands through `propose-change` / `revise` cycles
authored by the skill itself (dogfooding, per PROPOSAL.md
§"Self-application").

---

## 4. Phases

Each phase has a clear exit criterion. Phases are sequential;
sub-steps within a phase MAY run in parallel where noted.

### Phase 0 — Freeze the brainstorming folder

1. Confirm `brainstorming/approach-2-nlspec-based/PROPOSAL.md` is
   byte-identical to
   `history/v017/PROPOSAL.md` (the authoritative v017 snapshot).
2. Add a top-of-file note to
   `brainstorming/approach-2-nlspec-based/PROPOSAL.md`:
   > **Status:** Frozen at v017. Further evolution happens in
   > `SPECIFICATION/` via `propose-change` / `revise`. This file
   > and the rest of the `brainstorming/` tree are historical
   > reference only.
3. `tmp/` is deleted (empty; was working directory for earlier
   passes).
4. Nothing else in `brainstorming/` is modified.

**Exit criterion:** a single commit `freeze: v017 brainstorming`
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
    `reportImplicitStringConcatenation`).
  - `[tool.pytest.ini_options]` wiring `pytest-cov` +
    `pytest-icdiff`.
  - `[tool.coverage.run]` / `[tool.coverage.report]` with
    100% line+branch, `source` covering `livespec` package and
    `.claude-plugin/scripts/bin`, `fail_under = 100`.
  - `[tool.importlinter]` with the two authoritative contracts
    (`parse-and-validate-are-pure`, `layered-architecture`) per
    v013 M7 as narrowed by v017 Q3.
  - `[tool.mutmut]` with `threshold = 80`.
  - NO build-system section (livespec is not a published PyPI
    package; it ships via Claude Code plugin bundling).
- `justfile` with the canonical target list from the style doc
  §"Enforcement suite — Canonical target list". All recipes
  delegate to their underlying tool or to
  `python3 dev-tooling/checks/<name>.py`. Includes
  `just bootstrap`, `just check`, every `just check-*`,
  `just e2e-test-claude-code-mock`,
  `just e2e-test-claude-code-real`, `just check-mutation`,
  `just check-no-todo-registry`, `just fmt`, `just lint-fix`,
  `just vendor-update <lib>`.
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
  (`returns`, `fastjsonschema`, `structlog`, `jsoncomment`,
  `typing_extensions`). Each entry records `upstream_url`,
  `upstream_ref`, `vendored_at`; `typing_extensions` also
  records `shim: true`.
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
  `htmlcov/`, `.mypy_cache/` — the last is defensive, not used).

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
  upstream ref recorded in `.vendor.jsonc`:
  - `returns/` (dry-python/returns, BSD-2)
  - `fastjsonschema/` (MIT)
  - `structlog/` (BSD-2 / MIT dual)
  - `jsoncomment/` (MIT)
  - `typing_extensions/` — the ~15-line shim per v013 M1
    exporting exactly `override` and `assert_never`, with a
    verbatim PSF-2.0 `LICENSE`.
- `.claude-plugin/scripts/livespec/` — Python package with the
  subdirectories enumerated in the PROPOSAL tree
  (§"Skill layout"): `commands/`, `doctor/` (with
  `run_static.py` + `static/__init__.py` registry +
  per-check modules), `io/`, `parse/`, `validate/`,
  `schemas/` (plus `schemas/dataclasses/`), `context.py`,
  `types.py`, `errors.py`, `__init__.py`.
- `.claude-plugin/specification-templates/livespec/` and
  `.claude-plugin/specification-templates/minimal/` — both
  built-in templates. Each has `template.json`,
  `prompts/{seed,propose-change,revise,critique}.md`, and
  `specification-template/…`. The `livespec` template also
  ships `livespec-nlspec-spec.md` at its root (copied
  verbatim from
  `brainstorming/approach-2-nlspec-based/livespec-nlspec-spec.md`)
  and carries the optional
  `prompts/doctor-llm-subjective-checks.md`. The `minimal`
  template's prompts carry the hardcoded delimiter comments
  per v014 N9.

All code in this phase is stub-level EXCEPT the wrapper shapes,
`_bootstrap.py`, and `livespec/__init__.py` (structlog
configuration + `run_id` bind). Stubs return early with
`IOFailure(PreconditionError(...))` citing "not yet
implemented" where appropriate.

Every directory under `.claude-plugin/scripts/` (excluding the
entire `_vendor/` subtree) MUST carry a `CLAUDE.md` describing
its local constraints.

**Exit criterion:** `just check-wrapper-shape`,
`just check-claude-md-coverage`, `just check-main-guard`, and
`ruff check` all pass on the skeleton. `pyright` may still
report errors against the stub bodies (acceptable at this phase).

### Phase 3 — Minimum viable `livespec seed`

Flesh out exactly the code path required to run `livespec seed`
successfully against this repo. This is the bootstrap moment;
everything else is downstream of it.

Required implementation surface (everything else stays stubbed):

- `livespec/errors.py` — full `LivespecError` hierarchy +
  `HelpRequested` per the style doc §"Exit code contract".
- `livespec/types.py` — every canonical `NewType` alias listed in
  the style doc §"Domain primitives via `NewType`".
- `livespec/context.py` — `DoctorContext`, `SeedContext`, and
  the other context dataclasses with the exact fields named in
  the style doc §"Context dataclasses", including v014 N3's
  `config_load_status` / `template_load_status`.
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
  auto-capture of `seed.md` proposed-change + `seed-revision.md`.
- `livespec/doctor/run_static.py` — orchestrator per PROPOSAL.md
  §"Static-phase structure" + v014 N3 bootstrap lenience.
- `livespec/doctor/static/__init__.py` — static registry.
- `livespec/doctor/static/` — the minimum subset of checks the
  seed post-step exercises: `livespec_jsonc_valid`,
  `template_exists`, `template_files_present`,
  `proposed_changes_and_history_dirs`,
  `version_directories_complete`, `version_contiguity`,
  `revision_to_proposed_change_pairing`,
  `proposed_change_topic_format`. (Remaining checks —
  `out_of_band_edits`, `bcp14_keyword_wellformedness`,
  `gherkin_blank_line_format`, `anchor_reference_resolution` —
  stubbed to return a `skipped` finding with message
  "not-yet-implemented"; they're fleshed out in Phase 7.)
- `seed/SKILL.md` — real prose per PROPOSAL.md §"Per-sub-command
  SKILL.md body structure" covering the pre-seed template
  dialogue, the two-step `resolve_template.py` →
  Read(`prompts/seed.md`) dispatch, payload assembly, wrapper
  invocation, post-wrapper narration, exit-code handling with
  retry-on-4.
- `doctor/SKILL.md`, `help/SKILL.md` — real prose (enough to run
  the LLM-driven phase orchestration).
- Both built-in templates' `prompts/seed.md` — full authoring so
  the seed LLM round-trip produces a schema-valid
  `seed_input.schema.json` payload. Other prompts (`propose-change`,
  `revise`, `critique`) may still be stubs at this phase; they're
  authored in Phase 7.

**Exit criterion:** `just check` passes (phase-0 stubs elsewhere
still return early with `not-yet-implemented` findings but do
NOT trip type/purity/import/coverage gates, because 100%
coverage is enforced against all real code paths that exist).
Running `/livespec:seed` against a throwaway `tmp_path` fixture
produces a valid `.livespec.jsonc`, spec tree, and
`history/v001/`.

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
- `tests/e2e/` — skeleton directory, `CLAUDE.md`, placeholder
  `fake_claude.py`. Real E2E content is fleshed out in Phase 8
  (tied to the `end-to-end-integration-test` deferred item).
- `tests/fixtures/` — empty at this phase; grows through Phases
  6–9.
- `tests/heading-coverage.json` — initially empty array `[]`
  (populated alongside the seeded spec in Phase 6 and after each
  deferred-item-driven revise).
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
producing the real `SPECIFICATION/` tree.

Seed intent fed to the prompt:

> Seed this project's `SPECIFICATION/` from the material in
> `brainstorming/approach-2-nlspec-based/`: the frozen v017
> `PROPOSAL.md`, the `livespec-nlspec-spec.md` grounding
> document, `python-skill-script-style-requirements.md`, the
> goals-and-non-goals doc, prior-art survey, lifecycle
> diagrams, and the subdomains-and-unsolved-routing appendix.
> Use the `livespec` built-in template (multi-file).
> The `livespec-nlspec-spec.md` used at seed-time comes from
> the template's own copy, NOT from the brainstorming folder.
> `spec.md` carries the core PROPOSAL material (runtime and
> packaging, specification model, sub-command lifecycle,
> versioning, pruning, sub-commands, proposed-change /
> revision file formats, testing approach, developer-tooling
> layout, Definition of Done, non-goals, self-application).
> `contracts.md` carries the skill↔template JSON contracts
> (input/output schemas; wrapper CLI shapes) and the
> lifecycle exit-code table. `constraints.md` carries
> `python-skill-script-style-requirements.md` restructured to
> the target spec's conventions (BCP 14 where the style doc
> was normative). `scenarios.md` carries every Gherkin
> scenario the style doc and PROPOSAL imply (happy path +
> the three error paths v014 N9 enumerates + the recovery
> paths in §"seed", §"doctor", and §"Pruning history").

After seed, the working tree contains:

- `.livespec.jsonc` at repo root.
- `SPECIFICATION/{README.md, spec.md, contracts.md,
  constraints.md, scenarios.md}`.
- `SPECIFICATION/proposed_changes/` containing only the
  skill-owned `README.md`.
- `SPECIFICATION/history/v001/` containing frozen copies of every
  spec file + `proposed_changes/seed.md` +
  `proposed_changes/seed-revision.md`.

Running `/livespec:doctor` against this newly-seeded state
passes. (LLM-driven subjective checks may surface suggestions;
they are recorded in
`SPECIFICATION/proposed_changes/` as `critique`-authored
proposals for the next revise, they do NOT block the exit
criterion.)

Every `##` heading in the seeded spec files gets a corresponding
entry in `tests/heading-coverage.json` (entries with `test: "TODO"`
+ non-empty `reason` are acceptable at this point; Phase 7–8 work
replaces TODOs with real test IDs).

**Exit criterion:** `just check` passes; `/livespec:doctor` runs
cleanly (static phase `0`; LLM-driven phases report only
advisory findings, no hard failures).

### Phase 7 — Remaining sub-commands + full doctor coverage

With `SPECIFICATION/` in place, implement every sub-command left
stubbed from Phase 3 and flesh out the remaining doctor checks.
Every implementation lands via a `propose-change` → `revise`
cycle against the seeded spec, so PROPOSAL.md revisions and code
implementation land atomically per the dogfooding rule.

Work items (each is one or more propose-change files filed
against the seeded `SPECIFICATION/`):

- `livespec/commands/propose_change.py` — full implementation
  including topic canonicalization (v015 O3), reserve-suffix
  canonicalization (v016 P3; v017 Q1), unified author precedence,
  schema validation, collision disambiguation (v014 N6), single-
  canonicalization invariant routing (v016 P4).
- `livespec/commands/critique.py` — full implementation with
  internal delegation to `propose_change` via `-critique`
  reserve-suffix.
- `livespec/commands/revise.py` — full implementation including
  per-proposal LLM decision flow (skill-prose-side), delegation
  toggle, version cut, history materialization, rejection flow
  preserving audit trail.
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
  including author identifier `livespec-doctor`.
- `livespec/doctor/` — LLM-driven phase orchestration in
  `doctor/SKILL.md` including both objective and subjective
  checks + template-extension hooks.
- `parse/front_matter.py` — restricted-YAML parser (tracked by
  the `front-matter-parser` deferred item).
- All four non-seed prompts in the `livespec` template:
  `prompts/{propose-change,revise,critique,doctor-llm-subjective-checks}.md`
  (plus the optional `doctor-llm-objective-checks.md` if
  livespec-template wants one).
- All four non-seed prompts in the `minimal` template with
  delimiter comments per v014 N9.
- All seven real SKILL.md prose bodies per the deferred item
  `skill-md-prose-authoring`.

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

Canonical deferred items (16 entries; template entry excluded):

1. `template-prompt-authoring` — content already landed in
   Phase 7 prompts; revise file records the closure.
2. `python-style-doc-into-constraints` — verifies the style-doc
   migration into `constraints.md` happened cleanly in Phase 6.
3. `companion-docs-mapping` — verifies every companion doc has
   a mapped home in `SPECIFICATION/`.
4. `enforcement-check-scripts` — verifies every Phase-4 check
   script matches the canonical list and that `pyproject.toml`'s
   `[tool.importlinter]` carries the narrowed-to-two contracts
   per v017 Q3.
5. `claude-md-prose` — verifies every `CLAUDE.md` exists and
   carries real content (not lorem-ipsum stubs).
6. `task-runner-and-ci-config` — verifies `justfile`,
   `lefthook.yml`, `.github/workflows/*.yml` match PROPOSAL.md.
7. `static-check-semantics` — materializes the
   semantics-codification paragraph for every check touched by
   v006–v017 widenings (bootstrap lenience, GFM anchor rules,
   reserve-suffix algorithm, wrapper-shape blank-line tolerance,
   etc.) into `constraints.md` or `spec.md` as appropriate.
8. `returns-pyright-plugin-disposition` — decide and commit.
9. `basedpyright-vs-pyright` — decide and commit.
10. `front-matter-parser` — landed in Phase 7.
11. `skill-md-prose-authoring` — landed in Phase 7.
12. `wrapper-input-schemas` — every input schema authored
    (`seed_input`, `proposal_findings`, `revise_input`,
    `proposed_change_front_matter`, `revision_front_matter`,
    plus `doctor_findings`, `livespec_config`, `template_config`,
    `finding` as already done).
13. `user-hosted-custom-templates` — documented as v2 scope;
    revise closes the entry with a pointer to the v2 tracking.
14. `end-to-end-integration-test` — see Phase 9.
15. `local-bundled-model-e2e` — documented as v2 scope; revise
    closes.

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
  comments (format agreed with `template-prompt-authoring`) and
  drives wrappers deterministically.
- `tests/e2e/fixtures/` — `tmp_path`-template fixtures for the
  happy path + three error paths (retry-on-exit-4, doctor-
  static-fail-then-fix, prune-history-no-op).
- `tests/e2e/test_*.py` — common pytest suite; mode selected
  by `LIVESPEC_E2E_HARNESS=mock|real`. Mock-only tests carry
  explicit pytest markers / `skipif` annotations.
- `.github/workflows/e2e-real.yml` — per Phase-1 skeleton,
  triggered on `merge_group`, `push` to `master`, and
  `workflow_dispatch`. Requires `ANTHROPIC_API_KEY` secret.

**Exit criterion:**
`just e2e-test-claude-code-mock` passes locally and in CI as part
of `just check`. `just e2e-test-claude-code-real` passes in the
dedicated workflow (manual or merge-queue trigger).

### Phase 10 — Verify the v1 Definition of Done

Run through PROPOSAL.md §"Definition of Done (v1)" item-by-item
(DoD 1–15) and produce a checklist revision in
`SPECIFICATION/history/vNNN/` confirming each item. Any gaps
become `propose-change` inputs and are revised. When every DoD
item is marked done, tag the commit `v1.0.0`.

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

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md` (frozen at v017)
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

Treat PROPOSAL.md v017 as authoritative. Do not propose any
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

4. From Phase 6 onward, every change to `SPECIFICATION/` MUST
   flow through `propose-change` → `revise` (use the skill
   bundle's own sub-commands; dogfooding is mandatory per
   PROPOSAL.md §"Self-application"). Do not hand-edit
   `SPECIFICATION/*.md` after Phase 6.

5. Confirm with the user before:
   - Adding a dependency not already listed in PROPOSAL.md's
     runtime or developer-tooling sections.
   - Deviating from the PROPOSAL.md-declared directory layout.
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
