---
topic: doctor-critique-lifecycle-restructure
author: claude-opus-4-7
created_at: 2026-05-08T17:58:52Z
---

## Proposal: Restructure spec.md §Sub-command lifecycle per template content-role separation

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

Refile of doctor-critique deferred sub-proposals #5 (move wire-level + mechanism content out of spec.md §Sub-command lifecycle), #6 (promote bold-inline subheadings to ### subheadings), #7 (reorder spec.md so Lifecycle moves earlier). #8 (split §Sub-command lifecycle into multiple top-level sections) is obviated by #5+#6 — the trimmed section is small enough to stay as one coherent top-level section. Per the livespec-template content-role separation: spec.md content addresses project intent and high-level architecture; contracts.md content is wire-level / CLI-level; constraints.md content is architecture-level constraints.

### Motivation

Template-compliance findings originally surfaced by the doctor LLM-driven subjective phase and deferred during the v055 livespec-doctor-critique modify-revise as 'substantial restructuring requiring coordinated effort'. Coordination resolved here by landing #5, #6, #7 together with #8 obviated. The current spec.md §Sub-command lifecycle violates the role separation across multiple subsections: payload validation rules (wire-level), file-shaping clauses (mechanism), structured error envelope mechanics (wire-level), and pre-step skip control (wire-level + mechanism) all live in spec.md instead of contracts.md and constraints.md. The current ordering also forces readers to absorb extensive lifecycle, versioning, and tooling rules before seeing the high-level revision-loop diagram that motivates them.

### Proposed Changes

Three coordinated changes:

**#5 — Move wire-level and mechanism content out of `spec.md` §Sub-command lifecycle.**

Wire-level paragraphs MUST move to a new `contracts.md` ## Sub-command wire contracts section, organized as 5 ### sub-sections:

- ### `critique` payload validation
- ### `critique` internal delegation
- ### `revise` payload validation
- ### `revise` resulting_files path-relativity guard
- ### Pre-step skip control

Mechanism content (file-shaping clauses, doctor static check definition, no-op short-circuit details) MUST move to a new `constraints.md` ## Sub-command lifecycle mechanics section, organized as 3 ### sub-sections:

- ### `revise` file-shaping mechanics (the wrapper's clauses (a)-(h))
- ### `prune-history` file-shaping mechanics (the wrapper's clauses (a)-(e) plus the two no-op short-circuits (i)/(ii))
- ### `accept-decision-snapshot-consistency` doctor static check

Skill-prose responsibilities for `revise` and `prune-history` MUST STAY in `spec.md` §Sub-command lifecycle as new ### sub-sections (`### revise skill-prose responsibilities`, `### prune-history skill-prose responsibilities`), each cross-referencing the constraints.md mechanics section for the wrapper's deterministic file-shaping.

**#6 — Promote bold-inline subheadings to ### subheadings.**

The two remaining bold-inline subheadings in `spec.md` §Sub-command lifecycle (the `**revise lifecycle and responsibility separation.**` paragraph header and the `**prune-history lifecycle and responsibility separation.**` paragraph header) MUST become proper ### subheadings under the now-trimmed §Sub-command lifecycle. The other bold-inline subheadings (critique payload validation, critique internal delegation, revise payload validation, revise resulting_files path-relativity guard, accept-decision-snapshot-consistency static check, pre-step skip control) move out entirely with their paragraph content per #5 and become ### subheadings in their respective destination files.

**#7 — Reorder `spec.md`.**

`## Lifecycle` (with the revision-loop mermaid diagram + nested `### Terminology` subsection) MUST move from its current position (between `## Non-goals` and `## Prior Art`) to immediately after `## Specification model`, before `## Sub-command lifecycle`. The new top-of-spec reading order MUST be: Project intent → Runtime and packaging → Specification model → Lifecycle → Sub-command lifecycle → Versioning → Pruning history → Proposed-change and revision file formats → Author identifier resolution → Non-goals → Prior Art → Subdomain routing → Self-application. Heading text and content within each section MUST remain unchanged; only ordering changes.

**#8 — Obviated.**

After #5 + #6, `spec.md` §Sub-command lifecycle shrinks to the intent layer (sub-command list, applicability table, LLM-driven phase intent, Python composition note, revise/prune-history skill-prose responsibilities). At this size, splitting into `## Sub-command applicability`, `## Lifecycle: critique`, `## Lifecycle: revise`, `## Lifecycle: prune-history`, `## Static check: accept-decision-snapshot-consistency`, `## Pre-step skip control` would over-fragment the trimmed material. The cross-references to contracts.md and constraints.md handle the navigation that #8 was originally trying to solve.

**Companion test-surface change** (out of scope for this propose-change but MUST land in the same revise pass via the resulting_files mechanism): `tests/heading-coverage.json` gains 2 new entries — one for `## Sub-command wire contracts` (contracts.md), one for `## Sub-command lifecycle mechanics` (constraints.md). The existing `## Sub-command lifecycle` entry in spec.md remains. Internal ### sub-sections under the new H2s are NOT tracked (heading-coverage walks H2 only).
