---
proposal: condition-3-declaration-carrier.md
decision: modify
revised_at: 2026-08-02T06:29:45Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted with one modification. On the merits the proposal stands as filed: conditions 1 and 2 of the rendering-boundary clause are mechanizable and condition 1 already is, while condition 3 is SEMANTIC and no AST can decide it, so the clause cannot be concluded in the relieving direction at all and the ratified allowance reaches nothing. This section has already ruled how that class of question is answered — member 1 clause (e) refuses the whole X|None shape because the semantics are undecidable and member 2 is the DECLARED relief with a STRUCTURAL GATE — so the open question was never whether to add a carrier but what bounds it. The proposal's answer introduces no new mechanism: conditions 1 and 2 become the gate and stay COMPUTED, and only condition 3 is declared. Condition 2 is per-union and becomes a gate limb, so a union whose consumption drifts to an isinstance chain STOPS BEING DECLARABLE rather than carrying its declaration forward; condition 1 is per-function and no declaration reaches it, preserving this section's existing refusal to exempt a leaf. The gate was measured non-vacuous in BOTH directions rather than argued. MODIFIED because the proposal as filed carried no design-record citation, and spec.md section 'Intent preservation and design-record authority' requires every load-bearing semantic definition to carry its rationale AND cite its design record with a repo-qualified citation, holding that a definition without a reachable record 'is incomplete, not merely unadorned' because its next reader inherits a rule whose meaning cannot be recovered. Four new bounds and a structural gate are plainly load-bearing semantic definitions. The modification appends a repo-qualified citation naming the owning repo, the planning thread, and the ledger epic, plus the deciding reasoning and the measurement, in plain text and not as a URL, per the narrow provenance exception that section grants to reference discipline. Nothing in the proposal's normative content was altered, weakened, or widened.

## Modifications

Appended one bolded paragraph, 'THIS RULE'S DESIGN RECORD', to the end of the proposed rule block. It carries a repo-qualified design-record citation — repo `thewoolleyman/livespec-dev-tooling`, `plan/rop-railway-enforcement/handoff.md`, ledger epic `livespec-dev-tooling-8o8e` — together with the deciding reasoning (conditions 1 and 2 become the gate and stay computed; only condition 3 is declared) and the pre-ratification measurement establishing the gate is non-vacuous in both directions (19 of 21 relieved, 2 refused, over a universe of 168). No normative clause was added, removed, reworded, or rescoped: the four bounds, the gate limbs, the relaxing-only polarity, the not-a-required-role-key status, and the stated cross-repo residual are byte-identical to the filed proposal. The citation is provenance only and imposes no new obligation on any consumer.

## Resulting Changes

- non-functional-requirements.md
