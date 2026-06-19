---
topic: claude-opus-4-8-critique
author: claude-opus-4-8
created_at: 2026-06-19T04:09:51Z
---

## Proposal: Relocate livespec family-infrastructure sections from contracts.md to non-functional-requirements.md

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

contracts.md is a user-facing FUNCTIONAL file, yet five of its sections describe livespec's OWN sibling-repo family infrastructure — content a third-party project governed by livespec (single repo or many) inherits none of: it has no livespec-runtime sibling, is not scaffolded from templates/impl-plugin/, and does not consume livespec's enforcement suite. Per non-functional-requirements.md §"Boundary" ("internal-facing concerns that are NOT visible at the user-facing CLI/API surface") and the constraints.md split rule, these are self-application and MUST live in the non-functional doc. Relocate all five sections out of contracts.md into non-functional-requirements.md.

### Motivation

Direct user-steered critique (2026-06-19): the functional vs non-functional boundary, and the test 'does any livespec consumer inherit this?' Five contracts.md sections fail that test — they are livespec's family infrastructure, not the general consumer contract. Sweep note: spec.md was reviewed and is clean at the section level (its family references — naming the reference orchestrators and the 'no required cross-repo loop driver' boundary — are legitimately functional architecture); constraints.md has no section to relocate (see separate finding).

### Proposed Changes

Move the following five contracts.md sections into non-functional-requirements.md verbatim (preserving their content), placing each under the mirror subsection named: (1) §"Cross-repo coordination — pin-and-bump" -> NFR §Contracts (it is already a relocation pointer to livespec-dev-tooling; it is family release coordination, not general consumer contract); (2) §"Shared content sync — copier template" -> NFR §Contracts (the copier scaffold-sync channel for livespec's own livespec-impl-* repos); (3) §"Shared code sync — livespec-dev-tooling" -> NFR §Contracts for the consumption mechanism and NFR §Constraints for the wiring-completeness invariant; (4) §"Shared runtime — livespec-runtime" -> NFR §Contracts for the consumption mechanism and NFR §Constraints for the semver/Python-floor invariants; (5) §"Sibling spec ownership" -> NFR §Spec (process-intent rule for how the family's sibling specs partition ownership). After the move, contracts.md retains ONLY the general functional contract any consumer inherits (the orchestrator/spec-side CLI seam, doctor's CLI-callability invariant, plugin distribution, wrapper/harness contracts). Update tests/heading-coverage.json in lockstep: the five `##` headings leave contracts.md and arrive in non-functional-requirements.md.

## Proposal: Doctor cross-boundary checks keep their mechanism in contracts.md but reference the relocated family roster

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

The /livespec:doctor catalogue is a FUNCTIONAL product surface and constraints.md requires it be enumerable from one registry, so §"Doctor cross-boundary invariants" stays whole in contracts.md. But three of its entries reference sections that relocate. The fix separates the mechanism (general, functional, stays) from the data it reads (the sibling roster / required-scaffold list, which is self-application and moves to NFR). Flip the references; do NOT move the checks.

### Motivation

The genuinely contested case from the critique discussion. Argued both sides: the doctor catalogue is functional (stays) vs the check's subject is purely the family (moves). Resolution: mechanism stays functional, roster moves. The check is general ('walk whatever sibling registry config declares; a consumer with zero registered siblings is a no-op'); only the specific livespec roster is self-application.

### Proposed Changes

Keep `config-named-cli-callability`, `primary-checkout-commit-refuse-hook-installed`, `master-direct-uncommitted-spec-edits`, `copier-template-workflow-coverage`, and `wiring-completeness-cross-repo` as entries in contracts.md §"Doctor cross-boundary invariants". Update their cross-references so that every pointer to a relocated section resolves to its new non-functional-requirements.md home: (a) `wiring-completeness-cross-repo` — its 'registered sibling repos ... declared in this contracts.md' clause now points at the relocated §"Shared code sync" / §"Shared runtime" / §"Sibling spec ownership" content in NFR; (b) `copier-template-workflow-coverage` — its 'required-file list enumerated in §"Shared content sync — copier template"' now points at the relocated copier section in NFR; (c) `primary-checkout-commit-refuse-hook-installed` — its references to §"Shared content sync" and §"Shared code sync" now point at NFR. All such references are intra-tree (contracts.md -> non-functional-requirements.md, same SPECIFICATION/ tree), so the standalone-readability invariant and the external_references allowlist are unaffected.

## Proposal: constraints.md Reference discipline stays general-functional; genericize its family-specific examples

### Target specification files

- SPECIFICATION/constraints.md

### Summary

§"Reference discipline" looks cross-repo-heavy but is GENERAL functional: the standalone-readability invariant ('a SPECIFICATION/ tree MUST be readable standalone') binds every consumer's spec tree, and the external_references allowlist is its general escape-hatch. It STAYS in constraints.md. Only the family-specific examples read as livespec self-application; genericize them so the constraint does not masquerade as family contract.

### Motivation

Completeness sweep of constraints.md requested during the critique. Unlike the contracts.md sections, §"Reference discipline" is a general rule (same mechanism-vs-data split as the doctor checks): the rule is general, only the illustrative family data is self-application. No constraints.md section relocates.

### Proposed Changes

Keep §"Reference discipline" in constraints.md. Optionally soften the family-specificity: the external_references JSONC example currently keys on `livespec` / `livespec-runtime` citing livespec's own contracts.md headings, and §"Allowlist mechanism" cross-refs livespec-dev-tooling's §"Sibling discovery" — present these as illustrative examples of the general mechanism rather than as the livespec family's fixed roster. The three incidental dev-tooling mentions (constraint-scope dev-tooling/** inclusion; the livespec_runtime.cross_repo vendoring carve-out; the heading_coverage.py enforcer reference) are scoping notes on user-observable constraints and stay where they are.

## Proposal: Codify the functional-vs-self-application boundary in non-functional-requirements.md §Boundary

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add an explicit rule to §"Boundary": the user-facing functional files (spec.md / contracts.md / constraints.md / scenarios.md) describe ONLY what any livespec consumer inherits; livespec's own family — the sibling repos, the shared scaffold/code/runtime channels, and the sibling registry — is self-application and lives in this document. This is the root-cause gate preventing family infrastructure from re-bleeding into the contract files.

### Motivation

The bleed corrected by the relocation finding pooled in contracts.md precisely because no stated rule kept livespec's family infrastructure out of the functional contract. Stating the boundary explicitly is the durable fix (the gate, not just the instance), mirroring how the existing §"Boundary" decision rule already routes contributor-facing content here.

### Proposed Changes

In §"Boundary", after the existing 'how the project is built, tested, and maintained' framing, add a clause: livespec's self-application surface — its sibling-repo family (livespec-dev-tooling, livespec-runtime, the livespec-impl-* registry), the copier scaffold channel, the shared-code and shared-runtime channels, the family release-coordination surface, and the sibling registry the doctor cross-repo checks read — is internal-facing self-application and MUST be specified here, NOT in the user-facing functional files. The functional files describe only the contract a third-party livespec consumer inherits; a litmus test for new content is 'does a project merely governed by livespec inherit this, or is it livespec's own family infrastructure?'
