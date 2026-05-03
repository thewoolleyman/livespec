# Specification — `livespec` template

This sub-spec governs the `livespec` built-in template's user-visible behavior. The template ships with `livespec` itself at `.claude-plugin/specification-templates/livespec/` and is the recommended template for projects whose `SPECIFICATION/` is structured as multiple coordinating files (`spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`, `README.md`). Mutations to the template's prompts, starter content, or NLSpec discipline injection MUST flow through this sub-spec via `/livespec:propose-change --spec-target SPECIFICATION/templates/livespec/`.

## Template root layout

The `livespec` template root MUST contain (a) `template.json` with `template_format_version: 1`, `spec_root: "SPECIFICATION/"`, and the doctor LLM-driven prompt fields, (b) `prompts/<sub-command>.md` for each REQUIRED prompt (`seed`, `propose-change`, `critique`, `revise`), (c) `livespec-nlspec-spec.md` as the canonical NLSpec discipline reference document, and (d) `specification-template/` holding starter content scaffolding for new spec trees. Phase 7 widens the starter-content policy from the current `.gitkeep` placeholder.

## Seed interview flow

The `prompts/seed.md` prompt MUST implement the v020 Q2 sub-spec-emission contract: the prompt asks the pre-seed question "Does this project ship its own livespec templates that should be governed by sub-spec trees under `SPECIFICATION/templates/<name>/`?"; on "yes" it enumerates the user-named templates and emits one `sub_specs[]` entry per name per `seed_input.schema.json`'s `SubSpecPayload` shape; on "no" (the default) it emits `sub_specs: []`. The seed prompt regenerated from this sub-spec in Phase 7 MUST preserve this user-answer-driven behavior; Phase 7's revise step MUST reject regenerated prompts that hard-code emission per v019's now-superseded contract.

The seed prompt MUST capture a free-text user intent and use it to drive the per-file content authoring. The intent text MUST appear verbatim in the auto-emitted `history/v001/proposed_changes/seed.md` proposed-change file. The prompt SHOULD derive top-level `##` headings within each spec file from intent nouns rather than from a fixed taxonomy.

## Propose-change interview flow

The `prompts/propose-change.md` prompt MUST guide the user through composing a `proposal_findings.schema.json`-conforming JSON payload from the user's described change. The prompt SHOULD elicit per-finding `name`, `target_spec_files`, `summary`, `motivation`, and `proposed_changes` text. The prompt SHOULD reference the `livespec-nlspec-spec.md` BCP14 + gherkin-blank-line conventions when authoring the `proposed_changes` prose so the resulting propose-change file flows into the spec under the same NLSpec discipline.

## Revise interview flow

The `prompts/revise.md` prompt MUST walk the user through the per-proposal accept/reject decision for every pending proposed-change file under `<spec-target>/proposed_changes/`. The prompt SHOULD compose the `revise_input.schema.json`-conforming JSON payload describing per-proposal disposition AND the resulting spec edits. Phase 7 widens the prompt to handle multi-finding proposals plus partial accepts.

## Critique interview flow

The `prompts/critique.md` prompt MUST emit critique-driven `proposal_findings.schema.json`-conforming output suitable for downstream propose-change consumption. The prompt SHOULD ground each finding against the spec target's current state (read via `Read` on the spec files) and SHOULD apply the `livespec-nlspec-spec.md` discipline to surface ambiguities, contradictions, or missing-rule findings.

## NLSpec discipline injection

Each prompt MUST internalize the `livespec-nlspec-spec.md` discipline at seed/use time. The prompt SHOULD NOT include the discipline doc's content verbatim in any output file; instead, the prompt absorbs the doc's rules and applies them to the generated content. The discipline doc covers BCP14 keyword well-formedness, gherkin blank-line conventions, heading-taxonomy guidance, and the broader natural-language-spec hygiene rules `livespec` enforces.

## Starter-content policy

Per Phase 7 widening: when the seed prompt generates initial content for a new spec tree, the starter content SHOULD reflect the user's intent rather than a fixed boilerplate. Bootstrap-minimum starter shape (this revision): the seed-input JSON `files[]` array enumerates the spec-file paths and content; the `specification-template/` scaffolding under the template root is currently a `.gitkeep` placeholder pending Phase 7 work.

The seed prompt MUST author one `## Heading` entry per top-level concern in each spec file. The headings MUST be substantive enough that `tests/heading-coverage.json` entries can carry meaningful `reason` placeholders.
