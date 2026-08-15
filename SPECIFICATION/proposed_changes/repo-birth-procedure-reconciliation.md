---
topic: repo-birth-procedure-reconciliation
author: claude-fable-5-bootstrap-pi-driver-orch
created_at: 2026-08-15T22:31:37Z
---

## Proposal: Reconcile the repo birth procedure: repository creation precedes registration

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Amend the Repo birth procedure rule in non-functional-requirements.md §"Fleet membership contract" so that registration becomes the FINAL act of a birth — the manifest entry lands only when the member already exists, is clonable, and is conformance-ready — per the maintainer directive of 2026-08-16 (registering before a member is done breaks manifest consumers; make no breaking changes), which superseded the 2026-08-15 direction to merely re-sequence registration after repository creation. The invisible-straggler concern that motivated register-first is carried by the existing Discovery safety net rule instead, and manifest consumers other than the conformance check are bound to degrade per-member rather than failing fleet-wide on an unreadable member. One paragraph is replaced; no heading changes.

### Motivation

The ratified rule reads "register in the manifest FIRST" with the single rationale that register-first makes a half-wired repo red fleet CI rather than an invisible straggler. On 2026-08-15 the rule was followed literally for the driver-plugin birth of livespec-driver-pi: the manifest entry landed before the GitHub repository existed. The rationale anticipated red fleet-conformance CI — harmless, visible, designed. What actually happened was a fleet-wide dispatch outage: the reference orchestrator's sandbox setup clones every manifest member, the nonexistent repository 404d on every clone, and every dispatch was hard-blocked until the maintainer directed the entry's revert and re-sequenced registration after repo creation. The rule as written cannot distinguish the outage from the visibility signal it intends, and the bootstrap-pi-driver plan (epic livespec-g5h5ff) carries the standing follow-up to reconcile it. An earlier draft of this proposal preserved register-early (after repository creation) as the ordering, on the visibility rationale. The maintainer rejected that on 2026-08-16 and directed REGISTRATION LAST: a registered-but-unfinished member is load-bearing for every manifest consumer the moment its entry lands — the dispatch-outage post-mortem showed the failure is also actively misleading (a clone of a nonexistent repository surfaces as a credential-prompt error, `could not read Username`, which cost a separate misdiagnosis as a token problem before the race was found) — and the invisible-straggler concern register-first existed for is already carried by the Discovery safety net rule, which flags any fleet-named or fleet-topic repo absent from the manifest. This proposal therefore codifies registration-last and states the per-member degradation contract for manifest consumers, so the failure class is designed out rather than remembered.

### Proposed Changes

One replacement edit in SPECIFICATION/non-functional-requirements.md, in the fleet-manifest rule cluster. The replaced paragraph exists verbatim and exactly once in the live file. No `## ` heading is added, changed, or removed, so no tests/heading-coverage.json co-edit is required.

Replace exactly:

```
**Repo birth procedure.** Scaffold (via the copier template where the class has one) → register in the manifest FIRST → run `wire-fleet-member` → fleet conformance green. Register-first makes a half-wired new repo red fleet CI rather than an invisible straggler.
```

with:

```
**Repo birth procedure.** Create the GitHub repository → scaffold (via the copier template where the class has one) → bring the member to the readiness that does not require manifest membership (the repository exists, is clonable, and carries its scaffolded toolchain and CI) → register in the manifest LAST → immediately run `wire-fleet-member`, which applies the manifest-dependent rows of the **Obligations per repo class** rule → fleet conformance green. Registration is deliberately the FINAL act of a birth: a manifest entry MUST NOT land before the repository it names exists and is clonable, because the manifest is consumed beyond the conformance check — a consumer MAY enumerate and clone every registered member on every run, so a premature entry is a fleet-wide availability defect for every such consumer, not a visibility signal (observed 2026-08-15: a driver-plugin registration that preceded repository creation turned fleet-manifest consumption into a clone failure for every dispatch of the reference orchestrator until the entry was reverted — and the failure shape was misleading, a nonexistent-repository clone surfacing as a credential-prompt error). For a `fleet`-array member, the invisible-straggler concern that once motivated registering first is carried by the **Discovery safety net** rule instead: an unregistered repo matching the fleet naming or topic is flagged by the conformance run, so a mid-birth member stays visible without being load-bearing. An adopter matches neither discovery trigger and is not made visible by that rule; a mid-onboarding adopter is tracked by its own onboarding flow, driven from inside the adopter repository per the **Adopters** rule, not by the manifest — and its entry equally MUST NOT land before its repository exists and is clonable. A manifest consumer other than the conformance check MUST treat a registered member it cannot clone or read as that member's own defect to surface — never as a reason to fail work on other members.
```

Ratification ride-alongs (same PR, outside resulting_files): the .livespec-fleet-manifest.jsonc header comment restates the birth procedure as "register HERE first" and two adopter-entry comments cite the "register-first birth procedure" by name — update those to registration-last; the resume adopter's comment additionally lists the GitHub repo itself among the wiring deferred past registration, which the ratified text forbids, so that comment must drop "GitHub repo" from its deferred list rather than merely renaming the rule (independent review verified resume was registered roughly twenty minutes before its repository existed — the incident class is recurrent, not a one-off). .ai/adding-an-adopter.md also carries a "Register-first is deliberate" rationale line to update to the registration-last + Discovery-safety-net rationale. Cross-repo follow-up (the No-Circular-Dependency Directive forbids editing a sibling's spec from here): repo livespec-dev-tooling's own ratified SPECIFICATION/contracts.md restates the register-first procedure in full with its rationale, carries a "register-first" parenthetical on the reconcile-mode clause (whose wired-only-after-declared mechanic survives registration-last and needs only a relabel), and its .ai/fleet-and-secrets.md states "Register-first remains the governing shape"; the work-item livespec-dev-tooling-47s0, filed in that repository's own tenant, carries the rewrite of those statements to registration-last, and the accepting revise here cites it so neither record floats free. The consumer-side degradation obligation binds manifest consumers generically; the concrete hardening of the reference orchestrator's sandbox sibling-clone step is that repository's own work, filed in its tenant.
