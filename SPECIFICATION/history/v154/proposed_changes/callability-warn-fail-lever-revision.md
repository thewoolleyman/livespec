---
proposal: callability-warn-fail-lever.md
decision: accept
revised_at: 2026-07-02T05:38:25Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accept: reconciles the credential_wrapper callability prose (the config-named-cli-callability invariant paragraph in §"Doctor cross-boundary invariants" + the §"Spec-side CLI contract" parenthetical) with the shipped warn-vs-fail lever in config_named_cli_callability.py (_evaluate: unresolvable credential_wrapper -> warn, present-but-non-executable -> fail). Verified drift; no Gherkin scenario or heading-coverage co-edit needed (the invariant carries no dedicated scenario and no heading set changes). NOTE: contracts.md in resulting_files is the cumulative file that ALSO carries the coverage proposal's §"Python-rule compliance" edit, since both proposals in this revise pass touch contracts.md.

## Resulting Changes

- contracts.md
