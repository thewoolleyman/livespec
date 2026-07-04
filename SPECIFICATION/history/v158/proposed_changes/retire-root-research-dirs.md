---
topic: retire-root-research-dirs
author: claude-fable-5
created_at: 2026-07-04T00:48:58Z
---

## Proposal: Retire the root research/ tree from Planning Lane guidance

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Amend two sentences in non-functional-requirements.md §'Planning Lane guidance' that direct standalone analysis and living-reference research files to a root research/ tree. The fleet retires root research/ directories entirely (epic livespec-gt7crt, maintainer directive 2026-07-04): standalone analysis lives in a plan thread or the archive, and a living reference doc lives in docs/ or .ai/. The H2 heading set is unchanged.

### Motivation

Maintainer directive (2026-07-04, retire-research-dirs thread, epic livespec-gt7crt): after this epic no fleet repo (nor the openbrain adopter) carries a root research/ directory. This supersedes the cleanup-research-and-prompt-cruft (epic livespec-ztepy5) end-state that deliberately kept runtime-referenced docs in research/. The two Planning Lane guidance sentences are the only spec text that names the root research/ tree as a living destination; they must be revised before (or atomically with) the moves that de-reference the tree, per the epic's execution-order constraint.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §'Planning Lane guidance', two sentence-level replacements with no heading changes:

1. In the '**The planning thread.**' paragraph, replace the final sentence 'The broader `research/` tree stays for standalone analysis that is not an active planning thread.' with: 'Standalone analysis that is not an active planning thread lives in a plan thread of its own or in the archive; no repo carries a root-level research tree for it.'

2. In the '**Archive on epic close.**' paragraph, replace '; to keep a research file as living reference, copy it to `research/` deliberately.' with: '; to keep a research file as living reference, relocate it deliberately to a living home (`docs/` or `.ai/`), never to a root-level research tree, which the fleet does not carry.'
