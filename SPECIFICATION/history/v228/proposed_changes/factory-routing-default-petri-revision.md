---
proposal: factory-routing-default-petri.md
decision: accept
revised_at: 2026-10-22T22:18:07Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Maintainer-directed cutover of this repository's factory dispatch to the Petri-era Fabro factory on gmktec (coordinator ruling R668, relayed 2026-10-22: 'priority is getting fabro upgrade done and running on gmktec'; work-item bd-ib-iud52v). The registry already resolves petri. The amendment changes only the default-factory sentence of §"Factory routing" and keeps legacy declared so recorded legacy pins still resolve; the registry-backed rule is unchanged. Independent read-only reviews (opus, the configured ratification reviewer, and Codex gpt-6-astra) both returned NO BLOCKERS and found no other live spec text and no cross-repo citation asserting the legacy default.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-22T22:18:03Z
verdict: NO BLOCKERS
proposal_stem: factory-routing-default-petri
content_digest: 82c710702ec91a2ad24c9cbaf70043fa3b0fe41129e7b475be01993b0455762d
