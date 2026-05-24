---
topic: delegate-cross-repo-coordination-impl-to-dev-tooling
author: claude-opus-4-7
created_at: 2026-05-24T20:57:32Z
---

## Proposal: delegate-coordination-automation-detail-to-dev-tooling-spec

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Replace the existing 'auto-merge bot architecture deferred' half-sentence at contracts.md:185 with a cross-reference to livespec-dev-tooling's spec, which now owns the cross-repo coordination automation surface per its parallel propose-change cycle. The policy (bumps MUST happen on release; the acceptance criterion is the post-bump invariant suite) stays in livespec's spec where it correctly lives; the implementation deferral is resolved by dev-tooling's spec.

### Motivation

The original sentence reflects a v1 deferral that is now closed by the parallel propose-change landing the cross-repo coordination automation surface in livespec-dev-tooling's own contracts.md. With dev-tooling's spec owning the dispatch, autodiscovery, payload contract, auth model, and fallback procedures, livespec's spec MUST NOT continue to imply the mechanism is half-built or manual — it MUST cross-reference the now-canonical implementation contract. This change aligns with the user's plan that the implementation contract is owned by exactly one location (dev-tooling) and every consumer including livespec itself binds to that contract via the standard sibling discovery + reusable workflow shim pattern.

### Proposed Changes

Replace the existing sentence at `contracts.md:185`:

> When `livespec` ships a new release tag, a bump-pin pull request MAY be opened automatically (auto-merge bot architecture deferred; v1 MAY rely on manual bump-pin PRs). The bump-pin PR's acceptance criterion is that the consumer and the consumer project both continue to pass the post-bump invariant suite.

with the following:

> When `livespec` ships a new release tag, a bump-pin pull request MUST be opened automatically in every consumer per the cross-repo coordination automation surface specified in `livespec-dev-tooling`'s own `contracts.md` §"Cross-repo coordination automation surface". The bump-pin PR's acceptance criterion is that the consumer and the consumer project both continue to pass the post-bump invariant suite. The dispatch mechanism, autodiscovery rules, payload contract, auth model, and fallback procedures are all owned by `livespec-dev-tooling`'s spec; the policy this section establishes (the requirement that bumps happen and the acceptance criterion) is the consumer-facing contract `livespec` owns.

Rationale: the original sentence both establishes the policy (bumps happen on release) AND embeds an implementation deferral ("auto-merge bot architecture deferred; v1 MAY rely on manual"). The deferral is now resolved by `livespec-dev-tooling`'s spec. The revised sentence keeps the policy in livespec (where it correctly lives) and cross-references the implementation surface to its new owner.


## Proposal: tighten-shared-code-sync-section-to-delegate-surface-enumeration

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Modify §"Shared code sync — livespec-dev-tooling" at contracts.md:455 to explicitly acknowledge that the specific semver-stable surface enumeration is owned by dev-tooling's own contracts.md. The semver-stable surface PRINCIPLE (no breaks outside MAJOR bumps) stays in livespec; the specific list of covered elements (check invocation set, composite Actions, reusable workflows, plus the cross-repo coordination automation surface elements) is delegated to dev-tooling's spec where it can stay accurate as the surface grows.

### Motivation

The existing paragraph at contracts.md:455 mixes principle (semver-stable surface) with implementation specifics (the exact list of covered elements). The user's plan partitions these: livespec's spec keeps the policy, dev-tooling's spec owns the implementation contract. Without this delegation, livespec's spec would need to be edited every time dev-tooling adds a new check or reusable workflow — creating a stale-content risk that the user's plan explicitly avoids by centralizing the enumeration in the owning sibling's spec.

### Proposed Changes

Modify §"Shared code sync — livespec-dev-tooling" at `contracts.md:455` to explicitly acknowledge that the specific surface enumeration is owned by `livespec-dev-tooling`'s spec.

Replace the existing paragraph at line 455:

> `livespec-dev-tooling` MUST declare a semver-stable CLI surface: each check's argv contract, exit-code semantics (`0` = pass; non-zero = fail with structured stderr), and `python -m` invocation slug MUST NOT change without a MAJOR version bump. Composite-action and reusable-workflow input/output contracts are subject to the same rule. Implementation internals (function signatures, module structure inside `livespec_dev_tooling/`) MAY change at any version increment.

with:

> `livespec-dev-tooling` MUST declare a semver-stable surface covering its check invocation set, composite Action contracts, reusable workflow contracts, and any additional cross-repo coordination surface elements it ships. The canonical surface enumeration (the specific list of covered elements, the MAJOR/MINOR/PATCH bump rules, and the Conventional Commits → semver mapping) MUST live in `livespec-dev-tooling`'s own `contracts.md` §"Semver discipline" — the principle (semver-stable surface, no breaking changes outside MAJOR bumps) is `livespec`'s policy; the specific surface enumeration is the sibling's implementation contract.

Rationale: the original paragraph mixes principle (semver-stable, no breaks outside MAJOR) with implementation specifics (the exact list of covered elements). The user's plan partitions these: the principle stays in livespec, the specific surface enumeration moves to dev-tooling. This avoids the existing risk of the lists in livespec's spec going stale as dev-tooling's actual surface grows; dev-tooling's spec is the single place an author goes to extend the surface.


## Proposal: add-sibling-spec-ownership-meta-principle

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add a new short section §"Sibling spec ownership" to contracts.md, positioned after §"Shared runtime — livespec-runtime". The new section codifies the principle that implementation surfaces hosted by sibling libraries (dev-tooling's workflow/check inventory, runtime's subpackage APIs, any future sibling library's contractual surface) MUST be specified in those siblings' own contracts.md files; livespec's spec states the policy and consumer-facing shape, the sibling's spec owns the implementation contract. The principle generalizes the existing precedent at §"Shared code sync" line 453.

### Motivation

The principle is implicit in the existing spec architecture but has never been stated as a generalizable rule. Stating it explicitly (a) clarifies the partition for the cross-repo coordination contract landing in dev-tooling's spec via parallel proposal, (b) guides future similar decisions when new sibling libraries are added (e.g., a hypothetical livespec-cli sibling), (c) prevents the spec-content duplication risk that would otherwise creep in as siblings' surfaces grow. The user explicitly requested this meta-paragraph during the planning discussion to make the partition explicit instead of implicit.

### Proposed Changes

Add a new short section `## Sibling spec ownership` to `contracts.md`, positioned immediately after §"Shared runtime — livespec-runtime" (i.e., starting after the current line 471) and before §"Pre-commit step ordering" (current line 473). The new section's full content:

---

## Sibling spec ownership

Implementation surfaces hosted by livespec-governed sibling libraries — `livespec-dev-tooling`'s composite Action / reusable workflow / Python check inventory, `livespec-runtime`'s subpackage public APIs, and any future sibling library's contractual surface — MUST be specified in those siblings' own `contracts.md` files. `livespec`'s spec states the policy (the requirement that the surface exists, the consumer-facing shape, the semver discipline principle); the sibling's spec owns the specific surface enumeration and the implementation contract.

This partition mirrors the existing precedent at §"Shared code sync — livespec-dev-tooling" ("The canonical partition list MUST live in `livespec-dev-tooling`'s own `contracts.md`") and generalizes it across every sibling library. When a future sibling library joins the livespec family, its own seeded `SPECIFICATION/` tree becomes the authoritative location for its implementation contract; `livespec`'s own spec MUST NOT duplicate that content.

The rule applies symmetrically to automation surfaces hosted in `livespec-dev-tooling`'s `.github/` (per its `contracts.md` §"Cross-repo coordination automation surface"). `livespec`'s spec MAY cross-reference these surfaces but MUST NOT specify their input/output schemas, dispatch payload shapes, auth models, or any other implementation detail — those live in the owning sibling's spec.

---

Rationale: the principle is implicit in the existing spec structure (per the §"Shared code sync" line 453 precedent) but has never been stated as a generalizable rule. Stating it explicitly: (a) clarifies the partition for the cross-repo coordination contract landing in `livespec-dev-tooling`'s spec via parallel proposal, (b) guides future similar decisions when new sibling libraries are added, (c) prevents the spec-content duplication risk that would otherwise creep in as siblings' surfaces grow.

