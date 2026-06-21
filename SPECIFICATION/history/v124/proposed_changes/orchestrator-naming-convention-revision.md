---
proposal: orchestrator-naming-convention.md
decision: accept
revised_at: 2026-06-21T05:03:27Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Maintainer-ratified comprehensive core-spec prose rename: livespec-impl-<X> -> livespec-orchestrator-<ledger>[-<loop>], naming both the ledger and the optional loop axis (a loop is ledger-portable, so it must be nameable, not implied). Reference orchestrators renamed in prose: livespec-impl-beads -> livespec-orchestrator-beads-fabro; livespec-impl-git-jsonl -> livespec-orchestrator-git-jsonl. The livespec core name is preserved (the livespec->livespec-core rename was retired per history/v068). Every forward-looking livespec-impl-* glob, livespec-impl-<X> notation, concrete reference name, and impl-plugin/implementation-plugin class label across non-functional-requirements.md and contracts.md is renamed; the templates/impl-plugin/ copier-directory path token, the implementation.plugin config key, the impl-side concept term, and the livespec-impl-plaintext PR #26 historical incident citation are kept verbatim. No H2 heading changed (verified byte-identical ## sets before/after), so tests/heading-coverage.json is untouched and is NOT in resulting_files. One H3 retitle (Implementation plugin ecosystem -> Orchestrator plugin ecosystem), which heading-coverage does not track. Root S2 of the rename wave (livespec-4moata.4.2).

## Resulting Changes

- non-functional-requirements.md
- contracts.md
