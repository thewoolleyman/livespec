---
topic: inherit-dev-tooling-contracts
author: claude-opus-5-5:implement-test-performance
created_at: 2026-11-13T01:25:48Z
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
