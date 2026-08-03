---
topic: spec-governance-revise-decision-mode
author: openai-codex
created_at: 2026-08-03T07:56:13Z
spec_commitments:
  impl_followups:
    - id_hint: spec-governance-revise-decision-mode-core
      description: |
        Extend livespec core's spec_governance registry, config/front-matter schemas, effective-policy resolver and shared attention predicate, control actions, digest-only journal validation, and `.claude-plugin/prose/revise.md` so the ratified Increment-2 decision modes and hard floors are implemented with focused tests.
---

## Proposal: Delegate non-drift revise decisions only behind stronger independent agreement

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md

### Summary

Add `spec_governance.revise_decision_mode` and the per-proposal `decision_policy` override so non-drift revise decisions may be delegated or consensus-owned, while design-record contradiction or absence, ratification-review blockers, and every drift-origin proposal remain mandatory human decisions. The delegated path requires two independent AI signals and is therefore stricter than the current manual path.

### Motivation

Repo `thewoolleyman/livespec`, `plan/spec-side-autonomy/research/brainstorm.md` records the maintainer-resolved Increment-2 design: the existing session-only revise delegation toggle may become a safe-default config lever for non-drift proposals, but every listed escalation floor remains unconditional and is evaluated first. This turns a repeat mid-dialogue choice into an auditable policy without changing the separately ratified drift doctrine reserved for Increment 3.

### Proposed Changes

In `spec.md` §`Intent preservation and design-record authority`, strengthen the `revise` operational rule: effective decision ownership MUST first escalate a cited design-record contradiction, a missing or unreachable design record, and any ratification-review blocker to the maintainer. These floors MUST NOT be delegated or self-waived. State the design argument in the ratified text: for a non-drift proposal under `delegated`, an automatically spawned separate adversarial reviewer MUST return literal `NO BLOCKERS` for the exact final bytes and the delegated decider MUST independently accept those same bytes; any disagreement, unavailable participant, stale/mismatched evidence, or failed journal append MUST escalate. This two-party path is strictly stronger than the manual path because independent review is structural rather than a discipline the maintainer must remember. A `modify` decision MUST bind both signals to the converged final bytes.

In `spec.md` §`Spec-governance policy settings`, change the time-bounded `Increment-1 rows` preamble to a durable registry preamble and add `revise_decision_mode` with allowed values `manual | delegated | consensus`, safe default `manual`, and front-matter override `decision_policy`. Define `effective_revise_decision_mode` with this exact precedence: (1) design-record contradiction; (2) design-record absence; (3) any ratification-review blocker; (4) drift-origin proposal; (5) valid per-proposal override; (6) valid global setting; (7) safe default. The first four branches MUST require a human before later values are considered. In Increment 2 every drift-origin proposal MUST resolve to human regardless of global or per-proposal values; `drift_acceptance_mode` does not exist in this increment, and no configuration may route around that fact. The drift-doctrine sentence in §`Contract + reference implementations architecture` MUST remain byte-identical; changing it is explicitly outside this proposal.

Define mode behavior without ambiguity. `manual` MUST preserve explicit per-proposal human confirmation. `delegated` MAY own a non-drift decision only after the two independent exact-byte signals above agree and every floor is clear. `consensus` MUST require evidence from the separately ratified core consensus tier as well as the unconditional independent-review floor; until that tier and its evidence are available, selecting `consensus` MUST require maintainer input and MUST arm no unattended decision. `decision_policy` MAY override the global value for one proposed-change file but MUST NOT override any floor. An absent `decision_policy` MUST inherit the valid global value; a present malformed, unknown, or wrong-typed override MUST resolve safely to `manual`. Missing or malformed global config, an unknown global value, or a wrong global type MUST also resolve without raising to `manual`.

In `contracts.md`, specify the wire surfaces: add `decision_policy` to proposed-change front matter with exactly the three allowed values; add global and proposal control actions for `set-revise-decision-mode` with `clear` restoring inheritance; include the new registry row in `--show-effective`; and add a validated digest-only `revise_decision` journal event carrying proposal stem/content digest, effective mode/source, decider identity/model when applicable, selected decision, review outcome, final outcome, and any escalation reason, never raw proposal content. The event MUST append before mutation. Export `requires_revise_decision_input`; it MUST be true for `manual`, any hard floor, missing/unavailable/mismatched decision or review evidence, unavailable consensus, disagreement, or journal failure, and false only when one valid automated mode owns the exact proposal decision. Revise enforcement and every awareness surface MUST consume this same predicate rather than re-derive it. The deterministic Python wrapper MAY validate policy/evidence but MUST NOT spawn, review, or decide. The paired revision record SHOULD preserve the effective decision mode/source and delegated or consensus evidence needed for durable audit. Cite repo `thewoolleyman/livespec`, `plan/spec-side-autonomy/research/brainstorm.md` as the design record for the mode, floors, and stronger-than-manual composition.

In `constraints.md`, extend the safety rails so safe defaults arm no unattended revise decision; every resolver evaluates the four floors before overrides/global/default; automated decisions are journal-before-mutation and digest-bound; malformed policy fails safely to manual; and no config, per-proposal override, reviewer, delegated decider, or consensus result may waive a blocker or decide drift in Increment 2. The existing no-independent-review floor remains cumulative, not replaced.

In `scenarios.md` under the existing `## Happy-path revise` heading, add four scenario contracts without adding an H2: (1) global delegated mode proceeds only when a separately auto-spawned reviewer returns `NO BLOCKERS` and the independent delegated decider accepts the exact final bytes, while disagreement escalates; (2) `decision_policy: manual` overrides global delegated or consensus mode for that proposal; (3) a scenario outline proves each first-branch floor—design-record contradiction, design-record absence, ratification blocker, and drift origin—still requires a human before any configured value; and (4) with absent or malformed config/front matter, all defaults resolve to manual and arm nothing. Include consensus-unavailable behavior in the global-mode coverage. Existing scenario-section preambles and all H2 counts MUST remain truthful.
