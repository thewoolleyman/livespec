---
proposal: template-manifest-additional-files.md
decision: accept
revised_at: 2026-05-18T16:10:16Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

User-directed accept-as-drafted of the template-manifest-additional-files proposal (filed 2026-05-17 by claude-opus-4-7). Codifies the manifest mechanism, per-kind behavior axes, rendering lifecycle integration, transactional revise semantics, multi-diagram-per-source accommodation, schema v1→v2 versioning, heading-coverage rewiring obligation, new diagram-source/rendered drift check, explicitly-rejected alternatives, and the renderer-non-vendoring + render-command trust-boundary constraints across spec.md, contracts.md, and constraints.md. The new §"Template manifest" section in spec.md is anchored between §"Specification model" and §"Lifecycle". §"Specification model" is updated with a forward reference. contracts.md adds §"Template manifest wire contract" between §"Skill ↔ template JSON contracts" and §"Sub-spec structural mechanism". constraints.md adds §"Renderer non-vendoring" between §"Vendored-library discipline" and §"Exit code contract". The Python schema bump + heading-coverage rewiring + new doctor drift check are impl follow-ups for subsequent commits/PRs; this revise records the contract only per the architecture-vs-mechanism discipline.

## Resulting Changes

- spec.md
- contracts.md
- constraints.md
