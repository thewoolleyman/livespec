---
topic: v103-contract-re-steering-cleanup
author: claude-fable-5
created_at: 2026-06-09T23:13:47Z
---

## Proposal: reconcile-cli-e2e-harness-contract-with-orchestrator-architecture

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Re-scope §"CLI end-to-end harness contract" to core's own spec-side surface. The section still mandates driving livespec in lockstep with one installed impl plugin (today `livespec-impl-beads`), structural per-skill discovery of whatever the installed impl plugin exposes, and the consumer obligation to be installable solely via the `claude` CLI plugin-install surface — all artifacts of the retired plugin-as-contract model.

### Motivation

The v103 revision replaced the impl-plugin skill surface with the three config-named orchestrator CLIs and declared orchestrator front-end skills local-in-repo with plugin publication explicitly deferred. As written, the harness contract mandates installing and skill-enumerating a surface that core's contract no longer names and that the new architecture says need not be installable. This is the highest-severity internal contradiction the post-revise doctor pass surfaced.

### Proposed Changes

§"CLI end-to-end harness contract" MUST be re-scoped to core's spec-side surface only: the harness drives core's spec-side CLIs (and their interactive skill front-ends while those remain core's reference Driver binding) end-to-end. The lockstep-impl-plugin pairing, the per-skill discovery of the installed impl plugin's surface, and the impl-plugin installability obligation MUST be removed. The section MUST state that orchestrator-side end-to-end coverage is owned by each orchestrator's own repository and specification (consistent with §"Interactive dialogue ownership (orchestrator-side)"), and core's harness MAY exercise the cross-boundary seam only through the three config-named orchestrator CLIs (e.g. against a stub orchestrator fixture), never through plugin installation or skill enumeration.

## Proposal: repoint-compat-block-obligations-at-family-coordination-surface

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Fix the two surviving normative `compat`-block obligations in §"Shared code sync — livespec-dev-tooling" and §"Shared runtime — livespec-runtime" that still lean on §"Cross-repo coordination — pin-and-bump" for the block's definition, which v103 reduced to a relocation stub.

### Motivation

The v103 revision relocated the `compat` block schema and bump-pin policy to the family/dev-tooling coordination surface, hollowing the pin-and-bump section into a pointer. The two sibling-sync sections still read "MUST declare a `compat` block ... structurally identical to how every `livespec-impl-*` consumer declares its block per §'Cross-repo coordination — pin-and-bump'" — the heading still resolves but the definitional content those MUSTs lean on is gone from core, and the `livespec-impl-*` framing itself is retired vocabulary. The parallel sentence in non-functional-requirements.md was already corrected to pointer form by v103; these two sites were missed.

### Proposed Changes

In §"Shared code sync — livespec-dev-tooling" and §"Shared runtime — livespec-runtime", the `compat`-block sentences MUST be restated in pointer form: each sibling consumer MUST declare a `compat` block conforming to the schema owned by the family/dev-tooling coordination surface (see §"Cross-repo coordination — pin-and-bump" for the relocation pointer); core's contract MUST NOT restate or depend on the block's structural definition, and the retired `livespec-impl-*`-consumer comparison MUST be dropped.

## Proposal: drop-core-vendoring-mandate-for-livespec-runtime-cross-repo

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Remove the §"Locked vendored libs" mandate to vendor `livespec_runtime` (the typed `DependsOnEntry` union, `CrossRepoManifest`, and the `cross_repo` subpackages) into core's bundle.

### Motivation

The v103 revision declared the cross-repo work-item dependency machinery orchestrator-private and deleted every core consumer of the vendored library (the removed `depends_on`/cross-repo doctor invariants). Core now mandates vendoring a library the same revision declared orchestrator-private and left without a core consumer — an internal contradiction surfaced by the post-revise doctor pass.

### Proposed Changes

The `livespec_runtime` entry MUST be removed from the §"Locked vendored libs" mandate: core's bundle MUST NOT be required to vendor the `cross_repo` machinery. The orchestrator that uses `livespec_runtime.cross_repo` owns its own vendoring or dependency declaration per its own specification. The physical removal of the vendored tree and its `.vendor.jsonc` entry is implementation work that MAY land with the Phase-2 realization of the v103 contract; this change removes only the contractual mandate.

## Proposal: include-next-in-spec-side-cli-contract

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add `next` to the config-named, individually-overridable spec-side CLI set in §"Spec-side CLI contract", which currently enumerates only seed, propose-change, revise, critique, doctor, and prune-history.

### Motivation

The v103 revision kept §"`/livespec:next` spec-side thin-transport skill" (spec-side ranking is a spec-tier concern) and `next` has a backing wrapper like every other spec-side operation, but the new §"Spec-side CLI contract" omits it, leaving unspecified whether `next` is config-named and covered by the `config-named-cli-callability` invariant. Consistency favors inclusion: there is no principled reason the ranking CLI alone would be exempt from config naming and overridability.

### Proposed Changes

§"Spec-side CLI contract" MUST enumerate `next` alongside seed, propose-change, revise, critique, doctor, and prune-history: config-named, pre-populated with core's reference default, and individually overridable. The `config-named-cli-callability` invariant therefore covers it uniformly. §"`/livespec:next` spec-side thin-transport skill" SHOULD gain a one-sentence cross-reference recording that `next` participates in the spec-side CLI contract like every other spec-side operation.

## Proposal: retire-legacy-project-local-implementation-plugin-sections

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Remove the long-stale project-local `.claude/plugins/livespec-implementation/` machinery from non-functional-requirements.md: §"Project-local plugin layout", the legacy-plugin portions of §"Hook chaining" and the final §"Codex dogfooding constraints" paragraph, and the legacy Gherkin scenarios that codify work-item machinery (implementation-gaps current.json, beads issue mapping, gap-tied closure discipline) inside core's spec.

### Motivation

These sections specify a retired project-local plugin layout and restate work-item tracking disciplines (for example a current-gaps-map-to-exactly-one-beads-issue scenario) that the v103 revision declared orchestrator-private. They were already stale before v103; after it they actively contradict §"Doctor cross-boundary invariants" (cross-boundary job is CLI callability only) and §"Orchestrator contract delegation". The post-revise doctor pass flagged the block as the largest remaining contradiction surface.

### Proposed Changes

§"Project-local plugin layout" MUST be removed. §"Hook chaining" MUST be reduced to the generic rule (livespec-installed hooks MUST chain to pre-existing project hooks rather than replace them) with the legacy `livespec-implementation` example dropped. The final §"Codex dogfooding constraints" paragraph referencing the project-local implementation plugin MUST be removed. The Gherkin scenarios that specify orchestrator-internal work-item machinery (refreshed implementation gaps after a revision, planning creates beads issues, implementation closes or refuses gap-tied issues, beads setup and beads doctor behavior, current-gaps one-to-one mapping, implementation-workflow-remains-outside-core, Codex implementation workflow stays project-local) MUST be removed; the Codex scenarios that exercise core's own surface (help mapping, propose-change dry run, AGENTS bridge, plugin-registry non-assumption) MUST be retained. The corresponding tests/heading-coverage.json entries MUST ride in the same revise payload if any `## ` heading set changes (the affected headings are H3/H4 level, so no co-edit is expected).

## Proposal: fix-near-miss-section-references

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Correct four pre-existing near-miss §-references that point at heading text that does not exist: references to §"Primary-checkout commit-refuse hook" (actual content lives under the **Primary-checkout commit-refuse hook** bold lead-in and §"Commit-refuse hook bootstrap procedure"), §"Linter and formatter" / §"Typechecker constraints" (actual: §"Linter rule set" / §"Typechecker rule set"), §"Enforcement suite" (actual: §"Enforcement-suite invocation"), and a bare §"Shared check inventory" citation that names a sibling-repo heading without the allowlist form.

### Motivation

The post-revise doctor pass cross-checked every §-reference and found these four resolve to no heading in any core spec file. They predate the v103 revision but defeat mechanical anchor-reference checking and reader navigation; fixing them is mechanical and has one obviously-correct form per site.

### Proposed Changes

Each of the four references MUST be updated to the exact existing heading text it intends (or, for the sibling-repo §"Shared check inventory" citation, restated via the allowlist mechanism that constraints.md §"Allowlist mechanism" requires for cross-repo spec references). No semantic content changes; this is reference hygiene only and MUST NOT alter any normative rule.
