---
proposal: proposal-critique-v17.md
decision: accept
revised_at: 2026-04-24T22:45:00Z
author_human: thewoolleyman
author_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v17

## Provenance

- **Proposed change:** `proposal-critique-v17.md` — a targeted
  critique over v017 surfacing six gaps uncovered while
  reviewing the bootstrap plan
  (`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`) against
  PROPOSAL.md v017. Q1 (the major gap — built-in templates
  lack sufficient specifications for agentic regeneration) was
  captured in a prior session; Q2-Q6 were appended during the
  continuation session after user-driven triage of a
  candidate-items list.
  - Q1: Built-in templates lack sufficient specifications for
    agentic regeneration, and the main spec has no structural
    hook for template sub-specifications (incompleteness — major
    gap).
  - Q2: Self-application bootstrap exception is implicit, not
    articulated (incompleteness — ambiguity at boundary).
  - Q3: Initial-vendoring mechanism for upstream-sourced
    `_vendor/` libraries is circular (incompleteness — circular
    bootstrap dependency).
  - Q4: Typechecker + returns-pyright-plugin disposition
    deferred without closure criteria (incompleteness — under-
    specified closure criteria).
  - Q5: Seed-prompt LLM round-trip correctness unverifiable
    before the E2E integration test runs (incompleteness —
    verification gap).
  - Q6: Companion-doc migration policy under-specified for
    Phase 8 auditability (incompleteness).
- **Revised by:** thewoolleyman (human) in dialogue with Claude
  Opus 4.7 (1M context).
- **Revised at:** 2026-04-24 (UTC).
- **Scope:** v017 `PROPOSAL.md` + `deferred-items.md` +
  `python-skill-script-style-requirements.md` → v018
  equivalents. `PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
  (not part of the frozen brainstorming set but referenced by
  the critique) receives plan-side ripple edits for Q2-Q6
  decisions as part of this revision cycle.
  `livespec-nlspec-spec.md`, `goals-and-non-goals.md`,
  `prior-art.md`, `subdomains-and-unsolved-routing.md`, and the
  four 2026-04-19 lifecycle/terminology companion docs remain
  unchanged.

## Pass framing

This pass was a **recreatability-and-integration-gap critique**
grounded in the NLSpec test: could a competent implementer
produce a working livespec without being forced to invent
semantics the docs leave unspecified? The six findings cluster
around one theme: gaps between PROPOSAL.md's contracts and the
bootstrap plan's mechanical execution needs.

All six findings accepted at Option A, the recommended
disposition. The dispositions preserve earlier structural
decisions rather than reopening them:

- **Q1** extends the `SPECIFICATION/` structure with a new
  nested-sub-spec mechanism (`SPECIFICATION/templates/<name>/`)
  that confines scope expansion to livespec-shipped sub-
  artifacts without re-opening the v1 "Multi-specification per
  project" non-goal (that non-goal is about unrelated
  independent specs co-existing in one repo; this is
  hierarchical sub-specs of a single primary spec — a narrower,
  strictly smaller model). Closes `template-prompt-authoring`;
  opens `sub-spec-structural-formalization`.
- **Q2** codifies an implicit bootstrap exception that the
  bootstrap plan already assumes. The exception is explicitly
  bounded (ONCE per repo, at first seed only).
- **Q3** codifies an implicit one-time-manual initial-vendoring
  procedure that Phase 2 of the bootstrap plan has to invent
  otherwise. The procedure is explicitly bounded (ONCE per
  repo, at Phase 2 only; post-bootstrap all mutations flow
  through `just vendor-update`).
- **Q4** closes two deferred items (`returns-pyright-plugin-
  disposition`, `basedpyright-vs-pyright`) with concrete
  choices + rationale at spec level. Matches the "Specify
  architecture, not mechanism" discipline: typechecker choice
  IS architecture (affects public-API type guarantees
  pervasively), not mechanism.
- **Q5** adds a prompt-QA tier distinct from the E2E harness.
  The E2E tier stays harness-level (wrapper integration); the
  prompt-QA tier is unit-level (prompt behavior). Opens
  `prompt-qa-harness` deferred-items entry joint with
  `template-prompt-authoring` and `end-to-end-integration-test`.
- **Q6** replaces "or similar" hedging with a categorical
  migration-class policy (MIGRATED-to-SPEC-file / SUPERSEDED-
  by-section / ARCHIVE-ONLY) plus a per-doc assignment table in
  PROPOSAL.md. `companion-docs-mapping` deferred entry rewrites
  to a pointer.

## Governing principles reinforced

- **Architecture-level constraints legitimately extend to
  mechanism-adjacent decisions that affect agent-generation
  fidelity.** Q1 adds a directory-structure mechanism (sub-
  specs) and Q4 adds tool-choice mechanisms (typechecker +
  pyright plugin) because both are load-bearing for
  recreatability and agent-generation quality, not because
  livespec is broadening its mechanism-specification
  tolerance generally.
- **Narrow carve-outs for one-time operations are
  acceptable.** Q2 (bootstrap exception) and Q3 (initial-
  vendoring exception) both codify ONCE-per-repo procedures.
  Neither is a recurring loophole.
- **Verification tiers match concern levels.** Q5's prompt-QA
  tier is unit-level (per-prompt behavior); the E2E tier is
  harness-level (per-workflow integration). Keeping the two
  distinct preserves the "static enumeration over dynamic
  discovery" principle — every prompt has a deterministic test
  case enumerated in the test tree.
- **Formal categorization beats informal hedging.** Q6
  replaces "or similar" with MIGRATED / SUPERSEDED /
  ARCHIVE-ONLY classes because the former fails recreatability.
- **Governed loop invariant holds for every livespec-shipped
  deliverable AND every livespec-seeded spec tree.** Q1's
  sub-specs, Q2's post-bootstrap universality, and Q5's
  prompt-QA tier all converge on this invariant.

## Summary of dispositions

| Item | Failure mode | Disposition |
|---|---|---|
| Q1 | incompleteness (major gap) | Accept A — extend `SPECIFICATION/` to admit nested sub-specifications under `SPECIFICATION/templates/<name>/` per built-in template. Doctor parameterizes per-tree; propose-change/revise gain `--spec-target <path>`; `seed_input.schema.json` widens with `sub_specs: list[SubSpecPayload]`. Closes `template-prompt-authoring`; opens `sub-spec-structural-formalization`. |
| Q2 | incompleteness (ambiguity at boundary) | Accept A — add explicit bootstrap-exception clause to PROPOSAL.md §"Self-application" naming first seed as the boundary (applies ONCE per livespec repo at initial bootstrap). |
| Q3 | incompleteness (circular bootstrap dependency) | Accept A — add 7-step one-time manual initial-vendoring procedure to PROPOSAL.md §"Vendoring discipline" (mirror in style doc). Applies ONCE per livespec repo at Phase 2 of bootstrap plan; post-bootstrap all upstream-sourced-lib mutations flow through `just vendor-update`. Shims continue following their separate "widen manually via code review" rule. |
| Q4 | incompleteness (under-specified closure criteria) | Accept A — decide both at v018 spec level. **returns-pyright-plugin**: vendor alongside the library at `.claude-plugin/scripts/_vendor/returns_pyright_plugin/`; configure via `[tool.pyright]` `pluginPaths`. **typechecker**: stay on pyright. Close both deferred items in v018. PROPOSAL.md + style doc + `pyproject.toml` carry the decisions with rationale. |
| Q5 | incompleteness (verification gap) | Accept A — add dedicated prompt-QA tier at `tests/prompts/` mirroring each built-in template's `prompts/` directory. Per-prompt tests assert on structured output at `{seed,proposal,revise}_input.schema.json` boundary PLUS semantic properties. Runs in `just check` per-commit. Opens new `prompt-qa-harness` deferred-items entry joint-resolved with `template-prompt-authoring` and `end-to-end-integration-test`. |
| Q6 | incompleteness | Accept A — formalize migration-class policy (MIGRATED-to-SPEC-file / SUPERSEDED-by-section / ARCHIVE-ONLY) plus per-doc assignment table in PROPOSAL.md §"Self-application" (or a dedicated subsection). `companion-docs-mapping` deferred entry body rewrites to a pointer. |

## Disposition by item

### Q1. Built-in templates lack sufficient specifications + SPECIFICATION/ has no sub-spec hook (incompleteness / major gap → accepted, option A)

Accepted as proposed.

PROPOSAL.md §"SPECIFICATION directory structure (livespec
template)" is extended to admit nested sub-specifications:

- `SPECIFICATION/templates/<template-name>/` holds a complete
  sub-specification for each built-in template. Each sub-spec
  follows the same file conventions as the main spec — its own
  `spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`,
  `proposed_changes/`, `history/` — but scoped to the
  template's internal contracts, starter-content policies, and
  prompt interview flows.
- Template content (`template.json`, `prompts/*.md`, starter
  content under `specification-template/`) is generated by
  agents from its sub-spec. Changes flow through the same
  propose-change → revise loop, targeting the sub-spec's
  `proposed_changes/` and `history/` rather than the main
  spec's.

Implications that land in the same v018 revision:

- SPECIFICATION/ MAY contain a `templates/` subdirectory with
  one sub-directory per built-in template; each is
  structurally identical to a livespec-managed spec tree.
- Doctor-static checks parameterize over spec trees: the main
  `SPECIFICATION/` + each sub-spec under
  `SPECIFICATION/templates/<name>/`. Version-contiguity,
  history pairing, heading-coverage, BCP14 keyword, and
  Gherkin blank-line checks apply per-sub-spec (the `livespec`
  sub-spec uses Gherkin; the `minimal` sub-spec does not).
- `propose-change` and `revise` accept a
  `--spec-target <path>` flag (default: main spec root)
  selecting which sub-spec's `proposed_changes/` and `history/`
  are operated on. Default resolves from `.livespec.jsonc` at
  `--project-root`.
- `tests/heading-coverage.json` entries carry a `spec_root`
  field discriminating main-spec vs. sub-spec headings. The
  meta-test scopes its walk per entry.
- `seed` produces the full tree (main + sub-specs) atomically:
  one seed invocation populates main `spec.md`/etc. AND each
  template sub-spec. The `seed_input.schema.json` widens to
  carry a `sub_specs: list[SubSpecPayload]` field.
- v1 template scope: ONLY the `livespec` and `minimal`
  built-ins ship sub-specs. Custom templates MAY carry their
  own sub-spec but are NOT required to; livespec imposes no
  sub-spec requirement on extension authors (consistent with
  the user-provided extensions minimal-requirements principle).
- `template-prompt-authoring` deferred-items entry is CLOSED by
  this change: prompt content is generated from the sub-spec's
  `spec.md`/`contracts.md` content, not implementer-chosen. The
  closure revision points to the new sub-spec mechanism.
- A new deferred-items entry — `sub-spec-structural-
  formalization` — captures the expansion (doctor
  parameterization, propose-change/revise CLI widening, seed
  multi-tree output, heading-coverage scoping).

Does NOT re-open the v1 "Multi-specification per project"
non-goal: that non-goal is about unrelated independent specs
co-existing in one repo; this is hierarchical sub-specs of a
single primary spec — a narrower, strictly smaller model.

### Q2. Self-application bootstrap exception (incompleteness / ambiguity at boundary → accepted, option A)

Accepted as proposed.

PROPOSAL.md §"Self-application" gains an explicit bootstrap-
exception clause placed immediately after the numbered
bootstrap ordering:

> **Bootstrap exception.** The bootstrap ordering above (steps
> 1-4, ending with the first `livespec seed` invocation) lands
> imperatively. The governed propose-change → revise loop
> becomes operable starting at step 5 — after seed has produced
> the working `SPECIFICATION/` tree (main spec + every built-in
> template's sub-spec under `SPECIFICATION/templates/<name>/`
> per the v018 Q1 addition). From the second change onward
> (every change to livespec's skill bundle, developer tooling,
> built-in template content, or any seeded spec tree), the loop
> is MANDATORY; hand-editing any file under any spec tree or
> under `.claude-plugin/specification-templates/<name>/` after
> the first seed is a bug in execution, not a permitted
> fast-path. The exception applies ONCE per livespec repo, at
> initial bootstrap; it does NOT apply to v2+ releases of
> livespec (those flow through the governed loop against the
> then-existing SPECIFICATION).

### Q3. Initial-vendoring mechanism for upstream-sourced _vendor/ libraries (incompleteness / circular bootstrap dependency → accepted, option A)

Accepted as proposed.

PROPOSAL.md §"Vendoring discipline" (and
`python-skill-script-style-requirements.md` §"Vendoring
discipline") gain an explicit initial-vendoring clause:

> **Initial-vendoring exception (one-time).** The first
> population of every upstream-sourced vendored lib
> (`returns`, `fastjsonschema`, `structlog`, `jsoncomment`,
> and the v018 Q4 addition `returns_pyright_plugin`) is a
> one-time MANUAL procedure, distinct from the blessed
> `just vendor-update` path:
>
> 1. `git clone` the upstream repo at a working ref into a
>    throwaway directory.
> 2. `git checkout <ref>` matching the `upstream_ref` recorded
>    in `.vendor.jsonc`.
> 3. Copy the library's source tree under
>    `.claude-plugin/scripts/_vendor/<lib>/`.
> 4. Copy the upstream `LICENSE` file verbatim to
>    `.claude-plugin/scripts/_vendor/<lib>/LICENSE`.
> 5. Record the lib's provenance in `.vendor.jsonc`:
>    `upstream_url`, `upstream_ref`, `vendored_at` (ISO-8601
>    UTC).
> 6. Delete the throwaway clone.
> 7. Smoke-test: the wrapper bootstrap imports the vendored
>    lib successfully.
>
> Once `jsoncomment` is initially vendored, `just vendor-update
> <lib>` becomes the only permitted path for subsequent
> re-vendoring of upstream-sourced libs. The initial procedure
> applies ONCE per livespec repo, at Phase 2 of the bootstrap
> plan; thereafter all upstream-sourced-lib mutations flow
> through the blessed recipe. Shim libraries (currently only
> `typing_extensions`, per v013 M1) continue to follow the
> separate "widened manually via code review" rule —
> initial-vendoring of a shim is "the author writes the shim
> file by hand and copies the upstream LICENSE."

### Q4. Typechecker + returns-pyright-plugin disposition (incompleteness / under-specified closure criteria → accepted, option A)

Accepted as proposed.

**returns pyright plugin.** PROPOSAL.md §"Dependencies —
Vendored pure-Python libraries" is extended to include a sixth
vendored lib: the `dry-python/returns` pyright plugin, vendored
alongside the library at
`.claude-plugin/scripts/_vendor/returns_pyright_plugin/` with
its upstream LICENSE preserved. `pyproject.toml`'s
`[tool.pyright]` section declares the plugin via `pluginPaths =
["_vendor/returns_pyright_plugin"]`. Rationale captured in
PROPOSAL.md prose AND in a leading comment block in
`pyproject.toml` (per the bootstrap plan's Phase 1 convention).
The `returns-pyright-plugin-disposition` deferred-items entry
is CLOSED by this change.

**typechecker.** PROPOSAL.md §"Dependencies — Developer-time
dependencies" AND style doc §"Type safety" both state pyright
(microsoft/pyright) is the chosen typechecker, preserving the
v012 L14 original recommendation. Rationale: pyright strict-
plus (v012 L1 + L2 manually enabled) provides the load-bearing
guardrails; basedpyright's defaults-are-stricter advantage is
marginal given v012 already manually enabled every strict-plus
option; livespec starts strict from Phase 2 so baselining isn't
needed; community-fork maintainer-pool risk outweighs the
incremental defaults-simplification benefit. The
`basedpyright-vs-pyright` deferred-items entry is CLOSED by
this change.

Both closures are recorded with pointers to PROPOSAL.md +
style-doc sections in the respective `deferred-items.md` entry
bodies.

### Q5. Seed-prompt LLM round-trip correctness verification (incompleteness / verification gap → accepted, option A)

Accepted as proposed.

PROPOSAL.md §"Testing approach" gains a new subsection
"Prompt-QA tier (per-prompt verification)" between the
"Testing approach" opening and the §"End-to-end harness-level
integration test" subsection:

> **Prompt-QA tier.** Every built-in template's REQUIRED
> prompts (`prompts/seed.md`, `prompts/propose-change.md`,
> `prompts/revise.md`, `prompts/critique.md`) are exercised by
> per-prompt tests under `<repo-root>/tests/prompts/<template>/`
> before any end-to-end harness test runs. The prompt-QA
> harness is a small deterministic replay mechanism (scope-
> distinct from `tests/e2e/fake_claude.py`, which drives
> wrappers end-to-end): each test case provides a prompt-
> response pair, runs the prompt against the harness, and
> asserts on structured output at the corresponding
> `{seed,proposal,revise}_input.schema.json` boundary PLUS
> semantic properties (e.g., that a seed prompt given
> "build a web service" intent produces top-level headings
> matching the domain, not arbitrary taxonomy). Every built-
> in template MUST ship ≥ 1 prompt-QA test per REQUIRED
> prompt; `just check-prompts` runs them per-commit (included
> in `just check`). Custom templates MAY ship their own
> prompt-QA tests; livespec imposes no requirement (consistent
> with the user-provided-extensions minimal-requirements
> principle).

A new deferred-items entry — `prompt-qa-harness` — captures
the harness implementation (fixture format, schema-level vs
semantic-level assertions per prompt, CLI wrapper shape if
any). The new entry is joint-resolved with
`template-prompt-authoring` (which authors the prompts being
tested) and `end-to-end-integration-test` (which owns the
distinct E2E harness).

Under v018 Q1-Option-A, the prompt-QA tier validates every
built-in template's prompts BEFORE Phase 7 agent-generates
their final content from their sub-specs. Phase 7's
propose-change cycle against each sub-spec therefore targets
a prompt set whose behavior is already machine-verified.

### Q6. Companion-doc migration policy (incompleteness → accepted, option A)

Accepted as proposed.

PROPOSAL.md gains a new subsection "Companion documents and
migration classes" within §"Self-application":

> **Companion documents and migration classes.** Companion
> documents in `brainstorming/approach-2-nlspec-based/` are
> classified as exactly one of three migration classes:
>
> - **MIGRATED-to-SPEC-file**: content moves verbatim (or
>   restructured for BCP 14 + heading conventions) into a
>   named `SPECIFICATION/` file.
> - **SUPERSEDED-by-section**: content becomes a named
>   section in an existing `SPECIFICATION/` file.
> - **ARCHIVE-ONLY**: content lives in `brainstorming/` for
>   historical context; not migrated to `SPECIFICATION/`.
>   Explicit rationale required per doc.
>
> Assignments (class, destination, phase):
>
> | Companion doc | Class | Destination | Phase |
> |---|---|---|---|
> | `goals-and-non-goals.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Goals" + "Non-goals" sections | 6 |
> | `python-skill-script-style-requirements.md` | MIGRATED-to-SPEC-file | `SPECIFICATION/constraints.md` | 8 |
> | `subdomains-and-unsolved-routing.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Non-goals" appendix (subordinate to `goals-and-non-goals.md`'s "Non-goals" section) | 8 |
> | `prior-art.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Prior Art" appendix | 8 |
> | `2026-04-19-nlspec-lifecycle-diagram.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Lifecycle" section | 8 |
> | `2026-04-19-nlspec-lifecycle-diagram-detailed.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Lifecycle" section (subordinate to preceding entry) | 8 |
> | `2026-04-19-nlspec-lifecycle-legend.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Lifecycle" section (subordinate) | 8 |
> | `2026-04-19-nlspec-terminology-and-structure-summary.md` | SUPERSEDED-by-section | `SPECIFICATION/spec.md` "Lifecycle" section (subordinate) | 8 |
> | `livespec-nlspec-spec.md` | ARCHIVE-ONLY + TEMPLATE-BUNDLED | Archived in `brainstorming/`; shipped as-is at `.claude-plugin/specification-templates/livespec/livespec-nlspec-spec.md` | N/A (already shipped per PROPOSAL.md §"Built-in template: `livespec`") |
> | `deferred-items.md` | ARCHIVE-ONLY | Archived in `brainstorming/`; items processed as Phase 8 propose-changes | 8 (items) / N/A (doc itself) |
> | `critique-interview-prompt.md` | ARCHIVE-ONLY | Archived in `brainstorming/`; brainstorming-process artifact, not part of shipped livespec | N/A |
> | `PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` | ARCHIVE-ONLY | Archived in `brainstorming/` after bootstrap completes; execution artifact, not spec content | N/A (bootstrap-only) |

The `companion-docs-mapping` deferred-items entry body
rewrites to a pointer to PROPOSAL.md's new subsection.

## Deferred-items inventory (carried forward + scope-widened + new + removed)

Per the deferred-items discipline, every carried-forward item
is enumerated below.

**Carried forward unchanged from v017:**

- `python-style-doc-into-constraints`
- `front-matter-parser`
- `local-bundled-model-e2e`

**Scope-widened in v018:**

- `static-check-semantics`
  - Q1: `--spec-target` flag parameterization codified across
    every doctor-static check that walks spec-tree state
    (`out-of-band-edits`, `version-directories-complete`,
    `version-contiguity`, `revision-to-proposed-change-pairing`,
    `proposed-change-topic-format`, `gherkin-blank-line-format`,
    `anchor-reference-resolution`, `template-files-present`).
    Each check runs per-tree when a sub-spec tree is present.
    `DoctorContext` gains sub-spec-discovery information (list
    of sub-spec roots + their template associations).
  - Q5: prompt-QA harness's replay-pair semantics entered as a
    new subsection (the deterministic prompt-response fixture
    format; semantic-property assertion mechanism per prompt).
- `skill-md-prose-authoring`
  - Q1: seed's SKILL.md prose covers the multi-tree seed
    dispatch (main + each built-in template's sub-spec
    atomically); propose-change/critique/revise SKILL.md
    prose covers the `--spec-target <path>` flag surface.
- `enforcement-check-scripts`
  - Q4: new `pyproject.toml` `[tool.pyright]` `pluginPaths`
    entry pointing at
    `.claude-plugin/scripts/_vendor/returns_pyright_plugin/`.
    No new check script.
  - Q5: new `just check-prompts` recipe (per-commit; in
    `just check`) running the `tests/prompts/` suite. Added
    to the canonical just-target list.
- `task-runner-and-ci-config`
  - Q3: `.vendor.jsonc` schema widened to cover
    `returns_pyright_plugin` upstream ref (matching the
    Q4 plugin-vendoring decision).
  - Q4: `pyproject.toml` `[tool.pyright]` adds `pluginPaths`
    + rationale comment block naming the returns-plugin
    + typechecker decisions.
  - Q5: `.mise.toml` pinning is unchanged (no new
    mise-pinned tool); `justfile` adds
    `just check-prompts` as part of `just check`
    aggregation.
- `wrapper-input-schemas`
  - Q1: `seed_input.schema.json` gains `sub_specs:
    list[SubSpecPayload]` field; new `SubSpecPayload` schema
    authored (carries the sub-spec-tree payload shape).
    Paired `SubSpecPayload` dataclass at
    `schemas/dataclasses/sub_spec_payload.py`; paired
    validator at `validate/sub_spec_payload.py`.
    `check-schema-dataclass-pairing` three-way walker
    enforces drift-free pairing.
- `companion-docs-mapping`
  - Q6: body rewrites to a pointer to PROPOSAL.md
    §"Companion documents and migration classes". The
    per-doc assignment table moves from this entry to
    PROPOSAL.md.
- `end-to-end-integration-test`
  - Q5: scope cross-reference with the new `prompt-qa-harness`
    entry (the E2E harness + prompt-QA harness are
    structurally distinct but coordinate on fixture
    conventions).
- `user-hosted-custom-templates`
  - Q1: sub-spec-mechanism extension notes — v2+ template-
    discovery extensions MAY declare their own sub-spec
    structure; the `--spec-target` flag surface is v1-frozen
    and extends uniformly.
- `claude-md-prose`
  - Q5: `tests/prompts/CLAUDE.md` (new) notes the prompt-QA
    harness's fixture conventions and the
    schema-level-vs-semantic-level assertion split.

**New in v018:**

- `sub-spec-structural-formalization` (Q1) — captures the
  sub-spec mechanism's implementation details: doctor
  parameterization (per-tree check walks), propose-change/
  revise CLI widening (`--spec-target <path>`), seed
  multi-tree output (atomic main + sub-specs), heading-
  coverage scoping (the `spec_root` discriminator field). The
  entry body also names the sub-spec file conventions (every
  built-in sub-spec ships `spec.md`/`contracts.md`/
  `constraints.md`/`scenarios.md` per the main-spec
  convention; `livespec` sub-spec ships `scenarios.md` with
  Gherkin convention; `minimal` sub-spec ships
  `scenarios.md` without Gherkin — matching the built-in
  templates' top-level conventions).

- `prompt-qa-harness` (Q5) — captures the prompt-QA harness
  implementation (harness shape, fixture format, which
  schema-level vs semantic-level assertions apply per
  prompt). Joint-resolved with `template-prompt-authoring`
  (which authors the prompts) and `end-to-end-integration-
  test` (which owns the distinct E2E harness).

**Removed / closed in v018:**

- `template-prompt-authoring` — CLOSED by Q1 (content
  generated from sub-specs rather than implementer-chosen).
- `returns-pyright-plugin-disposition` — CLOSED by Q4
  (vendor the plugin; configure via `[tool.pyright]`
  `pluginPaths`).
- `basedpyright-vs-pyright` — CLOSED by Q4 (stay on pyright).

## Self-consistency check

(Populated during careful-review passes below; initial draft
covers the primary invariants; pass-specific findings update
this section.)

Post-apply invariants rechecked against the working docs:

- PROPOSAL.md §"SPECIFICATION directory structure" carries
  the main-spec + sub-spec layout; doctor-static checks
  parameterize per-tree; propose-change/revise accept
  `--spec-target`; `seed_input.schema.json` widens with
  `sub_specs`.
- PROPOSAL.md §"Self-application" carries the bootstrap-
  exception clause + the companion-documents migration-
  classes subsection.
- PROPOSAL.md §"Vendoring discipline" carries the one-time
  initial-vendoring procedure (mirrored in style doc).
- PROPOSAL.md §"Dependencies — Vendored pure-Python
  libraries" lists the returns pyright plugin as the sixth
  vendored lib.
- PROPOSAL.md §"Dependencies — Developer-time dependencies"
  AND style doc §"Type safety" both name pyright as the
  typechecker + vendor-plugin configuration.
- PROPOSAL.md §"Testing approach" carries the new
  "Prompt-QA tier" subsection; `just check-prompts` is in
  the canonical target list.
- `deferred-items.md` carries two new entries
  (`sub-spec-structural-formalization`,
  `prompt-qa-harness`); three closures
  (`template-prompt-authoring`,
  `returns-pyright-plugin-disposition`,
  `basedpyright-vs-pyright`); nine scope-widenings across
  existing entries per Q1-Q6 ripples.
- Bootstrap plan (outside the frozen brainstorming set but
  aligned per this cycle) receives plan-side ripple edits
  for Q2-Q6 (the plan already absorbs Q1-Option-A from the
  prior session).

### Careful-review passes

- **Careful-review pass 1** (6 load-bearing findings, all
  landed):
  1. PROPOSAL.md §"Skill↔template communication layer"
     (around line 1442) referenced the closed
     `template-prompt-authoring` deferred entry for schema
     + prompt authoring. Rewrote to reference
     `wrapper-input-schemas` (widened for v018 Q1 with
     `SubSpecPayload`) for schemas AND point at
     sub-specification trees for prompt authoring.
  2. PROPOSAL.md §"Built-in template: `minimal` (v014 N1)"
     minimal-as-E2E-fixture paragraph still described the
     delimiter-comment format as "implementer choice per
     `deferred-items.md`'s `template-prompt-authoring` and
     `end-to-end-integration-test` joint resolution" — the
     former is closed; rewrote to reference the v018 Q1
     codification in the `minimal` sub-spec's `contracts.md`
     "Template↔mock delimiter-comment format" section.
  3. PROPOSAL.md §"Prompt-QA tier (v018 Q5)" closing
     paragraph about joint resolution mentioned the closed
     `template-prompt-authoring`; rewrote to reference
     `sub-spec-structural-formalization` (which supersedes
     template-prompt-authoring for prompt authoring)
     alongside `end-to-end-integration-test`.
  4. PROPOSAL.md §"End-to-end harness-level integration
     test (v014 N9)" paragraph about delimiter-comment
     format's joint resolution likewise referenced the
     closed `template-prompt-authoring`; rewrote to
     reference the v018 Q1 sub-spec codification in
     `minimal`'s `contracts.md` (per bootstrap-plan
     Phase 7).
  5. PROPOSAL.md DoD item 14 (dogfooding) did not mention
     sub-spec trees or the per-tree propose-change/revise
     cycles; extended to cover main + each built-in
     template's sub-spec tree, and noted the closed-item
     bookkeeping revisions.
  6. PROPOSAL.md §"Configuration → Multi-specification per
     project" subsection (at line 1230) AND §"v1 non-goals"
     Multi-specification entry both needed clarifying
     notes distinguishing "unrelated independent specs
     co-existing" (still out of scope) from "hierarchical
     sub-specs of a single primary spec" (now in scope per
     v018 Q1 — a narrower, strictly smaller carve-out).
     Extended both.
  Two deferred-items.md follow-on fixes landed alongside:
  - Line 1290 `skill-md-prose-authoring` entry's reference
    to closed `template-prompt-authoring` for template-
    internal discipline-doc injection — redirected to
    `sub-spec-structural-formalization` per v018 Q1.
  - Line 1627-1628 `end-to-end-integration-test` entry's
    delimiter-comment format joint-resolution reference —
    redirected to `SPECIFICATION/templates/minimal/contracts.md`
    per v018 Q1.

- **Careful-review pass 2** (1 load-bearing finding,
  landed):
  1. PROPOSAL.md §"seed" wrapper deterministic
     file-shaping step 5 (sub-spec tree history/v001/
     creation) contained a slightly inconsistent phrasing
     that said "the v1 built-in sub-specs follow the same
     multi-file convention as the main `livespec` template,
     so each sub-spec ships a `README.md` + versioned
     README, EXCEPT the `minimal` sub-spec..." — the
     "same as main `livespec` template" was misleading
     (each sub-spec follows its OWN template's convention,
     not the main-spec's). Rewrote to say each sub-spec
     follows its OWN template's convention explicitly:
     `livespec` sub-spec ships README + versioned README;
     `minimal` sub-spec ships neither. The skill-owned
     `proposed_changes/README.md` + `history/README.md`
     clarification — same content across trees; only the
     `<spec-root>/` base differs — was added.

- **Careful-review pass 3** (2 load-bearing findings,
  landed — revision-file drift):
  1. Revision-file "Carried forward unchanged from v017"
     list showed only `front-matter-parser` and
     `local-bundled-model-e2e` — missed
     `python-style-doc-into-constraints`. Added.
  2. Revision-file "Scope-widened in v018" list included
     `template-prompt-authoring` (which is CLOSED, not
     widened) — removed from scope-widened; it remains
     only in "Removed / closed in v018" where it belongs.
     The "Outstanding follow-ups" count of 9 widened
     entries was already correct; the in-body section
     drifted from that count by listing 10. Restored
     to 9.

- **Careful-review pass 4** (0 load-bearing findings):
  end-to-end re-read confirms all working docs are
  self-consistent. Cross-doc references align; the
  sub-spec mechanism applies uniformly across the file-
  shaping steps, --spec-target flag surface, per-tree
  doctor iteration, heading-coverage registry, and DoD
  items. v018 Q4 returns_pyright_plugin vendored-lib
  list additions match between PROPOSAL.md, deferred-
  items.md, and the style doc. v018 Q3 initial-vendoring
  procedure identical between PROPOSAL.md §"Vendoring
  discipline" and style doc §"Vendoring discipline".
  v018 Q6 migration-class table matches between PROPOSAL.md
  §"Companion documents and migration classes" and the
  `companion-docs-mapping` deferred-entry pointer.
  Pass 4 is the final general careful-review pass per the
  "continue until a pass lands no load-bearing fixes"
  rule.

**Cumulative across 4 general careful-review passes: 9
inconsistencies caught and fixed (6 + 1 + 2 + 0).**

### Dedicated deferred-items-consistency pass

Walked every deferred-items entry and verified Source line
+ body against every v018 decision + every prior-version
decision that touched the entry.

- **Source-line drift check.** Every entry's Source line now
  records its v018 widening (or closure, or new-entry
  notation). Specifically verified:
  - Nine scope-widened entries have v018 widening notations
    (static-check-semantics per Q1 + Q5;
    skill-md-prose-authoring per Q1;
    enforcement-check-scripts per Q4 + Q5;
    task-runner-and-ci-config per Q3 + Q4 + Q5;
    wrapper-input-schemas per Q1;
    companion-docs-mapping per Q6 [body rewritten to
    pointer; Source line widened];
    end-to-end-integration-test per Q5;
    user-hosted-custom-templates per Q1;
    claude-md-prose per Q5).
  - Three closed entries (template-prompt-authoring per Q1;
    returns-pyright-plugin-disposition per Q4;
    basedpyright-vs-pyright per Q4) carry explicit
    "CLOSED in v018" notations + pointers to PROPOSAL.md's
    closure locations.
  - Two new entries (sub-spec-structural-formalization per
    Q1; prompt-qa-harness per Q5) carry proper "v018 (Qn;
    new)" Source lines.
  - Three carried-forward-unchanged entries
    (python-style-doc-into-constraints; front-matter-parser;
    local-bundled-model-e2e) have no v018 touch; Source lines
    correctly unchanged.

- **Layout-tree drift check.**
  - PROPOSAL.md `.claude-plugin/` tree (the big diagram
    around line 72+) extended with `returns_pyright_plugin/`
    under `_vendor/` per v018 Q4 vendored-lib addition.
  - PROPOSAL.md `tests/` tree (around the Testing-approach
    section) found missing the `tests/prompts/` subtree
    that v018 Q5 introduces. **Finding landed**: added a
    `tests/prompts/<template>/` subtree to the tree diagram
    covering both built-in templates' REQUIRED prompts
    (seed, propose-change, revise, critique) with a
    `CLAUDE.md` at `tests/prompts/` per the v018 Q5 +
    claude-md-prose (v018 note-only widening) discipline.
  - PROPOSAL.md `dev-tooling/` tree (in §"Developer tooling
    layout") unchanged — v018 Q1-Q6 introduce no new
    enforcement-check scripts under `dev-tooling/checks/`.
    Q4 adds `pluginPaths` to `pyproject.toml` (no new
    script); Q5 adds `just check-prompts` recipe (no new
    script; the recipe runs pytest against `tests/prompts/`).

- **Cross-reference validity.** All `§"..."` cross-references
  introduced by v018 Q# decisions resolve to existing
  headings:
  - `§"SPECIFICATION directory structure — Template sub-
    specifications"` → `### Template sub-specifications
    (v018 Q1)` heading present.
  - `§"Companion documents and migration classes"` → `###
    Companion documents and migration classes (v018 Q6)`
    heading present under §"Self-application".
  - `§"Sub-command dispatch and invocation chain — Spec-
    target selection contract"` → bulleted sub-item
    present in §"Sub-command dispatch and invocation
    chain".
  - `§"Prompt-QA tier (per-prompt verification)"` → `###
    Prompt-QA tier (per-prompt verification, v018 Q5)`
    heading present under §"Testing approach".
  - `§"Vendoring discipline"` cross-reference present in
    style doc.

- **Example-vs-rule alignment.**
  - Heading-coverage JSON example at PROPOSAL.md §"Testing
    approach → Coverage registry" updated to include
    `spec_root` in every entry; example values span
    main-spec (`SPECIFICATION`) and sub-spec
    (`SPECIFICATION/templates/livespec`) tree roots,
    matching the new rule.
  - `seed_input.schema.json` JSON example at PROPOSAL.md
    §"seed" extended with `sub_specs: []` showing the
    new shape; representative entry uses
    `template_name: "livespec"` and a sub-spec spec-file
    path `SPECIFICATION/templates/livespec/spec.md`.
  - Sub-spec ASCII tree layout in PROPOSAL.md §"Template
    sub-specifications" shows both built-in sub-spec
    trees structurally; the `minimal` sub-spec correctly
    omits a top-level `README.md` (per v015 O2 / v014 N1
    minimal convention), while the `livespec` sub-spec
    includes one (optional per livespec convention). Seed
    wrapper's step 5 was refined in pass 2 to state that
    each sub-spec follows its OWN template's convention
    for per-version README presence.

**Findings landed in this dedicated pass: 1 (the
`tests/prompts/` subtree addition to the test-tree
diagram).**

**Cumulative total findings across all 4 careful-review
passes + 1 dedicated deferred-items-consistency pass: 10
inconsistencies caught and fixed (6 + 1 + 2 + 0 + 1).**

## Outstanding follow-ups

Tracked in the updated `deferred-items.md`.

The v018 pass touches 9 existing entries with scope-widenings:

- `static-check-semantics` (Q1, Q5)
- `skill-md-prose-authoring` (Q1)
- `enforcement-check-scripts` (Q4, Q5)
- `task-runner-and-ci-config` (Q3, Q4, Q5)
- `wrapper-input-schemas` (Q1)
- `companion-docs-mapping` (Q6)
- `end-to-end-integration-test` (Q5)
- `user-hosted-custom-templates` (Q1)
- `claude-md-prose` (Q5)

Adds 2 new entries (`sub-spec-structural-formalization`,
`prompt-qa-harness`); closes 3
(`template-prompt-authoring`,
`returns-pyright-plugin-disposition`,
`basedpyright-vs-pyright`).

Plan-file ripple (outside the frozen brainstorming set):
`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` receives edits
for Q2 (bootstrap-exception cross-reference in §"Cutover
principle" and every phase that hand-authors code), Q3 (Phase
2 initial-vendoring procedure reference), Q4 (Phase 1's
typechecker + plugin decisions cross-reference PROPOSAL.md),
Q5 (Phase 5's test-suite phase adds `tests/prompts/` subtree
+ `just check-prompts` gate), Q6 (Phase 8's
companion-doc-migration iteration follows the PROPOSAL.md
migration-classes table).

## What was rejected

- Q1 Option B (lift Multi-specification per project non-goal
  for the livespec repo only) was rejected because it lifts a
  stated v1 non-goal wholesale rather than surgically; admits
  multi-spec-per-project as a general feature rather than as a
  livespec-internal mechanism.
- Q1 Option C (expand main spec.md / contracts.md with
  template content) was rejected because it entangles core
  spec material with per-template specification-level
  material; each template's prompt interview flow is
  several-hundred-line specification that would dominate core
  spec files.
- Q2 Option B (inline in bootstrap plan only) was rejected
  because the plan is a working document, not the spec;
  doesn't solve the recreatability test.
- Q2 Option C (apply loop from v1.0.0 onward) was rejected
  because it pushes the bootstrap boundary far out and
  contradicts established post-seed discipline (every
  Phase-6+ change flows through the loop).
- Q3 Option B (`just vendor-bootstrap-all` shell-only recipe)
  was rejected because it adds a second just recipe, diverges
  from the single-language principle, and gains nothing over
  A's one-time manual procedure.
- Q3 Option C (`dev-tooling/bootstrap_vendor.py` stdlib-only)
  was rejected because it creates a two-tier bootstrap
  splitting vendoring authority across two distinct
  mechanisms.
- Q4 Option B (leave deferred with criteria) was rejected
  because the typechecker choice is load-bearing enough to
  belong in the spec with rationale; pushing closure to
  Phase 1 is less robust than deciding at spec level.
- Q4 Option C (name bootstrap plan as closure mechanism)
  was rejected because it defers spec-level decisions to an
  external document that may evolve independently.
- Q5 Option B (expand E2E fake_claude.py to cover livespec
  template) was rejected because it breaks v014 N9's minimal-
  only scoping, forces delimiter comments in the `livespec`
  template's prompts (explicitly exempted), and conflates
  wrapper-integration vs prompt-behavior verification.
- Q5 Option C (defer verification to Phase 7's agent-
  generation step) was rejected because Phase 7 runs once at
  bootstrap and isn't re-executed per-commit — no regression
  coverage.
- Q6 Option B (defer classification to Phase 8 itself) was
  rejected because still leaves implementer judgment at
  spec-consumption time; doesn't resolve recreatability at
  spec level.
- Q6 Option C (name destinations without categorical labels)
  was rejected because it loses the reusable categorization
  that future custom-template authors could model against;
  small overhead for substantial reviewability gain.
