---
topic: retire-dogfooding-subspecs
author: claude-opus-4-8
created_at: 2026-06-24T12:38:30Z
---

## Proposal: Retire dogfooding sub-specs; relocate built-in template contracts

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/README.md
- SPECIFICATION/spec.md
- SPECIFICATION/scenarios.md

### Summary

Retire the two dogfooding sub-spec trees SPECIFICATION/templates/livespec/ and SPECIFICATION/templates/minimal/, KEEPING the sub_specs/--spec-target/multi-tree feature itself. The sub-spec trees were ~90% redundant narrative restating the main spec; the ~5 unique template-internal contracts that lived only there are consolidated into one new '## Built-in template contracts' section in contracts.md. The remaining main-spec edits genericize the few illustrative references to livespec's own two trees so the multi-tree feature scenario and structural mechanism survive without asserting livespec's own current state.

### Motivation

The dogfooding sub-spec trees were authored to exercise the multi-tree sub_specs feature on livespec itself, but they have drifted into mostly redundant restatement of the main spec, carry their own history/ snapshots, and bloat the spec tree. The genuinely unique residue is a small set of template-internal contracts (the livespec template's NLSpec reference doc and doctor LLM prompt paths; the minimal template's single-file SPECIFICATION.md shape, null doctor LLM prompts, HTML-comment region markers, and gherkin blank-line exemption). Those belong in the main contracts.md as first-class contracts; everything else is safe to drop. The multi-tree FEATURE stays.

### Proposed Changes

1. contracts.md: ADD a new '## Built-in template contracts' section immediately after '## Template manifest wire contract' and before '## Sub-spec structural mechanism', consolidating the ~5 unique template-internal contracts that previously lived only in the sub-specs (livespec template: NLSpec reference doc, doctor LLM objective/subjective prompt paths; minimal template: single-file SPECIFICATION.md shape with spec_root './', null doctor LLM prompt opt-out, HTML-comment region markers, gherkin blank-line-format exemption).
2. contracts.md: §'Sub-spec structural mechanism' — genericize the illustrative --spec-target path from the livespec template's own sub-spec to a generic '<name>' sub-spec tree.
3. README.md: DELETE the sentence describing templates/livespec/ and templates/minimal/ as sub-spec trees (the directories no longer exist).
4. spec.md: §'Self-application' — drop the parenthetical pointing mutations at the two sub-spec trees under templates/, so the rule ends at 'against this tree.'
5. scenarios.md: 'Happy-path doctor' — reframe the Given + Then from livespec's own two trees to a generic multi-tree project so the cross-tree FEATURE scenario survives without asserting livespec's current state.
6. (out of band, paired with this revise) tests/heading-coverage.json: add one TODO entry for the new contracts.md heading and remove the 46 entries whose spec_root is SPECIFICATION/templates/livespec or SPECIFICATION/templates/minimal.
The two orphaned sub-spec trees are removed structurally outside the propose-change/revise loop (plain git rm), along with repointing the two live citations that pointed at the deleted sub-specs.
