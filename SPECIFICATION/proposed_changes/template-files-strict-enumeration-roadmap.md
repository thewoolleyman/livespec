---
topic: template-files-strict-enumeration-roadmap
author: livespec-bootstrap-phase12
created_at: 2026-05-06T17:25:26Z
---

## Proposal: template-files-strict-enumeration-roadmap

### Target specification files



### Summary

Codify v1.0 acceptance of two doctor-static checks' loose file-enumeration behavior — `out_of_band_edits` and `anchor_reference_resolution` both walk top-level `*.md` files at HEAD under `<spec-root>/` without filtering against the active template's declared file set. Strict template-declared filtering is recognized as a future correctness improvement and tracked here as a post-v1.0 roadmap item (with prereq cascade enumerated). The acceptance is the v1.0 contract; this proposed change cuts a new history version recording it, with no spec-file edits (the v1.0 spec files are byte-identical to v045).

### Motivation

Bootstrap residue closure for items A1 + A2 (decisions.md 2026-05-05T07:30:00Z + 07:45:00Z). The Phase-7 dogfooding cycles surfaced that strict template-declared-file enumeration would require ~5 prereq Red→Green cycles plus an architectural call on sub-spec template-name resolution; the user explicitly chose deferral, with the v1.0 behavior preserved. Phase 12.2 codifies that acceptance via a single audit-trail-bearing propose-change/revise cycle, then archives the bootstrap directory.

### Proposed Changes

No spec-file edits (this is a roadmap acknowledgment cycle, not a contract revision). The v1.0 acceptance + post-v1.0 prereq cascade are documented in this proposed-change file's body below.

## v1.0 behavior (accepted)

Two doctor-static checks under `livespec/doctor/static/` use a loose top-level enumeration when listing spec-tree files at HEAD:

- `out_of_band_edits` walks `<spec-root>/*.md` at HEAD via `list_at_head` and treats every match as a candidate spec file.
- `anchor_reference_resolution._list_top_level_md_files` walks the working-tree `<spec-root>/` directory for `*.md` matches via `fs.list_dir`.

Neither filters against the active template's declared file set (which would require resolving the template root + reading `template.json`'s `specification-template/` walk and comparing each candidate's path against the declared tuple).

For the v1 built-in templates (`livespec`, `minimal`), `specification-template/` subtrees are `.gitkeep`-only at the templates' canonical state, so strict and loose enumerations return functionally identical sets in practice. Loose enumeration is functionally correct for v1.0; strict tightening is a future correctness improvement, not a current-behavior bug fix.

## Post-v1.0 roadmap (strict tightening)

When the DoctorContext widening for richer template-config inspection lands (anticipated as part of the doctor LLM-driven phase orchestration), apply this tightening. The prereq cascade is captured here verbatim from `bootstrap/decisions.md` 2026-05-05T07:45:00Z so a future implementer has the full context:

1. **Introduce `livespec/io/template_files.py`** exporting `enumerate_template_spec_files(*, template_root: Path) -> IOResult[tuple[Path, ...], LivespecError]`. The helper reads `<template_root>/template.json`'s `spec_root`, walks `<template_root>/specification-template/<spec_root>/` for immediate file children, and returns the sorted tuple of paths relative to `<spec_root>`.
2. **Update `out_of_band_edits.run`** to use the strict enumerator instead of `list_at_head` on `spec_root`. Tests pin: a non-template-declared file at HEAD that diverges is IGNORED; a template-declared file diverging is flagged.
3. **Apply the same tightening** to `anchor_reference_resolution._list_top_level_md_files` (replace working-tree `fs.list_dir` walk with the strict enumerator).
4. **Architectural call on sub-spec template-name resolution.** Sub-specs under `SPECIFICATION/templates/<name>/` have no per-tree `.livespec.jsonc`. The strict enumerator needs each sub-spec to know its template root. Two viable mechanisms: (a) directory-name inheritance — `SPECIFICATION/templates/livespec/` resolves template-name = `livespec`, looked up via the resolve_template helper; (b) per-sub-spec `.livespec.jsonc` config. Decision pending; (a) is recommended for ergonomic reasons but requires no per-tree opt-out.
5. **DoctorContext widening.** Add `template_root: Path` (or equivalent) to `DoctorContext` so checks can read the active template's declared files without re-resolving per call.

Estimated work: ~5 Red→Green cycles + 1 architectural call. Tracked here as a single roadmap item rather than 5 separate proposed changes; a future maintainer files an implementation propose-change against the live spec when the work begins.

## Acceptance

This proposed change is accepted as v1.0 contract with no spec-file edits; the v046 history snapshot is byte-identical to v045 (per the v038 D1 Statement B mechanism for accept-with-no-resulting-files). The roadmap text above is preserved verbatim in `SPECIFICATION/history/v046/proposed_changes/template-files-strict-enumeration-roadmap.md` for future implementer reference.
