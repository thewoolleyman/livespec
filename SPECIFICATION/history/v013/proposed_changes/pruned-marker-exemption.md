---
topic: pruned-marker-exemption
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-05T03:00:13Z
---

## Proposal: doctor version-directories-complete pruned-marker exemption

### Target specification files

- SPECIFICATION/spec.md

### Summary

Codify in spec.md §"Pruning history" the exemption granted to the pruned-marker directory by the `version-directories-complete` doctor static check. Every `<spec-root>/history/vNNN/` directory that is not the pruned-marker directory MUST contain its template-required files, a `proposed_changes/` subdir, and (when the active template declares a per-version `README.md`) a matching `README.md`; the pruned-marker directory (the oldest surviving v-directory, identified by the presence of `PRUNED_HISTORY.json` at its root) MUST contain ONLY `PRUNED_HISTORY.json` and is exempt from the standard contents requirement. The `version-directories-complete` doctor static check honors this exemption.

### Motivation

PROPOSAL.md §"Doctor static checks" lines 2777-2785 codify the `version-directories-complete` doctor static check and grant a specific exemption for the pruned-marker directory: the consumer-side rule that a marker directory contains ONLY `PRUNED_HISTORY.json` (no template-required spec files, no `proposed_changes/` subdir, no per-version README.md). This exemption is the doctor-check counterpart to the producer-side mechanic codified at spec.md line 40 (the `prune-history` lifecycle paragraph) which describes how `prune-history` constructs the marker directory by replacing `v(N-1)/`'s contents with a single `PRUNED_HISTORY.json` document.

The Phase 6 seed materialized minimum-viable contracts.md content but did not enumerate per-doctor-check semantics; the existing spec.md §"Pruning history" paragraph (line 49-51) covers the producer-side summary only. Without codifying the consumer-side exemption explicitly, a clean re-implementation of the doctor's `version-directories-complete` check could mistakenly fail-flag the pruned-marker directory for missing template-required files (the directory only contains `PRUNED_HISTORY.json` post-prune) — and Phase 7 sub-step 6.c.7's prune-history Green impl, which produces the marker directory shape the doctor check must tolerate, cannot land cleanly without the round-trip pre-step doctor static check cascading on its own marker output.

This proposal closes that gap by codifying the exemption inline at the natural producer/consumer adjacency in spec.md §"Pruning history". The architecture-vs-mechanism discipline (constraints.md §"Code style") leaves the exact check-implementation algorithm (file-listing predicate, marker-presence detection helper, applicability dispatch) to the doctor-check author.

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md §"Pruning history"**: append a new paragraph immediately after the existing single-paragraph summary (currently a one-sentence summary at line 51) codifying the `version-directories-complete` pruned-marker exemption.

Old text (the existing single-paragraph contents of §"Pruning history"):

> `prune-history` MAY remove the oldest contiguous block of `history/v*/` directories down to a caller-specified retention horizon while preserving the contiguous-version invariant for the remaining tail. Phase 3 lands the parser-only stub; Phase 7 widens it to the actual pruning mechanic.

New text (existing paragraph plus appended exemption paragraph):

> `prune-history` MAY remove the oldest contiguous block of `history/v*/` directories down to a caller-specified retention horizon while preserving the contiguous-version invariant for the remaining tail. Phase 3 lands the parser-only stub; Phase 7 widens it to the actual pruning mechanic.
>
> **`version-directories-complete` pruned-marker exemption (PROPOSAL.md §"Doctor static checks" lines 2777-2785).** The `version-directories-complete` doctor static check enforces that every `<spec-root>/history/vNNN/` directory contains the full set of template-required spec files, a `proposed_changes/` subdir, and — when the active template declares a versioned per-version `README.md` (the built-in `livespec` template declares one; the built-in `minimal` template does not, per v014 N1 / v015 O2) — a matching `README.md`. The pruned-marker directory is exempt from this requirement: the oldest surviving v-directory under `<spec-root>/history/`, when its root contains a `PRUNED_HISTORY.json` document, MUST contain ONLY `PRUNED_HISTORY.json` (no template-required spec files, no `proposed_changes/` subdir, no per-version `README.md`). The marker-detection predicate is the literal presence of `PRUNED_HISTORY.json` at the directory root; the `version-directories-complete` static check honors this exemption uniformly across main spec and sub-spec trees. This is the consumer-side counterpart to the producer-side mechanic in §"Sub-command lifecycle" (the `prune-history` lifecycle paragraph), which describes how `prune-history` replaces `<spec-root>/history/v(N-1)/`'s contents with a single `PRUNED_HISTORY.json` file when constructing the marker directory.
