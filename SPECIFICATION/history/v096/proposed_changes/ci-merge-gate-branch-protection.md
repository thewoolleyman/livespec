---
topic: ci-merge-gate-branch-protection
author: livespec-orchestrate
created_at: 2026-05-29T04:59:21Z
---

## Proposal: CI as a merge gate (branch protection)

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a new family-wide non-functional-requirement to non-functional-requirements.md mandating that every livespec-governed primary repo's master branch carry GitHub branch protection marking the repo's CI matrix checks as REQUIRED status checks, so a pull request MUST NOT merge while CI is red. The new section is a `### ` (H3) sub-section under `## Constraints`, placed adjacent to the existing commit-refuse-hook material, and is modeled on the canonical family-wide infra NFR at the same depth (the `### Commit-refuse hook bootstrap procedure` / `**Primary-checkout commit-refuse hook.**` rule). It states the enforce_admins + strict requirements, the rationale that branch protection is GitHub repo settings rather than a committed file (so it does NOT propagate via the copier template and MUST be enabled per-repo), and names `branch_protection_alignment` (shipped from livespec-dev-tooling's shared inventory) as the mechanical enforcer that completes the same NFR-rule + bootstrap + doctor-invariant triad the commit-refuse-hook NFR uses.

### Motivation

CI currently runs but is purely advisory in repos whose master lacks required-check branch protection: `gh pr merge --auto` merges instantly without waiting for CI, which already allowed a red pull request to land on master. Branch protection is GitHub repo settings, NOT a committed file, so it does not propagate when a sibling is scaffolded from the copier template and must be enabled explicitly per-repo. The livespec family needs this declared once, family-wide, alongside the existing commit-refuse-hook infra NFR, with a mechanical enforcer so the discipline is structurally enforceable rather than author-vigilance-dependent.

### Proposed Changes

Add a new `### CI as a merge gate (branch protection)` sub-section to `non-functional-requirements.md` under the `## Constraints` section, immediately after the `### Commit-refuse hook bootstrap procedure` sub-section (i.e., before `### Project-local plugin layout`). Because this is a `### ` (H3) sub-section and `tests/heading-coverage.json` tracks only `## ` (H2) headings (the shared `heading_coverage` check's `_extract_h2_headings` matches `## ` and excludes `### `), NO heading-coverage co-edit is required. The new section body MUST read:

---

### CI as a merge gate (branch protection)

**CI as a merge gate.** Every livespec-governed primary repo's `master` branch MUST have GitHub branch protection configured so that the repo's CI matrix checks are REQUIRED status checks. A pull request MUST NOT be mergeable while CI is red: the required-check gate MUST block the merge until every CI matrix check reports success. The rule is family-wide-by-intent: it applies UNIFORMLY to `livespec` itself, every `livespec-impl-*` plugin, `livespec-dev-tooling`, `livespec-runtime`, and every future sibling repo generated from the copier template per `contracts.md` §"Shared content sync — copier template". A repo whose `master` lacks required-check branch protection is out-of-contract regardless of which family role it plays.

The protection MUST set `enforce_admins` (no admin bypass of the required checks — repository administrators are subject to the same red-CI block as every other contributor) AND MUST require branches be up to date before merging (`strict`, so a pull request MUST be rebased onto the latest `master` before its required checks count toward mergeability). The required-check set MUST cover the repo's full CI matrix; a protection whose required-check set omits any CI matrix check is out-of-contract because the omitted check becomes advisory again.

IMPORTANT — why this is declared as its own infra rule rather than treated as already-covered by CI existing: branch protection is GitHub repository *settings*, NOT a committed file in the repository tree. It therefore does NOT propagate when a sibling is scaffolded from the copier template (the copier channel ships only static files per `contracts.md` §"Shared content sync — copier template"), and it MUST be enabled per-repo as an explicit out-of-band setup step. Without it, CI runs but is purely advisory: `gh pr merge --auto` merges a pull request instantly without waiting for the CI run, and a red pull request can land on `master`. That exact failure already occurred (a red pull request merged to `master` because no required-check gate existed); this rule is the contract that prevents its recurrence.

The rule pairs with two companion mechanisms, realizing the same NFR-rule + bootstrap + doctor-invariant triad the commit-refuse-hook rule uses (see §"Primary-checkout commit-refuse hook"): a per-repo setup step that enables the protection on `master` with the required-check set, `enforce_admins`, and `strict` (the exact entry-point shape is implementation choice — a `gh api` call in a bootstrap recipe, a documented one-time `gh` invocation, or template-adjacent setup tooling — but the contractual requirement is that the protection is enabled per-repo, since the copier template cannot carry it); and the `branch_protection_alignment` shared check, which is the mechanical enforcer. The `branch_protection_alignment` check ships from `livespec-dev-tooling`'s shared inventory per `contracts.md` §"Shared code sync — livespec-dev-tooling" (its intent and CLI surface are stable across every livespec-governed project, so a single implementation is correct for the whole family). The check MUST fail when branch protection is absent on `master`, when `enforce_admins` is not set, when `strict` is not set, or when the protection's required-check set does not cover the repo's CI matrix. Every consumer repo MUST wire `branch_protection_alignment` into its `just check` aggregate AND CI matrix on the same invocation-agnostic cadence governing every other shared check, per the wiring-completeness invariant codified in §"Shared code sync — livespec-dev-tooling". Together the three (this NFR rule, the per-repo enable step, and the `branch_protection_alignment` check) make the merge-gate discipline structurally enforceable rather than author-vigilance-dependent — and the universality of the rule means a single shared implementation of the check satisfies the contract for every sibling at once.
