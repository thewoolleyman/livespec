---
proposal: seed-prompt-regeneration.md
decision: accept
revised_at: 2026-05-06T00:20:42Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: Claude Opus 4.7 (1M context)
---

## Decision and Rationale

Accept as proposed. The catalogue widening names the 2 existing properties + adds the assertion-function contract paragraph. The in-line widening rule (Plan §3543-3550) is satisfied: this revise lands the catalogue widening; the same commit also lands the regenerated `.claude-plugin/specification-templates/livespec/prompts/seed.md` (Phase-7-final body referencing the catalogue), the updated `tests/prompts/livespec/seed/baseline.json` (with the property names in `expected_semantic_properties` + ships_own_templates+named_templates in input_context), and the populated `tests/prompts/livespec/_assertions.py` (with the 2 assertion functions registered).

## Resulting Changes

- contracts.md
