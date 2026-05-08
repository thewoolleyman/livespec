---
proposal: codex-dogfood-compatibility.md
decision: modify
revised_at: 2026-05-08T07:55:53Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Proposal predates the v053 NFR boundary migration. Modifying to re-target all 4 sections (spec.md, contracts.md, constraints.md, scenarios.md) to non-functional-requirements.md under the 4 mirror sub-sections (## Spec, ## Contracts, ## Constraints, ## Scenarios). All content is contributor-facing Codex dogfooding for repository maintainers — end users of livespec don't invoke /livespec:* through Codex; they use Claude Code. Content preserved verbatim; only heading levels demote (H2 → H3) and gherkin scenarios drop their fenced blocks per the NLSpec gherkin-blank-line convention.

## Modifications

Re-targeted from the proposal's original main-spec placement (spec.md, contracts.md, constraints.md, scenarios.md) to `non-functional-requirements.md` under the 4 mirror sub-sections per the v053 NFR boundary. The proposal predates v053 (filed 2026-05-07T10:03:00Z, before NFR migration at 2026-05-08T03:17:18Z); all content is contributor-facing dogfooding (end users of livespec don't use Codex to invoke /livespec:* — they use Claude Code), so the entire proposal lands in NFR.

**Re-targeting map:**

- Original spec.md §"Codex dogfooding compatibility" → NFR ## Spec ### Codex dogfooding compatibility
- Original contracts.md §"Codex dogfooding contracts" → NFR ## Contracts ### Codex dogfooding contracts
- Original constraints.md §"Codex dogfooding constraints" → NFR ## Constraints ### Codex dogfooding constraints
- Original scenarios.md §"Codex dogfooding scenarios" → NFR ## Scenarios (5 ### Scenario sub-sections, populating the previously-empty Scenarios section)

**Content preserved verbatim:**

- All BCP14 normative language, command-mapping tables, verification command lists, and scenario steps are byte-identical to the original proposal.
- Heading levels demote from H2 to H3 (and existing H3+ within scenario bodies stays the same since scenarios in the proposal were embedded under H2 with no inline H3).
- The scenario fenced-gherkin blocks from the proposal are unfenced per the gherkin-blank-line convention pinned in `constraints.md` §"Heading taxonomy" / NLSpec discipline.

**No content additions or removals beyond the mirror restructuring.**

**Out of scope (proposal §"Non-goals" — separate follow-up commits/PRs):**

- Creating `.agents/skills/*` symlinks (file-creation work; the spec only declares they MUST exist).
- Authoring the `AGENTS.md` Codex command-mapping tables (file-creation work).
- Codex-native plugin marketplace registration (the spec explicitly says NOT to claim that).

**Coordinates with `implementation-workflow-on-non-functional-requirements`:**

The Codex dogfooding constraints and scenarios reference `livespec-implementation`. That implementation-workflow refile is filed but not yet revised. The Codex content's references are CONDITIONAL ("if the project-local livespec-implementation plugin exists, AGENTS.md MUST also map..."), so they hold whether or not the implementation-workflow revise has landed yet.


## Resulting Changes

- non-functional-requirements.md
