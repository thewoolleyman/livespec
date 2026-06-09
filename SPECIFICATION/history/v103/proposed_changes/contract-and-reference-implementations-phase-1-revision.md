---
proposal: contract-and-reference-implementations-phase-1.md
decision: accept
revised_at: 2026-06-09T22:34:05Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accepted as written. All seven naming/architecture calls were decided by the user on 2026-06-09 and are inlined in the proposal as a normative decision record, so the proposal is fully adjudicated: LiveSpec becomes a contract plus reference implementations; core is agnostic to both the Driver and the orchestrator; the cross-boundary contract becomes the three config-named orchestrator CLIs (spec-reader, gap-capture, drift-capture) plus the config-named, individually-overridable spec-side CLIs; doctor's cross-boundary job shrinks to the single config-named-cli-callability invariant; work-item, dependency-graph, and store machinery relocate out of core (pin-and-bump to the family/dev-tooling coordination surface, cross_repo_targets split between orchestrator and family surface); and the Layer-3 surface retires with its loop discipline preserved as non-normative orchestrator-internal Dispatcher guidance. Resulting files additionally carry the mechanical cross-reference fallout in constraints.md (the Cross-boundary doctor static checks paragraphs and retired vocabulary) and the tests/heading-coverage.json co-edit required by the Self-application discipline for the H2 set changes (one rename in spec.md; four removals and four additions in contracts.md).

## Resulting Changes

- spec.md
- contracts.md
- non-functional-requirements.md
- constraints.md
- ../tests/heading-coverage.json
