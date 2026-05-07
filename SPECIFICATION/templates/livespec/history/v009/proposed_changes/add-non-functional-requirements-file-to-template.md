---
topic: add-non-functional-requirements-file-to-template
author: claude-opus-4-7
created_at: 2026-05-07T22:19:33Z
---

## Proposal: Add non-functional-requirements.md to the livespec template

### Target specification files

- SPECIFICATION/templates/livespec/spec.md
- SPECIFICATION/templates/livespec/constraints.md

### Summary

Widen the livespec template's declared spec-file surface to add a sixth file, non-functional-requirements.md, alongside README.md, spec.md, contracts.md, constraints.md, and scenarios.md. Define the boundary between non-functional-requirements.md and the existing files. This proposal does NOT migrate any existing content; migration from spec.md and constraints.md into non-functional-requirements.md is a separate atomic propose-change that follows once this one lands.

### Motivation

The current livespec template surfaces no dedicated home for dev-process and dev-environment requirements. Projects using the template must mix Test-Driven Development discipline, linter and formatter rules, code-coverage targets, complexity thresholds, hook configuration, repo-local task tracking, and contributor commit discipline into either spec.md (which is meant to capture user-facing intent and behavior) or constraints.md (which is meant for constraints whose violation an end user could observe). Adding non-functional-requirements.md as a first-class part of the template gives that content a coherent home and clarifies the boundary between user-facing spec material and contributor-facing requirements. The boundary problem also surfaces concretely when proposals like livespec-implementation-workflow attempt to land repo-local implementation tooling: today such proposals must spread across four spec files because none of them is the right home; tomorrow they land in non-functional-requirements.md.

### Proposed Changes

Two sections of `SPECIFICATION/templates/livespec/spec.md` and one section of `SPECIFICATION/templates/livespec/constraints.md` MUST change. No content migration MUST occur in this propose-change.

### `SPECIFICATION/templates/livespec/spec.md` — `## Template root layout` section

At the end of the existing paragraph, the spec MUST add a forward reference to the new section: "See §\"Non-functional-requirements file\" below for the new sixth member of the seedable spec-file set."

### `SPECIFICATION/templates/livespec/spec.md` — new section `## Non-functional-requirements file`

The spec MUST add a new top-level section reading:

> The `livespec` template MUST seed a `non-functional-requirements.md` spec file alongside `spec.md`, `contracts.md`, `constraints.md`, and `scenarios.md`. The file holds the project's non-functional requirements: dev-environment invariants, repository tooling, build and test discipline, contributor workflow, and other internal-facing concerns that are NOT visible at the user-facing CLI/API surface.
>
> The file MUST open with a "Boundary" section (or equivalent preamble) clarifying which content belongs in `non-functional-requirements.md` versus `spec.md`, `contracts.md`, `constraints.md`, and `scenarios.md`, so future contributors land new material in the correct file.
>
> The seed prompt MUST author the boundary preamble at seed time. Beyond the preamble, the seed prompt MAY surface project-specific non-functional requirements derived from the user's intent.

### `SPECIFICATION/templates/livespec/constraints.md` — `## Spec-file-set well-formedness` section

The required file set MUST widen from `{README.md, spec.md, contracts.md, constraints.md, scenarios.md}` to `{README.md, spec.md, contracts.md, constraints.md, non-functional-requirements.md, scenarios.md}`. The doctor static-phase `template-files-present` check MUST treat `non-functional-requirements.md` as required and MUST fail when it is missing.

### `SPECIFICATION/templates/livespec/constraints.md` — new section `## Non-functional-requirements scope`

The constraints file MUST add a new top-level section reading:

> `non-functional-requirements.md` content covers dev-environment and contributor-facing requirements only. The boundary against the other spec files is:
>
> - User-facing intent and behavior MUST stay in `spec.md`.
> - User-facing wire contracts MUST stay in `contracts.md`.
> - Constraints whose violation an end user could observe MUST stay in `constraints.md`. Examples: Python runtime version, end-user dependency envelope, exit-code contract, structured-logging schema, vendored-library discipline (because vendoring affects shipped artifacts).
> - Constraints that bind only the project's contributors MUST move to `non-functional-requirements.md`. Examples: linter and formatter rules, code-coverage targets, complexity thresholds, comment discipline, hook configuration, enforcement-suite invocation, repo-local task tracking, contributor commit discipline.
>
> Doctor static-phase `template-files-present` check MUST treat `non-functional-requirements.md` as required and MUST fail when it is missing.

### Boundary preamble — seed-time content for the new file

The new `non-functional-requirements.md` file SHOULD open with the following boundary preamble when the template is seeded into a fresh project (subject to per-project authoring during the seed step):

> # Non-functional requirements
>
> This file declares the project's non-functional requirements: invariants on the development environment, repository tooling, build and test discipline, contributor workflow, and any other internal-facing concerns that are NOT visible at the user-facing CLI/API surface.
>
> ## Boundary
>
> `non-functional-requirements.md` covers concerns of the form "how the project is built, tested, and maintained" — for example: Test-Driven Development discipline, linter and formatter rules, code-coverage targets, complexity thresholds, enforcement suites, hook configuration, repo-local task tracking, dev-environment tool pinning, and contributor onboarding.
>
> It does NOT cover:
>
> - User-facing intent or behavior (`spec.md`)
> - User-facing wire contracts (`contracts.md`)
> - Constraints on the running shipped system that an end user could observe — runtime versions, exit-code contracts, dependency envelopes, structured-logging schemas (`constraints.md`)
> - User-facing scenarios (`scenarios.md`)
>
> The trickiest boundary is `constraints.md` ↔ `non-functional-requirements.md`: constraints whose violation an end user could observe MUST stay in `constraints.md`; constraints that bind only the project's contributors MUST move to `non-functional-requirements.md`.

### Companion code and asset changes (out of scope for this propose-change; land in the same PR)

The following changes are NOT part of this propose-change because they are code and asset edits, not spec content. They MUST land in the same PR as this revision:

- A seed-time scaffolding stub at `.claude-plugin/specification-templates/livespec/specification-template/SPECIFICATION/non-functional-requirements.md` carrying the boundary preamble.
- An update to the seed prompt at `.claude-plugin/specification-templates/livespec/prompts/seed.md` to author the new file at seed time per the boundary discipline.
- An update to the doctor `template-files-present` check (or whatever enumerates the spec-file-set) to include `non-functional-requirements.md`.
- Any tests pinning the seed-time file-set or per-template fixtures MUST update to include the new file.

### Out of scope for this propose-change

This propose-change MUST NOT migrate any existing content from `SPECIFICATION/spec.md` or `SPECIFICATION/constraints.md` into `non-functional-requirements.md`. That migration is a separate atomic propose-change that follows once this one lands.

This propose-change MUST NOT add `SPECIFICATION/non-functional-requirements.md` to the main spec tree. The main-tree file creation happens at the start of the migration propose-change, since revise cannot create new files (the schema requires existing targets).
