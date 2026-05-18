---
proposal: implementation-plugin-contract-9-skill-surface.md
decision: accept
revised_at: 2026-05-18T21:23:48Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accepting all four `## Proposal:` sections in implementation-plugin-contract-9-skill-surface as one atomic landing per the 2026-05-18 post-orchestration batch's dependency-order plan. The four proposals are mutually reinforcing: (1) thin-transport doctrine establishes the skill-weight terminology and the contract-surface-via-skills rule; (2) the 9-skill impl-plugin contract enumerates the heavyweight + thin-transport skill set every `livespec-impl-*` MUST expose, including cross-boundary handoffs and the backend-variability asymmetry; (3) the spec-side `next` thin-transport skill grows livespec-core's surface from 7 to 8 commands as the spec-side counterpart to the impl-side `next`; (4) the Spec Reader required-capability surface names the four within-plugin capabilities every impl plugin MUST provide for its own skills. Placement: `Thin-transport skill doctrine` lands after the JSON-contracts cluster; the three impl-plugin-side sections land between §"Cross-repo coordination — pin-and-bump" and §"Shared content sync — copier template" to keep the impl-plugin-contract material contiguous; spec.md gains the two new terminology entries and the §"Sub-command lifecycle" updates that add `next` as the 8th sub-command and codify the thin-transport orchestration split. Wording follows research/workflow-processes/architecture-summary.html (Decisions 8, 17, 18) and research/workflow-processes/tool-agnostic-workflow.md (the Thin-transport skill and Spec Reader glossary entries, the §"Cross-boundary contracts" table, and the §"Required thin-transport query skills" section).

## Resulting Changes

- spec.md
- contracts.md
