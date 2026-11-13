---
topic: inherit-dev-tooling-contracts
author: claude-opus-5-5:implement-test-performance
created_at: 2026-11-13T02:10:39Z
---

## Proposal: Inherit livespec-dev-tooling's contracts.md by declaration

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Add one H2, `## Inherited from livespec-dev-tooling`, to SPECIFICATION/constraints.md, immediately after `## Constraint scope`, before `## Non-interactive execution`. Its body is exactly one sentence on a single line, declaration form one of livespec-orchestrator-beads-fabro SPECIFICATION/contracts.md (ratified v362) quoted verbatim: "Every constraint in `livespec-dev-tooling/SPECIFICATION/contracts.md` applies to this plugin without restatement." This plugin already consumes livespec-dev-tooling's shared checks and contracts at its pin, and the declaration makes that inheritance explicit, so the orchestrator's spec-stated judgement reads livespec-dev-tooling/SPECIFICATION/contracts.md as part of this repository's specification text.

### Motivation

Orchestrator spec v362 (livespec-orchestrator-beads-fabro#5031, ratified 2026-11-12 as 8eae5b181) makes the spec-stated judgement select from the governed repository's ratified tree TOGETHER WITH each inherited specification file. A file is inherited only when this repository's constraints.md declares it by one of two closed forms; a citation or cross-reference adds nothing. Measured 2026-11-11: 7 of 22 held items were already stated by the ratified specification, some only through an inherited file the selection never read. Until this repository declares livespec-dev-tooling's contracts.md, a work item whose asked-for behaviour that file states is judged against a specification that omits it. Filed under plan implement-test-performance (epic livespec-dev-tooling-sv6m5p) on legacy-coordinator-agent's grade of the seven-repository batch, 2026-11-13.

### Proposed Changes

Insert, in SPECIFICATION/constraints.md, immediately after `## Constraint scope`, before `## Non-interactive execution`:

```markdown
## Inherited from livespec-dev-tooling

Every constraint in `livespec-dev-tooling/SPECIFICATION/contracts.md` applies to this plugin without restatement.
```

The sentence MUST stay verbatim and on ONE line, because the declaration forms are matched as sentences: `<path>` is `livespec-dev-tooling/SPECIFICATION/contracts.md` (relative to the directory holding the sibling clones) and `<scope>` is `plugin`. No other text changes. The revise that accepts this proposal adds a `tests/heading-coverage.json` row for the new H2 in the same commit (a `test: "TODO"` row naming its tier and owning `work_item`, registered in the heading-coverage debt register where this repository keeps one), per the revise co-edit discipline.

## Proposal: Inheritance declarations are an authorized exception to the cross-tree reference ban

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Add a subsection, `### Inheritance declarations (authorized exception)`, to §"Reference discipline" in SPECIFICATION/constraints.md, immediately after `### Design-record citations (authorized exception)`, and name it in the opening sentence of `### Forbidden: references OUTSIDE the same \`SPECIFICATION/\` tree` beside the design-record exception. A constraints.md sentence in one of the two closed inheritance-declaration forms names a sibling-repo specification file by path, which that section otherwise forbids. Without this exception the first proposal of this file, and every existing Driver's `## Inherited from livespec` declaration, contradicts it.

### Motivation

legacy-coordinator-agent's batch grade of this proposal (2026-11-13) found that §"Reference discipline" forbids a SPECIFICATION file from referencing `livespec-dev-tooling/SPECIFICATION/...` except through the allowlist or a design-record citation, while a form-one declaration names exactly that path. A declaration is not a citation a reader must follow to understand this tree; it states which other tree's constraints apply here. The rule's purpose, standalone readability against reference rot, is better served by stating the exception than by leaving every governed repository's inheritance declaration in apparent violation.

### Proposed Changes

1. In `### Forbidden: references OUTSIDE the same \`SPECIFICATION/\` tree`, change the opening sentence's exception list from "EXCEPT via the allowlist mechanism in §\"Allowlist mechanism\" or — for design-record citations only — the authorized exception in §\"Design-record citations (authorized exception)\"" to "EXCEPT via the allowlist mechanism in §\"Allowlist mechanism\", the authorized exception for design-record citations in §\"Design-record citations (authorized exception)\", or the authorized exception for inheritance declarations in §\"Inheritance declarations (authorized exception)\"".

2. Insert after `### Design-record citations (authorized exception)`:

```markdown
### Inheritance declarations (authorized exception)

An **inheritance declaration** is a sentence in a `constraints.md` that states that another repository's specification file applies to this tree, in exactly one of two forms, where `<path>` is the inherited file's path beginning with the owning repository's directory name and `<scope>` is one of `plugin`, `library` or `application`: "Every constraint in `<path>` applies to this <scope> without restatement." or "Every constraint in `<path>` that applies to a Driver binding applies here unmodified; this tree does not relax or restate them.". An inheritance declaration is an authorized exception to the prohibition on naming sibling-repo specification files, and needs no allowlist entry. It declares which constraints govern this tree; it is not a citation a reader must follow to resolve this tree's own text. The exception is narrow: it covers the two declaration sentences ONLY, never a `§"…"` heading reference, which stays governed by §"Allowlist mechanism", and never any other mention of a sibling-repo path.
```

No other text changes. The revise that accepts this proposal adds a `tests/heading-coverage.json` row only if it adds an H2; this change adds an H3 under an existing H2, so it owes none.
