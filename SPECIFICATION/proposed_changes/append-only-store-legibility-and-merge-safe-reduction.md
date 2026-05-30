---
topic: append-only-store-legibility-and-merge-safe-reduction
author: claude-opus-4-8
created_at: 2026-05-30T21:44:43Z
spec_commitments:
  impl_followups:
    - id_hint: impl-plaintext-supersedes-field
      description: |
        Realize the self-identification + order-independent-reduction obligations in livespec-impl-plaintext: add a supersession field (the 16th key) to the Work-items and Memos JSONL record schemas; define the materialized-view reduction by supersession-chain head with a deterministic tie-break (captured_at, then a stable per-record identity); deprecate and remove the 'latest record by file order wins' rule from spec.md and contracts.md; and add a `.gitattributes` `*.jsonl merge=union` entry (now safe precisely because reduction no longer depends on physical line order).
    - id_hint: impl-plaintext-reducer-in-livespec-runtime
      description: |
        Move the plaintext append-log reduction into the canonical livespec_runtime reducer and refactor the list-work-items, list-memos, and next thin-transport wrappers (plus migrate_beads/detect-impl-gaps where they read the store) to delegate to it, so no wrapper re-implements reduction independently.
    - id_hint: append-store-doctor-integrity-invariants-impl
      description: |
        Implement the no-divergent-heads and no-raw-store-read doctor cross-boundary invariants for the plaintext (JSONL) backend and wire them into the doctor invariant catalogue, covering both the work-items and memos stores.
---

## Proposal: merge-order-independent-materialized-reduction

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Refine the cross-plugin materialized-view contract so the reduction from a git-committed append-structured store to current state is independent of the physical order of records. Today the contract anchors reduction on physical position ("the materialized view is the latest JSONL line"), which is non-commutative under git merge: two concurrent appends merged in opposite directions can elect different winners, silently corrupting state.

### Motivation

Concrete incident (2026-05-30, openbrain): the work-items store is append-only with 'latest record by file order wins' reduction; an entity that transitioned open then closed has two physical records. Separately from a read-side misread, the order-based reduction is itself unsafe under concurrency: there is no `.gitattributes merge=union` or merge driver anywhere in the ecosystem (verified across livespec, livespec-impl-plaintext, openbrain), so concurrent appends from parallel worktree agents produce textual conflicts whose manual resolution can reorder lines and flip the elected record. Reduction must not depend on a property (line order) that git is free to change during a merge.

### Proposed Changes

Amend §"Implementation-plugin contract — the 10-skill surface" (anchored at §"Backend-variability asymmetry") and the materialized-view references in §"Cross-repo dependency awareness" → §"Exhaustive live-walk resolution semantics":

- Add a scoping definition: a *git-committed append-structured store* is any impl-plugin Work Items / Memos store that (a) is committed to git as its audit trail and (b) records state transitions by appending new records rather than rewriting existing ones. The obligations below apply ONLY to backends that make this design choice; a backend whose store has no such property (e.g. a transactional database) is exempt.

- For such stores: the materialized view of an entity MUST be derivable by a reduction that is INDEPENDENT of the physical order of records in the store file. Each appended record MUST carry an in-record signal sufficient to determine supersession order among records sharing one entity id (e.g. a pointer to the prior record's stable per-record identity, or a causal/logical clock). Physical file/line position MUST NOT be the reduction key.

- Replace the phrase "the materialized view is the latest JSONL line" at §"Exhaustive live-walk resolution semantics" with "the materialized view as defined by the impl-plugin's order-independent reduction (per §\"Backend-variability asymmetry\")", preserving the surrounding rule that uncommitted/just-appended state is included when resolving against the current repo.

- State explicitly that concurrent divergence (two records for one entity, neither superseding the other) MUST be representable and detectable by the reduction, NOT silently resolved by picking one (see the companion no-divergent-heads invariant).

## Proposal: append-store-record-self-identification

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Require every record in a git-committed append-structured store to self-identify, from record content alone, as either an original (non-superseding) record or an amendment that supersedes a specific prior record. This makes append history mechanically unambiguous to any reader and eliminates the failure mode where multiple physical records for one entity are mistaken for duplicates or data corruption.

### Motivation

Concrete incident (2026-05-30, openbrain): an agent inspecting the work-items store directly saw two physical lines for one id (open, then closed) and concluded 'duplicate record / data anomaly,' then reported it as a defect. Nothing in the record content marked the second line as a superseding version of the first; the latest-record-wins semantics lived only in skill-private reducer code. A self-identifying record makes 'these are duplicates' an unreasonable reading rather than a plausible one.

### Proposed Changes

Add to §"Implementation-plugin contract — the 10-skill surface" → §"Backend-variability asymmetry":

- For a git-committed append-structured store, the record schema MUST include a field by which each record either (a) declares the stable per-record identity of the prior record it supersedes, or (b) is identifiable as an original record that supersedes nothing. This is the in-record signal the order-independent reduction consumes (companion finding merge-order-independent-materialized-reduction).

- A reader encountering more than one record for a single entity id MUST be able to determine, from record content alone, which record is the current head and which are superseded history — WITHOUT consulting external file order and without running skill-private logic. Superseded records remain in the store as audit trail (existing rule); the new requirement is only that they be self-evidently superseded.

- Note (non-normative): this complements but does not replace the existing `superseded_by` field semantics in impl backends; the realization finding reconciles the concrete field shape in livespec-impl-plaintext.

## Proposal: store-state-only-via-query-surface

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Extend the Thin-transport skill doctrine so that any consumer needing impl-store state obtains it through the published thin-transport query skills (or the shared livespec_runtime reducer they delegate to), and never by directly parsing the backing store file. This governs the READ PATH only; the backing file remains the source of truth and the audit trail.

### Motivation

Root cause of the 2026-05-30 incident: the agent had the correct query skill available (list-work-items, which returns the reduced one-record-per-id view) but switched to hand-parsing the raw store file for a detail drill-down, which re-derived the reduction badly and exposed unreduced history. The doctrine currently mandates that every contract-surface API be a skill, but is silent on consumers bypassing the surface to read the backing file directly.

### Proposed Changes

Extend §"Thin-transport skill doctrine":

- Add: any consumer of impl-store state — doctor's cross-boundary invariants, the project-local orchestration layer, another plugin, or operator/agent tooling — MUST obtain that state through the active impl-plugin's thin-transport query skills (e.g. list-work-items, list-memos, next) or through the shared livespec_runtime reduction primitive those skills delegate to. Direct parsing of a backing store file by shipped code is NON-CONFORMING.

- Clarify scope: this constrains the READ PATH, not storage. The backing append store remains the committed source of truth and audit trail. 'Non-conforming' targets shipped code in livespec-governed repos; it is enforced mechanically by the companion no-raw-store-read invariant. It cannot police an ad-hoc interactive shell command, and the doctrine MUST say so — the residual risk there is mitigated by the self-identification and order-independent-reduction obligations, which make a raw read self-explanatory rather than misleading.

## Proposal: canonical-reduction-in-livespec-runtime

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Locate the canonical append-log-to-materialized-view reduction in livespec_runtime as the single implementation that every impl-plugin thin-transport query skill and every doctor cross-boundary invariant consumes. This prevents reduction logic from being re-derived (and drifting) per skill.

### Motivation

If each thin-transport wrapper carries its own copy of 'latest-record-wins,' the reduction algorithm can drift between skills and between skills and doctor, and an ad-hoc reducer (as in the incident) has no shared, tested implementation to fall back on. A single shared reducer is also the only sane home for supersession-chain resolution and divergent-head detection introduced by the companion findings.

### Proposed Changes

Extend §"Shared runtime — livespec-runtime":

- Add a canonical store-reduction surface (e.g. `livespec_runtime.store`) that accepts the append records of a git-committed append-structured store and returns the materialized current-state set, resolving supersession chains in an order-independent way (companion finding merge-order-independent-materialized-reduction) and surfacing any entity with divergent un-superseded heads as an explicit, detectable result rather than a silently-chosen winner.

- Require that every impl-plugin's thin-transport query wrappers and doctor's cross-boundary invariants consume this function rather than re-implementing reduction. The per-backend adapter (how a backend's records map onto the reducer's record/identity/supersession concepts) is owned by the impl-plugin per §"Backend-variability asymmetry"; the reduction algorithm itself is shared.

## Proposal: doctor-append-store-integrity-invariants

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add two doctor cross-boundary invariants that make the preceding obligations self-proving and regression-proof in every livespec-governed repo: no-divergent-heads (fail when any entity resolves to more than one un-superseded head) and no-raw-store-read (fail when shipped code reads a backing store file directly instead of via the reducer/skill surface).

### Motivation

Mechanical enforcement is the whole point: a contract MUST with no doctor teeth is what allowed the incident (the contract already says 'readers MUST read materialized views,' and nothing stopped a raw read). The no-divergent-heads check converts a silent bad merge into a hard gate failure across every append-structured store (work-items, memos, future stores); no-raw-store-read keeps the read-path discipline true in committed code over time.

### Proposed Changes

Add two entries to §"Doctor cross-boundary invariants" (both STRUCTURAL — binary, contract-level, mechanically checkable per the transient-vs-durable-pending principle; neither is a productivity heuristic):

- `no-divergent-heads` — For each git-committed append-structured store declared by the active impl-plugin, materialize via the livespec_runtime reduction and fire `fail` when any entity id resolves to more than one un-superseded head (an unresolved concurrent-merge divergence). Narration MUST name the offending entity id and point at the conflicting record identities so the operator can append a reconciling record.

- `no-raw-store-read` — Fire `fail` when shipped plugin or consumer code in a livespec-governed repo opens a declared backing store path directly (bypassing the reduction/skill surface required by §"Thin-transport skill doctrine"). The check's scope is committed code; the contract MUST state explicitly that it cannot police ad-hoc interactive shell invocations, so the self-identification and order-independent-reduction obligations remain the defense for that residual surface.
