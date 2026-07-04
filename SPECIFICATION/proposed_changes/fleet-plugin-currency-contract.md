---
topic: fleet-plugin-currency-contract
author: claude-fable-5
created_at: 2026-07-04T09:38:21Z
---

## Proposal: Fleet plugin-currency + release-train contract

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Single-source the fleet plugin-currency contract into `SPECIFICATION/non-functional-requirements.md`: add one new `### Plugin currency and the release train` H3 sub-section under `## Spec` that states (a) the currency invariant — every new session in every governed repo, on every declared surface (interactive Claude Code and `codex exec`), runs the latest-released build of every livespec-ecosystem plugin behind a fail-loud staleness gate; (b) its release-train precondition — every `feat:`/`fix:` change must actually become a release and a parked/stalled release train must fail visibly; and (c) the full five-slot Conformance-Pattern expansion (Contract, Mechanism, Installer, Verifier, Exemption). The section explicitly separates this from the existing Pin-freshness concern (the third staleness axis: producer + running-build here; declared-pin stays single-sourced at §"Cross-repo coordination — pin-and-bump"). The second edit adds a one-line `Plugin-currency` member to the Conformance Pattern registry's "Further recognized members" list pointing at the new section. No `## ` (H2) heading is added, renamed, or removed, so no `tests/heading-coverage.json` co-edit is required.

### Motivation

The mechanism is fully landed and verified on master (Phase 4/5 of the fleet plugin-currency work): the per-plugin `release` ref, the fail-loud currency chokepoint in core's plugin bootstrap, the release auto-merge automation, and the fleet-conformance + release-park verifiers are in place. This proposal codifies the durable invariant ONCE as fleet self-application infrastructure, so the verifiers enforce a rule the spec records. Design record: `plan/fleet-plugin-currency/research/design.md` (L0/L1/L2 layers of one guarantee; the L0c distinction between pin-staleness and release-park-staleness is carried verbatim into the "third staleness axis" paragraph). Two deliberate scope deferrals, flagged so they are not lost: (1) the `contracts.md` §"Plugin distribution"/§"Plugin versioning" install-parity edit (the `ref=release` re-registration + install-snippet parity) is a SEPARATE work-item and is NOT in this payload; (2) the copier-template exhaustive-workflow-list amendment for the release-park guard shim workflow (§"Shared content sync — copier template", the exhaustive workflow list + `copier-template-workflow-coverage` doctor-invariant update) is deliberately deferred to the L0c/contracts-parity rollout work-item — this section's Verifier slot POINTS at that section as the workflow home so the single-source link exists now, but the list edit itself rides with the L0c rollout item, not this invariant-codification payload. Filing only; acceptance is maintainer-gated after an independent Fable review verifies replace-target and design-record fidelity.

### Proposed Changes

This proposal makes two edits to `SPECIFICATION/non-functional-requirements.md` — one INSERT and one MODIFY — using the same "insert AFTER X / BEFORE Y" and verbatim-replace precision the other fleet proposals use.

**Edit 1 — INSERT a new `### Plugin currency and the release train` sub-section under `## Spec`.** Insert the following sub-section immediately AFTER the `### Governed-repo lifecycle` section (i.e. after its closing `**The surface boundary.**` paragraph) and immediately BEFORE `### Codex dogfooding compatibility`, with exactly this content:

```markdown
### Plugin currency and the release train

**Plain-language summary.** Every livespec-ecosystem plugin a governed repo runs MUST be the latest *released* build, and staleness MUST be impossible to hide: a session that would run an older build, or a release train that quietly stops producing releases, MUST fail loudly rather than lag unnoticed. This is fleet self-application infrastructure, not a contract a governed consumer inherits (§"Boundary"), and — like the Conformance Pattern of which it is a member (§"Conformance Pattern") — it introduces NO new core skill, NO new core CLI, and NO new core doctor invariant on core's *functional* surface.

**The currency invariant.** Every new session, in every governed repo, on every declared surface (interactive Claude Code and `codex exec`), MUST run the latest-released build of every livespec-ecosystem plugin, over a coherent cache. A `/livespec:*` operation that would run a build OLDER than the one the repo's marketplace registration pins MUST FAIL LOUDLY, naming the exact fix, rather than proceed on the stale build. "Latest-released build" is the newest release-tag artifact per the fleet's pinned-release discipline (§"Cross-repo coordination — pin-and-bump"), because a release — not a raw commit — carries the release-gate validation that per-commit checks skip.

**The release-train precondition.** The currency invariant is meaningful only while the release train stays live, so currency SUBSUMES a release-permanence obligation: every release-eligible change (a `feat:` / `fix:` commit, per `contracts.md` §"Plugin versioning") MUST actually become a release, and a release train that stalls — an open release pull request that ages unmerged, or release-eligible commits that never reach a release tag — MUST fail visibly rather than lag silently. (The fleet-wide stall of 2026-06-30..07-03, when green release pull requests sat open because the release automation's merge path excluded the release bot, is the illustrative failure this obligation exists to make impossible; it is rationale, not contract.)

**The third staleness axis — distinct from Pin-freshness.** These obligations guard different artifacts and MUST NOT be conflated with the Pin-freshness concern (§"Conformance Pattern"; substance at §"Cross-repo coordination — pin-and-bump"). Pin-freshness guards the *declared dependency pin* — whether a consumer's `compat` release-tag pin has drifted behind the latest release. Plugin-currency guards the *running build* — whether the plugin a live session actually executes matches the latest-released build — and its release-permanence precondition guards the *producer* — whether the release train is still cutting releases at all. The three form one chain: a release must EXIST (release-permanence), a consumer's declared pin must TRACK it (Pin-freshness), and the running build must BE it (Plugin-currency). This section owns the producer and running-build axes; the declared-pin axis stays single-sourced at Pin-freshness.

**Conformance-Pattern member (all five slots).** Plugin-currency is a `baseline` Conformance-Pattern concern (§"Conformance Pattern"), binding every governed repo. Its five slots:

- **Contract** — the currency invariant and its release-train precondition stated above.
- **Mechanism** — (a) a per-plugin-repo `release` ref that advances to each release tag, at which the fleet marketplaces register, so a new session resolves the latest-released build with no manual step; (b) a fail-loud currency chokepoint shipped inside core's plugin bootstrap that compares the running build against the marketplace clone's pinned-ref tip (comparing on-disk build identities, so it is offline-tolerant) and refuses to proceed when the running build is older; (c) release automation that auto-merges a green release pull request. Because the chokepoint ships inside core's plugin, it reaches every governed repo and both declared surfaces from one site with no per-repo adoption.
- **Installer** — the idempotent session-currency recipe (the `ensure-plugins` recipe surface) that registers each governed repo's marketplaces at the `release` ref and updates the project-scoped install, together with the release-ref advance carried by the release flow and the release-automation configuration. The marketplace-registration mechanics and the committed install declaration are owned by `contracts.md` §"Plugin distribution"; this section states only the currency guarantee they MUST satisfy.
- **Verifier** — fail-closed checks wired into `just check` and the fleet-conformance sweep (§"Fleet membership contract"): a plugin-currency conformance row asserting each governed member's running build equals its marketplace's pinned-ref release tip; a release-park freshness guard that fails loud on an aged-open release pull request or an unreleased release-eligible backlog (a sibling of the pin-freshness guard, distinct in what it measures); and the structural checks that keep the ref-pinning mechanism intact — every fleet catalog plugin `source` stays a relative in-repo path (a non-relative source silently ignores the ref pin), and every governed repo carries the session-currency hook. The release-automation and release-park workflows are carried through the copier template's workflow set per §"Shared content sync — copier template".
- **Exemption** — two declared, fail-closed levers, never silent relaxations. (1) A repo declared `posture: pinned` in the fleet manifest (§"Fleet membership contract" → "Adopters") deliberately holds an older release; its staleness is an adopter choice and MUST NOT be "helpfully" updated. (2) When currency is NOT determinable (the marketplace clone is absent or offline, or a running build's identity cannot be resolved), the chokepoint warns loudly and proceeds under one declared severity lever, `LIVESPEC_CURRENCY_GATE` (`warn` by default; `fail` in CI and factory dispatch) — a severity lever, not an invariant relaxation, per §"Conformance Pattern" ("explicit exemptions, default fail-closed"). A confirmed-stale build always fails hard regardless of the lever.

**Surface scope.** The currency chokepoint covers the surfaces that drive a `/livespec:*` operation through core's plugin bootstrap — interactive Claude Code and `codex exec`. The sandbox factory resolves no host plugins (fresh clone plus a pinned image), so its currency axis is its image pin, not this gate, and is out of scope here.
```

**Edit 2 — MODIFY the Conformance Pattern registry to add a `Plugin-currency` member.** In `### Conformance Pattern`, the "Further recognized members" paragraph, add `Plugin-currency` to the recognized-members list. Replace this exact text (verbatim, the paragraph's closing list conjunction and final sentence):

```
and **Archive-on-epic-close** (a `plan/<topic>/` thread is active if and only if its ledger epic is open — see §"Planning Lane guidance"). None is adopted until all five of its slots are filled.
```

with:

```
**Archive-on-epic-close** (a `plan/<topic>/` thread is active if and only if its ledger epic is open — see §"Planning Lane guidance"), and **Plugin-currency** (every governed repo, on every declared surface, runs the latest-released build of every livespec-ecosystem plugin behind a fail-loud staleness gate, and the release train that produces those builds never silently parks — see §"Plugin currency and the release train"). None is adopted until all five of its slots are filled.
```

(The leading `and ` is dropped from the replace-target because the new `, and **Plugin-currency** (...)` now supplies the list's final conjunction.)
