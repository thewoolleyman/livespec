---
topic: shared-ci-logic-channel-and-partition-repair
author: claude-opus-5
created_at: 2026-08-11T23:32:29Z
---

## Proposal: Single-authority shared-content channel partition

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The shared-content channel partition is currently asserted in four separate places, and those assertions have already drifted into contradiction: one says there are TWO channels partitioned on a static-vs-executable axis, another says THREE on a static-vs-buildtime-vs-runtime axis. This change makes the existing section §"Shared content provenance" the SINGLE authority for the partition, rewrites every other site as a reference rather than a restatement, and removes every cardinal count from the enumeration so that adding a channel can never again leave a stale number behind. It repairs the ratified contradiction filed as work-item `livespec-n0ka`, and it is a precondition for the sibling proposal in this same file, which adds a channel and would otherwise be amending into a clause that contradicts itself.

### Motivation

Work-item `livespec-n0ka` (P2, bug) records that the ratified spec states the shared-content partition twice with contradictory counts and axes, and it is linked as a BLOCKER of `livespec-jvdvx4.9`. A drift sweep performed while drafting this proposal found the problem is broader than the two sites the bug reports: `non-functional-requirements.md` asserts the partition at line 9 (an enumeration of channels that omits any channel added later), line 109 ("two parallel sibling provenance channels along the static-vs-executable axis"), line 117 ("one of two mechanisms keyed to the channel"), line 216 ("the existing two-channel partition"), line 463 ("The two channels ... along the static-vs-executable axis") and line 496 ("The three channels ... along the static-vs-buildtime-vs-runtime axis"). The defect class is clause-lockstep: a set is described in N places, each carrying its own count, so every addition to the set silently invalidates N-1 sentences. Repairing only the two sentences the bug names would leave four more instances of the same defect live, and the next channel addition would re-open it. The structural fix is to state the partition exactly once, reference it everywhere else, and never assert its cardinality.

### Proposed Changes

All changes are in `SPECIFICATION/non-functional-requirements.md`. Section §"Shared content provenance" MUST become the single authority for the shared-content channel partition; every other site MUST reference it and MUST NOT restate it; and no site MAY assert a cardinal count of channels.

**(1) Line 9, §"Boundary" — the self-application enumeration MUST name the channel set completely.** Replace the fragment:

> its sibling-repo fleet (`livespec-dev-tooling`, `livespec-runtime`, the `livespec-orchestrator-*` registry), the copier scaffold channel, the shared-code and shared-runtime channels, the fleet release-coordination surface, and the sibling registry the doctor cross-repo checks read

with:

> its sibling-repo fleet (`livespec-dev-tooling`, `livespec-runtime`, the `livespec-orchestrator-*` registry), the copier scaffold channel, the shared-code, shared-runtime and shared-CI-logic channels, the fleet release-coordination surface, and the sibling registry the doctor cross-repo checks read

**(2) Line 109, §"Shared content provenance" — the partition MUST be stated here and only here, without a count.** Replace the sentence:

> The non-functional requirements documented in this spec partition across two parallel sibling provenance channels along the static-vs-executable axis:

with:

> The non-functional requirements documented in this spec reach each livespec-governed consumer through a set of parallel sibling provenance channels, partitioned by WHAT is shared and WHERE it executes, and enumerated below by requirement class. This section is the SINGLE authority for that partition: every channel's own contract section MUST reference this enumeration rather than restate it, and no statement of the partition — here or elsewhere — MAY assert a cardinal count of channels. Both disciplines exist for the same reason: a restated partition drifts against its original, and an asserted count rots the moment a channel is added.

**(3) Line 117, §"Shared content provenance" — the drift-surfacing rule MUST be keyed to the channel without asserting a count.** Replace the sentence-opening fragment:

> Drift between `livespec`'s requirements and a consumer repo's content MUST surface via one of two mechanisms keyed to the channel: static-scaffold drift

with:

> Drift between `livespec`'s requirements and a consumer repo's content MUST surface via a mechanism keyed to the channel that carries it: static-scaffold drift

**(4) Line 216, §"Conformance Pattern" — the cross-reference MUST NOT carry a count.** Replace the sentence:

> This applies the existing two-channel partition (§"Shared content provenance") per concern.

with:

> This applies the shared-content channel partition (§"Shared content provenance") per concern.

**(5) Line 463, §"Shared code sync — livespec-dev-tooling" — the restatement MUST become a reference.** Replace the two sentences:

> The mechanism is sibling-and-complementary to `copier` (which remains the shared-SCAFFOLD mechanism per §"Shared content sync — copier template"); `copier` MUST NOT deliver executable Python or shell code, and `livespec-dev-tooling` MUST NOT deliver static scaffolds. The two channels partition livespec's shared content along the static-vs-executable axis.

with:

> The mechanism is sibling-and-complementary to `copier` (which remains the shared-SCAFFOLD mechanism per §"Shared content sync — copier template"); `copier` MUST NOT deliver executable Python or shell code, and `livespec-dev-tooling` MUST NOT deliver static scaffolds. This channel's place in livespec's shared-content partition is stated in §"Shared content provenance" and MUST NOT be restated here.

**(6) Line 496, §"Shared runtime — livespec-runtime" — the restatement MUST become a reference.** Replace the sentence:

> The three channels partition livespec's shared content along the static-vs-buildtime-vs-runtime axis: `copier` ships static files; `livespec-dev-tooling` ships build-time check modules consumed via `[dependency-groups].dev`; `livespec-runtime` ships runtime modules consumed by skills, doctor invariants, hooks, and CI workflows at invocation time.

with:

> This channel's place in livespec's shared-content partition is stated in §"Shared content provenance" and MUST NOT be restated here.

No `## ` heading is added, changed, or removed by this proposal, so `tests/heading-coverage.json` requires no co-edit.

## Proposal: Shared CI logic channel — core-hosted reusable workflows

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

None of the ratified shared-content channels can carry livespec core's OWN executable CI logic, so a contract core owns and requires every consumer's CI to enforce — §"Spec pull-request auto-merge requirement" — has no delivery lane and is today implemented in core's root workflow only, with the copier template's twin left unimplemented. This change names the missing channel: `livespec` itself publishes reusable GitHub Actions workflows and the core scripts they invoke, consumers call them at a pinned release tag, and the derivation lives in exactly ONE implementation that every caller executes. It also amends the copier template's reusable-workflow allowance to permit the new target, and requires core's root workflow and the template's generated workflow to satisfy the spec-PR requirement through the same shared implementation rather than through two copies.

### Motivation

Work-item `livespec-jvdvx4.9` must ship the copier template's half of the v200 spec-PR merge-policy requirement, and a design pass measured six candidate delivery mechanisms and disqualified four. The two survivors both require this amendment, because the ratified channels have no lane for core's own CI logic: `copier` ships static files only, `livespec-dev-tooling` ships build-time enforcement-suite checks, and `livespec-runtime` explicitly has NO reusable GitHub Actions surface. The obvious alternative — ship it through `livespec-dev-tooling` — was examined first and rejected on three independent grounds, recorded here because it is the first question any reader will ask. First, `spec_governance` is core PRODUCT code, not CI tooling: it is a package at `.claude-plugin/scripts/livespec/spec_governance/`, exposed as a CLI wrapper at `.claude-plugin/scripts/bin/spec_governance.py`, and imported by revise's own command modules `_revise_decision.py` and `_revise_ratification.py`; CI is one more caller of it, not its purpose, while `livespec-dev-tooling`'s ratified scope is enforcement-suite code (style, coverage, AST shape, CI alignment, red-green-replay). Second, `livespec-dev-tooling` is upstream of core and MUST NOT take a dependency on `livespec`, so core would be consuming its own product back from a sibling that is not permitted to know core exists — and that sibling is consumed as a pip package via `[dependency-groups].dev`, whereas this script runs under bare `python3` against vendored dependencies with no package manager involved. Third, the half-measure of hosting only the WORKFLOW upstream while the script stays in core is the specifically banned shape: the fleet's No-Circular-Dependency Directive names the tell verbatim — "the upstream repo's CI would have to clone/fetch the downstream repo to run this check. That clone IS the cycle." Core as producer is not a workaround but the correct host: that same directive states verbatim that "The canonical upstream repo is `livespec-dev-tooling` (the shared enforcement suite every fleet repo consumes), and `livespec` core (the contract + templates). The orchestrator, the console, the Drivers, and every adopter are downstream of those." A consumer calling core is therefore `consumer -> producer`, which the directive names as its allowed resolution 2: "Put the check on the DOWNSTREAM (consumer) side, reading UP ... cycle-free, because the consumer already depends on the producer." The single-implementation requirement below is not stylistic: `livespec-jvdvx4.13` fixed two real defects in core's root workflow — a rename-blind stem derivation and an inherited-errexit crash — and the template's twin, had it been a copy, would still carry both.

### Proposed Changes

All changes are in `SPECIFICATION/non-functional-requirements.md`, and depend on the sibling proposal in this file, which makes §"Shared content provenance" the single authority for the channel partition.

**(1) §"Shared content provenance" — a new requirement-class bullet MUST be added** immediately after the `**Executable-enforcement-suite requirements.**` bullet:

> - **CI-enforced core-contract requirements.** Requirements whose expression is CI logic enforcing a contract `livespec` ITSELF owns — notably §"Spec pull-request auto-merge requirement" — MUST flow into every livespec-governed consumer via core-hosted reusable workflows and the `livespec`-shipped scripts they invoke (see §"Shared CI logic — core-hosted reusable workflows"). Such a requirement MUST NOT be satisfied by a per-consumer copy of the logic.

**(2) §"Shared content provenance" — the drift-surfacing sentence MUST cover the new channel.** Append to the sentence amended by the sibling proposal (the one beginning "Drift between `livespec`'s requirements and a consumer repo's content MUST surface via a mechanism keyed to the channel that carries it"), after its final clause `since both channels' pins live in the same `compat` mechanism`:

> ; and CI-enforced core-contract drift MUST surface as a stale pinned reference under the pinned-release discipline of §"Shared CI logic — core-hosted reusable workflows", the consumer's only local artifact for that channel being the pinned reference itself.

**(3) Line 451, §"Shared content sync — copier template" — the pass-through allowance MUST permit the core-hosted target.** Replace the fragment:

> Each enumerated file MAY be a Jinja-templated thin pass-through that delegates to a reusable workflow at `thewoolleyman/livespec-dev-tooling/.github/workflows/<name>.yml@vX.Y.Z` (per §"Shared code sync — livespec-dev-tooling")

with:

> Each enumerated file MAY be a Jinja-templated thin pass-through that delegates to a reusable workflow — at `thewoolleyman/livespec-dev-tooling/.github/workflows/<name>.yml@vX.Y.Z` (per §"Shared code sync — livespec-dev-tooling") when the implementation is fleet-stable enforcement tooling, or at `thewoolleyman/livespec/.github/workflows/reusable-<name>.yml@vX.Y.Z` (per §"Shared CI logic — core-hosted reusable workflows") when it enforces a contract `livespec` itself owns —

**(4) A new sub-section §"Shared CI logic — core-hosted reusable workflows" MUST be added** immediately after §"Shared runtime — livespec-runtime" and before the `## Constraints` heading, with the following body:

> ### Shared CI logic — core-hosted reusable workflows
>
> The shared-CI-logic mechanism between `livespec` and every livespec-governed consumer is `livespec` ITSELF: reusable GitHub Actions workflows published from `github.com/thewoolleyman/livespec` at `.github/workflows/reusable-<name>.yml`, invoked as `uses: thewoolleyman/livespec/.github/workflows/reusable-<name>.yml@vX.Y.Z` from a consumer's own workflow, together with the `livespec`-shipped scripts those workflows invoke. It is the channel by which a contract `livespec` owns, but which MUST be enforced INSIDE a consumer's CI, reaches that consumer's runner.
>
> **Why core is the producer.** Every other channel is produced by a repository UPSTREAM of `livespec`, and both `livespec-dev-tooling` and `livespec-runtime` MUST NOT take a dependency on `livespec` itself; shipping core's own contract logic through either would place downstream code inside an upstream artifact. Hosting only the WORKFLOW upstream while the script it invokes stays in core is not a lesser version of the same idea but a worse one: the upstream workflow would then have to check out its own downstream consumer, which is a circular dependency. With core as the producer the direction is consumer → producer — the consumer already depends on core — so the channel is cycle-free.
>
> **Scope.** This channel MUST carry only logic that (a) derives or enforces a contract `livespec` itself owns, (b) MUST execute inside a consumer repository's CI, and (c) MUST NOT be duplicated per consumer. Content that is a static scaffold MUST go through `copier`; a fleet-stable enforcement-suite check MUST go through `livespec-dev-tooling`; a reusable runtime library module MUST go through `livespec-runtime`. This channel MUST NOT be used to route content away from those channels, and in particular MUST NOT become a second home for enforcement-suite checks.
>
> **One implementation, never one per consumer.** The derivation a reusable workflow performs MUST live in a `livespec`-shipped script invoked from the checked-out core tree, so that every caller — core's own workflows and every generated sibling's alike — executes the SAME implementation. The logic MUST NOT be embedded in a workflow body that is then copied into the copier template: two copies of one derivation drift, and the drift is silent, because each copy passes its own repository's CI while a defect fixed in one persists in the other. Whether a given consumer file `uses:` the reusable workflow or invokes the shipped script directly is the consumer's choice; carrying a second copy of the logic is not.
>
> **Bare-runner constraint.** A script invoked through this channel MUST run under the runner's system `python3` with no dependency-installation step — no virtual environment and no package-manager invocation — relying only on the dependencies `livespec` vendors alongside its scripts. A consumer's CI MUST NOT be required to install `livespec` in order to satisfy a `livespec`-owned contract.
>
> **Pinning.** A consumer MUST pin both the `uses:` reference and the core checkout the workflow performs to a `livespec` RELEASE tag (`@vX.Y.Z`), never to `@master` or any other moving ref, matching the pinned-release discipline §"Shared code sync — livespec-dev-tooling" applies to that channel's reusable workflows. A moving ref would let a change in core alter a consumer's merge behavior with no consumer-side change to review.

**(5) §"Spec pull-request auto-merge requirement" — the two implementations MUST NOT be independent copies.** Append to the end of the section's first paragraph (the one beginning "Both `livespec`'s root-repo `.github/workflows/auto-enable-merge.yml` AND the orchestrator-plugin copier template's"):

> Both files MUST satisfy this requirement through the SAME shared implementation, per §"Shared CI logic — core-hosted reusable workflows"; two independent copies of the derivation are PROHIBITED, because a defect fixed in one copy silently persists in the other while both repositories' CI stays green.

No `## ` heading is added, changed, or removed by this proposal, so `tests/heading-coverage.json` requires no co-edit.
