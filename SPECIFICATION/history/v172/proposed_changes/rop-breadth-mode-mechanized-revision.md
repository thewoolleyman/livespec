---
proposal: rop-breadth-mode-mechanized.md
decision: accept
revised_at: 2026-07-22T21:47:38Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Aligns SPECIFICATION/non-functional-requirements.md with the enforcement shipped by livespec-dev-tooling PR #516 (merged 2be20e19): check-no-except-outside-io is now breadth-aware and mechanically requires a closed-set marker on a broad main()-boundary catch. Applies the five byte-exact replacement spans (EDIT 1/2/3 in the ROP composition bullets; EDIT 4a/4b re-deriving the Supervisor discipline enforcement-split paragraph). Cleared the mandatory independent Fable review NO-BLOCKERS after a redraft that fixed three prior blockers (closed-set presence is mechanized not review-enforced; the 673 drift; and not ratifying the check's over-flagging of sanctioned loop-iteration/foreign-code catches as spec offenses). No ## heading is added, removed, or renamed, so tests/heading-coverage.json is not co-edited.

## Resulting Changes

- non-functional-requirements.md
