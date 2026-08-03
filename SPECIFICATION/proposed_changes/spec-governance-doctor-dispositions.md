---
topic: spec-governance-doctor-dispositions
author: openai-codex
created_at: 2026-08-03T01:29:45Z
---

## Proposal: Default doctor finding verbs by check id and escalate everything unmapped

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md

### Summary

Add `spec_governance.doctor_dispositions` as a type-strict map from canonical `check_id` to doctor verb. A valid executable mapping may discharge the disposition dialogue for that finding, while unmapped, malformed, unavailable, design-record-sensitive, or failed dispositions always require human input.

### Motivation

The doctor operation already defines the complete decision vocabulary and relies on the active agent to execute a selected verb. Repo thewoolleyman/livespec, plan/spec-side-autonomy/research/brainstorm.md classifies this as Class (b): the deciding machinery exists and only a safe arming surface is missing. Mapping stable check ids avoids repeating the same finding dialogue while preserving an empty-map default and every design-record escalation. The proposal does not pre-authorize orchestrator store writes: `capture-as-work-item` remains subject to the active orchestrator's own consent contract.

Scope note for the reviser, not text to ratify: this proposal does not edit repository livespec-orchestrator-beads-fabro or its `drive` action boundary, and it does not disposition any sibling proposed-change file.

### Proposed Changes

In spec.md under the existing `## Sub-command lifecycle` heading, create or extend `### Spec-governance policy settings` and the core-owned top-level `.livespec.jsonc` `spec_governance` block. Add `doctor_dispositions`, an object map from `check_id` strings matching the canonical finding-schema pattern `^doctor-[a-z0-9-]+$` to one of `fix-now | capture-as-work-item | propose-change | defer | dismiss`; the safe default is `{}` and no per-proposal override applies. Missing/malformed config, a non-object map, an invalid key, an unknown verb, or a wrong-typed entry MUST resolve safely at entry granularity: the invalid or absent check id is treated as unmapped and requires human input, while other valid entries remain usable. The resolver MUST NOT raise.

Define `effective_doctor_disposition` with fixed hard-floor-first precedence: (1) a finding that reports a cited design-record contradiction, a missing/unreachable design record, or another contract-declared never-self-waived class MUST require human input regardless of any mapping; (2) a valid `check_id=verb` entry supplied in an invocation-scoped doctor disposition envelope; (3) a valid `doctor_dispositions[check_id]` mapping; (4) the safe unmapped result, human input required. A mapped `fix-now` whose corrective action is not mechanically available under the doctor menu contract MUST require human input. A mapped `capture-as-work-item` MUST invoke the active orchestrator's published capture front end and MUST still satisfy that orchestrator's store-write consent discipline; when the necessary invocation-scoped consent is absent, it MUST require human input rather than write. A mapped `propose-change` MUST thread `proposed_change_hint` and spec target into critique/propose-change: when `spec_governance.propose_change_mode` exists and resolves to a complete batch path it consumes them, otherwise they pre-fill the interactive dialogue without suppressing it. Any disposition execution failure MUST require human input and MUST NOT silently fall through to another verb.

In contracts.md under `## Doctor per-finding disposition dialogue`, amend the existing dialogue contract rather than retaining contradictory unconditional clauses. Replace the opening sentence beginning `The doctor operation prose, through the active Driver binding, MUST offer a per-finding disposition dialogue for every non-\`pass\` finding` so it requires dialogue for every non-pass finding whose shared `requires_doctor_disposition_input` predicate is true. Amend the two option clauses ending `This disposition MUST ALWAYS be offered` so they apply whenever a finding reaches dialogue. Amend `The dialogue MUST run BEFORE the Driver binding aborts`, `The dialogue MUST run for static-phase \`warn\` findings too`, and the menu content/availability paragraph so each applies to findings that reach dialogue through the predicate. The canonical five verbs, their order, and their conditional availability remain unchanged for every displayed menu.

Under `## Sub-command wire contracts`, add the invocation disposition-envelope and map wire shapes and create or extend the core spec-governance control contract independently of sibling proposals. Its deterministic reference CLI is `.claude-plugin/scripts/bin/spec_governance.py`; it owns `--project-root <path> --show-effective`, allowlisted `--action <action>` config edits, and validated `--journal-event-json <path>` appends. Create or extend the single declarative `ConfigKey` registry, the committed manifest `.claude-plugin/scripts/livespec/spec_governance/api_configurable_keys.json`, and the action grammar; amend any wrapper/CLI catalogue whose wording would otherwise exclude this non-LLM control CLI. Add `set-doctor-disposition:<check-id>:<verb-or-clear>`; the action MUST validate the finding-schema check-id pattern and verb allowlist, and `clear` removes only that map entry. Changing the map MUST NOT disposition a finding or mutate spec/work-item state. The CLI MUST atomically replace only the named config value while preserving unrelated JSONC keys/comments.

The shared `requires_doctor_disposition_input` predicate gates per-finding dialogue enforcement. It is true for every hard-floor finding, unmapped/invalid check id, unavailable mapped verb, absent downstream consent, journal failure, or failed action, and false only when one valid executable default owns the finding. Any awareness or advertisement surface that surfaces doctor findings as requiring human disposition MUST consume this exported predicate rather than re-derive it.

Create or extend the append-only journal `<project-root>/tmp/livespec-spec-governance-journal.jsonl`, written through the reference CLI. Every automatically selected verb MUST append an event carrying the finding check id, spec root, optional path/line, SHA-256 digest of the UTF-8 finding message, selected verb, governing `doctor_dispositions` key, effective source, and outcome. Full finding text MAY remain in ordinary doctor output but need not be duplicated into the journal. `dismiss` and `defer` MUST be journaled like mutating verbs; journal failure requires human input before any disposition executes.

In constraints.md, state the empty-map and malformed-entry safe behavior, hard-floor-first precedence, exact verb allowlist, escalation-on-unavailability/failure, audit requirement, and the positive core-owned boundary: execution of a selected spec-side verb is Spec-Plane work performed by a supervising upstream caller or attended Driver session, and no spec-governance policy confers spec-side execution or store-write authority on an orchestrator executor.

In scenarios.md, extend `## Happy-path doctor` with scenarios for a mapped executable verb, a mapped `capture-as-work-item` with consent, an explicit invocation disposition overriding a map entry, and a structured audit event. Extend `## Conflicting ratified statements resolve toward the cited design record` with a mapping that attempts to dismiss a design-record finding but still requires human input. Add `## Error path — doctor disposition requires attention` for absent capture consent, unmapped/invalid/unavailable/failed dispositions, journal failure, and all-defaults `{}` arming nothing. The revise payload MUST add that heading to `tests/heading-coverage.json` with a `TODO` reason and maintain every new behavior clause's `clauses[]` link in the same `resulting_files[]` payload.
