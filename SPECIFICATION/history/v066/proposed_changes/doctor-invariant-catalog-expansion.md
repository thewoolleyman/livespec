---
topic: doctor-invariant-catalog-expansion
author: claude-opus-4-7
created_at: 2026-05-18T17:25:48Z
---

## Proposal: Transient vs durable-pending principle in spec terminology

### Target specification files

- SPECIFICATION/spec.md

### Summary

Articulate the transient-vs-durable-pending principle in the spec's foundational terminology. Items that flow through queue/archive boxes (Proposed Changes, Specification History, and — by extension via the impl-plugin contract — Work Items and Memos) divide into two categories with distinct hygiene treatment. Transient items (memos) are defined by needing disposition; pile-up violates the item type and doctor MUST enforce drain pressure via a hygiene-threshold invariant. Durable-pending items (open work items and pending proposed changes) have pending as a normal state; doctor MUST NOT enforce staleness on them. The principle governs which queue/archives are subject to doctor's hygiene invariants and which are left to productivity tooling.

### Motivation

The 2026-05-18 research revisions in `research/workflow-processes/architecture-summary.html` (Decision 20) and `research/workflow-processes/tool-agnostic-workflow.md` (the new glossary entries for **Durable-pending** and the revised **Doctor** entry) articulated this distinction explicitly after the user raised the asymmetric treatment question (why does doctor enforce memo hygiene but not open work item staleness?). Without the principle stated in the spec, the asymmetry looks arbitrary and future contributors are likely to either (a) add staleness invariants to doctor against the design intent, or (b) drop the memo-hygiene invariant for symmetry with work items. Naming the principle prevents both drifts.

### Proposed Changes

In `SPECIFICATION/spec.md` §"Terminology", add two new term definitions in alphabetical order (**Durable-pending** placed before **Intent**; **Transient (queue/archive item)** placed after **Intent**):

**Transient (queue/archive item)** — An item category in which the item type is defined by needing disposition: the item's value is exhausted on routing to one of its terminal dispositions. Memos are the canonical transient category — every memo MUST eventually flow to a proposed change (spec-bound), a work item (impl-bound), persistent agent knowledge (graduated), or be discarded. Pile-up of transient items violates the type, and doctor MUST enforce drain pressure via a hygiene-threshold invariant against the count of unrouted items. Transient items contrast with **durable-pending** items.

**Durable-pending (queue/archive item)** — An item category in which pending is a normal, expected state. Open work items and pending proposed changes are durable-pending: work takes time, deliberation takes time, and a long-open item is not a hygiene violation. Doctor MUST NOT enforce staleness invariants on durable-pending items. Pile-up and staleness heuristics for durable-pending items are the domain of productivity tooling (the impl-plugin's `next` skill and `livespec-core:next`, both defined by the `implementation-plugin-contract-9-skill-surface` propose-change cycle), NOT of doctor invariants. Doctor MAY enforce structural invariants on durable-pending items (e.g., gap-tracking uniqueness, blocker resolvability, gap-id integrity); the rule is that structural invariants are in scope and productivity heuristics are not.

The **Transient** and **Durable-pending** terms MUST be referenced wherever the spec describes doctor's responsibilities or describes a queue/archive's drain semantics. The principle that doctor enforces structural invariants but not productivity heuristics MUST be load-bearing for proposals that expand doctor's invariant catalog.

## Proposal: Doctor's expanded structural invariant catalog — four work-item invariants

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

Expand doctor's documented invariant catalog with four cross-boundary structural invariants targeting the active impl-plugin's work-items store: 1:1 gap-tracking (every detected gap has exactly one tracked work item across all statuses), no-orphan-blocker (a work item's declared `blocked_by` MUST resolve to an existing work item), no-stale-gap-tied (a gap-tied open work item whose underlying gap no longer detects MUST be closed via a non-fix disposition), and no-duplicate-gap-id (no two open work items MAY claim the same gap-id). All four are STRUCTURAL invariants — binary, contract-level, mechanically checkable — and contrast with productivity heuristics (staleness, pile-up) which doctor MUST NOT enforce. Doctor reads the impl-plugin's work-items store via the impl-plugin's published machine query surface (the exact skill surface is defined by a separate propose-change cycle for the implementation-plugin contract).

### Motivation

The 2026-05-18 research revisions in `research/workflow-processes/architecture-summary.html` (Decision 19) and `research/workflow-processes/tool-agnostic-workflow.md` (the revised **Doctor** glossary entry) identified that doctor's currently-documented invariant catalog (memo hygiene only on the cross-boundary side) under-specifies what doctor SHOULD be checking. The 1:1 gap-tracking invariant is already named in the existing spec (in the §"Beads invariants" section being removed by Proposal 1's deferral to the impl-plugin's own spec) but is not currently associated with doctor as the enforcer. The other three invariants (no-orphan-blocker, no-stale-gap-tied, no-duplicate-gap-id) are new but follow naturally from the structural-vs-productivity principle articulated in the companion transient-vs-durable-pending finding. Without these invariants documented, doctor's responsibility surface remains incomplete and impl-plugin authors lack a clear specification of what doctor will query and how.

### Proposed Changes

In `SPECIFICATION/contracts.md` (add a new section titled "Doctor cross-boundary invariants" placed after the existing §"Doctor cross-cutting hygiene" content or as a new top-level section if no such section yet exists):

- Doctor's responsibilities MUST include structural invariants targeting the active impl-plugin's work-items store, queried via the impl-plugin's published machine query surface (the specific skill is defined by the implementation-plugin contract — a separate propose-change cycle). The catalog MUST include:

  - **`gap-tracking-one-to-one`** — Every gap surfaced by a fresh impl-plugin gap-detection run (i.e., invoking the active impl-plugin's `capture-impl-gaps` skill in a non-mutating dry-run mode at check time) MUST correspond to exactly one tracked work item across all statuses (open, in-progress, closed). The check is a SNAPSHOT — gap detection runs at check time and the resulting gap-id set is compared against the work-items store's current set of gap-id labels. The check fires `fail` when a gap-id appears zero times (untracked gap) or two-or-more times (duplicated tracking) in the work-items store. Replaces the gap-tied invariant content currently embedded in the soon-to-be-removed §"Beads invariants" / §"Gap-tied issue closure verification" sections (per the `multi-repo-distribution-and-coordination` propose-change cycle's section removals).

  - **`no-orphan-blocker`** — Every work item's declared `blocked_by` reference MUST resolve to an existing work item in the same impl-plugin's store. The check fires `fail` when a `blocked_by` reference targets a non-existent work-item id. Closed blockers are NOT orphans (their blocked-by relationship is historically valid); only missing-from-store ids fire the check.

  - **`no-stale-gap-tied`** — A gap-tied open work item whose underlying gap no longer surfaces in a fresh impl-plugin gap-detection run MUST be closed via a non-fix disposition (`spec-revised`, `no-longer-applicable`, `resolved-out-of-band`, or equivalent administrative reason). The check fires `warn` (NOT `fail`) when an open gap-tied work item's gap-id is absent from a fresh detection run, with narration directing the user to close the item via the appropriate non-fix path.

  - **`no-duplicate-gap-id`** — No two open work items MAY claim the same gap-id label. The check fires `fail` when two or more open items share a gap-id. (Closed items sharing a historical gap-id with an open item are exempt; this is the dual of `gap-tracking-one-to-one` viewed from the work-items-store side.)

- All four checks MUST be classified as STRUCTURAL invariants per the transient-vs-durable-pending principle. Doctor MUST NOT add productivity-heuristic invariants (work-item staleness, work-item pile-up counts, etc.); those concerns belong to the impl-plugin's `next` skill and any project-local orchestration layer.

In `SPECIFICATION/constraints.md` (add a new sub-section under the existing doctor-static-check pattern, alongside `accept-decision-snapshot-consistency`):

- For each of the four invariants above, the cross-boundary nature of the check (it queries the impl-plugin's machine surface, not livespec-core-internal state) MUST be reflected in the check's exit-code derivation: a missing or unresponsive impl-plugin query surface MUST surface as a `fail` Finding (lifting the wrapper exit to non-zero) rather than as a silent skip. The check IDs MUST follow the existing slug convention (lowercase-hyphenated, e.g., `gap-tracking-one-to-one`, `no-orphan-blocker`).

- The doctor invariant catalog MUST be enumerable from a single named registry inside `livespec.doctor.static` so contributors and tools can list all checks programmatically; the registry contract follows the existing slug↔module-name mapping pattern stated for §"File naming and invocation". The four new check IDs MUST appear in this registry.

## Proposal: Contract-version-compatibility doctor invariant

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add a `contract-version-compatibility` doctor invariant that fires when the active impl-plugin's pinned `livespec-core` release tag (declared in the per-plugin `compat` block in `.livespec.jsonc` per the pin-and-bump cross-repo coordination mechanism) drifts beyond a configured threshold against the actually-installed `livespec-core` version. The invariant closes the loop between Proposal 1's pin-and-bump mechanism and doctor's enforcement: pin-and-bump declares intent and audits version state; this invariant turns version drift into a hard finding rather than silent breakage.

### Motivation

Proposal 1 introduces the pin-and-bump cross-repo coordination mechanism (`livespec.compat.json` with a `compat` block declaring `livespec_core` semver range and `pinned` tag) but leaves enforcement of drift unspecified. Without doctor-level enforcement, the pin-and-bump mechanism is advisory only — consumers can let their impl-plugin's pin drift arbitrarily far behind a `livespec-core` release without any signal, eroding the whole multi-version-served discipline. The 2026-05-18 research revisions in `research/workflow-processes/architecture-summary.html` (Decisions 16 and 19, which include contract-version compatibility in the doctor invariant catalog) and `research/architecture/multi-repo-implementation-providers.md` §"Genuine concerns → Concern 3 (Contract evolution)" (marked substantially resolved by this mechanism) identified the invariant as the bridge between the structural decision and operational enforcement.

### Proposed Changes

In `SPECIFICATION/contracts.md` (under the same "Doctor cross-boundary invariants" section introduced by Finding 2, or as a follow-on subsection):

- A `contract-version-compatibility` doctor invariant MUST be defined. The invariant reads the active impl-plugin's `compat` block from `.livespec.jsonc` (the block defined by Proposal 1's pin-and-bump cross-repo coordination section) and compares:
  1. The `livespec_core` semver range against the actually-installed `livespec-core` version (from `livespec-core`'s `plugin.json.version`). When the installed version falls OUTSIDE the declared range, the check MUST fire `fail`.
  2. The `pinned` tag value against the most-recent published `livespec-core` release tag. When the pinned tag is older than a configured drift threshold (measured in number of intermediate releases — exact threshold value deferred to a configuration key under `livespec-core`'s top-level `.livespec.jsonc` section, default value to be set by a follow-on refinement), the check MUST fire `warn` with narration directing the user to open a bump-pin PR.

- A missing or malformed `compat` block on the active impl-plugin MUST fire `fail` — the pin-and-bump mechanism is REQUIRED, not optional. (Consumers using a `livespec-impl-*` plugin without declaring `compat` are running out-of-contract.)

- A missing `livespec-core` installation MUST be detected by doctor's existing pre-step lifecycle (the `pre_check` static phase that runs before each invariant check; doctor's wrapper resolves the installed `livespec-core` version once and fails fast if it cannot be located), NOT by this invariant. This invariant assumes `livespec-core` is installed and reports the version it finds via the pre-step resolution.

- The check ID MUST be `contract-version-compatibility` per the slug convention. The check MUST appear in the doctor static registry alongside the four work-item structural invariants from Finding 2.
