---
proposal: livespec-doctor-critique.md
decision: modify
revised_at: 2026-05-08T07:24:18Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

The propose-change file aggregates 10 doctor-surfaced sub-proposals across 5 different spec files and 2 different sub-spec trees. Modifying to accept the 4 mechanical small fixes (sub-proposals 1-4 targeting main SPECIFICATION/) lands the immediate corrections; the 4 restructuring sub-proposals (5-8) need a coordinated focused effort with proper sketch-and-approve; the 2 sub-spec-targeting sub-proposals (9-10) cannot apply in a main-spec revise pass and need their own per-sub-spec passes. See modifications field for the per-sub-proposal disposition.

## Modifications

Accepted (4 of 10 sub-proposals): mechanical small fixes targeting main SPECIFICATION/.

1. **Six→seven sub-command count.** spec.md "six sub-commands" → "seven sub-commands" enumerating help. Help row split out from the doctor applicability row to clarify it is a SKILL.md-only sub-command with no Python wrapper.
2. **Prune-history scenario rewrite.** scenarios.md `## Recovery path` rewritten to match the actual prune-history mechanic (no retention-horizon flag; collapses to a single PRUNED_HISTORY.json marker at v(N-1)). Heading renamed from "Recovery path — pruning history before a long retention horizon" to "Recovery path — pruning history".
3. **Wrapper-shape 6→5.** All 8 active "6-statement"/"6 statements"/"six statements" references in non-functional-requirements.md (6 refs) and constraints.md (2 refs) replaced with "5-statement"/"5 statements" framing. The constraints.md substantive edit clarifies "5 top-level AST statements (the shebang is a comment, not a statement)" to disambiguate the AST-vs-textual count. The dev-tooling/checks/wrapper_shape.py docstring still says "6-statement" at lines 1 and 6 — separate code-tree fix, NOT applied in this revise (revise targets SPECIFICATION/ files only).
4. **Deferred-items.md dangling refs removed.** Both spec.md cross-references (line 77 reserve-suffix algorithm; line 100 author-slug semantics) re-framed as "mechanism-level detail covered by the wrapper's implementation" per the architecture-vs-mechanism discipline. Per Option A from the proposal (preferred): no deferred-items.md file is created; the references are removed and the architectural framing preserved without inlining mechanism details.

Deferred (4 sub-proposals — substantial restructuring; warrants its own focused effort with sketch-and-approve cycle):

5. **Wire-level / constraint-level content split** out of spec.md §Sub-command lifecycle into contracts.md / constraints.md — large structural change.
6. **Promote bold inline subheadings to ### subheadings** in revise lifecycle — heading-restructure that interacts with #5 and #8.
7. **Move revision-loop diagram and Terminology section earlier in spec.md** — section reordering.
8. **Split §Sub-command lifecycle into multiple top-level sections** — major heading restructure that interacts with #5, #6, #7.

The four restructuring proposals are interrelated (all about the same area of spec.md) and should land as a coordinated effort, not as ad-hoc independent revisions.

Deferred (2 sub-proposals — different spec-target trees; cannot apply in this revise pass which targets main SPECIFICATION/):

9. **Fix line-number reference in templates/livespec/contracts.md** — would land via revise against `SPECIFICATION/templates/livespec/`.
10. **Align minimal sub-spec prune-history scenario with actual mechanic** — would land via revise against `SPECIFICATION/templates/minimal/`.

Both are tracked for separate revise passes against the corresponding sub-spec trees.

## Resulting Changes

- spec.md
- constraints.md
- non-functional-requirements.md
- scenarios.md
