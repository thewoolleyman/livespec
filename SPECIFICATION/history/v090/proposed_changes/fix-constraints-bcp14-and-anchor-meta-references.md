---
topic: fix-constraints-bcp14-and-anchor-meta-references
author: claude-opus-4-7
created_at: 2026-05-27T07:48:00Z
---

## Proposal: rephrase-bcp14-shall-meta-reference-to-avoid-literal-keyword

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Rephrase the §BCP14 normative language meta-reference in constraints.md:298 so it does not contain the literal mixed-case word that the bcp14_keyword_wellformedness check is itself supposed to detect. The check scans for the literal token regardless of inline-code backticks, so the rule's own prose has been tripping the rule.

### Motivation

The constraints.md text describing what the bcp14_keyword_wellformedness check MUST detect contains the literal mixed-case BCP 14 keyword as an example. The check's regex uses `\bShall\b` and does not skip backtick-wrapped tokens, so the rule's documentation has been self-violating since the rule was authored. doctor's static phase currently emits a `fail` finding pointing at this self-violation on every run. The rewrite preserves the rule's intent while expressing the example via lowercase-form descriptive language that the check correctly skips.

### Proposed Changes

Edit constraints.md line 298. Old text: "Doctor's static-phase `bcp14_keyword_wellformedness` check MUST detect mixed-case `Shall` as the unambiguous-mismatch case — no descriptive English usage of "Shall" is realistic at sentence boundaries." New text: "Doctor's static-phase `bcp14_keyword_wellformedness` check MUST detect the mixed-case form of `SHALL` (uppercase-S followed by lowercase characters) as the unambiguous-mismatch case — no descriptive English usage of the mixed-case form is realistic at sentence boundaries." The replacement MUST preserve the rest of the paragraph (mixed-case `Must` / `Should` / `May` deferral to LLM phase, first-violation short-circuit preservation, sub-tree exemption preservation) intact.

## Proposal: rephrase-anchor-reference-example-to-avoid-literal-markdown-link

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Rephrase the §SPECIFICATION/-to-SPECIFICATION/ references example in constraints.md:243 so it does not contain a literal Markdown link pattern that the anchor-reference-resolution check parses as a real link. The check uses regex `\[([^\]]*)\]\(([^)]+)\)` and does not skip backtick-wrapped tokens.

### Motivation

The constraints.md text describing Markdown-link anchor references contains a literal `[text](#slug)` example. The anchor-reference-resolution check parses this as a real anchor reference and attempts to resolve `#slug` to a heading in constraints.md, which fails. doctor's static phase currently emits a `fail` finding pointing at this self-violation on every run. The rewrite preserves the descriptive intent without using a literal `[text](url)` form that the regex would parse.

### Proposed Changes

Edit constraints.md line 243. Old text: "Same-file anchor references via Markdown link syntax (`[text](#slug)`) remain governed by `doctor-anchor-reference-resolution`." New text: "Same-file anchor references using Markdown link syntax (link text plus a `#<heading-slug>` URL fragment) remain governed by `doctor-anchor-reference-resolution`." The replacement MUST preserve the surrounding sentence intact: the citation form `<filename>.md §"<Heading text>"` for peer-file references AND the carve-out that same-file anchor references remain governed by `doctor-anchor-reference-resolution`.
