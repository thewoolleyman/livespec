## Proposal: Seed wrapper emits skill-owned files per spec tree

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md

### Summary

Sharpen the seed-wrapper file-emission contract in `contracts.md` and `spec.md` to enumerate the per-tree skill-owned files (`proposed_changes/README.md` and `history/README.md`) and the per-tree `history/vNNN/proposed_changes/` subdirectory marker that the wrapper writes for every spec tree, including each sub-spec. Today the contract only mentions the auto-captured `seed.md` + `seed-revision.md` for the main spec, leaving the per-tree skill-owned files implicit; the wrapper currently writes the skill-owned `proposed_changes/README.md` for the main spec only and never writes any `history/README.md`, which Phase 6 patched imperatively to satisfy doctor.

### Motivation

Phase 6 self-application discovered the gap (open-issues 2026-05-03T02:39:00Z, resolved): `/livespec:doctor`'s per-tree static checks failed against the seeded `SPECIFICATION/` because `proposed_changes/README.md` and `history/README.md` were missing under both sub-spec trees and `history/v001/proposed_changes/` was missing for sub-specs. Phase 6 patched these imperatively under the v018 Q2 / v019 Q1 imperative-window carve-out. Phase 7 sub-step 1 brings the wrapper into alignment with the spec, removing the imperative-window dependency so future seeds against other projects produce a doctor-clean tree end-to-end.

### Proposed Changes

Two atomic edits, one per target file.

**SPECIFICATION/contracts.md §"Sub-spec structural mechanism".** Replace the current second paragraph ("The seed wrapper materializes the main spec tree AND each sub-spec tree atomically per v018 Q1: a single `bin/seed.py --seed-json <payload>` invocation writes every file in every tree, plus the per-tree `history/v001/` snapshot, plus the auto-captured `history/v001/proposed_changes/seed.md` + `seed-revision.md` for the main spec only (sub-specs do NOT receive auto-captured seed proposals per v018 Q1 — the main-spec seed.md documents the multi-tree creation as a whole).") with the sharper enumeration:

> The seed wrapper materializes the main spec tree AND each sub-spec tree atomically per v018 Q1: a single `bin/seed.py --seed-json <payload>` invocation writes, for every spec tree, (a) every template-declared spec file, (b) the skill-owned `proposed_changes/README.md` and `history/README.md` directory-description files, (c) the `history/v001/` snapshot of every template-declared spec file, and (d) the `history/v001/proposed_changes/` subdirectory marker preserved in git via `.gitkeep` when the directory would otherwise be empty. The auto-captured `history/v001/proposed_changes/seed.md` + `seed-revision.md` are emitted for the main spec only; sub-specs do NOT receive auto-captured seed proposals per v018 Q1 — the main-spec `seed.md` documents the multi-tree creation as a whole, and each sub-spec's `history/v001/proposed_changes/` is consequently empty (the `.gitkeep` is the marker).

**SPECIFICATION/spec.md §"Specification model".** Append one sentence to the existing `proposed_changes/` and `history/` subdir paragraph (currently: "The tree MUST contain the template-declared spec files (e.g., `spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`, `README.md` for the `livespec` template), a `proposed_changes/` subdir, and a `history/` subdir.") so it reads:

> The tree MUST contain the template-declared spec files (e.g., `spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`, `README.md` for the `livespec` template), a `proposed_changes/` subdir, and a `history/` subdir. Both the `proposed_changes/` and `history/` subdirs carry a skill-owned `README.md` written by the seed wrapper at seed time and never modified by `revise`; per `contracts.md` §"Sub-spec structural mechanism", every sub-spec tree carries the same skill-owned README pair.

These edits are spec-level only; the wrapper-implementation work that brings `livespec/commands/_seed_railway_emits.py` into alignment lands in the same Phase 7 sub-step 1 cycle, atomically with the revise commit per the Phase 7 dogfooding rule ("every change in this phase lands via a propose-change → revise cycle ... SPECIFICATION/ revisions and code implementation land atomically").
