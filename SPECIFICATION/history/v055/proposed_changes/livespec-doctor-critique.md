---
topic: livespec-doctor-critique
author: livespec-doctor
created_at: 2026-05-07T21:01:36Z
---

## Proposal: Reconcile sub-command count between spec.md and contracts.md

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md

### Summary

spec.md and contracts.md disagree on how many sub-commands livespec exposes. spec.md:28 says 'six sub-commands' listing seed, propose-change, critique, revise, prune-history, doctor. contracts.md:81 says 'seven slash commands' adding /livespec:help. The help skill is real and user-invocable, so the count in spec.md is wrong.

### Motivation

Doctor LLM-driven objective phase surfaced this as an internal contradiction. The two numbers create reader ambiguity about whether help (and resolve_template) are first-class sub-commands. spec.md:30 also references 'help' and 'resolve_template' as exempt from pre/post-step doctor, implying they ARE sub-commands.

### Proposed Changes

Update spec.md §'Sub-command lifecycle' line 28 to read 'livespec exposes seven sub-commands: seed, propose-change, critique, revise, prune-history, doctor, and help'. Reconcile the per-sub-command applicability enumeration at lines 33-37 to include help explicitly with classification 'no pre-step / no post-step / no LLM-driven phase'. Optionally clarify that resolve_template is an internal helper rather than a user-facing sub-command (it has no SKILL.md). The contracts.md §'Plugin distribution' count of seven is treated as authoritative.

## Proposal: Align prune-history scenario with actual mechanic

### Target specification files

- SPECIFICATION/scenarios.md

### Summary

scenarios.md §'Recovery path — pruning history before a long retention horizon' (lines 113-120) describes a 'retention horizon of 5' parameter that does not exist in spec.md or contracts.md. The scenario describes a non-existent API.

### Motivation

spec.md:56 specifies the prune-history mechanic as 'delete every vK where K < N-1' (collapse to a single PRUNED_HISTORY.json marker at v(N-1) plus vN intact). contracts.md:15 lists prune-history flags as --skip-pre-check / --run-pre-check / --project-root only — no retention-horizon flag exists. The scenario misleads readers about the API surface.

### Proposed Changes

Rewrite the scenario in scenarios.md to match the actual mechanic. Replacement: 'Given the repository has 20 history versions at v001/ through v020/. When the user invokes /livespec:prune-history. Then the wrapper deletes v001/ through v018/. And v019/ contains only PRUNED_HISTORY.json with {pruned_range: [1, 19]}. And v020/ remains unchanged. And the wrapper exits 0.' Remove the 'retention horizon' phrasing entirely. The contiguous-version invariant is preserved by the version-directories-complete pruned-marker exemption.

## Proposal: Reconcile wrapper-shape statement count from 6 to 5

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/constraints.md

### Summary

Spec text repeatedly says wrapper shape is '6 statements' / 'exactly 6 statements' but the actual implementation enforces 5. The canonical example in constraints.md:567-575 itself shows 5 statements; the enforcement check dev-tooling/checks/wrapper_shape.py:20 reads 'exactly 5 top-level statements' and the error message at :155 says '5-statement form'.

### Motivation

Spec ↔ implementation drift surfaced by the doctor LLM-driven subjective phase. spec.md:114 and constraints.md lines 91, 171, 277, 412, 424, 562, 566 all claim '6-statement' wrapper shape (eight active spec sites). Even the enforcement check's own module docstring at lines 1 and 6 says '6-statement' while its body says '5'. The statement count is wrong wherever it appears as '6'.

### Proposed Changes

Replace every active occurrence of '6 statement' / '6-statement' / 'six statement' / 'exactly 6 statements' in SPECIFICATION/spec.md (line 114) and SPECIFICATION/constraints.md (lines 91, 171, 277, 412, 424, 562, 566) with the corresponding '5'-prefixed phrasing. The canonical example block at constraints.md:567-575 already shows 5 statements correctly and remains unchanged. Separately, the docstring of dev-tooling/checks/wrapper_shape.py:1 and :6 should also be reconciled to '5-statement' as a code-tree fix (lands outside SPECIFICATION/, so via resulting_files in the same revise pass or a follow-up cleanup commit). The structural rule itself is unchanged; only the count is corrected.

## Proposal: Resolve dangling deferred-items.md cross-reference

### Target specification files

- SPECIFICATION/spec.md

### Summary

spec.md:77 and :100 reference 'deferred-items.md's static-check-semantics entry' as the codified location for two algorithms (reserve-suffix canonicalization, author-identifier-to-filename-slug transformation). No deferred-items.md exists in any active spec tree (only inside archive/).

### Motivation

Dangling-reference finding from the doctor LLM-driven objective phase. The cross-reference is unresolvable for a current reader. Either the file is supposed to exist (and the bootstrap process didn't carry it forward into the active SPECIFICATION/ tree) or the reference is stale (and the algorithm details should be inlined or moved elsewhere).

### Proposed Changes

Resolve in one of two directions. Option A (preferred): inline the algorithm details directly into spec.md §'Proposed-change and revision file formats' under 'Reserve-suffix canonicalization', and into §'Author identifier resolution' under 'Author identifier → filename slug transformation'. Remove the deferred-items.md cross-reference entirely. Option B: author SPECIFICATION/deferred-items.md as a sibling spec file holding the static-check-semantics entries, update the livespec template's template.json files[] declaration to include it, and keep cross-references internal to the spec tree. Option A avoids adding a new template-declared spec file.

## Proposal: Move wire-level and constraint-level content out of spec.md §Sub-command lifecycle

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

spec.md §'Sub-command lifecycle' (lines 43-58) contains extensive wire-level (schema-payload validation rules, structured LivespecError envelope mechanics, exit-code-to-error mappings) and constraint-level (file-shaping mechanics, byte-identical move semantics, precondition error class names, accept-decision-snapshot-consistency check definition) content. Per the livespec template's content-role separation, this content belongs in contracts.md or constraints.md.

### Motivation

Template-compliance finding from the doctor LLM-driven subjective phase per the livespec template's doctor-LLM-subjective-checks prompt §'Template-compliance semantic judgments': spec.md content addresses project intent and high-level architecture; contracts.md content is wire-level / CLI-level; constraints.md content is architecture-level constraints. The current spec.md violates this separation across multiple subsections.

### Proposed Changes

Split as follows: (1) leave a high-level lifecycle summary in spec.md describing which sub-commands run pre-step / post-step doctor static and which run an LLM-driven phase — intent-level content. (2) Move wire-level details (payload validation against schemas, exit-code-to-error mappings, structured error envelope, retry-on-exit-4 contract) to contracts.md §'Wrapper CLI surface' and §'Lifecycle exit-code table'. (3) Move file-shaping mechanics (byte-identical move semantics, file-shaping clauses (a)-(h), accept-decision-snapshot-consistency static check definition, pre-step skip control resolution chain) to constraints.md, either as a new §'Sub-command lifecycle mechanics' section or distributed across existing constraints.md sections. Coordinate with the §Sub-command lifecycle structural-split proposal in this critique batch.

## Proposal: Promote bold inline subheadings to ### subheadings in revise lifecycle

### Target specification files

- SPECIFICATION/spec.md

### Summary

spec.md:49 ('revise lifecycle and responsibility separation') is a single unbroken paragraph carrying eight bold inline sub-headings (clauses (a) through (h)) plus several other distinct rules. Reader navigation suffers; the bold-prefixed prose pattern is used throughout §Sub-command lifecycle but the revise paragraph is the most extreme.

### Motivation

Prose-quality finding from the doctor LLM-driven subjective phase. Long bold-header-prefixed paragraphs defeat the heading-as-navigation function. The revise paragraph alone covers payload validation, skill responsibility separation, file-shaping clauses (a)-(h), proposal ordering, decision-coverage cases, and pre-existing/missing target file handling.

### Proposed Changes

Promote bold inline sub-headings to ### subheadings under §'Sub-command lifecycle'. Specifically: ### revise schema validation, ### revise lifecycle and responsibility separation, ### revise file-shaping clauses (with each clause (a)-(h) as a #### or bullet list), ### revise path-relativity guard. The content stays the same; only the structure changes. Apply the same treatment to other bold-header-prefixed paragraphs in the section (critique payload validation, critique internal delegation, etc.). Coordinate with the §Sub-command lifecycle structural-split proposal in this critique batch.

## Proposal: Move revision-loop diagram and Terminology section earlier in spec.md

### Target specification files

- SPECIFICATION/spec.md

### Summary

spec.md §'Lifecycle' (line 197+) contains the revision-loop mermaid diagram and §'Terminology' explaining intent / specification / scenarios vocabulary. They appear after Sub-command lifecycle, Versioning, Pruning, Proposed-change formats, Author resolution, Testing, TDD, Developer tooling, DoD, and Non-goals — yet they describe the high-level mental model that all those earlier sections elaborate.

### Motivation

Spec readability finding from the doctor LLM-driven subjective phase. New readers benefit from forming the mental model before diving into mechanism. The current order asks readers to absorb extensive lifecycle, versioning, and tooling rules before seeing the high-level loop diagram that motivates them.

### Proposed Changes

Reorder spec.md to put §'Lifecycle' (with the revision-loop mermaid diagram) and §'Terminology' immediately after §'Specification model' and before §'Sub-command lifecycle'. The new top-of-spec order becomes: Project intent → Runtime and packaging → Specification model → Lifecycle (loop diagram) → Terminology → Sub-command lifecycle → Versioning → Pruning → Proposed-change formats → Author resolution → Testing → TDD → Developer tooling → DoD → Non-goals → Prior Art → Subdomain routing → Self-application. Heading text and content within each section is unchanged; only ordering moves.

## Proposal: Split §Sub-command lifecycle into multiple top-level sections

### Target specification files

- SPECIFICATION/spec.md

### Summary

§'Sub-command lifecycle' bundles eight conceptually distinct topics under one ## heading: per-command lifecycle applicability table, critique payload validation, critique internal delegation, revise payload validation, revise lifecycle and responsibility separation, revise path-relativity guard, accept-decision-snapshot-consistency static check, prune-history lifecycle and responsibility separation, and pre-step skip control. A single ## heading for so many distinct topics defeats heading-as-navigation.

### Motivation

NLSpec economy + conceptual fidelity finding from the doctor LLM-driven subjective phase. tests/heading-coverage.json registry treats each ## heading as an indivisible unit; a single overpacked heading inflates the per-section coverage entry and obscures section-by-section reasoning.

### Proposed Changes

Split into separate top-level sections: ## Sub-command applicability (the lifecycle table at lines 33-37); ## Lifecycle: critique; ## Lifecycle: revise; ## Lifecycle: prune-history; ## Static check: accept-decision-snapshot-consistency (or moved to constraints.md per the wire-level content relocation proposal in this critique batch); ## Pre-step skip control. Each section then carries its own content as a navigable unit with proper ### sub-structure. Coordinate with the wire-level content relocation, the inline-bold to ### promotion, and the Lifecycle/Terminology placement proposals in this critique batch.

## Proposal: Fix line-number reference in templates/livespec/contracts.md

### Target specification files

- SPECIFICATION/templates/livespec/contracts.md

### Summary

templates/livespec/contracts.md:20 cites 'SPECIFICATION/constraints.md §"Heading taxonomy" line 47'. Line 47 of main constraints.md is in §'Vendored-library discipline'; §'Heading taxonomy' actually begins at line 644.

### Motivation

Dangling-reference finding from the doctor LLM-driven objective phase. Cross-references with hard-coded line numbers in spec text are fragile across revise cycles and bit-rot quickly — especially given that other proposals in this critique batch reorder constraints.md sections.

### Proposed Changes

Replace 'line 47' with the section name only — drop the line number entirely. The reference becomes 'SPECIFICATION/constraints.md §"Heading taxonomy" which pins intent-derivation to level 1'. Establish the general pattern: cite spec sections by §"<heading text>" rather than by line number throughout the spec tree.

## Proposal: Align minimal sub-spec prune-history scenario with actual mechanic

### Target specification files

- SPECIFICATION/templates/minimal/scenarios.md

### Summary

templates/minimal/scenarios.md:42-51 ('Prune with retention horizon larger than available versions') repeats the retention-horizon premise from the main spec; same root cause as the main-spec prune-history scenario alignment proposal in this critique batch.

### Motivation

Internal-contradiction finding from the doctor LLM-driven objective phase. The minimal sub-spec's e2e-fixture scenario must reflect the actual prune-history API (no retention-horizon flag). The current scenario describes the no-op case but frames it through the non-existent retention-horizon parameter.

### Proposed Changes

Rewrite as 'Prune with only v001/ in history (no-op short-circuit)': 'Given the fixture repo has history/v001/ only. When the user invokes /livespec:prune-history. Then the wrapper emits a {findings: [{check_id: prune-history-no-op, status: skipped, message: "nothing to prune; oldest surviving history is already PRUNED_HISTORY.json or is the only version"}]} JSON document. And exits 0. And no version directories are removed.' This matches the actual no-op short-circuit at SPECIFICATION/spec.md:56.
