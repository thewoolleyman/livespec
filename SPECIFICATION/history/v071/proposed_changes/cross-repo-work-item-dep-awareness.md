---
topic: cross-repo-work-item-dep-awareness
author: claude-opus-4-7
created_at: 2026-05-22T02:22:17Z
---

## Proposal: cross-repo-dep-work-item-metadata-fields

### Target specification files

- contracts.md

### Summary

The impl-plugin work-items store contract MUST add two optional fields — `depends_on_external` (array of `<repo>:<work-item-id>` reference strings) and `external_dep_cache` (object keyed by reference string, value `{status: "open"|"closed", checked_at: ISO8601-Z}`) — and the impl-side `next` ranker MUST honor a cached `open` status as a blocker.

### Motivation

Per the parent design discussion, this is the only contract surface that the `next` ranker touches for cross-repo dep awareness: the ranker stays LOCAL-ONLY (preserving the contracts.md line 252 pin that forbids cross-side reads in `next`), and the cross-repo crossing is confined to the resolver skill (separate finding). The two fields are the data shape that resolver writes and ranker reads. Refining the existing 9-skill surface rather than adding a new field-at-a-distance keeps the contract pieces locally cohesive.

### Proposed Changes

Amend `contracts.md` §"Implementation-plugin contract — the 9-skill surface" (specifically the work-item record contract referenced by the `list-work-items`, `capture-work-item`, and `next` skills) to introduce two OPTIONAL work-item fields:

- `depends_on_external` — array of reference strings. Each reference MUST be syntactically `<repo>:<work-item-id>`, where `<repo>` MUST name a configured cross-repo target in `.livespec.jsonc` (per the parallel `cross-repo-dep-livespec-jsonc-target-block` finding). When the field is absent or empty, the work-item has no declared cross-repo dependencies.
- `external_dep_cache` — object keyed by reference string (from `depends_on_external`); each value MUST be an object with two fields: `status` (string enum, `"open"` or `"closed"`) and `checked_at` (string, ISO 8601 with trailing `Z` per existing front-matter conventions). The cache is populated and refreshed only by the resolver skill (per the parallel `cross-repo-dep-resolver-skill` finding); the work-item store itself does NOT mutate this field outside the resolver.

The impl-side `next` ranker MUST honor `external_dep_cache[ref].status == "open"` for any `ref` declared in `depends_on_external` as a hard blocker: work-items with at least one unsatisfied external dep MUST NOT appear in the ranked candidates list, OR MUST appear with an explicit `blocked` urgency band (impl-plugin author's choice; the contract MUST specify ONE of these dispositions per impl-plugin to keep behavior deterministic). When `external_dep_cache` is missing for a declared `ref`, the ranker MUST treat the dep as unsatisfied (conservative default) and surface a `next`-level warning that the resolver hasn't run.

Impl-plugins SHOULD persist these fields using whatever native storage shape their backend supports (JSONL extra keys for plaintext, beads custom fields for beads-backed, etc.); the field NAMES and SEMANTICS are the contract, not the storage layout.

## Proposal: cross-repo-dep-resolver-skill

### Target specification files

- contracts.md

### Summary

A new `livespec` plugin skill — `/livespec:resolve-cross-repo-deps` — MUST be the SOLE place in the system that performs cross-repo reads for work-item dependency resolution. It walks each work-item's `depends_on_external` field, queries the named external repo's impl-plugin via the cross-plugin invocation convention, and writes updated `external_dep_cache` entries back to the local work-item store.

### Motivation

The design principle from the parent discussion: confine the cross-repo crossing to ONE explicit place so that `next` (local-only), doctor (structural-only), and the work-item stores (per-repo) can all stay simple. The resolver is the only piece that knowingly reaches across a repo boundary to look up state. This mirrors the existing thin-transport doctrine (one skill, one contract, one job) and the existing cross-plugin invocation contract (line 52: cross-plugin calls go through the skill namespace).

### Proposed Changes

Add a new skill `/livespec:resolve-cross-repo-deps` backed by a Python wrapper at `.claude-plugin/scripts/bin/resolve_cross_repo_deps.py`. The skill MUST:

1. Read the active impl-plugin's work-items store via `/<impl-plugin>:list-work-items --json` (existing thin-transport surface; cross-plugin invocation per `contracts.md` line 52).
2. Aggregate the union of all `depends_on_external` references across all open work-items.
3. For each external reference `<repo>:<work-item-id>`, look up the target repo's path and impl-plugin from the `cross_repo_targets` block in `.livespec.jsonc` (per the parallel `cross-repo-dep-livespec-jsonc-target-block` finding); if `<repo>` is not configured, surface a finding (NOT a hard error) and skip that reference.
4. For each resolvable external reference, invoke the target repo's impl-plugin via cross-plugin namespace (e.g. `/livespec-impl-plaintext:list-work-items --filter=<id> --json --project-root <target-path>`) to retrieve the external work-item's open/closed status.
5. Write the updated `{status, checked_at}` back to the LOCAL work-item store via the active impl-plugin's update mechanism (the impl-plugin contract MUST surface a write path for the `external_dep_cache` field — e.g., extending `capture-work-item` to accept a partial-update mode, or adding a dedicated `update-work-item` skill; the precise shape is the impl-plugin's prerogative).
6. Emit a structured JSON summary to stdout: total references walked, per-status counts, list of unresolvable references with reasons.

The resolver MUST accept `--project-root <path>` (uniform with all wrappers) and MAY accept `--filter <work-item-ref-substring>` to scope to a single reference. The resolver MUST NOT mutate any spec-side state; it touches ONLY impl-side work-item stores (local for the write-back, remote-via-skill for the read).

The skill MAY be invoked: on-demand by the user, as a doctor pre-step (per `contracts.md` §"Sub-command lifecycle" pre-step extension), or by the project-local Layer 3 loop driver. The skill is lifecycle-exempt from doctor's pre-step/post-step LLM phases (it is mechanical resolution, not authored content).

## Proposal: cross-repo-dep-doctor-structural-invariant

### Target specification files

- contracts.md

### Summary

Doctor's structural invariant catalogue MUST add a new cross-repo dependency invariant that validates the syntactic well-formedness of `depends_on_external` references, the resolvability of each `<repo>` segment against `.livespec.jsonc`, the presence of an `external_dep_cache` entry for each declared reference, and the freshness of cached entries against a configurable staleness threshold.

### Motivation

Doctor is the structural validator that crosses the spec/impl boundary per `contracts.md` line 101. Cross-repo dep references are a new structural surface: malformed refs, dangling refs (pointing at a `<repo>` not configured), and stale caches are exactly the kind of binary mechanically-checkable invariants doctor exists to enforce. This invariant complements (does not duplicate) the existing cross-repo coordination invariant that reads the `compat` block: that one is version-level pin-and-bump; this one is work-item-level dep references.

### Proposed Changes

Amend `contracts.md` §"Doctor's responsibilities" (the catalogue at line 101) to add a new STRUCTURAL invariant entry: **cross-repo work-item dependency well-formedness**. The invariant MUST check, for each open work-item with a non-empty `depends_on_external` field:

1. **Reference syntax**: every entry MUST match `<repo>:<work-item-id>`, where `<repo>` is a non-empty string of `[a-z0-9-]` characters and `<work-item-id>` is a non-empty string matching the impl-plugin's native ID syntax. Malformed refs are findings.
2. **Repo resolvability**: every `<repo>` segment MUST name a key in `.livespec.jsonc`'s `cross_repo_targets` block (per the parallel finding). Unresolvable refs are findings.
3. **Cache presence**: for every reference in `depends_on_external`, `external_dep_cache[ref]` MUST exist. Missing entries are findings (corrective action: run `/livespec:resolve-cross-repo-deps`).
4. **Cache freshness**: `external_dep_cache[ref].checked_at` MUST be within the configurable staleness threshold (new `.livespec.jsonc` key, e.g. `doctor.cross_repo_cache_staleness_hours`, default `24`). Entries older than the threshold are findings (corrective action: run the resolver).

Doctor MUST NOT mutate the work-item store as part of this invariant — staleness/missing-cache findings recommend the user invoke the resolver skill but doctor itself stays read-only, preserving its existing contract role.

This invariant is STRUCTURAL per the contract-pin in line 101 (binary, contract-level, mechanically-checkable) and is NOT a productivity heuristic — it does not rank, score, or judge work-item readiness; it only verifies that the cross-repo dep machinery is in a well-formed state.

## Proposal: cross-repo-dep-livespec-jsonc-target-block

### Target specification files

- contracts.md

### Summary

A new `.livespec.jsonc` top-level configuration block — `cross_repo_targets` — MUST be defined for projects that participate in cross-repo work-item dependency coordination. Each entry maps a short repo name (used as the `<repo>` segment in `depends_on_external` references) to a filesystem path and the impl-plugin to query at that path.

### Motivation

The resolver skill, the doctor invariant, and the work-item metadata fields all depend on a shared way to name external repos and locate them on disk. `.livespec.jsonc` is already the project-level configuration surface; adding the cross-repo target block here keeps configuration centralized rather than scattered across per-skill config files. Filesystem paths are sufficient for the current development pattern (sibling repo checkouts under `/data/projects/` for this maintainer; analogous local layouts for other contributors); git-URL-based remote resolution is a future widening explicitly out of scope for this proposal.

### Proposed Changes

Add a new top-level OPTIONAL key to `.livespec.jsonc`, documented in `contracts.md` §"Cross-repo coordination — pin-and-bump" (or a new sub-section §"Cross-repo work-item dependencies" if the pin-and-bump section is too narrowly scoped to version compat):

```jsonc
{
  // ... existing keys ...
  "cross_repo_targets": {
    "livespec-core": {
      "path": "../livespec",
      "plugin": "livespec"
    },
    "livespec-dev-tooling": {
      "path": "../livespec-dev-tooling",
      "plugin": "livespec-impl-plaintext"
    }
  }
}
```

Each entry's key is the short name used in `depends_on_external` references (e.g., `"livespec-core:li-xyz"`). Each entry's value MUST be an object with exactly two fields:

- `path` — string, filesystem path to the external repo's project root. MAY be absolute or relative to the containing project's root. The path MUST resolve to an existing directory containing a `.livespec.jsonc` file; doctor's invariant (per the parallel finding) MUST verify this.
- `plugin` — string, the impl-plugin name (e.g. `"livespec-impl-plaintext"`) to invoke when querying the external repo's work-items. MUST match a registered impl-plugin namespace.

The block is OPTIONAL at the top level — projects with no cross-repo dependencies omit it entirely. Git-URL-based remote resolution is explicitly deferred to a future propose-change cycle (in scope: filesystem paths only). The block MUST NOT be conflated with the existing `compat` block under `.livespec.jsonc`'s `<impl-plugin>` key, which handles version pin-and-bump — `cross_repo_targets` operates at the work-item-dependency level, not the version level.
