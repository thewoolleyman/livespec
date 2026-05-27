---
topic: family-wide-bare-flag-invariant
author: claude-opus-4-7
created_at: 2026-05-27T22:50:00Z
---

## Proposal: family-wide-bare-flag-invariant

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/contracts.md

### Summary

Promote the `core.bare = true` primary-checkout discipline from a livespec-private rule to a family-wide invariant that applies universally to every livespec-governed primary checkout: `livespec` itself, every `livespec-impl-*` plugin's repo, `livespec-dev-tooling`, `livespec-runtime`, and every future sibling repo generated from the copier template. Anchor the check on the shared implementation that ships in `livespec-dev-tooling` at `livespec_dev_tooling.checks.primary_checkout_bare_flag_set` (available since v0.3.0), and require every consumer repo to (a) wire that shared check into its `just check` aggregate AND CI matrix and (b) carry an idempotent `just bootstrap` (or equivalent) that sets `core.bare = true` on the primary checkout. The discipline is universal-by-intent per the §"Shared check inventory" partition criterion at `contracts.md` §"Shared code sync — livespec-dev-tooling": the bare-flag rule is stable across every livespec-governed project and so its check belongs to the shared inventory, not to any single repo's private catalogue.

### Motivation

The bare-flag invariant currently reads as livespec-private in three places: `non-functional-requirements.md` §"Bare-flag enforcement" and §"Bare-flag bootstrap procedure", and `contracts.md` §"Doctor cross-boundary invariants" → §"`primary-checkout-bare-flag-set`". Each reads literally as "every livespec-governed primary checkout" but the surrounding context (the doctor-static catalogue, the bootstrap-step contract) implies the rule lands in livespec's own check inventory and is enforced repo-locally via the plugin doctor's static phase. With the shared check now shipped in `livespec-dev-tooling` v0.3.0, the discipline can become structurally enforceable across the whole family in the same `just check`/CI cadence that every livespec-governed sibling already runs against the dev-tooling pin — closing the same author-vigilance loophole that the original rule closed for livespec, but for every sibling at once. The Phase 1 port (which landed the check in dev-tooling) is meaningless without the spec asserting "yes, every sibling MUST adopt it"; this PC writes the spec side of that.

### Proposed Changes

1. **`non-functional-requirements.md` §"Bare-flag enforcement"** (the paragraph at line 760): keep the existing "every livespec-governed primary checkout" framing but make the universality explicit by enumerating the in-scope set (livespec, every `livespec-impl-*` plugin, `livespec-dev-tooling`, `livespec-runtime`, future copier-template-generated siblings) and pointing at the shared check's module path. The existing three-companion-mechanism framing (NFR rule + bootstrap step + doctor invariant) stays; the only change is the explicit family-wide framing and the redirect from "livespec's plugin doctor" to "the shared check in `livespec-dev-tooling`".

2. **`non-functional-requirements.md` §"Bare-flag bootstrap procedure"** (lines 762–771): keep the four numbered contract clauses (documented entry point, sets `core.bare = true`, idempotent, uncoupled from other setup) and the "the bootstrap step is the mechanism by which a user resolves a doctor `fail` finding" closing sentence. Add a paragraph noting that EVERY livespec-governed sibling repo MUST surface an equivalent bootstrap entry point — i.e., the bootstrap rule is itself family-wide. Reference the shared check as the mechanical verifier and the per-consumer bootstrap (typically a `just bootstrap` recipe per repo) as the mechanical fixer.

3. **`contracts.md` §"`primary-checkout-bare-flag-set`"** (lines 178–186): make the family-wide scope explicit in the opening paragraph. State that the canonical implementation ships in `livespec-dev-tooling` at `livespec_dev_tooling.checks.primary_checkout_bare_flag_set` (available since `livespec-dev-tooling` v0.3.0) and that every consumer repo MUST run it in their `just check` aggregate AND CI matrix per the same invocation-agnostic discipline that governs every other shared check (per §"Shared code sync — livespec-dev-tooling"). Clarify the relationship between the shared check (runs once against the project root per `just check`/CI invocation) and any repo-local plugin-doctor catalog instance of the check (e.g., the livespec plugin doctor's static-phase entry, which runs per spec tree under each `/livespec:doctor` invocation): both are valid; both run at different scopes/cadences; defense-in-depth keeps both.

The wording stays MINIMAL — the goal is to make universal-by-intent explicit, not to introduce new contracts. The bootstrap procedure's contract clauses, the doctor invariant's binary structural framing, and the existing cross-references to `contracts.md` §"Shared code sync — livespec-dev-tooling" all stay verbatim.

### Spec commitments

This PC declares no `spec_commitments.impl_followups[]` — the impl side of the family-wide rule will land repo-by-repo as follow-on bump-pin PRs in each sibling that pull in dev-tooling v0.3.0 and adopt the shared check. Those PRs are tracked as their own per-repo work items via each impl-plugin's normal capture flow; the spec promotes the rule but does not pre-bind each sibling's adoption schedule.
