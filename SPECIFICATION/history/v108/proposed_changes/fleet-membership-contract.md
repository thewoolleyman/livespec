---
topic: fleet-membership-contract
author: claude-fable-5
created_at: 2026-06-12T03:52:37Z
---

## Proposal: fleet-membership-contract

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a new section §"Fleet membership contract" to SPECIFICATION/non-functional-requirements.md defining: a committed fleet manifest in livespec core enumerating every family repo and its repo class; per-class obligations across three obligation types (committed files, GitHub-side state, host-side state); a central fleet-conformance check in dev-tooling that runs on a schedule and as a blocking preflight of the release fan-out; an idempotent `wire-fleet-member` reconcile mode sharing the same contract definition; a discovery safety net over naming and topic; a register-first repo birth procedure; a new-obligation discipline (the retrofit travels with the rule); and a no-circular-gating rule.

### Motivation

A 2026-06-12 root-cause analysis of the bump-automation hole found that the pin-and-bump discipline was retrofitted manually to the four repos existing in late May; livespec-impl-beads (born June 8 from the copier template) inherited the workflow FILES but not the side-effect secrets, and livespec-driver-claude (born June 11, hand-bootstrapped because no template exists for its class) got neither. The release fan-out then skipped or failed both silently. All existing enforcement was repo-local and could not see absence — a repo missing wiring never fails checks it does not run — and nothing asserted fleet-wide presence. A central membership contract with a manifest, a conformance check, and a reconcile operation closes that class of hole structurally.

### Proposed Changes

A new section §"Fleet membership contract" MUST be added to SPECIFICATION/non-functional-requirements.md carrying the following normative rules:

1. **Fleet manifest.** A committed file in livespec core — `fleet-manifest.jsonc` at the repo root — enumerates every family repo and its repo class (core / enforcement-suite / impl-plugin / driver-plugin / library). Livespec core owns fleet-level facts (precedent: the copier template at `templates/impl-plugin/` is already core-hosted and sibling-consumed); per-repo facts stay in consumer-local config. Both the release fan-out and the fleet-conformance check (rule 3) MUST read the manifest — fetched from livespec master at run time — with the GitHub `livespec-sibling` topic demoted to a discovery safety net (rule 5).

2. **Obligations per repo class.** Each repo class carries obligations organized by the three obligation types: committed files (the shim workflows `bump-pin-from-dispatch.yml` / `pin-freshness.yml` / `release-dispatch.yml` for pin-consuming classes, `ci.yml`, the dev-tooling pin, and copier-answers for template-born classes); GitHub-side state (the `livespec-sibling` topic, `APP_ID` + `APP_PRIVATE_KEY` secrets present, the GitHub App installation, branch protection present AND aligned); and host-side state (the beads tenant and the primary-checkout hooks — cross-referencing the existing sections that define those).

3. **Fleet-conformance enforcement.** A dev-tooling check enumerates the manifest and asserts each member's obligations from a central vantage point — the piece repo-local CI cannot provide, because a repo missing wiring never fails checks it does not run. It runs on a schedule AND as a BLOCKING preflight of the dev-tooling release fan-out: an unwired member fails the release fast and loudly instead of being silently skipped.

4. **Reconcile mode.** An idempotent `wire-fleet-member` operation shares the conformance check's contract definition — assert mode is CI; reconcile mode is wiring — with secrets flowing through the 1Password projection (cross-reference §"Family secrets — 1Password Environment as canonical source", proposed in the sibling proposal file `family-secrets-1password-environment.md`).

5. **Discovery safety net.** The conformance run also flags any repo under the family owner matching the `livespec-*` naming or carrying the `livespec-sibling` topic that is NOT in the manifest.

6. **Repo birth procedure.** Scaffold (via the copier template where the class has one) → register in the manifest FIRST → run `wire-fleet-member` → fleet conformance green. Register-first makes a half-wired new repo red fleet CI rather than an invisible straggler.

7. **New-obligation discipline.** A change adding an obligation row MUST wire all current members in the same change — the retrofit travels with the rule. The check's fail-fast bite is reserved for new members and regressions, so the fleet is never red by construction at the moment a rule lands.

8. **No-circular-gating rule.** No conformance failure may be fixable only by an action the check itself gates; wiring must never depend on a dev-tooling release going out.
