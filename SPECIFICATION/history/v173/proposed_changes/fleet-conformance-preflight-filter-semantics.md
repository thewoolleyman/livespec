---
topic: fleet-conformance-preflight-filter-semantics
author: claude-opus-4-8-fleet-pin-propagation
created_at: 2026-07-24T08:57:27Z
---

## Proposal: Fleet-conformance preflight is a per-member filter, not a whole-job gate

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Amend §"Fleet membership contract" → "Fleet-conformance enforcement" so it describes the release-fan-out preflight as the per-member FILTER it now is, not the whole-job GATE it used to be. The live sentence asserts an unwired member fails the WHOLE release; since livespec-dev-tooling PR #580 the preflight instead emits per-member verdicts that the dispatch-matrix filter consumes, excluding only the offending sibling while dispatch proceeds to every conformant one. This is the livespec-core companion to the livespec-dev-tooling `pin-currency-severity-policy` propose-change under the fleet-pin-propagation epic; the two must ratify together so no fleet spec is left asserting the superseded semantics.

### Motivation

livespec core work-item livespec-dh9r, cross-repo consistency leg. The independent adversarial review of the livespec-dev-tooling proposal (which re-contracts the preflight from GATE to FILTER, matching the shipped code) found that this sibling paragraph in livespec core still asserts the whole-job-gate behavior verbatim. Ratifying the dev-tooling change while this stands would leave the fleet's own spec self-contradictory across repos: dev-tooling saying the preflight filters per member, core saying it fails the whole release on one member. A broad sweep across every fleet repo's live governed spec, AGENTS.md, and .ai/*.md confirmed this is the ONLY sibling occurrence of the superseded semantics.

### Proposed Changes

ONE replacement to SPECIFICATION/non-functional-requirements.md, in the §"Fleet membership contract" section's "Fleet-conformance enforcement." paragraph. FIND re-verified against origin/master 2026-07-24: occurs exactly once.

FIND:

It runs on a schedule AND as a BLOCKING preflight of the dev-tooling release fan-out: an unwired member fails the release fast and loudly instead of being silently skipped.

REPLACE WITH:

It runs on a schedule AND as the preflight of the dev-tooling release fan-out. In the fan-out context it emits per-member verdicts that the dispatch-matrix filter consumes: a non-conformant sibling in that release's dispatch set is excluded — loudly, with an annotation naming the sibling and its failing rows — while dispatch proceeds to every conformant sibling. A structural failure of the preflight — the check crashing, an unusable verdict artifact, or a run whose conformance findings attach to no member at all — still reds the whole release. The no-silent-skip guarantee is therefore preserved for the dispatch sibling set: a non-conformant sibling is never silently skipped. The exact preflight taxonomy — including how a conformance finding OUTSIDE the dispatch sibling set (a non-conformant publishing repository at its own release, or a finding attributable to no member that co-occurs with a non-conformant member) is surfaced by the scheduled sweep and livespec-dev-tooling's CI rather than by this dispatch — is owned by the dev-tooling producer spec, `contracts.md` §"`reusable-release-dispatch.yml`".

RATIONALE: the live sentence describes the pre-PR-#580 whole-job gate, in which a single unwired member failed the entire release. The shipped behavior is a per-member filter; the replacement states that behavior while explicitly preserving the original sentence's load-bearing point — that an unwired member is never silently skipped — now realized as a loud per-member exclusion rather than a whole-release failure. The severity policy that decides WHICH findings reach error in WHICH context is contracted on the producer side (livespec-dev-tooling contracts.md §"Pin-currency severity policy", the paired proposal); this core paragraph deliberately states only the fleet-membership-level behavior and does not restate that policy, keeping each repo's spec at its own altitude.

NO HEADING CHANGE: "Fleet-conformance enforcement." is a bold lead-in within the existing §"Fleet membership contract" section, not a `## ` or `### ` heading, so no tests/heading-coverage.json co-edit is required.

DRIFT SWEEP (2026-07-24): a broad grep for the superseded semantics ("blocking preflight", "fails the release fast and loudly", "unwired member fails", "silently skip") across all five livespec-core spec files plus AGENTS.md and .ai/*.md found this paragraph as the sole live contradiction; line 217's preflight mention is neutral, and the AGENTS.md/.ai mentions are point-in-time narration, not contract. The sweep grepped the superseded BEHAVIOR (gate-vs-filter language), not any single changed attribute, precisely because the dev-tooling-side review showed that a sweep scoped to the changed property misses a contradiction phrased without that property's vocabulary.
