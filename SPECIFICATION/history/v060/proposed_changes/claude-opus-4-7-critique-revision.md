---
proposal: claude-opus-4-7-critique.md
decision: accept
revised_at: 2026-05-10T21:51:45Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

User-confirmed accept of all three proposals as drafted. The three edits to spec.md land coherently as a unit and are all real cross-section/cross-file inconsistencies surfaced by claude-opus-4-7's critique. (1) Adds `seed` to the opening-sentence except-list at section 'Sub-command lifecycle' line 72, resolving the direct contradiction between the opening sentence and the per-sub-command bullets that exempt seed from pre-step. The rewrite preserves the bullet list as the authoritative per-sub-command applicability table and introduces no new constraint not already in the bullets, per the proposal's normative requirements. (2) Rewrites the snake_case `resolve_template` token on the same opening sentence to kebab-case `resolve-template`, matching the convention used in contracts.md section 'Wrapper CLI surface' and section 'Plugin distribution' and the surrounding `propose-change` / `prune-history` wrapper sub-command names. (3) Splits the ~600-word single-sentence section 'revise skill-prose responsibilities' paragraph into a six-bullet list with the closing prose preserved verbatim; every normative obligation from the original sentence is preserved (LLM-driven per-proposal acceptance dialogue framing, accept/modify/reject decision-and-rationale capture, `modify` iteration to convergence, apply-to-all-remaining toggle, steering-intent warn-and-proceed, stale-pending-proposal narration with all its non-gating qualifiers, retry-on-exit-4, the `bin/revise.py` MUST-NOT closing, and the constraints.md cross-reference). All three changes are encoded into a single combined resulting_files entry for spec.md so they apply atomically as one vNNN cut.

## Resulting Changes

- spec.md
