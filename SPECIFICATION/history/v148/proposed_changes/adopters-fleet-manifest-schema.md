---
topic: adopters-fleet-manifest-schema
author: claude-opus-4-8
created_at: 2026-06-26T05:26:05Z
---

## Proposal: Adopters in the fleet manifest contract; rename members array to fleet

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Extend §"Fleet membership contract" to define the manifest's two arrays explicitly: a `fleet` array (renamed from the pre-convergence leftover `members`) carrying livespec's own repos, and an `adopters` array carrying governed repos that adopted the workflow but are not the livespec fleet. This gives the Conformance Pattern's declarative profile/posture machinery a central, normative home without registering any adopter yet, and reconciles the live manifest with the locked design (research/factory-conformance/cross-repo-conformance-pattern.md:142-148) and the family->fleet terminology convergence. The §"Conformance Pattern" "Profiles and the declarative manifest" paragraph already names the `fleet` array; this makes it consistent with the manifest.

### Motivation

Conformance-Pattern milestone M4 (livespec-zs22.7.5), re-scoped to the livespec-side adopter-enablement machinery only. The umbrella term for fleet+adopters is `governed repo`. The live manifest's array was named `members` (a leftover from before the family->fleet convergence); the locked design and §"Conformance Pattern" both use `fleet`. No adopter is registered here — the Open Brain adopter migration is deferred to OB-tenant epic ob-23p.

### Proposed Changes

1) In §"Fleet membership contract", update the **Fleet manifest** paragraph so the manifest's arrays are named explicitly: it enumerates every fleet member in a `fleet` array (each carrying its repo `class`) and MAY carry an `adopters` array (see **Adopters**). (The array was historically `members`; renamed to `fleet` to match the converged domain language and the locked design.)

2) Add a new **Adopters** paragraph immediately after the **Fleet manifest** paragraph:

> **Adopters.** Beyond the fleet `members` it enumerates in the `fleet` array, the manifest MAY carry an `adopters` array — governed repos or families that adopted the workflow but are not the livespec fleet (§"Conformance Pattern" → "Ubiquitous language"). Each adopter entry names its `repo`, its conformance `profile` (the `baseline` floor plus any additive layers, per §"Conformance Pattern" → "Profiles and the declarative manifest"), and a `posture` (`released` / `pinned` / `none`) governing how it tracks upstream livespec releases. A fleet member's profile is DERIVED from its `class` and is not stored; an adopter has no fleet `class`, so it declares its `profile` explicitly. This `adopters` array is the central, declarative list the fleet sweep and the orchestrator iterate; an adopter's own `.livespec.jsonc` carries the same `profile` as the local declaration its Verifiers read. Registering an adopter here does NOT make it a fleet member: adopters carry no per-class obligations (the **Obligations per repo class** rule binds the `fleet` array only) and are absent from the release fan-out's member set — their upstream tracking is governed by `posture`, not by fleet membership.

3) In §"Conformance Pattern" → "Profiles and the declarative manifest", tighten the clause for precision now that the `fleet` array name is consistent: change "gains an `adopters` array beside the existing `fleet` array, each entry naming its `profile` and each adopter entry additionally a `posture` (`released` / `pinned` / `none`)" to "gains an `adopters` array beside the existing `fleet` array, each adopter entry naming its `profile` and a `posture` (`released` / `pinned` / `none`)".

MANIFEST + CROSS-REPO REALIZATION (rides along; not spec files): `.livespec-fleet-manifest.jsonc` renames its `members` array to `fleet` and gains an empty, schema-documented `adopters: []`; the header comment documents the adopter entry shape `{ repo, profile, posture }` and the profile/posture enums. The dev-tooling parser is migrated FIRST (separate PR) to accept BOTH `fleet` and `members` keys + parse `adopters`, and the release fan-out jq to read `(.fleet // .members)`, so the runtime manifest-fetch never breaks during the rename (required-key migration discipline).

No `## ` (H2) heading set changes, so tests/heading-coverage.json is unaffected.
