---
topic: spec-governance-drift-acceptance-mode
author: claude-opus-5
created_at: 2026-08-04T11:43:56Z
---

## Proposal: Drift acceptance admits the consensus tier, opt-in per repo

### Target specification files

- SPECIFICATION/spec.md

### Summary

Amend the drift-doctrine paragraph in spec.md section 'Contract + reference implementations architecture' so drift acceptance MAY be raised to the consensus tier, opt-in per repo, through a dedicated key -- while the propose-change/revise adjudication mechanism, the machine-files/human-adjudicates split, and the ban on any single delegated decider accepting drift all remain intact.

### Motivation

Increment 3 of epic livespec-jvdvx4 (work item livespec-jvdvx4.5). The maintainer resolved on 2026-08-03 that drift acceptance is amendable to the consensus tier ONLY, through a DEDICATED `spec_governance.drift_acceptance_mode` key, never through `revise_decision_mode` and never to `delegated`. v193 deliberately deferred this sentence: its own proposed change states that the drift-doctrine sentence MUST remain byte-identical and that changing it is explicitly outside that proposal. The blocking precondition -- that the cross-vendor consensus panel exist -- is now satisfied: `bin/foreman-consensus` ships in the released `livespec-overseer` cache build installed for this project, and its pins were corrected to fable/opus/gpt-sol with a one-non-Anthropic guard.

### Proposed Changes

In `SPECIFICATION/spec.md`, section 'Contract + reference implementations architecture', the drift-doctrine paragraph currently ends with this exact sentence:

    Orchestrators MAY file drift (the machine path); only humans accept it.

That sentence MUST be replaced by the following, and the preceding sentences of the same paragraph MUST be left byte-identical:

    Adjudication authority is human BY DEFAULT and MUST remain so unless a repo has explicitly opted in: a repo MAY raise drift acceptance to the consensus tier, and ONLY to the consensus tier, through the dedicated `spec_governance.drift_acceptance_mode` key. Orchestrators MAY file drift (the machine path); an orchestrator executor MUST NOT accept it. No `revise_decision_mode` value -- including `delegated` and `consensus` -- MAY accept a drift-origin proposal, and `drift_acceptance_mode` MUST NOT accept the value `delegated`: a single delegated decider MUST NOT own a drift acceptance.

The replacement MUST preserve every existing guarantee that is not the acceptance authority itself: drift MUST continue to land as a proposed-change and never as a direct spec write; the propose-change/revise gate MUST remain the adjudication mechanism; and the machine path MUST remain file-only. The amendment widens WHO may adjudicate, and only when a repo opts in; it MUST NOT widen WHAT may be adjudicated without the gate.

## Proposal: drift_acceptance_mode registry row, effective resolution, and control surface

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md

### Summary

Add `drift_acceptance_mode` as a registry row in the spec-governance policy settings table, define its effective resolution with the unconditional floors first, re-point the drift branch of `effective_revise_decision_mode` at it, and specify its manifest row and journalling obligation in contracts.md.

### Motivation

The doctrine amendment is inert without the lever it authorizes, and the existing `effective_revise_decision_mode` text hard-codes the Increment-2 state in which `drift_acceptance_mode` does not exist. v193 is the pattern to mirror: one declarative registry row driving parsing, coercion, diagnostics, control-surface rendering and the committed manifest, with the hard floors resolving before any configured value.

### Proposed Changes

1. In `SPECIFICATION/spec.md`, section 'Spec-governance policy settings', the registry table MUST gain one row, inserted immediately after the `revise_decision_mode` row so the two drift-relevant keys read together:

    | `drift_acceptance_mode` | `human | consensus` | `human` | no |

2. In the same section, the following paragraph MUST be added immediately after the `effective_revise_decision_mode` paragraph:

    `effective_drift_acceptance_mode` MUST resolve in this order: a cited design-record contradiction; a missing or unreachable design record; any ratification-review blocker; absent, stale, or non-conforming consensus-tier evidence; the valid global `drift_acceptance_mode`; and the safe default. Each of the first four branches requires maintainer input before any later value is considered. The key takes NO per-proposal override: no proposed-change front-matter field MAY raise drift acceptance above `human`, and a present field purporting to do so MUST be ignored without raising. `human` preserves the explicit human ruling. `consensus` MAY own a drift acceptance only when unanimous cross-vendor evidence from the separately ratified core consensus tier is present, fresh, and conforming; anything less MUST require maintainer input and MUST arm no unattended decision. `delegated` is NOT an allowed value for this key. A missing or malformed global value MUST resolve to `human` without raising.

3. In the same section, the `effective_revise_decision_mode` paragraph currently ends with these two exact sentences:

    In Increment 2 every drift-origin proposal resolves to human regardless of either configured value. `drift_acceptance_mode` does not exist in this increment, so no configuration can delegate drift acceptance.

   Both MUST be replaced by:

    A drift-origin proposal MUST resolve through `effective_drift_acceptance_mode` and MUST NOT be routed by `revise_decision_mode` or by a per-proposal `decision_policy` under any value, including `consensus`.

   The rest of that paragraph MUST be left byte-identical; in particular the clause stating that `delegated` may own a NON-DRIFT decision MUST survive unchanged.

4. In `SPECIFICATION/contracts.md`, the wire surface MUST state that `spec_governance.drift_acceptance_mode` appears as one row in the committed API-configurable-key manifest with allowed values `human | consensus`, safe default `human`, and no per-proposal override; that the control surface MUST refuse any other value, including `delegated`, with the allowed-value diagnostic; and that every consensus-tier drift acceptance MUST be journaled through the deterministic control surface before mutation, carrying the consensus-evidence digest, with a journal failure escalating before mutation.

## Proposal: Scenarios for drift acceptance under each mode

### Target specification files

- SPECIFICATION/scenarios.md

### Summary

Add Gherkin scenarios covering the safe default, an armed consensus acceptance with conforming evidence, escalation on absent or stale evidence, refusal of `delegated`, and the ban on routing drift through `revise_decision_mode`.

### Motivation

The propose-change authoring discipline requires that load-bearing behavior be stated as a BCP14 clause AND carry a `## Scenario` in `scenarios.md`; behavioral prose with no scenario is malformed. These scenarios also pin the negative cases, which is where a safety lever silently rots -- an armed mode that accepts on absent evidence would satisfy a happy-path test.

### Proposed Changes

`SPECIFICATION/scenarios.md` MUST gain the following scenarios.

Scenario: drift acceptance defaults to human. GIVEN a repo whose `.livespec.jsonc` declares no `drift_acceptance_mode`, WHEN a drift-origin proposed change is revised, THEN `effective_drift_acceptance_mode` MUST resolve to `human` and the decision MUST require maintainer input.

Scenario: armed consensus accepts only on conforming evidence. GIVEN a repo declaring `drift_acceptance_mode: consensus`, AND unanimous cross-vendor consensus-tier evidence that is present, fresh and conforming, WHEN a drift-origin proposed change is revised, THEN the consensus tier MAY own the acceptance, AND the acceptance MUST be journaled with the consensus-evidence digest before any mutation.

Scenario: armed consensus escalates on absent or stale evidence. GIVEN a repo declaring `drift_acceptance_mode: consensus`, AND consensus-tier evidence that is absent, stale, or non-conforming, WHEN a drift-origin proposed change is revised, THEN the decision MUST require maintainer input, AND no unattended decision MUST be armed.

Scenario: delegated is refused for drift acceptance. GIVEN a repo whose `.livespec.jsonc` sets `drift_acceptance_mode` to `delegated`, WHEN the effective policy is resolved, THEN the value MUST be refused with the allowed-value diagnostic AND the effective value MUST resolve to `human` without raising.

Scenario: revise_decision_mode cannot route drift. GIVEN a repo declaring `revise_decision_mode: consensus` and no `drift_acceptance_mode`, WHEN a drift-origin proposed change is revised, THEN the drift decision MUST resolve through `effective_drift_acceptance_mode` to `human`, AND `revise_decision_mode` MUST NOT route it.

Because these add `## ` headings to a spec file, the revise pass that accepts this proposal MUST co-edit `tests/heading-coverage.json` in the same `resulting_files[]` payload, per `spec.md` section 'Self-application'.
