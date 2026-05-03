# Constraints — `minimal` template

This sub-spec's constraints scope the `minimal` template's structural well-formedness invariants. NLSpec discipline rules (BCP14, gherkin, heading taxonomy) are inherited from the `livespec` template's sub-spec for any `minimal`-rooted project that authors gherkin scenarios; the `minimal` template itself does NOT enforce those conventions on end-user content beyond the BCP14 keyword discipline.

## Single-file end-user output

End-user output of the `minimal` template MUST be a single `SPECIFICATION.md` file at the project root. The `template.json` `spec_root: "./"` plus a single declared file path enforces this. Multi-file `SPECIFICATION/` layouts are NOT compatible with the `minimal` template; projects that need multi-file should use the `livespec` template.

This constraint applies only to end-user output. This sub-spec — internal to `livespec` — uses the multi-file livespec layout uniformly per v020 Q1.

## `spec_root: "./"` convention

The `minimal` template's `template.json` MUST declare `spec_root: "./"` (literal). The doctor static phase's `template-exists` check MUST tolerate this string value plus the single-file shape; per-tree spec-file path validation MUST resolve `SPECIFICATION.md` relative to the project root rather than to `<spec_root>/SPECIFICATION/`.

## Gherkin blank-line format check exemption

The doctor static phase's `gherkin-blank-line-format` check (Phase 7 widening) MUST exempt `minimal`-rooted projects whose `SPECIFICATION.md` does NOT contain any fenced ` ```gherkin ` blocks. The exemption avoids false-positive failures for spec content that has no scenario-style narrative. When `SPECIFICATION.md` does contain gherkin blocks, the check MUST apply normally.

This exemption is selective, not blanket. End-user `minimal`-rooted projects that adopt gherkin-style scenarios within their single-file spec carry the same well-formedness obligation as `livespec`-template-rooted projects.

## BCP14 normative-keyword well-formedness

End-user `SPECIFICATION.md` content for `minimal`-rooted projects MUST use BCP 14 (RFC 2119 + RFC 8174) requirement language for normative statements. The doctor static phase's BCP14 well-formedness check (Phase 7 widening) MUST detect malformed normative usage in `SPECIFICATION.md` regardless of the template chosen.

The `minimal` template ships with no `livespec-nlspec-spec.md` reference doc of its own; the BCP14 discipline is inherited from `livespec`'s baseline normative conventions. Custom-template authors who fork `minimal` MUST decide whether to ship their own NLSpec discipline doc or inherit `livespec`'s.

## Single-file delimiter-comment well-formedness

When the Phase 7 delimiter-comment format lands (TBD per this sub-spec's contracts.md), `SPECIFICATION.md` content MUST satisfy the well-formedness invariants stated there: HTML-comment marker syntax, paired open/close, kebab-case region names, no nested-boundary crossing. Pre-Phase-7, end-user content MAY omit delimiter markers entirely.

## Version-contiguity and topic-format constraints

`minimal`-rooted projects' `<project-root>/history/v<NNN>/` directories follow the same contiguous-version invariant the `livespec` template enforces. `<project-root>/proposed_changes/<topic>.md` filenames follow the same kebab-case topic-format constraint. These constraints are template-agnostic invariants of `livespec`'s lifecycle layer, not template-specific to `minimal`.
