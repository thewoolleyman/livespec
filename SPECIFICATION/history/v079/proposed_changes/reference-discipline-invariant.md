---
topic: reference-discipline-invariant
author: claude-opus-4-7
created_at: 2026-05-25T17:25:13Z
---

## Proposal: codify-spec-and-code-reference-discipline-as-a-constraint

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Add a §"Reference discipline" section to `constraints.md` that codifies two paired invariants the spec currently has no rule for: (a) source code (Python modules, test modules, skill prose) MUST NOT cite specific spec sections via `§"…"` or analogous formal anchor references, because such citations rot silently when headings rename or move; (b) `SPECIFICATION/*.md` files MUST NOT reference files OUTSIDE the same `SPECIFICATION/` tree (sibling-repo spec files, work-item IDs, epic phase identifiers, or paths into the implementation tree), EXCEPT via a declared, machine-readable allowlist in `.livespec.jsonc`. The allowlist is the carve-out mechanism so that cross-repo coordination contracts (which inherently must name parent-spec sections) can continue to work; everything else is forbidden.

### Motivation

This propose-change emerged from a `/livespec:doctor` LLM-objective phase run against the sibling `livespec-dev-tooling` SPECIFICATION/ tree, which surfaced two findings that are instances of a rule the spec has no name for:

- A broken cross-file `§"Coordination-surface bootstrap procedure"` reference in `livespec-dev-tooling/SPECIFICATION/contracts.md:181` — a companion amendment that never landed but whose citation remained. The static-phase `anchor-reference-resolution` check is intentionally scoped to same-file Markdown link anchors (`[text](#slug)`) per the check's own docstring at `livespec/doctor/static/anchor_reference_resolution.py:17-20` ("Cross-file references and external links are out of scope at the static layer"); the LLM-driven phase caught the dangle but only because a human asked. There is no mechanical guardrail.
- Numerous references in the same sibling spec to `livespec epic li-fgqgnk Phase G.2 / G.4 / G.6` and to `livespec-core` — external work-item / sibling-repo identifiers that the sibling spec can't define internally, so they're undefined-terms when read standalone.

Two paired symptoms surface this same root cause everywhere in the family:

- **Spec rot from heading renames.** `livespec/doctor/static/depends_on_ref_wellformedness.py:14-15` carries the docstring `Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" → §"`depends_on-ref-wellformedness`"`. If either heading is renamed via a revise pass, the docstring rots silently because the static-phase doctor checks intra-file anchors only.
- **Anachronistic stale-proposal language.** `livespec/SPECIFICATION/contracts.md:208` reads `…the threshold value itself is out of scope for this proposal` inside the ratified contract, and `livespec/SPECIFICATION/non-functional-requirements.md:592` reads `As part of accepting this proposal, every comment in the in-scope trees…`. The author wrote these inside a proposed_change file, the revise pass accepted them, but neither file was rewritten in past-tense to reflect post-acceptance state. The pattern is invisible to every existing check; only an LLM-objective sweep notices.

Adding the invariant turns both patterns into mechanically-detectable violations once the companion static check ships, and creates a stable home (the §"Reference discipline" section) for the rule that every doctor-LLM finding of this class can be classified against.

### Proposed Changes

Add a new §"Reference discipline" section to `constraints.md`, placed between the existing §"Heading taxonomy" (line 218) and §"BCP14 normative language" (line 236) since both deal with cross-cutting authoring discipline:

> ## Reference discipline
>
> Two paired invariants govern how `SPECIFICATION/` files reference other content and how source code references spec content. Both invariants exist to keep references stable under heading renames, file moves, and revise-pass content reshuffling; both ROT SILENTLY without the static-phase check codified below.
>
> ### `SPECIFICATION/`-to-`SPECIFICATION/` references
>
> Within a single `SPECIFICATION/` tree, files MAY cite peer files and peer headings via the canonical `<filename>.md §"<Heading text>"` form. Same-file anchor references via Markdown link syntax (`[text](#slug)`) remain governed by `doctor-anchor-reference-resolution`.
>
> ### Forbidden: references OUTSIDE the same `SPECIFICATION/` tree
>
> A `SPECIFICATION/<file>.md` MUST NOT reference any of the following EXCEPT via the allowlist mechanism in §"Allowlist mechanism":
>
> - Sibling-repo spec files (e.g., `livespec/SPECIFICATION/contracts.md` from a non-livespec tree, or `livespec-dev-tooling/SPECIFICATION/...` from a non-dev-tooling tree).
> - Implementation-tree files (`livespec/doctor/`, `livespec_dev_tooling/checks/`, etc.).
> - Work-item identifiers (`li-fgqgnk`, `li-tvi7lm`, etc.) — these live in the active impl-plugin's JSONL store, not in the spec.
> - Epic phase identifiers (`Phase G.2`, `Phase G.4`, etc.) — these are external work-tracking terminology.
> - GitHub PR numbers, branch names, commit SHAs, or other version-control identifiers.
> - URLs pointing to GitHub, Slack, Notion, or any other external system that may go stale.
>
> The invariant exists because a `SPECIFICATION/` tree MUST be readable standalone — a reader with only the tree's files in hand MUST be able to resolve every reference. Cross-repo coordination contracts inherently need to name parent-spec content; the allowlist mechanism is the supported escape hatch, NOT an open license to scatter cross-repo citations through prose.
>
> ### Forbidden: `§"…"` citations from source code
>
> Source code (Python modules under the implementation tree, test modules under `tests/`, skill prose under `skills/<name>/SKILL.md`) MUST NOT cite spec sections via the `§"…"` form or any analogous formal anchor reference. The static-phase `doctor-no-spec-section-citations-in-code` check (codified at §"Doctor static-phase enforcement" below) scans the implementation tree for the pattern and fails on any match.
>
> Source code MAY reference spec files at the FILE level (e.g., `Per SPECIFICATION/contracts.md, this module implements the runtime contract`), but MUST NOT name specific headings within those files. The file-level reference is stable across heading renames; the heading-level reference is not.
>
> ### Allowlist mechanism
>
> Cross-repo coordination requires that sibling-spec trees reference parent-spec content (e.g., this library's spec references `livespec/SPECIFICATION/contracts.md §"Cross-repo coordination — pin-and-bump"`). The allowlist mechanism MUST be declared as a typed block in `.livespec.jsonc` under a top-level `external_references` key:
>
> ```jsonc
> {
>   "external_references": {
>     "livespec": [
>       "SPECIFICATION/contracts.md §\"Cross-repo coordination — pin-and-bump\"",
>       "SPECIFICATION/contracts.md §\"Shared code sync — livespec-dev-tooling\""
>     ],
>     "livespec-runtime": [
>       "SPECIFICATION/contracts.md §\"DependsOnEntry union\""
>     ]
>   }
> }
> ```
>
> The top-level key under `external_references` is a sibling-repo short name (per the §"Sibling discovery" convention in `livespec-dev-tooling/SPECIFICATION/contracts.md`, once that contract is itself promoted into `livespec`'s spec or remains a cross-reference under this allowlist). The value is an array of `<file> §"<heading>"` strings. Any `§"…"` reference to a sibling-repo spec heading MUST appear in the allowlist; references to non-`SPECIFICATION/` paths in sibling repos remain absolutely forbidden.
>
> ### Doctor static-phase enforcement
>
> Two new static-phase doctor checks MUST land alongside this invariant:
>
> - `doctor-no-cross-spec-reference` — scans every `SPECIFICATION/<file>.md` for the `§"…"` pattern; for each match, resolves the target heading. Same-tree matches pass; allowlist-declared external matches pass; everything else fires `fail` with the file path, line number, and the suggested allowlist entry.
>
> - `doctor-no-spec-section-citation-in-code` — scans every source file under the implementation tree (Python modules under `livespec/`, `livespec_dev_tooling/`, etc., and Markdown files under `skills/`) for the `§"…"` pattern. Any match fires `fail` with the file path, line number, and the offending citation.
>
> Both checks MUST short-circuit on the first violation per the existing static-check discipline. The wrapper exit code follows the standard `3 = at least one fail Finding` mapping.

The invariant places carve-outs in `.livespec.jsonc` rather than in `constraints.md` itself because the allowlist is inherently per-consumer (each sibling tree has different parent-spec references) and inherently churning (every new cross-repo amendment adds entries); embedding it in the contract would invert the dependency.

NO change required to existing `dev-tooling/checks/`. The new checks live alongside other doctor static-phase checks at `livespec/doctor/static/`; once `livespec-dev-tooling` Phase G.4 migrates the shared check shape, the new checks MAY migrate too if their argv contract is project-agnostic.

This propose-change documents the SPEC change. The IMPLEMENTATION work — authoring `livespec/doctor/static/no_cross_spec_reference.py` + `no_spec_section_citation_in_code.py` + paired tests + retroactive sweep of existing violations (in livespec's own spec AND in every sibling spec) + populating each sibling's `.livespec.jsonc` `external_references` block — tracks separately as a work-item filed after this propose-change is accepted into v079 (or whichever next-version land matches the revise schedule).
