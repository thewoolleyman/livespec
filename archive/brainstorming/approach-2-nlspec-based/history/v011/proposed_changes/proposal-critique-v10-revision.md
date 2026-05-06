---
proposal: proposal-critique-v10.md
decision: modify
revised_at: 2026-04-23T12:00:00Z
author_human: thewoolleyman
author_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v10

## Provenance

- **Proposed change:** `proposal-critique-v10.md` (in this directory) — a
  recreatability-focused defect critique surfacing 11 integration gaps
  (K1–K11) left in v010 PROPOSAL.md,
  `python-skill-script-style-requirements.md`, and `deferred-items.md`
  after the J1–J14 landings.
- **Revised by:** thewoolleyman (human) in dialogue with Claude Opus 4.7
  (1M context).
- **Revised at:** 2026-04-23 (UTC).
- **Scope:** v010 PROPOSAL.md + python style doc + `deferred-items.md`
  → v011 equivalents. `livespec-nlspec-spec.md` unchanged by this pass
  (its Architecture-Level Constraints + Error Handling Discipline
  sections continue to be normative authority for livespec's own
  implementation). Focus areas: layout malformations from the v010 J3
  `resolve_template.py` addition; wrapper-shape × coverage discipline
  conflict from v010 J8; domain-term rename `reviser` → `author`
  propagated everywhere; template coupling removed from the skill
  (`livespec-nlspec-spec.md` is now template-internal only);
  doctor extensibility widened via per-category `template.json` hooks;
  Ruby-style keyword-only argument discipline mandated for all livespec
  Python; `livespec-` prefix demoted from enforced reservation to
  convention.

## Pass framing

This pass was a **recreatability-focused defect critique** producing
11 items (K1–K11). Three items departed from the originally recommended
disposition based on user pushback, and two items expanded scope
mid-interview into broader project-level discipline decisions:

- **K3** (wrapper-shape × coverage conflict) moved from original
  Recommended A (omit wrappers from coverage config) to user-chosen A
  (cover wrappers directly via tests). User preferred uniform 100%
  coverage rule; ~60–90 lines of wrapper-boilerplate tests replace
  pragma machinery.
- **K4** (HelpRequested match-destructure) expanded from per-class
  `__match_args__` patching to a **project-wide keyword-only argument
  + keyword-only match-pattern discipline** mandated in the Python
  style doc. Covers all livespec-authored code; exempts third-party
  library destructures and Python-mandated dunder signatures. Adds
  two new AST enforcement checks.
- **K5** (`livespec-nlspec-spec.md` injection mechanism) expanded from
  a per-sub-command SKILL.md body-structure addition to a
  **full decoupling of the skill from the discipline doc**, plus a
  three-category template-extension architecture for doctor
  (python-static / LLM-objective / LLM-subjective), each declared via
  new `template.json` fields. The original "skill injects the
  discipline doc" mandate is removed entirely; the skill is now
  discipline-doc-agnostic. The user flagged that skill-level coupling
  breaks template-shape agnosticism.
- **K7** (CLI author-flag asymmetry) expanded from a documentation fix
  into a **full domain-term rename** `reviser` → `author` across the
  env var, wrapper payload fields, and revision-file front-matter
  fields, plus a **uniform `--author <id>` CLI flag** across all
  three LLM-driven wrappers (`propose-change`, `critique`, `revise`).
  User flagged the semantic mismatch of `LIVESPEC_REVISER_LLM` being
  used for `propose-change` (not a revise operation).
- **K8** (style doc bin/ tree missing `resolve_template.py`) moved
  from Recommended A (one-line insertion) to user-chosen B (remove
  both layout-tree duplications from the style doc entirely;
  PROPOSAL.md is sole source of truth for directory layout). Applied
  consistently to both the package-layout tree and the tests-tree.
- **K9** (`livespec-` prefix enforcement wording contradiction)
  reframed from a status-quo-cleanup disposition (Option A original)
  to **Path 1 — convention-only**. User asked what problem the
  reservation was originally solving; answer revealed it was solving
  provenance disambiguation in the audit trail, but no code branches
  on the reservation — it's pure convention. Mechanical enforcement
  (schema pattern + wrapper rejection) is removed; the `livespec-`
  prefix remains as a SHOULD NOT convention documented in prose.

Each K item carried one of four NLSpec failure modes (ambiguity /
malformation / incompleteness / incorrectness) and was grouped by
impact: major gaps (K1–K3; recreatability-blocking), significant
gaps (K4–K7; load-bearing guesses or wrong behavior), smaller
cleanup (K8–K11; enumerate / clarify / freeze).

No item reopened any v005–v010 decision about what livespec does.

## Summary of dispositions

| Item | Failure mode | Disposition |
|---|---|---|
| K1 | malformation | A — remove `commands/doctor.py` from layout tree |
| K2 | incompleteness | A — codify six-invariant `resolve_template.py` wrapper contract in PROPOSAL.md |
| K3 | malformation | A — cover wrappers directly via `tests/bin/test_<cmd>.py`; no pragma, no omit; wrapper-shape discipline unchanged |
| K4 | ambiguity | A+ — mandate keyword-only arguments + keyword-only match patterns for all livespec-authored Python code |
| K5 | incompleteness | (refined) strip all skill-level coupling to `livespec-nlspec-spec.md`; three template-extensible check categories declared in `template.json`; two symmetric skip/run flag pairs |
| K6 | ambiguity | B — accept asymmetric narration (warn only on silent skips); rule extends to K5 flag pairs |
| K7 | ambiguity | (refined) full rename `reviser` → `author` everywhere; uniform `--author` CLI flag across all three LLM wrappers |
| K8 | malformation | B — remove both layout-tree duplications from style doc; PROPOSAL.md is sole source of truth |
| K9 | ambiguity | Path 1 — convention-only; drop mechanical enforcement of `livespec-` prefix (SHOULD NOT in prose) |
| K10 | ambiguity | A — doctor-static checks MUST map domain failures to fail-Finding; IOFailure reserved for boundary errors |
| K11 | incompleteness | A — add `schemas/dataclasses/` to PROPOSAL.md's tests-tree example |

## Governing principles reinforced (not newly established) during this pass

- **Template-agnostic skill boundary** (from v009 I0 architecture-
  vs-mechanism discipline + v010 J3 custom-template extensibility).
  Reconfirmed at K5: the skill runtime knows only `template.json`,
  `prompts/`, `specification-template/`, and the three new
  `doctor_*_checks` fields; everything else is template-internal.
- **Architecture-vs-mechanism** (v009 I0). Reconfirmed at K4 via the
  keyword-only discipline: the rule names what properties code
  MUST have (keyword-only in function signatures; keyword-only in
  match patterns for livespec classes) and lets the enforcement
  suite verify, rather than illustrating "correct" code at the
  style-doc level.
- **Domain-vs-bugs** (v009 I10). Reconfirmed at K10: doctor-static
  checks route domain-meaningful failures through the Finding
  channel (fail-Finding → exit 3); `IOFailure` is reserved for
  check-cannot-continue boundary errors. The same
  domain/bugs split carries over into the static-phase output
  contract.
- **Strongest-possible guardrails for agent-authored Python.**
  Reconfirmed at K4: keyword-only + match-pattern discipline adds
  two more mechanical guardrails so agents have minimal room to
  make positional-confusion bugs.
- **Don't couple the skill to a specific template's shape.**
  Reinforced at K5 by stripping `livespec-nlspec-spec.md` from the
  skill's runtime vocabulary entirely. The built-in `livespec`
  template's prompts reference it template-internally; custom
  templates are not required to have it.

## Disposition by item

### K1. `commands/doctor.py` orphan (malformation → accepted, option A)

PROPOSAL.md line 105 listed `commands/doctor.py` but no wrapper imports
from it; `bin/doctor_static.py` imports from `livespec.doctor.run_static`
per §"Note on `bin/doctor.py`." The file was mechanically unreachable.

Resolution:

- Remove `│       │   ├── doctor.py` from PROPOSAL.md skill-layout tree
  (line 105).
- Soften the `commands/` comment: "one module per sub-command *with a
  Python wrapper*; `doctor` has no wrapper — see §'Note on
  `bin/doctor.py`'."

### K2. `resolve_template.py` wrapper contract (incompleteness → accepted, option A)

PROPOSAL.md added `bin/resolve_template.py` in v010 J3 with only coarse
output-contract language. Six invariants codified:

- **Invocation:** `python3 .claude-plugin/scripts/bin/resolve_template.py`
  with zero positional args and an optional `--project-root <path>`
  flag (default: `Path.cwd()`; wrapper walks up from `--project-root`
  looking for `.livespec.jsonc`).
- **Stdout:** exactly one line = the resolved template directory as
  an absolute POSIX path, trailing `\n`. Paths with spaces are emitted
  literally.
- **Built-in resolution:** `"template": "livespec"` in `.livespec.jsonc`
  resolves to `<bundle-root>/specification-templates/livespec/`
  where `<bundle-root>` is the ancestor of `bin/resolve_template.py`
  (computed via `Path(__file__).resolve().parent.parent`).
- **User-path resolution:** any other string is a path relative to
  `--project-root` (resolved absolute); wrapper validates the path
  exists and contains `template.json`.
- **Lifecycle:** `resolve_template` has no pre-step and no post-step
  doctor static (exempt like `help` and `doctor`). It is a utility
  wrapper; running doctor-static before template resolution would
  recurse.
- **Exit codes:** 0 on success; 3 on any of {.livespec.jsonc not
  found above `--project-root`, malformed/schema-invalid, resolved
  path missing, resolved path lacks `template.json`}; 2 on bad
  `--project-root` flag; 127 on too-old Python via `_bootstrap.py`.
- **Extensibility shield:** output contract (one-line absolute POSIX
  path) is frozen in v1; v2 extensions (`user-hosted-custom-
  templates` deferred item) must preserve the exact shape.

Added as new §"Template resolution contract" subsection in
PROPOSAL.md under §"Templates."

### K3. Wrapper-shape × coverage-pragma conflict (malformation → accepted, option A)

v010 J8 extended coverage to `scripts/bin/**`, but the wrapper-shape
rule's "no other lines" forbade pragma comments, and the per-file
3-pragma-line cap made per-line pragmas non-viable. No configuration
satisfied all three invariants.

Resolution:

- Each `bin/*.py` wrapper (except `_bootstrap.py`) gets a test at
  `tests/bin/test_<cmd>.py` that imports it and catches
  `SystemExit` via `pytest.raises`. Wrappers execute under test →
  coverage registers them as covered.
- Remove "wrapper bodies are pragma-excluded" language from
  PROPOSAL.md §"Shebang-wrapper contract" and style doc §"Code
  coverage."
- Remove the `# pragma: no cover` application statement from style
  doc §"Shebang-wrapper contract."
- Wrapper-shape 6-line discipline preserved unchanged; coverage
  uniformity restored.
- `test_wrappers.py` meta-test continues to verify the 6-line shape
  (now in parallel to per-wrapper coverage tests).

### K4. Keyword-only discipline (ambiguity → accepted, option A+)

The v010 supervisor pattern `case IOFailure(HelpRequested(text))`
required `__match_args__` on `HelpRequested` per Python's PEP 634.
User expanded scope to project-wide discipline.

Resolution — **two new rules** added to the Python style doc:

- **Keyword-only arguments.** Every function definition in
  `scripts/livespec/**`, `scripts/bin/**`, and `dev-tooling/**` MUST
  use `*` as its first parameter separator (or immediately after
  `self`/`cls` for methods). Every `@dataclass` MUST include
  `kw_only=True`. Enforced by new `check-keyword-only-args` AST
  walker. Exempt: dunder methods with Python-mandated signatures
  (`__eq__(self, other)`, `__hash__(self)`, `__getitem__(self, key)`,
  `__init__` for Exception subclasses where `super().__init__(arg)`
  call-sites hit stdlib positional surface).
- **Structural pattern matching.** Class patterns destructuring
  livespec-authored classes MUST use keyword form (`case Foo(x=x)`);
  positional destructure is permitted only for third-party library
  types (e.g., `dry-python/returns`'s `IOFailure`, `IOSuccess`,
  `Result.Success`, `Result.Failure`). Enforced by new
  `check-match-keyword-only` AST walker.

**Consequence for `HelpRequested`:** no `__match_args__` declared
on any livespec-authored class. `HelpRequested.__init__` is
keyword-only (`def __init__(self, *, text: str)`) and supervisor
destructures via keyword form (`case IOFailure(HelpRequested(text=text))`).

New AST checks added to the canonical `just` target list and to the
`enforcement-check-scripts` + `static-check-semantics` deferred-
items entries.

### K5. `livespec-nlspec-spec.md` decoupling + three-category doctor extensibility (incompleteness → accepted, refined)

Two-part resolution:

**Part 1 — Decouple skill from `livespec-nlspec-spec.md` entirely:**

- PROPOSAL.md line 867: delete `├── livespec-nlspec-spec.md (OPTIONAL: discipline doc the skill injects)` from generic template-directory-layout diagram.
- PROPOSAL.md lines 897–899: delete the "skill concatenates it as reference context" paragraph.
- PROPOSAL.md lines 977–980: rewrite §"Built-in template: `livespec`" paragraph to drop "skill injects" language. New wording: "The built-in `livespec` template ships `livespec-nlspec-spec.md` at its template root — the adapted NLSpec guidelines document. The template's own prompts reference it internally where NLSpec discipline is needed. This is a template-internal convention; the skill is not aware of the file."
- PROPOSAL.md lines 1777–1790: **delete the entire §"NLSpec conformance" section.**
- PROPOSAL.md DoD item 8: drop the "discipline doc" clause. New: "Every sub-command that does spec work invokes template prompts with schema-validated I/O."

**Part 2 — Three template-extensible doctor check categories:**

Doctor checks belong to one of three categories, each extensible
per-template via a `template.json` declaration:

- **Python-driven static checks.** Deterministic; fail only on
  Python/dependency bug. Skill-baked under `livespec/doctor/static/`.
  Template extension: `template.json` field `doctor_static_check_modules:
  list[str]` (paths relative to template root). Each module exports
  `TEMPLATE_CHECKS: list[tuple[str, CheckRunFn]]`. Loaded via
  `importlib.util.spec_from_file_location`.
- **LLM-driven objective checks.** Non-deterministic (LLM fallibility)
  but unambiguous pass/fail. Skill-baked in `doctor/SKILL.md` prose.
  Template extension: `template.json` field
  `doctor_llm_objective_checks_prompt: string` (path to markdown
  file relative to template root; default location by convention:
  `prompts/doctor-llm-objective-checks.md`).
- **LLM-driven subjective checks.** Non-deterministic AND ambiguous
  (preference-dependent; LLM may misread the subjectivity). Skill-
  baked template-agnostic items (prose quality, spec↔impl drift) in
  `doctor/SKILL.md` prose. Template extension: `template.json` field
  `doctor_llm_subjective_checks_prompt: string`.

Two symmetric flag pairs replacing v010's single
`--skip-subjective-checks`:

- `--skip-doctor-llm-objective-checks` / `--run-doctor-llm-objective-checks`
  (mutually exclusive; both → argparse usage error exit 2).
- `--skip-doctor-llm-subjective-checks` / `--run-doctor-llm-subjective-checks`
  (mutually exclusive; both → argparse usage error exit 2).

Config keys in `.livespec.jsonc`:
- `post_step_skip_doctor_llm_objective_checks` (default `false`).
- `post_step_skip_doctor_llm_subjective_checks` (default `false`).

Precedence: CLI → config → hardcoded default.
All flags are **LLM-layer only** — never passed to Python wrappers.

Remove: `--skip-subjective-checks`, `post_step_skip_subjective_checks`,
every reference to "Objective checks" / "Subjective checks" as
pre-v011 skill-baked-only categories.

For the built-in `livespec` template:
- `specification-templates/livespec/template.json` declares
  `doctor_llm_subjective_checks_prompt:
  "prompts/doctor-llm-subjective-checks.md"`.
- `specification-templates/livespec/prompts/doctor-llm-subjective-checks.md`
  contains the NLSpec-conformance evaluation + template-compliance
  semantic judgments. Its prose Reads `../livespec-nlspec-spec.md`
  (template-root-relative) internally for discipline-doc injection.
- Other extension slots (`doctor_static_check_modules`,
  `doctor_llm_objective_checks_prompt`) left unset for the
  livespec template in v1.

Deferred-items updates (see §"Deferred-items inventory" below).

### K6. `--run-pre-check` narration symmetry (ambiguity → accepted, option B)

Accept the documented asymmetry: narration fires only when pre-step
is silently skipped (config-driven, user may have forgotten); CLI-
override-to-run cases produce no narration because the user's explicit
CLI flag is self-evident. Same rule extends to K5's new flag pairs.

No PROPOSAL.md changes needed (the rule already fires only on skip).

### K7. Domain-term rename `reviser` → `author` (ambiguity → accepted, refined)

Full rename with uniform CLI flag across all three LLM wrappers:

**Env var:** `LIVESPEC_REVISER_LLM` → `LIVESPEC_AUTHOR_LLM`.

**Wrapper payload fields:**
- propose-change payload `author` (unchanged).
- critique payload `reviser_llm` → `author`.
- revise payload `reviser_llm` → `author`.

**Revision-file front-matter fields:**
- `reviser_human` → `author_human`.
- `reviser_llm` → `author_llm`.

**Proposed-change front-matter field:** `author` (unchanged).

**CLI flag (uniform):**
- `bin/propose_change.py --author <id>` (unchanged).
- `bin/critique.py --author <id>` (new; replaces positional
  `<author>`; topic still derived as `<author>-critique` from the
  resolved author value).
- `bin/revise.py --author <id>` (new).

**Precedence (uniform across all three):**
1. CLI `--author <id>` if passed and non-empty.
2. Env var `LIVESPEC_AUTHOR_LLM` if set and non-empty.
3. Payload `author` field if present and non-empty.
4. Literal `"unknown-llm"` fallback.

**Exemptions (bypass precedence):**
- `bin/seed.py` hardcodes `livespec-seed`.
- Doctor out-of-band-edits auto-backfill hardcodes `livespec-doctor`.
- `bin/prune_history.py` has no author concept.

Reserved `livespec-` prefix convention stands as SHOULD NOT per K9;
wrappers no longer mechanically reject user-supplied `livespec-`
values.

Update scope: PROPOSAL.md Configuration / propose-change / critique /
revise / Revision file format sections; `deferred-items.md`
`wrapper-input-schemas`, `front-matter-parser`,
`skill-md-prose-authoring` entries.

History files (v010 and earlier) remain unchanged; their use of
`reviser_llm` / `LIVESPEC_REVISER_LLM` is historical and immutable.

### K8. Style doc layout-tree duplication (malformation → accepted, option B)

Both layout-tree duplications in the style doc removed entirely:

- Style doc §"Package layout" tree (lines ~178–232) deleted.
  Replaced with: "Layout: see PROPOSAL.md §'Skill layout inside the
  plugin' for the canonical directory tree." Per-sub-package
  conventions (rules, not layouts) retained.
- Style doc §"Testing" tree (lines ~683–703) deleted.
  Replaced with: "Layout: see PROPOSAL.md §'Testing approach' for
  the canonical test tree." Testing rules retained.

PROPOSAL.md is now the sole source of truth for directory layouts.

### K9. `livespec-` prefix: convention-only (ambiguity → accepted, Path 1)

Mechanical enforcement dropped. The reservation was pure convention
— no code branched on it.

Resolution:

- PROPOSAL.md §"Proposed-change file format" — rewrite the
  "Author-identifier namespace convention" paragraph to SHOULD NOT:
  "Author identifiers beginning with `livespec-` (e.g., `livespec-seed`,
  `livespec-doctor`) are used by skill-auto-generated artifacts
  (seed auto-capture, doctor out-of-band-edits backfill). Human
  authors and LLMs SHOULD NOT use this prefix for their own
  artifacts so that the audit trail can visually distinguish
  skill-auto artifacts from user/LLM-authored ones. This is a
  convention; no mechanical enforcement exists."
- PROPOSAL.md §"propose-change" — delete the second passage
  claiming "validation failure at the proposed-change format layer
  (not the schema layer)." No format-layer rejection exists.
- Front-matter schemas drop the `^livespec-[a-z-]+$` pattern on
  author / author_llm fields. `deferred-items.md`
  `front-matter-parser` entry updated to drop the pattern.

### K10. Doctor-static check domain-failure-to-fail-Finding discipline (ambiguity → accepted, option A)

Add to PROPOSAL.md §"Static-phase checks" opening paragraph:

> Doctor-static checks MUST map domain-meaningful failure modes
> (validation failure, missing file, permission denied, etc.) to
> `IOSuccess(Finding(status="fail", ...))` rather than
> `IOFailure(err)`. The `IOFailure` track is reserved for
> unexpected impure-boundary failures where the check itself
> cannot continue (e.g., `.livespec.jsonc` path was unreadable
> due to an I/O error, not a validation error). Domain findings
> are user-reportable via the Findings channel and map to exit 3
> via the "any fail finding" supervisor clause; `IOFailure` is
> short-circuit-and-abort only. This preserves the discipline
> that `bin/doctor_static.py` never emits exit 4.

Update `static-check-semantics` deferred-items entry to reference
this discipline.

### K11. Tests-tree example missing `schemas/dataclasses/` (incompleteness → accepted, option A)

Add `tests/livespec/schemas/dataclasses/` subtree to PROPOSAL.md
§"Testing approach" example tree:

```
│   ├── schemas/
│   │   └── dataclasses/
│   │       ├── test_finding.py
│   │       ├── test_doctor_findings.py
│   │       └── ...
```

Tests cover `pass_finding` / `fail_finding` constructor contracts.
Mirror rule already universal; this just makes the example visible.
Style doc's tests tree is removed entirely per K8-B; PROPOSAL.md's
tree is the sole example.

## Deferred-items inventory (carried forward + scope-widened + new)

Per the deferred-items discipline, every carried-forward item is
enumerated below. Additions, scope-widenings, and renames are
flagged.

**Carried forward unchanged from v010:**

- `template-prompt-authoring` (v001).
- `python-style-doc-into-constraints` (v005).
- `companion-docs-mapping` (v001).
- `claude-md-prose` (v006).
- `returns-pyright-plugin-disposition` (v007).
- `user-hosted-custom-templates` (v010 J3).

**Scope-widened in v011:**

- `enforcement-check-scripts` (v005). v011 additions:
  - K4: new `check-keyword-only-args` and `check-match-keyword-only`
    AST checks added to the check suite.
- `static-check-semantics` (v007; widened every pass since). v011
  additions:
  - K3: wrapper coverage via per-wrapper tests (not pragma); no
    omit from coverage config; wrapper-shape meta-test continues in
    parallel.
  - K4: `check-keyword-only-args` and `check-match-keyword-only`
    semantics — `ast.arguments.args` must be empty after self/cls
    (all params in `kwonlyargs`); `@dataclass(kw_only=True)` for
    dataclass decorators; match-pattern class patterns over
    livespec-authored classes use keyword sub-patterns (detected by
    class-resolution at AST walk time). Exemptions for dunder
    methods and third-party library destructures enumerated.
  - K5: `doctor_static_check_modules` loading via
    `importlib.util.spec_from_file_location` (template-extension
    Python modules); the `TEMPLATE_CHECKS` export contract on each
    module; how template-extension checks compose with skill-baked
    checks through `livespec/doctor/static/__init__.py` registry.
  - K10: doctor-static check domain-failure-to-fail-Finding
    discipline codified; IOFailure reserved for boundary errors.
- `front-matter-parser` (v007; widened v009). v011 additions:
  - K7: field renames `reviser_human` → `author_human`,
    `reviser_llm` → `author_llm` in
    `revision_front_matter.schema.json`; payload field in
    revise/critique wrappers renamed `reviser_llm` → `author`;
    env var rename `LIVESPEC_REVISER_LLM` → `LIVESPEC_AUTHOR_LLM`.
  - K9: drop `^livespec-[a-z-]+$` pattern validation from
    `proposed_change_front_matter.schema.json` and
    `revision_front_matter.schema.json`.
- `wrapper-input-schemas` (v008; widened v009 + v010). v011
  additions:
  - K2: `resolve_template.py` has no JSON input schema (takes no
    `--*-json` file); standalone wrapper contract codified in
    PROPOSAL.md per K2.
  - K7: rename `reviser_llm` → `author` in `revise_input.schema.json`
    (file-level field); rename matching field in
    critique wrapper payload (if explicit schema exists).
- `task-runner-and-ci-config` (v006; widened every pass since).
  v011 additions:
  - K3: no coverage omit for `bin/*.py` wrappers; each wrapper
    covered via `tests/bin/test_<cmd>.py`.
  - K4: `just check-keyword-only-args` and `just check-match-
    keyword-only` targets added to the canonical target list.
  - K7: lefthook/CI hook invocations use `--author` uniformly if
    supplying an author override (otherwise rely on env var
    `LIVESPEC_AUTHOR_LLM`).
- `skill-md-prose-authoring` (v008 H4; widened every pass since).
  v011 additions:
  - K5: no SKILL.md step injects `livespec-nlspec-spec.md` from the
    skill layer; the built-in `livespec` template's prompts
    (including the new `prompts/doctor-llm-subjective-checks.md`)
    reference the discipline doc internally. SKILL.md prose no
    longer names `livespec-nlspec-spec.md` as a file it Reads.
  - K5: per-sub-command SKILL.md bodies describe the two new
    flag pairs (skip/run for objective + subjective LLM checks);
    narration rules per K6 (warn only on silent skips).
  - K7: `--author <id>` flag described in Inputs section for
    propose-change, critique, and revise bodies; precedence chain
    documented.

**New in v011:**

None. All v011 changes are scope-widenings of existing deferred
entries.

**Removed:**

None.

## Self-consistency check

Post-revision invariants rechecked:

- **`commands/doctor.py` fully absent** from PROPOSAL.md. Doctor's
  Python entry is uniformly at `livespec/doctor/run_static.py::main()`.
- **`resolve_template.py` contract fully codified.** Six invariants
  explicit in PROPOSAL.md; `user-hosted-custom-templates` deferred
  entry references the stdout-contract stability shield.
- **Wrapper coverage via tests.** Every bin/*.py wrapper (except
  `_bootstrap.py`) has a `tests/bin/test_<cmd>.py` that imports it
  and catches `SystemExit`. No `# pragma: no cover` applied anywhere
  to wrapper files. Wrapper-shape meta-test + per-wrapper coverage
  tests both pass.
- **Keyword-only discipline applied uniformly.** Every
  livespec-authored def uses `*` separator; every `@dataclass`
  uses `kw_only=True`; every match pattern over livespec-authored
  classes uses keyword form. `__match_args__` not declared on any
  livespec-authored class.
- **`livespec-nlspec-spec.md` not referenced by skill runtime.** No
  PROPOSAL.md section names it outside the Built-in template's own
  description and the NLSpec-authority citations (which are
  brainstorming-doc-level, not runtime coupling).
- **Three doctor check categories codified.** Static / LLM-objective
  / LLM-subjective each have skill-baked defaults + template-
  extension hook declared in `template.json`.
- **Two symmetric skip/run flag pairs.** Old
  `--skip-subjective-checks` fully replaced; new pairs follow J10's
  bidirectional pattern.
- **Domain-term rename `reviser` → `author`.** Env var, wrapper
  payloads, revision front-matter, CLI flags all say "author."
  Revision file has `author_human` + `author_llm` two-field split.
- **`livespec-` prefix = convention.** No schema pattern validates
  it; no wrapper rejects it; SHOULD NOT in PROPOSAL.md prose.
- **Style doc layout trees removed.** PROPOSAL.md sole source of
  truth for directory layout.
- **Doctor-static domain-failure discipline explicit.** Validator
  failures produce fail-Finding (exit 3); IOFailure reserved for
  boundary errors.
- **Test-tree example covers `schemas/dataclasses/`.** Mirror rule
  universal and visible in PROPOSAL.md example.
- **Recreatability.** A competent implementer can generate the
  v011 livespec plugin + built-in template + sub-commands +
  enforcement suite + dev-tooling from v011 PROPOSAL.md +
  `livespec-nlspec-spec.md` + updated
  `python-skill-script-style-requirements.md` + updated
  `deferred-items.md` alone. All residual stale references cleaned;
  cross-document disagreements resolved; template-agnostic skill
  boundary preserved.

## Outstanding follow-ups

Tracked in the updated `deferred-items.md` (see inventory above).
The v011 pass touched 6 existing entries (adding scope-widenings)
and added 0 new entries. No entries were removed.

## What was rejected

Nothing was rejected outright. Three items moved from originally
recommended to alternate option based on user input:

- **K3** (wrapper-shape × coverage conflict) — moved from original
  A (omit wrappers from coverage config) to chosen A (cover
  wrappers directly via tests) after user asked why wrapper bodies
  need to be excluded from coverage at all. The "cover them
  directly" answer dissolves the conflict more cleanly than the
  omit-config approach.
- **K8** (style doc layout drift) — moved from A (one-line fix) to
  B (remove both layout-tree duplications entirely). User's choice
  permanently prevents this class of drift.
- **K9** (`livespec-` prefix enforcement) — moved from the originally-
  recommended two-layer-enforcement path to Path 1 (convention-only)
  after user asked what problem the prefix was solving. Answer:
  provenance disambiguation in the audit trail — a convention, not
  a code invariant. Mechanical enforcement removed.

Two items expanded scope mid-interview from localized documentation
fixes into broader project-level discipline:

- **K4** (HelpRequested match-destructure) expanded into the
  keyword-only argument + keyword-only match-pattern project-wide
  discipline, with two new AST enforcement checks.
- **K5** (discipline-doc injection) expanded into full decoupling
  of the skill from `livespec-nlspec-spec.md`, plus the three-
  category doctor extensibility architecture with new `template.json`
  fields.

One item (K7) expanded from CLI-asymmetry documentation into a
full domain-term rename `reviser` → `author` across env var,
payload fields, and revision-file fields, plus uniform `--author`
CLI flag.

No item "pulled threads" into reopening prior-version decisions
about what livespec does. The v009 I0 architecture-vs-mechanism
discipline and I10 domain-vs-bugs discipline held throughout the
pass. v011 preserves v010's structural architecture while
tightening cross-document consistency, removing template-shape
coupling, and strengthening agent-guardrail discipline.
