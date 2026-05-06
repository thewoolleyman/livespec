---
topic: catalogue-heading-level-fix
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T00:15:03Z
---

## Proposal: Catalogue heading-level typo: ## → #

### Target specification files

- SPECIFICATION/templates/livespec/contracts.md

### Summary

Correct the catalogue rule at SPECIFICATION/templates/livespec/contracts.md line 20 from `##` to `#`. The current text ("top-level `##` headings within each spec file from intent nouns") is a typo: `##` is by definition not top-level; `#` is. The corrected rule aligns with SPECIFICATION/constraints.md line 47 ("Top-level `#` headings in spec files SHOULD reflect intent rather than a fixed taxonomy").

### Motivation

Discovered during Phase 7 sub-step (c) prep on 2026-05-06: the seed-prompt catalogue's `##` heading-derivation rule contradicted the actual seeded SPECIFICATION/spec.md (which uses fixed-taxonomy `##` section headings like "Project intent", "Runtime and packaging", etc. under a single `# Spec` H1). The seeded spec.md is internally consistent: its `# Spec` H1 reflects livespec's intent (the spec lifecycle), and its `##` headings are section organizers (out of scope for the top-level rule). The catalogue's `##` was the mismatch — a one-character typo where the rule's scope (top-level) and the heading level (`##`) are definitionally incompatible. The corrected rule (`#`) is consistent with constraints.md line 47, with PROPOSAL.md line 1587 ("spec.md: top-level headings derived from the seed intent"), and with the seeded spec.md as-authored. No downstream impact on per-prompt regeneration cycles — the corrected rule preserves the `# Spec`-style top-level intent-derivation contract that the seed-prompt template already produces.

### Proposed Changes

One atomic edit to **SPECIFICATION/templates/livespec/contracts.md** §"Per-prompt semantic-property catalogue → prompts/seed.md" line 20:

Replace:

> The prompt MUST derive top-level `##` headings within each spec file from intent nouns, NOT from a fixed taxonomy. (Asserts the v020 Q4 starter-content policy.)

with:

> The prompt MUST derive top-level `#` headings within each spec file from intent nouns, NOT from a fixed taxonomy. (Asserts the v020 Q4 starter-content policy; aligns with SPECIFICATION/constraints.md §"Heading taxonomy" line 47 which pins intent-derivation to level 1.)

