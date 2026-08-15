---
topic: repo-birth-procedure-reconciliation
author: claude-fable-5-bootstrap-pi-driver-orch
created_at: 2026-08-15T22:31:37Z
---

## Proposal: Reconcile the repo birth procedure: repository creation precedes registration

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Amend the Repo birth procedure rule in non-functional-requirements.md §"Fleet membership contract" so that creating the GitHub repository explicitly precedes manifest registration, the registration-ordering rationale is stated as two separate rules (existence is a hard precondition; earliness within it is the visibility mechanism), and manifest consumers other than the conformance check are bound to degrade per-member rather than failing fleet-wide on an unreadable member. One paragraph is replaced; no heading changes.

### Motivation

The ratified rule reads "register in the manifest FIRST" with the single rationale that register-first makes a half-wired repo red fleet CI rather than an invisible straggler. On 2026-08-15 the rule was followed literally for the driver-plugin birth of livespec-driver-pi: the manifest entry landed before the GitHub repository existed. The rationale anticipated red fleet-conformance CI — harmless, visible, designed. What actually happened was a fleet-wide dispatch outage: the reference orchestrator's sandbox setup clones every manifest member, the nonexistent repository 404d on every clone, and every dispatch was hard-blocked until the maintainer directed the entry's revert and re-sequenced registration after repo creation. The rule as written cannot distinguish the outage from the visibility signal it intends, and the bootstrap-pi-driver plan (epic livespec-g5h5ff) carries the standing follow-up to reconcile it. This proposal preserves the register-early visibility rationale while making repository existence a hard precondition and stating the per-member degradation contract for manifest consumers, so the failure class is designed out rather than remembered.

### Proposed Changes

One replacement edit in SPECIFICATION/non-functional-requirements.md, in the fleet-manifest rule cluster. The replaced paragraph exists verbatim and exactly once in the live file. No `## ` heading is added, changed, or removed, so no tests/heading-coverage.json co-edit is required.

Replace exactly:

```
**Repo birth procedure.** Scaffold (via the copier template where the class has one) → register in the manifest FIRST → run `wire-fleet-member` → fleet conformance green. Register-first makes a half-wired new repo red fleet CI rather than an invisible straggler.
```

with:

```
**Repo birth procedure.** Create the GitHub repository → scaffold (via the copier template where the class has one) → register in the manifest → run `wire-fleet-member` → fleet conformance green. Two rules order the registration step. Registration MUST NOT precede repository creation: a manifest entry MUST name a repository that exists and is clonable when the entry lands, because the manifest is consumed beyond the conformance check — a consumer MAY enumerate and clone every registered member, so an entry naming a nonexistent repository is an availability defect for every such consumer, not a visibility signal (observed 2026-08-15: a driver-plugin registration that preceded repository creation turned fleet-manifest consumption into a clone failure for every dispatch of the reference orchestrator until the entry was reverted). Within that precondition, registration comes EARLY — before the member is fully wired — because register-early makes a half-wired new repo red fleet CI rather than an invisible straggler; a red conformance row is the DESIGNED state of a mid-birth member. A manifest consumer other than the conformance check MUST treat a registered member it cannot clone or read as that member's own defect to surface — never as a reason to fail work on other members.
```

Ratification ride-alongs (same PR, outside resulting_files): the .livespec-fleet-manifest.jsonc header comment restates the birth procedure as "register HERE first" and two adopter-entry comments cite the "register-first birth procedure" by name; update those comments to match the amended rule (create → register early within the existence precondition) so the config commentary does not contradict the ratified text. The consumer-side degradation obligation binds manifest consumers generically; whether the reference orchestrator's sandbox setup needs a code change to conform is that repository's own work to assess and file.
