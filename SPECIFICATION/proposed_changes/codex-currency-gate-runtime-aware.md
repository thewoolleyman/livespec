---
topic: codex-currency-gate-runtime-aware
author: claude-opus-4-8
created_at: 2026-07-08T12:57:31Z
---

## Proposal: Runtime-aware, fail-soft Codex plugin-currency gate

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Make the fleet plugin-currency runtime gate RUNTIME-AWARE and fail-soft on Codex, in `SPECIFICATION/non-functional-requirements.md` §"Plugin currency and the release train". Three surgical prose edits inside the five-slot Conformance-Pattern member bullets: (1) the currency chokepoint's compare is now runtime-aware — on interactive Claude Code it stays a local, offline-safe compare of the running installed build against the LOCAL marketplace-clone tip, while on `codex exec` (where Codex installs a version-keyed cache copy and natively auto-upgrades its marketplace clone to the configured ref's REMOTE tip every session start, making a local running-vs-clone compare tautological) it instead compares the registration's recorded local revision (Codex config `last_revision`) against the REMOTE tip of its configured ref, a short-timeout network read; (2) a confirmed-stale build still fails HARD on Claude, but a confirmed-BEHIND build on Codex is a lever-gated SOFT signal that WARNS-and-proceeds by default and fails hard only under `LIVESPEC_CURRENCY_GATE=fail` (CI/dispatch), because Codex auto-upgrades a release-tracking marketplace before the session is usable so an interactive hard block over the benign one-session-lag window is inappropriate; (3) the “applies updates before the session exists” mechanism is native on Codex (Codex's own session-start marketplace auto-upgrade, no livespec hook) versus the committed `SessionStart` updater hook on Claude, mirroring the adopter posture contract in `docs/livespec-installation-prompt.md`. The undeterminable/offline warn case and the `LIVESPEC_CURRENCY_GATE` warn-default/fail-in-CI framing are unchanged. No `## ` (H2) heading is touched, so no `tests/heading-coverage.json` co-edit is required.

### Motivation

The plugin-currency contract (ratified as v160/v161, work-item livespec-c1k9.6) was authored describing a single offline on-disk running-vs-clone compare that always fails hard on a confirmed-stale build. That description is Claude-accurate but Codex-false. On `codex exec` Codex installs a version-keyed cache COPY from the marketplace clone and NATIVELY auto-upgrades that release-tracking clone to its configured ref's remote tip at every session start (the same behavior the adopter posture contract in `docs/livespec-installation-prompt.md` already documents: “Codex auto-upgrades a release-tracking git marketplace to its `--ref` tip at every session start… no hook, no manual step”). Two consequences follow that the current spec text contradicts: (a) a local running-vs-clone compare on Codex is tautological — both sides are the just-upgraded build — so the meaningful Codex compare is the registration's recorded local revision (`last_revision`) against the REMOTE tip of its configured ref, a network read; and (b) because Codex has already auto-upgraded the release-tracking marketplace before the session is even usable, a hard interactive block over the benign one-session-lag window is inappropriate — the confirmed-behind signal on Codex should WARN and proceed by default, failing hard only under the existing `LIVESPEC_CURRENCY_GATE=fail` lever used in CI and factory dispatch. This proposal codifies the runtime split so the spec matches the shipped runtime-aware, fail-soft Codex behavior and mirrors the already-shipped adopter posture contract (blocking on Claude, non-blocking warning on Codex). Work-item livespec-c1k9.4. Filing only; acceptance is maintainer-gated after an independent Fable review verifies replace-target and design-record fidelity.

### Proposed Changes

This proposal makes THREE surgical prose edits to `SPECIFICATION/non-functional-requirements.md`, all inside the `### Plugin currency and the release train` sub-section's `**Conformance-Pattern member (all five slots).**` bullets. Each edit replaces exactly the sentence(s) that Codex's real behavior has made false; the section's structure and its `LIVESPEC_CURRENCY_GATE` warn-default/fail-in-CI framing are preserved. No `## ` (H2) heading is added, renamed, or removed, so no `tests/heading-coverage.json` co-edit is required. Every replace-target below is quoted VERBATIM from the live section.

**Edit 1 — Runtime-aware compare (two co-fixes: the `Mechanism` bullet's compare, and the `Exemption` bullet's re-statement of it).**

**Edit 1a.** In the `- **Mechanism**` bullet, replace this exact text (verbatim):

```
(b) a fail-loud currency chokepoint shipped inside core's plugin bootstrap that compares the running build against the marketplace clone's pinned-ref tip (comparing on-disk build identities, so it is offline-tolerant) and refuses to proceed when the running build is older;
```

with:

```
(b) a fail-loud currency chokepoint shipped inside core's plugin bootstrap whose compare is RUNTIME-AWARE: on interactive Claude Code it compares the running installed build (resolved from the plugin registry) against the LOCAL marketplace-clone tip — a local, offline-safe on-disk compare — and refuses to proceed when the running build is older; on `codex exec`, because Codex installs a version-keyed cache COPY from the marketplace clone AND natively auto-upgrades that clone to its configured ref's REMOTE tip at every session start, a local running-vs-clone compare is tautological, so the chokepoint instead compares the marketplace registration's recorded local revision (Codex config `last_revision`) against the REMOTE tip of its configured ref — a network read with a short timeout;
```

**Edit 1b.** In the `- **Exemption**` bullet's item (1), replace this exact text (verbatim):

```
it compares each repo's running build ONLY against that repo's OWN marketplace clone tip,
```

with:

```
it performs only the runtime-aware compare of Mechanism (b) against that repo's OWN marketplace registration,
```

(This keeps the posture-coherence argument intact — a `posture: pinned` repo's running build still matches its own pinned registration, and on Codex its configured ref is that same fixed tag, so its remote tip matches too — while no longer asserting a Codex-false local clone-tip compare.)

**Edit 2 — Fail-soft on Codex.** In the `- **Exemption**` bullet's item (2), replace this exact text (verbatim):

```
A confirmed-stale build always fails hard regardless of the lever.
```

with:

```
A confirmed-stale build fails hard on interactive Claude Code regardless of the lever; on `codex exec` a confirmed-BEHIND build is instead a lever-gated SOFT signal — it WARNS and proceeds by default and fails hard (exit non-zero) ONLY under `LIVESPEC_CURRENCY_GATE=fail` (CI and factory dispatch) — because Codex natively auto-upgrades a release-tracking marketplace to the remote tip before the session is usable, so an interactive hard block over the benign one-session-lag window is inappropriate.
```

(The undeterminable/offline case immediately preceding this sentence remains a lever-gated warn on both runtimes — unchanged.)

**Edit 3 — Mechanism (a) on Codex is native.** In the `- **Mechanism**` bullet, replace this exact text (verbatim):

```
(a) a per-plugin-repo `release` ref that advances to each release tag, at which the fleet marketplaces register, so a new session resolves the latest-released build with no manual re-pinning per release;
```

with:

```
(a) a per-plugin-repo `release` ref that advances to each release tag, at which the fleet marketplaces register, so a new session resolves the latest-released build with no manual re-pinning per release — a mechanism that applies updates BEFORE the session exists, realized per runtime: on `codex exec` by Codex's OWN native session-start marketplace auto-upgrade, which pulls the advanced `release` ref with no livespec hook, and on interactive Claude Code by the committed `SessionStart` updater hook (Claude does not auto-update a project-scoped install), mirroring the adopter posture contract in `docs/livespec-installation-prompt.md`;
```

