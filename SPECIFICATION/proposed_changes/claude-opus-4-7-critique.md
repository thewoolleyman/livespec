---
topic: claude-opus-4-7-critique
author: claude-opus-4-7
created_at: 2026-05-10T07:47:48Z
---

## Proposal: Add seed to opening-sentence except-list in Sub-command lifecycle

### Target specification files

- SPECIFICATION/spec.md

### Summary

spec.md §"Sub-command lifecycle" opens by stating that every command except `help`, `doctor`, and `resolve_template` MUST run a pre-step `doctor`-static check before its action and a post-step `doctor`-static check after. The bullet list immediately below adds that `seed` is exempt from pre-step `doctor` static (it materializes the spec tree, so pre-step has nothing to check). Extend the opening sentence's except-list to additionally call out `seed` as exempt from the pre-step (still runs post-step), keeping the bullet list as the authoritative per-sub-command applicability table.

### Motivation

The opening sentence and the immediately-following per-sub-command bullets are in direct contradiction over whether `seed` runs the pre-step doctor-static check. The opening sentence asserts `seed` MUST run pre-step (since `seed` is not in the except-list); the bullet exempts `seed` from pre-step. The contradiction silently misleads any reader or automation that consults only the opening sentence for the lifecycle envelope. The bullets are operationally correct (seed materializes the spec tree, so pre-step has no consistent state to check); the opening sentence's except-list is the side that needs the fix.

### Proposed Changes

Rewrite the opening sentence of `SPECIFICATION/spec.md` §"Sub-command lifecycle" so its except-list aligns with the per-sub-command bullets immediately below. The current text—"Every command except `help`, `doctor`, and `resolve_template` MUST run a pre-step `doctor`-static check before its action and a post-step `doctor`-static check after."—SHOULD be revised to acknowledge that `seed` is exempt from the pre-step (while still running the post-step), so the sentence and the bullet list state the same applicability rule. One acceptable rewrite: "Every command except `help`, `doctor`, and `resolve-template` MUST run a post-step `doctor`-static check after its action; every such command except `seed` MUST also run a pre-step `doctor`-static check before its action (`seed` is exempt from pre-step because it materializes the spec tree)." The bullet list MUST remain as the authoritative per-sub-command applicability table; the opening-sentence rewrite MUST NOT introduce any new constraint not already encoded in the bullets.

## Proposal: Use kebab-case resolve-template in Sub-command lifecycle opening sentence

### Target specification files

- SPECIFICATION/spec.md

### Summary

spec.md §"Sub-command lifecycle" opening sentence spells the wrapper sub-command as `resolve_template` (snake_case), but `SPECIFICATION/contracts.md` §"Wrapper CLI surface" and §"Plugin distribution" use `resolve-template` (kebab-case). All other wrapper sub-command names in `spec.md` use kebab-case (`propose-change`, `prune-history`). Rewrite the snake_case occurrence to `resolve-template` to match the kebab-case convention used everywhere else for wrapper-level sub-command names.

### Motivation

The naming inconsistency between `resolve_template` (snake_case in `spec.md`) and `resolve-template` (kebab-case in `contracts.md` and elsewhere) is a cross-file inconsistency for the same artifact. A reader cannot tell whether the snake_case spelling is an intentional reference to a different artifact (e.g., a Python module name) or simply a typo. Since `spec.md`'s sentence is enumerating wrapper sub-command names (the same level as `propose-change` / `prune-history`), kebab-case is the convention in force; the snake_case occurrence is therefore inconsistent with the surrounding context.

### Proposed Changes

In `SPECIFICATION/spec.md` §"Sub-command lifecycle" opening sentence, rewrite the literal token `resolve_template` as `resolve-template` so it matches the kebab-case spelling used in `SPECIFICATION/contracts.md` §"Wrapper CLI surface" (line 17) and §"Plugin distribution" (line 70). No other change is required; the surrounding sentence structure stays identical.

## Proposal: Split the monster sentence in revise skill-prose responsibilities into bullets

### Target specification files

- SPECIFICATION/spec.md

### Summary

spec.md §"`revise` skill-prose responsibilities" consists of a single ~600-word sentence built from compound parentheticals enumerating eight or more discrete skill-prose obligations: per-proposal accept/modify/reject decision-and-rationale capture, modify-iteration to convergence, apply-to-all-remaining toggle, optional `<revision-steering-intent>` disambiguation with warn-and-proceed, start-of-revise stale-pending-proposal narration with detailed formatting requirements, and the retry-on-exit-4 handshake. The sentence is barely parseable as written. Split into a bulleted list with one bullet per discrete obligation, preserving the closing statement that `bin/revise.py` MUST NOT invoke template prompts / LLM / interactive flow, and preserving the cross-reference to `constraints.md` §"Sub-command lifecycle mechanics".

### Motivation

The current single-sentence form of §"`revise` skill-prose responsibilities" makes the discrete obligations unclear by burying each one inside compound parentheticals. A reader cannot easily tell where one obligation ends and the next begins, and the parenthetical depth makes it ambiguous whether the warn-and-proceed clause attaches to the steering-intent disambiguation or to the stale-pending-proposal narration. Splitting into bullets makes each obligation independently readable and removes the parenthetical-depth ambiguity.

### Proposed Changes

Rewrite `SPECIFICATION/spec.md` §"`revise` skill-prose responsibilities" to replace the single ~600-word sentence with a bulleted list. Each bullet SHOULD enumerate one discrete skill-prose obligation: (1) per-proposal accept/modify/reject decision-and-rationale capture; (2) `modify`-decision iteration to convergence; (3) the apply-to-all-remaining-proposals delegation toggle; (4) the optional `<revision-steering-intent>` disambiguation with warn-and-proceed when steering-intent contains spec content; (5) the start-of-revise stale-pending-proposal narration (with the count of in-flight proposals and the canonical topic + `created_at` of the oldest pending proposal, formatted as a single informational line; non-gating; sole purpose pending-proposal-accumulation visibility); (6) the retry-on-exit-4 handshake. After the bullets, preserve the closing prose statements: that `bin/revise.py` MUST NOT invoke the template prompt, the LLM, or the interactive confirmation flow; and the cross-reference to `constraints.md` §"Sub-command lifecycle mechanics" for the wrapper's deterministic file-shaping mechanics. The bullet rewrite MUST preserve every normative obligation already stated in the current single sentence; no obligations may be added, removed, or weakened by the rewrite.
