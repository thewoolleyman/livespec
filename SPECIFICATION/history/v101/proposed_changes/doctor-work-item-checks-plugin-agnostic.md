---
topic: doctor-work-item-checks-plugin-agnostic
author: claude-opus-4-8
created_at: 2026-06-09T01:36:24Z
---

## Proposal: Doctor work-item invariants enforce plugin-agnostically via the list-work-items wrapper

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Replace the v1 'direct JSONL read … only livespec-impl-plaintext supported' cross-boundary mechanism for the six work-item integrity invariants (no-orphan-dependency, no-stalled-epic, no-duplicate-gap-id, no-stale-gap-tied, depends_on-ref-wellformedness, unresolved-spec-commitment) with a plugin-agnostic mechanism: each check acquires the materialized work-items by invoking the ACTIVE impl-plugin's `list-work-items --filter all --json` thin-transport wrapper, resolved via the `LIVESPEC_IMPL_LIST_WORK_ITEMS` environment variable. This makes the invariants ENFORCE under any impl-plugin backend (plaintext JSONL store AND beads/Dolt-server tenant) rather than hard-gating to plaintext and skipping family-wide.

### Motivation

Today the six checks read `<project_root>/work-items.jsonl` directly and hard-gate to `_SUPPORTED_PLUGINS = {livespec-impl-plaintext}`, returning a `skipped` Finding for every other plugin. Since the livespec family migrated off the plaintext JSONL store onto the beads/Dolt-server backend (work-item dolt-server-db6q3r), the checks SKIP everywhere and provide zero enforcement. The fix is to read work-items through the impl-plugin's existing `list-work-items` thin-transport machine surface (a top-level JSON array of materialized work-item views), which every impl-plugin exposes per the §'Thin-transport skills' required surface and which is backend-agnostic by construction.

### Proposed Changes

Amend the §'Doctor cross-boundary invariants' section as follows.

(1) Section intro: state that the six work-item integrity invariants acquire their work-items by invoking the active impl-plugin's `list-work-items --filter all --json` thin-transport wrapper, resolved via the `LIVESPEC_IMPL_LIST_WORK_ITEMS` environment variable (an absolute path to the active impl-plugin's `list_work_items.py`). The wrapper emits a top-level JSON ARRAY of materialized work-item views; the doctor check runs it as a subprocess from cwd=`<project_root>`, inheriting the caller's environment (which supplies any backend-specific connection prerequisites, e.g. the beads tenant credentials). This mechanism is plugin-agnostic — it works identically for `livespec-impl-plaintext` (a JSONL store) and `livespec-impl-beads` (a Dolt-server tenant) and any future backend.

(2) Graceful skip (no CI regression): when `LIVESPEC_IMPL_LIST_WORK_ITEMS` is unset, OR the wrapper invocation fails to connect (no live provider / no credentials / nonzero exit / non-array output), each of the six checks MUST return a `skipped` Finding with a clear message ('no live work-item provider configured' / 'work-item store unreachable') — NOT a `fail`. A genuine wrapper CONNECTION failure is treated as a skip; only an actual invariant violation fires `fail` (or `warn` for no-stale-gap-tied). This preserves the hermetic-CI behavior (where the env var is unset and the checks already skip) while enabling live enforcement at the orchestrator's doctor janitor gate.

(3) Remove the 'direct JSONL read of the active impl-plugin's work-items store. Only `livespec-impl-plaintext` is supported in v1; other plugins receive a `skipped` Finding' language wherever it appears in the section intro and in each of the six per-invariant sub-sections (`no-orphan-dependency`, `no-stalled-epic`, `no-duplicate-gap-id`, `no-stale-gap-tied`, `depends_on-ref-wellformedness`, `unresolved-spec-commitment`), replacing it with a reference to the plugin-agnostic `list-work-items`-wrapper mechanism above. The invariant LOGIC each sub-section describes is unchanged; only the data-acquisition path changes.

(4) Note that the `LIVESPEC_IMPL_LIST_WORK_ITEMS` env var (plus the per-tenant backend connection) is exported by the Layer 3 orchestrator's doctor janitor gate (per the orchestrate driver's §'Cross-repo state aggregation' read-path), so the six checks RUN live at the gate; in hermetic CI the env var is unset and they skip. The `no-stale-gap-tied` invariant additionally derives its current-gap-id set from the live `<spec-root>/` content (unchanged).
