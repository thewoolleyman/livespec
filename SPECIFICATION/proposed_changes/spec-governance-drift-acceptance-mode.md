---
topic: spec-governance-drift-acceptance-mode
author: claude-opus-5
created_at: 2026-08-04T13:32:30Z
---

## Proposal: Drift acceptance admits the consensus tier, opt-in per repo — swept across every statement

### Target specification files

- SPECIFICATION/spec.md

### Summary

Amend EVERY statement in `spec.md` that reserves drift acceptance to a human, so the tree is self-consistent on ratification: the drift-doctrine paragraph, the Terminology entry, and the canonical architecture diagram's edge label. The propose-change/revise adjudication mechanism, the machine-files/human-adjudicates split, and the ban on any single delegated decider accepting drift all remain.

### Motivation

Increment 3 of epic livespec-jvdvx4 (work item livespec-jvdvx4.5). Supersedes the first draft of this proposal, which replaced ONLY the doctrine paragraph's final sentence and mandated the preceding sentences stay byte-identical. Two independent adversarial reviews both blocked that: the preserved lead says "Only a human CAN rule ...", a capability claim that cannot coexist with a consensus tier owning the same ruling, and the same paragraph would have contradicted itself on ratification. The reviews also found two further unamended statements in this file. All three are swept here.

### Proposed Changes

Three exact replacements in `SPECIFICATION/spec.md`. Each target below is quoted verbatim from the live file and occurs exactly once.

1. The drift-doctrine paragraph. REPLACE THE WHOLE PARAGRAPH, not only its final sentence:

OLD:

    **Drift's human gate is load-bearing doctrine.** Only a human can rule "the implementation is right, the spec is wrong"; that is why drift lands as a proposed-change and never a direct spec write — the propose-change/revise gate IS the human adjudication mechanism, and it is the irreducible human touchpoint that survives even a fully autonomous orchestrator. Orchestrators MAY file drift (the machine path); only humans accept it.

NEW:

    **Drift's human gate is load-bearing doctrine.** Ruling "the implementation is right, the spec is wrong" is an adjudication, not a mechanical check, and it is reserved to a human BY DEFAULT; only where a repo has explicitly opted in through `spec_governance.drift_acceptance_mode` MAY the unanimous cross-vendor consensus tier own it instead. That is why drift lands as a proposed-change and never a direct spec write: the propose-change/revise gate IS the adjudication mechanism, and it is the touchpoint that survives even a fully autonomous orchestrator — human unless a repo has deliberately raised it, and never absent. Orchestrators MAY file drift (the machine path); an orchestrator executor MUST NOT accept it. No `revise_decision_mode` value — including `delegated` and `consensus` — MAY accept a drift-origin proposal, and `drift_acceptance_mode` MUST NOT accept `delegated`: a single delegated decider MUST NOT own a drift acceptance. Maintainer design record: 2026-08-03, repo `thewoolleyman/livespec`, `plan/spec-side-autonomy/research/brainstorm.md`.

2. The Terminology entry:

OLD:

    **Drift (flow)** — the implementation → spec flow: a divergence corrected by changing the SPEC, landing as a proposed-change owned by the spec lifecycle and accepted only by a human. See §"Contract + reference implementations architecture".

NEW:

    **Drift (flow)** — the implementation → spec flow: a divergence corrected by changing the SPEC, landing as a proposed-change owned by the spec lifecycle and accepted by a human, or by the consensus tier only where a repo has opted in via `spec_governance.drift_acceptance_mode`. See §"Contract + reference implementations architecture".

3. The canonical architecture diagram's edge label. This diagram is the declared single source of truth for the architecture, so it MUST NOT keep asserting an unconditional human acceptance:

OLD:

    drift -->|"O3: files proposed-changes (human accepts)"| scli

NEW:

        drift -->|"O3: files proposed-changes (human accepts; consensus tier on opt-in)"| scli

No other sentence in `spec.md` MUST change under this proposal; the registry and resolver edits are proposal 2.

## Proposal: drift_acceptance_mode: registry row, resolver, control action, journal event, and the enforcement predicate

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

Ship the lever the doctrine amendment authorizes, complete enough to actually fire: the registry row, `effective_drift_acceptance_mode`, the re-pointed drift branch of `effective_revise_decision_mode` with its count re-derived, the `set-drift-acceptance-mode` control action, a journal event carrying the consensus-evidence digest, the `requires_revise_decision_input` carve-out, and the matching constraints.md floors.

### Motivation

The first draft omitted four mechanism pieces, and adversarial review showed the lever could never fire without them. Decisive: `contracts.md` defines `requires_revise_decision_input` as true for "any design-record/review/drift floor" and `spec.md` requires revise enforcement to CONSUME that predicate rather than re-derive it — so an armed `drift_acceptance_mode: consensus` with conforming evidence would still demand human input. The draft also mandated a control-surface refusal with no `set-*` action to trigger it (v193 added its `set-revise-decision-mode` actions alongside its row), mandated a journal entry carrying a consensus-evidence digest that no event kind defines, retained "Each of the first four branches requires maintainer input" while re-pointing the drift branch away from maintainer input, and omitted `constraints.md` entirely although it carries the Increment-2 twin.

### Proposed Changes

Every target below is quoted verbatim from the live file and occurs exactly once.

1. `SPECIFICATION/spec.md` §"Spec-governance policy settings" — the registry table MUST gain one row immediately after this existing row:

    | `revise_decision_mode` | `manual | delegated | consensus` | `manual` | `decision_policy` front matter |

   The new row:

    | `drift_acceptance_mode` | `human | consensus` | `human` | no |

2. `SPECIFICATION/spec.md` — the branch enumeration MUST be replaced so the drift branch routes to the new resolver AND the count is re-derived:

OLD:

    `effective_revise_decision_mode` MUST resolve in this order: a cited design-record contradiction; a missing or unreachable design record; any ratification-review blocker; a drift-origin proposal; a valid per-proposal `decision_policy`; the valid global `revise_decision_mode`; and the safe default. Each of the first four branches requires maintainer input before any later value is considered.

NEW:

    `effective_revise_decision_mode` MUST resolve in this order: a cited design-record contradiction; a missing or unreachable design record; any ratification-review blocker; a drift-origin proposal, which MUST resolve through `effective_drift_acceptance_mode`; a valid per-proposal `decision_policy`; the valid global `revise_decision_mode`; and the safe default. Each of the first three branches requires maintainer input before any later value is considered, and the drift branch requires whatever `effective_drift_acceptance_mode` requires.

3. `SPECIFICATION/spec.md` — the Increment-2 drift sentences MUST be replaced:

OLD:

    In Increment 2 every drift-origin proposal resolves to human regardless of either configured value. `drift_acceptance_mode` does not exist in this increment, so no configuration can delegate drift acceptance.

NEW:

    A drift-origin proposal MUST resolve through `effective_drift_acceptance_mode` and MUST NOT be routed by `revise_decision_mode` or by a per-proposal `decision_policy` under any value, including `consensus`.

4. `SPECIFICATION/spec.md` — this paragraph MUST be added immediately after the `effective_revise_decision_mode` paragraph:

    `effective_drift_acceptance_mode` MUST resolve in this order: a cited design-record contradiction; a missing or unreachable design record; any ratification-review blocker; absent, stale, or non-conforming consensus-tier evidence; the valid global `drift_acceptance_mode`; and the safe default. Each of the first four branches requires maintainer input before any later value is considered. The key takes NO per-proposal override: no proposed-change front-matter field MAY raise drift acceptance above `human`, and a present field purporting to do so MUST be ignored without raising. `human` preserves the explicit human ruling. `consensus` MAY own a drift acceptance only when unanimous cross-vendor evidence from the separately ratified core consensus tier is present, fresh, and conforming. `delegated` is NOT an allowed value for this key. A missing or malformed global value MUST resolve to `human` without raising.

5. `SPECIFICATION/contracts.md` — the enforcement predicate MUST stop treating every drift floor as unconditionally human, or the ratified lever can never fire:

OLD:

    `requires_revise_decision_input` is true for `manual`, any design-record/review/drift floor, missing or unavailable exact-byte decision evidence, unavailable consensus evidence, disagreement, or journal failure; it is false only when one valid automated mode owns the exact proposal decision.

NEW:

    `requires_revise_decision_input` is true for `manual`, any design-record or review floor, a drift floor UNLESS `effective_drift_acceptance_mode` validly owns that decision on present, fresh and conforming consensus evidence, missing or unavailable exact-byte decision evidence, unavailable consensus evidence, disagreement, or journal failure; it is false only when one valid automated mode owns the exact proposal decision.

6. `SPECIFICATION/contracts.md` — the Drift-capture CLI bullet:

OLD:

    Filing is a machine path; acceptance is human, per the two-flow doctrine of `spec.md` §"Contract + reference implementations architecture".

NEW:

    Filing is a machine path; acceptance is human by default and MAY be owned by the consensus tier only under an explicit per-repo opt-in via `spec_governance.drift_acceptance_mode`, per the two-flow doctrine of `spec.md` §"Contract + reference implementations architecture".

7. `SPECIFICATION/contracts.md` — the control-action grammar MUST gain a `set-drift-acceptance-mode` action so the mandated allowed-value refusal has a trigger. There is NO per-proposal form, because the key takes no per-proposal override:

OLD:

    - `set-revise-decision-mode:proposal:<proposal-stem>:<manual-or-delegated-or-consensus-or-clear>`;

NEW:

    - `set-revise-decision-mode:proposal:<proposal-stem>:<manual-or-delegated-or-consensus-or-clear>`;
- `set-drift-acceptance-mode:global:<human-or-consensus-or-clear>`;

8. `SPECIFICATION/contracts.md` — the journal-event taxonomy MUST carry the consensus evidence. The `revise_decision` event MUST additionally carry, for a drift-origin decision, the effective `drift_acceptance_mode`, its effective source, and a SHA-256 digest of the consensus-tier evidence; it MUST NOT carry raw evidence content. The control surface MUST refuse any `drift_acceptance_mode` value other than `human`, `consensus`, or `clear` — including `delegated` — with the allowed-value diagnostic, and MUST append the event before mutation.

9. `SPECIFICATION/constraints.md` — the Increment-2 twin MUST be replaced so the constraints tree stops asserting an unconditional drift floor:

OLD:

    Automated revise decisions MUST remain cumulative with that independent-review floor. `effective_revise_decision_mode` MUST require maintainer input for a cited design-record contradiction, a missing/unreachable design record, any ratification-review blocker, or a drift-origin proposal before it considers `decision_policy`, `revise_decision_mode`, or `manual`. No config value, per-proposal override, reviewer, delegated decider, or consensus result may waive those branches. In Increment 2 a drift-origin proposal MUST remain human-decided under every configuration.

NEW:

    Automated revise decisions MUST remain cumulative with that independent-review floor. `effective_revise_decision_mode` MUST require maintainer input for a cited design-record contradiction, a missing/unreachable design record, or any ratification-review blocker before it considers `decision_policy`, `revise_decision_mode`, or `manual`, and MUST route a drift-origin proposal through `effective_drift_acceptance_mode`. No config value, per-proposal override, reviewer, delegated decider, or consensus result may waive those branches. A drift-origin proposal MUST remain human-decided under every configuration EXCEPT an explicit per-repo `drift_acceptance_mode: consensus` opt-in satisfied by present, fresh and conforming unanimous cross-vendor evidence; `drift_acceptance_mode` MUST NOT accept `delegated`, and no `revise_decision_mode` value may accept drift.

## Proposal: Scenarios for drift acceptance under each mode, under one named new heading

### Target specification files

- SPECIFICATION/scenarios.md
- ../tests/heading-coverage.json

### Summary

Add five Gherkin scenarios covering the safe default, an armed acceptance on conforming evidence, escalation on absent or stale evidence, refusal of `delegated`, and the ban on routing drift through `revise_decision_mode` — under one explicitly named new `## ` heading, with its paired `tests/heading-coverage.json` entry.

### Motivation

The authoring discipline requires load-bearing behavior to carry a scenario. The first draft claimed its scenarios "add `## ` headings" without naming one, which review showed was unverifiable and, as written, false: `scenarios.md` carries 13 `## ` section headings each wrapping a fenced gherkin block, and `Scenario:` lines are NOT markdown headings (33 of them exist under those 13 headings). The mandated heading-coverage co-edit could not be derived from an unnamed heading. This proposal names the heading, so the co-edit entry is derivable.

### Proposed Changes

`SPECIFICATION/scenarios.md` MUST gain exactly ONE new `## ` heading, named verbatim:

    ## Drift acceptance under each mode

Under it, one fenced gherkin block (surrounded by blank lines, per the `doctor-gherkin-blank-line-format` check) containing five scenarios:

Scenario: drift acceptance defaults to human. GIVEN a repo whose `.livespec.jsonc` declares no `drift_acceptance_mode`, WHEN a drift-origin proposed change is revised, THEN `effective_drift_acceptance_mode` MUST resolve to `human` and the decision MUST require maintainer input.

Scenario: armed consensus accepts only on conforming evidence. GIVEN a repo declaring `drift_acceptance_mode: consensus` AND unanimous cross-vendor evidence that is present, fresh and conforming, WHEN a drift-origin proposed change is revised, THEN the consensus tier MAY own the acceptance, AND `requires_revise_decision_input` MUST be false for that decision, AND the acceptance MUST be journaled with the consensus-evidence digest before any mutation.

Scenario: armed consensus escalates on absent or stale evidence. GIVEN a repo declaring `drift_acceptance_mode: consensus` AND evidence that is absent, stale or non-conforming, WHEN a drift-origin proposed change is revised, THEN the decision MUST require maintainer input AND no unattended decision MUST be armed.

Scenario: delegated is refused for drift acceptance. GIVEN a `set-drift-acceptance-mode:global:delegated` invocation, WHEN the control surface resolves it, THEN it MUST be refused with the allowed-value diagnostic AND the effective value MUST remain `human` without raising.

Scenario: revise_decision_mode cannot route drift. GIVEN a repo declaring `revise_decision_mode: consensus` and no `drift_acceptance_mode`, WHEN a drift-origin proposed change is revised, THEN the decision MUST resolve through `effective_drift_acceptance_mode` to `human` AND `revise_decision_mode` MUST NOT route it.

Because this adds one `## ` heading, the accepting revise MUST co-edit `tests/heading-coverage.json` in the SAME `resulting_files[]` payload, adding one entry for `SPECIFICATION/scenarios.md` heading `Drift acceptance under each mode`, per `spec.md` §"Self-application". The path MUST be spelled `../tests/heading-coverage.json` so the wrapper's `spec_target / path` join resolves it to the project-root-relative file.
