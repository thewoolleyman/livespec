---
topic: retire-workflow-processes-split-mandate
author: claude-fable-5
created_at: 2026-07-03T08:01:12Z
---

## Proposal: Retire the research/workflow-processes/ split mandate

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Remove the H3 section §"research/workflow-processes/ tool-agnostic vs implementation-specific split" (under ## Constraints) in full. The section mandates that the research/workflow-processes/ directory host two structurally separate artifacts (tool-agnostic-workflow.md as source of truth; architecture-summary.html as the livespec-specific rendering). The mandate is obsolete: the living tool-agnostic view now resides in spec.md §"Tool-agnostic workflow — spec / implementation lifecycle" (authored by the accepted v151 tool-agnostic-workflow-diagram proposal, which re-authored the stale SVG into the spec itself), and the mandated research artifact is frozen at the retired memo paradigm (76 stale `memo` mentions; memo retired at v123). This is an H3 removal only — the file's H2 heading set is unchanged, so no tests/heading-coverage.json co-edit is required. No replacement clause is inlined: the still-true content (the tool-agnostic lifecycle view) already lives in spec.md.

### Motivation

cleanup-research-and-prompt-cruft epic (fleet anchor livespec-ztepy5; livespec child livespec-kg6paq), Phase 2 CONFIRMED verdict: the research/workflow-processes/ tree is SPEC-ABSORB — retire the spec mandate first, then archive the whole directory under archive/research/workflow-processes/. The mandate's artifacts stopped being maintained when the memo paradigm was retired (v123) and were superseded as the tool-agnostic source of truth by the v151 spec.md diagram section; keeping a MUST that forces contributors to maintain a stale, memo-era research artifact contradicts the actual architecture. Evidence: plan/cleanup-research-and-prompt-cruft/research/02-dispositions-livespec.md.

### Proposed Changes

The section §"research/workflow-processes/ tool-agnostic vs implementation-specific split" MUST be removed from SPECIFICATION/non-functional-requirements.md in full — the H3 heading and its single body paragraph — leaving the surrounding ## Constraints subsections (§"Developer-tooling layout" before it, §"Package layout" after it) unchanged and separated by a single blank line. No replacement clause is added: the tool-agnostic workflow view's living, normative home is spec.md §"Tool-agnostic workflow — spec / implementation lifecycle" (v151), and the archived research artifacts remain reachable under archive/research/workflow-processes/ and in git history. The file's H2 heading set MUST remain unchanged (the removal is an H3), so tests/heading-coverage.json is deliberately not co-edited.
