---
proposal: declare-livespec-dev-tooling-shared-code-mechanism.md
decision: accept
revised_at: 2026-05-21T05:04:03Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

All three findings are accepted as authored. The proposal partitions livespec's shared-content channels along the static-vs-executable axis (copier for scaffolds, livespec-dev-tooling for code), generalizes pin-and-bump to cover sibling libraries identically to impl-plugins, and updates the non-functional-requirements provenance section so both channels are codified. The amendments resolve the structural gap surfaced by the 2026-05-20 just-bootstrap failure in livespec-impl-plaintext (epic li-fgqgnk) without introducing new mechanisms - the compat block schema, the bump-pin PR shape, and the additive-breaking-change rule are unchanged in substance, and only the consumer enumeration widens. Co-edit: a new heading entry for `## Shared code sync - livespec-dev-tooling` is added to tests/heading-coverage.json per the self-application discipline so the heading-coverage doctor check stays in lockstep with the spec.

## Resulting Changes

- contracts.md
- non-functional-requirements.md
- ../tests/heading-coverage.json
