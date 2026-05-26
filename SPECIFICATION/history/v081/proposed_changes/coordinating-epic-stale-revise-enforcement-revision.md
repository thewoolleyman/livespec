---
proposal: coordinating-epic-stale-revise-enforcement.md
decision: accept
revised_at: 2026-05-26T07:41:09Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accept the whole coordinating-epic-stale-revise-enforcement file (all 4 sub-proposals, file-level accept). Wave 0 cleared the stale spec/* branches that would have tripped Layer 1's own precondition. The four sub-proposals land together as the cross-cutting contract surface for the family-wide "work must reach master" guarantee:
(1) introduce optional parent_proposed_change front-matter field (documented in spec.md §"Proposed-change and revision file formats"; schema widening at proposed_change_front_matter.schema.json is filed as impl follow-up);
(2) Layer 1 (refuse /livespec:revise while stale spec/* branches exist) lands as prose contract here; SKILL.md edit at .claude-plugin/skills/revise/SKILL.md is filed as impl follow-up (matches the v079 doctor-uniform-per-finding-disposition pattern: SKILL.md regeneration tracks separately because resulting_files[] cannot reach skill files cleanly);
(3) Layer 2 (auto-enable-merge.yml required across every livespec-sibling repo) lands as a new §"Auto-enable-merge workflow" subsection under contracts.md §"Cross-repo coordination — pin-and-bump" (no H2 set change; tests/heading-coverage.json unchanged);
(4) Layer 3' (doctor LLM-driven phase surfaces open spec-PR status) lands as cross-cutting acceptance — doctor SKILL.md edit + new prompt file at specification-templates/livespec/prompts/doctor-llm-objective-checks.md + template.json field set are filed as impl follow-ups (the prompt file does not yet exist; revise's resulting_files[] cannot create new files).
The retroactive parent_proposed_change annotation of the inaugural epic (this PC + two children in sibling repos) is documented in the PC body as a follow-up admin commit, not part of this revise.

## Resulting Changes

- spec.md
- contracts.md
