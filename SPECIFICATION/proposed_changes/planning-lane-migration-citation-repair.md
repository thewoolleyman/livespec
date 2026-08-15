---
topic: planning-lane-migration-citation-repair
author: codex
created_at: 2026-08-14T22:14:58Z
---

## Proposal: Preserve both legacy handoff artifact names during migration

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/scenarios.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Clarify that a pre-existing supervisor-handoff.md, as well as handoff.md, is historical evidence that a Planning Lane migration must relocate under research/ rather than delete.

### Motivation

The completed planning-lane migrations correctly preserved both file types, but the currently ratified singular wording makes the supervisor-handoff preservation look forbidden.

### Proposed Changes

In `SPECIFICATION/spec.md` Planning Lane migration clause and `SPECIFICATION/non-functional-requirements.md` Planning Lane guidance, change the preservation sentence so it applies to a pre-existing `handoff.md` **or** `supervisor-handoff.md`, requiring either existing file to be preserved as a write-once historical-evidence file under `plan/<slug>/research/` and never deleted from the git tip. In `SPECIFICATION/scenarios.md` Scenario: Migration preserves a pre-existing handoff as write-once evidence, change the Given and Then wording to cover either legacy filename while preserving the same relocation and no-deletion behavior.

**Carve-out for the immediately-following prohibition.** `spec.md`'s bullet also states "The plan store MUST NOT contain `supervisor-handoff.md`, mutable status files, or any other mutable planning-state document" — read literally, this categorically forbids `supervisor-handoff.md` anywhere in the plan store, contradicting this same proposal's requirement to preserve an archived copy under `research/`. The replacement text below adds an explicit carve-out so the prohibition binds only a *live* `supervisor-handoff.md` (one still receiving writes, sitting outside `research/`), not the write-once historical copy this proposal requires preserving.

#### Exact replacement text — `SPECIFICATION/spec.md` bullet at line 375

Replace this existing bullet verbatim:

> The plan store MUST contain only write-once research inputs under `plan/<slug>/research/` and exactly one write-once metadata anchor written at plan open. The anchor MUST name the epic id and MUST NOT be updated to mirror children, statuses, handoffs, readiness, or archive state. The plan store MUST NOT contain `supervisor-handoff.md`, mutable status files, or any other mutable planning-state document. A plan created after ratification MUST NOT create a live `handoff.md`; migration of a pre-existing `handoff.md` MUST preserve it as a write-once historical-evidence file under `plan/<slug>/research/` and MUST NOT delete it from the git tip. A migration that relocates any plan path MUST update, in the same change or an explicitly linked work-item, every fleet-spec statement whose design-record citation names that pre-relocation path, mechanically findable by grepping each fleet repository's `SPECIFICATION/` tree for the old path. Rationale: the foreman post-mortem showed prose-only state disappears from ledger completion checks, and the maintainer ruled mutable planning state belongs in the ledger; design records: repo `thewoolleyman/livespec`, `plan/archive/planning-lane-redesign/research/seed-prompt.md`, `plan/archive/planning-lane-redesign/research/brainstorm.md`, and `plan/archive/planning-lane-redesign/research/maintainer-rulings.md`.

With this new bullet (adds the `supervisor-handoff.md` carve-out; also applies the citation-form fix from the next proposal below, since the plan remains live):

> The plan store MUST contain only write-once research inputs under `plan/<slug>/research/` and exactly one write-once metadata anchor written at plan open. The anchor MUST name the epic id and MUST NOT be updated to mirror children, statuses, handoffs, readiness, or archive state. The plan store MUST NOT contain a live `supervisor-handoff.md`, mutable status files, or any other mutable planning-state document, except a pre-existing `handoff.md` or `supervisor-handoff.md` preserved as a write-once historical-evidence file under `plan/<slug>/research/` per the migration-preservation sentence below. A plan created after ratification MUST NOT create a live `handoff.md` or `supervisor-handoff.md`; migration of a pre-existing `handoff.md` or `supervisor-handoff.md` MUST preserve it as a write-once historical-evidence file under `plan/<slug>/research/` and MUST NOT delete it from the git tip. A migration that relocates any plan path MUST update, in the same change or an explicitly linked work-item, every fleet-spec statement whose design-record citation names that pre-relocation path, mechanically findable by grepping each fleet repository's `SPECIFICATION/` tree for the old path. Rationale: the foreman post-mortem showed prose-only state disappears from ledger completion checks, and the maintainer ruled mutable planning state belongs in the ledger; design records: repo `thewoolleyman/livespec`, `plan/planning-lane-redesign/research/seed-prompt.md`, `plan/planning-lane-redesign/research/brainstorm.md`, and `plan/planning-lane-redesign/research/maintainer-rulings.md`.

## Proposal: Repair stale Planning Lane design-record citations

### Target specification files

- SPECIFICATION/spec.md

### Summary

Update all sixteen archive-form Planning Lane design-record occurrences across the nine ratified `SPECIFICATION/spec.md` Planning Lane bullets to the current live research location.

### Motivation

The planning-lane plan was migrated but remains live; every archive-form citation in the nine Planning Lane bullets now points to a path that does not exist, defeating the design-record traceability they are meant to preserve.

### Proposed Changes

Sweep every one of the sixteen archive-form occurrences across bullets 374–382 in `SPECIFICATION/spec.md`, including the `<record>.md` policy exemplar and every concrete seed-prompt, brainstorm, maintainer-rulings, and bd-long-prose-spike citation. While the plan remains live, each citation MUST use `plan/<slug>/...`; archival MUST update citations to `plan/archive/<slug>/...` in the archival change or an explicitly linked work-item, and ratified text MUST NOT prewrite an archive-only citation while the live plan remains. Replace the current archive-stable-path explanatory sentence with that explicit active-path-to-archive-path transition. No headings are added, removed, or renamed.

**This explicitly REPLACES, not merely augments, the existing citation-resolution rule.** The currently ratified bullet 381 requires every design-record citation to use the archive-form path even while the plan is still live ("cite ... `plan/archive/<slug>/research/<record>.md`, not the currently live ... path") and separately says a citation "resolves at `plan/<slug>/...` or `plan/archive/<slug>/...`, whichever exists." This proposal reverses that: citations MUST use the live path while the plan is live, and MUST be updated to the archive path only at archival. The reversal is deliberate, for two reasons: (1) coherence — the migration clause in bullet 375 already obligates a relocation to update every fleet-spec citation of the pre-relocation path, so requiring archive-form citations before archival just creates a citation this repo's own doctor cannot resolve until archival catches up, which is the exact defect this proposal exists to repair; (2) mechanical greppability — a live-path citation is trivially found and rewritten by grepping for the plan's slug at archival time, the same grep the migration clause already performs, whereas a pre-written archive path gives no signal of *when* it becomes valid.

#### Exact replacement text — `SPECIFICATION/spec.md` bullet at line 381

Replace this existing bullet verbatim:

> Design-record citations added to ratified text by this revision MUST use archive-stable paths. For this proposal's design records, cite repo `thewoolleyman/livespec`, `plan/archive/planning-lane-redesign/research/<record>.md`, not the currently live `plan/planning-lane-redesign/research/<record>.md` path, so the citations remain reachable after archive. A plan-record citation resolves at `plan/<slug>/...` or `plan/archive/<slug>/...`, whichever exists, while the cited text keeps the single archive-form path. Rationale: the intent-preservation requirement applied to this migration; design record: repo `thewoolleyman/livespec`, `plan/archive/planning-lane-redesign/research/maintainer-rulings.md`.

With this new bullet:

> Design-record citations added to ratified text MUST use the plan's current live path while the plan remains live: cite repo `thewoolleyman/livespec`, `plan/<slug>/research/<record>.md`, not an archive-form path, so a reader can resolve the citation immediately. This supersedes the prior archive-stable-path rule (which required citing a not-yet-existing archive path before the plan closed): a live-path citation is mechanically greppable at archival time by the same sweep the migration clause above already requires when relocating any plan path, so no ratified sentence is ever left citing a path that does not yet exist, and live-path citations cohere with that relocation-update obligation rather than fighting it. Archival of a plan MUST update, in the archival change itself or an explicitly linked work-item, every design-record citation naming that plan's pre-archival `plan/<slug>/...` path to the corresponding `plan/archive/<slug>/...` path. For this proposal's own design records, cite repo `thewoolleyman/livespec`, `plan/planning-lane-redesign/research/maintainer-rulings.md`. Rationale: the intent-preservation requirement applied to this migration, superseding the archive-stable-path rule for the coherence and greppability reasons stated above; design record: repo `thewoolleyman/livespec`, `plan/planning-lane-redesign/research/maintainer-rulings.md`.
