---
proposal: factory-routing.md
decision: accept
revised_at: 2026-10-20T16:03:37Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted per coordinator rulings R318 and R320 (2026-10-20, answering for the maintainer under R202/R301 authority, plan petri-factory-on-gmktec, epic bd-ib-fyozyd): every fleet repository ratifies the same `## Factory routing` heading so the registry-switch work-item can reference it. Placed in non-functional-requirements.md per its §"Boundary" litmus test, because the rule binds only this repository's own .livespec.jsonc and no governed project inherits it; the preamble and §"Boundary" are amended in the same pass so the sixth top-level section is stated rather than contradicting the five-section description. The heading-coverage row is a TODO owned by livespec-6fb1, mirrored into the debt register.

## Resulting Changes

- non-functional-requirements.md
- ../tests/heading-coverage.json
- ../tests/heading-coverage-debt.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-20T16:03:25Z
verdict: NO BLOCKERS
proposal_stem: factory-routing
content_digest: 2df880b0334c79c10212a0334f1a46a6162ff9a52a9ad2ccc57337f31eeeb06f
