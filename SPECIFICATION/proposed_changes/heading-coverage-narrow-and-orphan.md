## Proposal: Narrow heading-coverage walk to template-declared NLSpec files at tree roots; add (spec_root, spec_file, heading) triple and orphan direction

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Sharpen `SPECIFICATION/constraints.md` §"Heading taxonomy" so it codifies the heading-coverage registry contract from PROPOSAL.md §"Coverage registry" (lines 3771-3813): (a) entries carry the `(spec_root, spec_file, heading)` triple, not just `(spec_root, heading)`; (b) the walk is narrowed to **template-declared NLSpec files at each spec-tree root** (`spec.md`, `contracts.md`, `constraints.md`, `scenarios.md` for the `livespec` template), excluding the skill-owned `README.md` and never recursing into `proposed_changes/`, `history/`, or `templates/<name>/history/`; (c) the check must fail on the orphan direction too — registry entries whose triple no longer matches any spec heading are flagged. The revise commit rewrites `dev-tooling/checks/heading_coverage.py` against this contract, adds `spec_file` to every surviving registry entry, and prunes `tests/heading-coverage.json` from ~168 entries down to the ~84 spec-root entries (drop everything whose `spec_root` is under `history/` or `proposed_changes/`).

### Motivation

Three pre-existing PROPOSAL-impl drift items, surfaced during Phase 6 + Phase 7 sub-step 1 (decisions.md 2026-05-03T10:50:00Z carried this forward as a deferred Phase 7 propose-change cycle): (1) the check treats every `## ` heading under `SPECIFICATION/**/*.md` as a spec heading, including `## Proposal: <name>` boilerplate in propose-change files, `## Decision and Rationale` in revision records, and per-version snapshot headings — adding ~2 entries of bookkeeping tax to every propose-change cycle; (2) PROPOSAL says the meta-test fails on TWO directions (uncovered + orphan) but the impl only checks one; (3) PROPOSAL specifies entries as `(spec_root, spec_file, heading)` triples, but the impl uses only `(heading, spec_root)` pairs and the registry doesn't carry `spec_file` (so heading-text collisions across files within one tree cannot be disambiguated). User-gated 2026-05-03 as Mini-track item M2 in the Phase 7 enforcement-suite mini-track (Option C). Largest item of the five — relieves the per-cycle bookkeeping tax for sub-step 1.c cycles 2-4 plus all subsequent propose-change cycles.

### Proposed Changes

Single atomic edit: replace `SPECIFICATION/constraints.md` §"Heading taxonomy" (currently two short paragraphs at lines 37-41) with the sharper contract below.

**SPECIFICATION/constraints.md §"Heading taxonomy".** Replace:

> Top-level `#` headings in spec files SHOULD reflect intent rather than a fixed taxonomy. `##` headings within each spec file form the test-anchor surface: every `##` heading MUST have a corresponding entry in `tests/heading-coverage.json` whose `spec_root` field matches the heading's tree per v021 Q3.
>
> The `dev-tooling/checks/heading_coverage.py` script enforces the binding mechanically. Pre-Phase-6 the check tolerates an empty `[]` array; from this seed forward (Phase 6 onward), emptiness is a failure if any spec tree exists.

With the sharper contract:

> Top-level `#` headings in spec files SHOULD reflect intent rather than a fixed taxonomy.
>
> Every `##` heading in a **template-declared NLSpec file at a spec-tree root** MUST have a corresponding entry in `tests/heading-coverage.json`. The registry maps `(spec_root, spec_file, heading)` triples to pytest test identifiers per PROPOSAL.md §"Coverage registry" (lines 3771-3813). The `spec_root` field is the repo-root-relative path to the spec tree's root (main spec = `SPECIFICATION`; sub-specs = `SPECIFICATION/templates/<name>`). The `spec_file` field is the `spec_root`-relative path to the spec file containing the heading (e.g., `spec.md`, `contracts.md`). The `heading` field is the exact `##` heading text. Each entry's `test` field is a pytest node identifier (`<path>::<function>`) OR the literal `"TODO"`; `"TODO"` entries MUST also carry a non-empty `reason` field.
>
> The `dev-tooling/checks/heading_coverage.py` script enforces the binding mechanically at `just check` time. Per tree, the check walks **only the template-declared NLSpec files at the tree root** — for the `livespec` template, the four files `spec.md`, `contracts.md`, `constraints.md`, and `scenarios.md`. The check does NOT recurse into `proposed_changes/`, `history/`, `templates/<name>/history/`, or any other subdirectory; it does NOT include the skill-owned `README.md` at the tree root. Boilerplate headings such as `## Proposal: ...` in propose-change files, `## Decision and Rationale` in revision records, and per-version snapshot headings under `history/v*/` are out of scope for the registry and are NOT counted by the check.
>
> The check fails in three directions:
>
> 1. **Uncovered heading** — a `(spec_root, spec_file, heading)` triple appears in some template-declared spec file but no matching registry entry exists. Diagnostic: `spec heading missing coverage entry`.
> 2. **Orphan registry entry** — a registry entry's `(spec_root, spec_file, heading)` triple does not match any heading in any template-declared spec file (heading was renamed or removed without updating the registry). Diagnostic: `registry entry orphaned — no matching spec heading`.
> 3. **Missing `reason` on a `TODO` entry** — entry carries `test: "TODO"` but no non-empty `reason` field. Diagnostic: `TODO registry entry missing reason`.
>
> The check SKIPS `##` headings whose text begins with the literal `Scenario:` prefix per PROPOSAL.md lines 3779-3782: scenario blocks are exercised by the per-spec-file rule test for the scenario-carrying spec file; per-scenario registry entries are not required.
>
> Pre-Phase-6 the check tolerated an empty `[]` array; from the Phase 6 seed forward (this revision and later), emptiness is a failure if any spec tree exists.

Implementation work that lands atomically with the revise commit per the Phase 7 dogfooding rule: rewrite `dev-tooling/checks/heading_coverage.py` against the new walk + triple-key + orphan-direction contract; add a `spec_file` field to every surviving entry in `tests/heading-coverage.json`; prune the registry to drop every entry whose `spec_root` is under `history/` or `proposed_changes/` (these become out-of-scope under the narrowed walk); update the paired test at `tests/dev-tooling/checks/test_heading_coverage.py` to cover the new walk + the new orphan direction + the missing-reason direction.
