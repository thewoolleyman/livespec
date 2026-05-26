---
proposal: reference-discipline-invariant.md
decision: accept
revised_at: 2026-05-26T05:59:02Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Lands the new ## Reference discipline section in constraints.md between ## Heading taxonomy and ## BCP14 normative language as proposed. The two paired invariants (SPECIFICATION/ tree cannot reference outside content except via an external_references allowlist in .livespec.jsonc; source code cannot cite spec sections via §"…") have clean scope discipline: the spec change documents the rule; the static-check implementation (livespec/doctor/static/no_cross_spec_reference.py + no_spec_section_citation_in_code.py + paired tests + retroactive sweep + .livespec.jsonc allowlist population) is explicitly punted to a follow-up work-item per the proposal's own spec-vs-impl partition. tests/heading-coverage.json gets a TODO entry for the new ## heading.

## Resulting Changes

- constraints.md
- ../tests/heading-coverage.json
