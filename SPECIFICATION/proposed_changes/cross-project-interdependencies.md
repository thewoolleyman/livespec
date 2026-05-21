---
topic: cross-project-interdependencies
author: claude-opus-4-7
created_at: 2026-05-21T22:35:29Z
---

## Proposal: cross-project-interdependencies

### Target specification files

- contracts.md

### Summary

Add a new section §"Cross-project interdependencies" to contracts.md establishing the mechanism for driving multi-repo epics cohesively without a coordinating repo. The mechanism comprises four small, additive pieces: (1) a new top-level `cross_project_interdependencies` field in `.livespec.jsonc` listing participating repos and the relative filesystem path to each one's work-items store; (2) a `<repo-slug>:<work-item-id>` form for cross-repo entries in the existing `depends_on` field, with colon presence as the syntactic discriminator; (3) an extension of the existing `no-stalled-epic` doctor invariant to resolve cross-repo entries uniformly with local entries via the manifest; (4) an extension of the impl-plugin's `next` ranking skill to walk every store in the manifest so a single maintainer is mechanically driven to the next ripe action across the entire family. Epic records live as `type=epic` work-items in the foundational repo's work-items store, never under `<spec-root>/` — epics are impl-tier tracking, not spec-tier contracts.

### Motivation

Cross-repo work currently has no mechanism to ensure all participating repos complete their share of an epic. The existing §"Cross-repo coordination — pin-and-bump" contract handles version compatibility and partial-deployment safety via additive contract changes and `compat`-block drift detection, but it does NOT enforce work-tracking completion. Two failure modes are already observed in practice: PR #158 lays the upstream-dispatch piece of the auto-bump pin bot in `livespec` but the corresponding handlers in `livespec-impl-plaintext` and `livespec-dev-tooling` depend on maintainer discipline to land later, with no mechanical surfacing of the incomplete state; and the dispatch payload schema could drift between this PR and the eventual follow-up handler PRs because there is no mechanical cross-repo consistency check. A coordinating-repo answer has been deliberately ruled out. The minimum mechanical driver — manifest field plus cross-repo `depends_on` form plus extensions of two existing primitives (`no-stalled-epic` doctor invariant and `next` ranking skill) — preserves the no-coordinating-repo discipline while making epic completion mechanically verifiable and the maintainer's next action mechanically rankable across the family.

### Proposed Changes

Add the following new H2 section to `contracts.md`, placed immediately after the existing `§"Cross-repo coordination — pin-and-bump"` section (the new layer sits above pin-and-bump as the epic-management counterpart to that contract).

```markdown
## Cross-project interdependencies

The cross-project epic-management layer above §"Cross-repo coordination — pin-and-bump" governs how multi-repo work — work whose completion requires coordinated landings across two or more livespec-governed repos — is mechanically driven to completion without a coordinating repo. The layer reuses existing primitives (the `type=epic` work-item shape, the `depends_on` reference array, the `no-stalled-epic` doctor invariant, and the impl-plugin's `next` ranking skill) and adds exactly one configuration field plus one cross-repo identifier convention.

### Cross-project manifest

Each `.livespec.jsonc` MAY declare a top-level `cross_project_interdependencies` field whose value MUST be a JSON array of objects, each carrying two required fields: `name` (the repo's short slug, e.g., `livespec-impl-plaintext`) and `work_items` (a relative filesystem path string to that repo's work-items store, e.g., `../livespec-impl-plaintext/work-items.jsonl`). The manifest declares which repos participate in this project's cross-project epic management. Repos that are not declared MUST NOT be referenced by cross-repo `depends_on` entries.

Path resolution for each manifest entry's `work_items` value MUST follow this order:

1. The literal relative path resolved against the directory containing `.livespec.jsonc`.
2. If (1) does not resolve to an existing file, the path resolved against the project root (the directory containing the consumed project's outermost `.livespec.jsonc`).
3. If neither resolves, the resolver MUST fail with a diagnostic naming the manifest entry, the attempted paths, and the recommended fix.

Continuous-integration runners MUST honor the same resolution order. Sibling repos checked out into a flat layout (e.g., `<workspace>/livespec/`, `<workspace>/livespec-impl-plaintext/`, `<workspace>/livespec-dev-tooling/`) satisfy resolution step (1) without per-CI configuration; non-flat layouts MAY satisfy resolution step (2) via project-root-relative paths.

### Cross-repo `depends_on` form

Cross-repo entries in the existing `depends_on` field MUST take the form `<repo-slug>:<work-item-id>`, where `<repo-slug>` matches a `name` entry in the declaring repo's `cross_project_interdependencies` manifest and `<work-item-id>` is a work-item id in that repo's store. Local `depends_on` entries (work items in the same store) MUST NOT contain a colon; colon presence is the syntactic discriminator between local and cross-repo references. Cross-repo and local entries MAY appear together in the same `depends_on` array.

### `no-stalled-epic` invariant extension

The existing `no-stalled-epic` doctor invariant MUST be extended to resolve cross-repo `depends_on` entries via the manifest. For each `type=epic` work-item with cross-repo entries, the check MUST treat each resolved cross-repo entry's status uniformly with local entries when applying the closure-aggregation rule defined in the existing `no-stalled-epic` section. The existing exemption for unresolvable `depends_on` entries MUST extend uniformly to unresolvable cross-repo entries (entries referencing a repo absent from the manifest, an unreadable work-items store, or a missing work-item id within a resolved store) — these MUST NOT fire `no-stalled-epic` per the existing rule. Manifest-resolution diagnostics MUST be surfaced on stderr so the user can repair the manifest or file the missing sub-task; the diagnostics MUST name the offending cross-repo entry verbatim.

The pre-existing local-only semantics for repos that omit the `cross_project_interdependencies` field MUST be preserved unchanged; only repos declaring a manifest opt into cross-repo resolution.

### `next` skill extension

The active impl-plugin's `next` skill (defined by the implementation-plugin contract surface) MUST walk every store named in the `cross_project_interdependencies` manifest when ranking the next ripe work item. The ranking semantics MUST be applied uniformly across the union of all stores, so a single maintainer running `next` in any participating repo is driven to the most-ripe action across the entire family. When the manifest is absent, `next` MUST continue to rank against the local store only — the cross-project behavior is purely additive on top of the existing single-store ranking contract.

### Epic ownership

A cross-project epic record (the `type=epic` work item that holds the cross-repo `depends_on` entries) MUST live in exactly one repo's work-items store. By convention, the epic record SHOULD live in the repo whose contract change motivates the epic; for epics that do not introduce contract changes, the epic SHOULD live in the foundational `livespec` repo's work-items store. Epic records MUST NOT be filed under `<spec-root>/` — epics are impl-tier tracking, not spec-tier contracts. The spec-is-for-contracts discipline (per the broader spec-vs-impl partition that flows through every authored section of this contract) MUST be preserved.

### Failure-mode partitioning

The cross-project layer is mechanical work-completion tracking ONLY. It MUST NOT enforce release coordination — that responsibility belongs to the existing §"Cross-repo coordination — pin-and-bump" mechanism, which uses additive contract changes plus `compat`-block drift detection (enforced by the `contract-version-compatibility` invariant) to make partial deployment safe by construction. The cross-project layer answers the question "is the work done across all participating repos" without re-litigating the question "is the partial-deployed contract surface safe" — those concerns are partitioned by design.
```
