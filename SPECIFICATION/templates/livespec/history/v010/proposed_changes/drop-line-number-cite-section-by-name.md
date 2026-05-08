---
topic: drop-line-number-cite-section-by-name
author: claude-opus-4-7
created_at: 2026-05-08T17:49:46Z
---

## Proposal: Drop line-number reference; cite by section name only

### Target specification files

- SPECIFICATION/templates/livespec/contracts.md

### Summary

Replace the `SPECIFICATION/constraints.md §"Heading taxonomy" line 47` cross-reference with a section-name-only reference. The line number was already wrong when the proposal was filed (Heading taxonomy was at constraints.md line 644 then) and is now even more stale post-v053 (Heading taxonomy is at constraints.md:211 after the dev-process content migrated to non-functional-requirements.md). Refile of doctor-critique deferred sub-proposal #9.

### Motivation

Hard-coded line numbers in spec cross-references bit-rot quickly across revise cycles. The v053 main-spec migration moved 14 sections out of constraints.md, shifting every subsequent line offset; the cited `line 47` now points at content under §"Vendored-library discipline" rather than §"Heading taxonomy". The proposal recommends establishing a general pattern: cite spec sections by §"<heading text>" rather than by line number throughout the spec tree.

### Proposed Changes

In `SPECIFICATION/templates/livespec/contracts.md`, the `headings_derived_from_intent` bullet currently reads `aligns with SPECIFICATION/constraints.md §"Heading taxonomy" line 47 which pins intent-derivation to level 1`. The phrase ` line 47` MUST be removed; the bullet MUST read `aligns with SPECIFICATION/constraints.md §"Heading taxonomy" which pins intent-derivation to level 1`. The general pattern this establishes — cite spec sections by §"<heading text>" rather than by line number — applies repo-wide; future spec edits MUST follow the same convention. No other content changes.
