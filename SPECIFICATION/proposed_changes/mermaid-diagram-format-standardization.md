---
topic: mermaid-diagram-format-standardization
author: claude-fable-5
created_at: 2026-06-10T06:13:27Z
---

Adopt **Mermaid as livespec's standardized diagram format** (user decision
2026-06-10), with PlantUML retained as a per-diagram-type escape hatch.
Rationale and evidence:
`research/workflow-processes/mermaid-vs-plantuml-llm-readable-specs.md`
(GitHub-native rendering eliminates the source↔render pairing and the render
pipeline for the common diagram types; training-data familiarity and token
compactness favor Mermaid; the expressiveness gap is confined to specialty
types). This is Wave 0a of the v103-realization rollout (epic
livespec-4moata, work-item livespec-0nfr). Two pre-recorded cosmetic riders
from the v104 doctor pass (memo livespec-bhwnuk items 1–2) ride along as
Proposals 3–4.

The existing `spec_files` manifest mechanism (`diagram_source` /
`diagram_rendered` kinds, `render_commands`, transactional render-in-revise)
is NOT removed — it becomes the escape-hatch machinery, paid for only by the
minority of diagrams that need PlantUML.

## Proposal: mermaid-first-template-manifest-wording

### Target specification files

- SPECIFICATION/spec.md

### Summary

Re-word §"Template manifest" so Mermaid is the standard diagram format:
common diagram types live as fenced ` ```mermaid ` blocks INSIDE
`kind: markdown` spec files (rendering natively on GitHub and most viewers
with no manifest entries, no render command, and no history special-casing),
and the `livespec-with-diagrams` template variant is described Mermaid-first,
retaining the `diagram_source`/`diagram_rendered` mechanism solely as the
PlantUML escape hatch.

### Motivation

The current wording ("the canonical PlantUML-supporting variant ships as a
separate `livespec-with-diagrams` template") makes PlantUML the default
diagram story and therefore makes the render pipeline, the source↔render
pairing, and the history-bloat tradeoff the COMMON case. Under Mermaid-first
those costs apply only to the escape hatch: a fenced Mermaid block is plain
markdown content — it is versioned, snapshotted, LLM-readable, and rendered
by the hosting platform with zero additional machinery. The per-kind behavior
axes and the render-in-revise lifecycle remain exactly as specified for the
files that still need them.

### Proposed Changes

1. In §"Template manifest", replace the clause "the canonical
   PlantUML-supporting variant ships as a separate `livespec-with-diagrams`
   template that uses the mechanism to add `diagram_source` and
   `diagram_rendered` entries" with wording stating: **Mermaid is livespec's
   standard diagram format.** Common diagram types (sequence, class, state,
   ER, flowchart/dependency, light C4) SHOULD be authored as fenced
   ` ```mermaid ` blocks inside `kind: markdown` spec files — such diagrams
   require NO manifest entries, NO render command, and NO history
   special-casing (they are markdown content and follow the markdown file's
   lifecycle). The separate `livespec-with-diagrams` template variant is
   Mermaid-first: it seeds diagram conventions and example fenced blocks into
   the template's spec files, and uses the `diagram_source` /
   `diagram_rendered` manifest mechanism ONLY for the **PlantUML escape
   hatch** — diagram types Mermaid lacks first-class support for
   (deployment, timing, object, mind map, rich C4/sprites). Existing
   PlantUML diagrams migrate to Mermaid opportunistically when next touched,
   not big-bang.
2. In the §"Per-kind behavior axes" history-snapshots bullet, add one
   clarifying sentence: the rendered-files-in-history requirement applies to
   the escape-hatch `diagram_source`/`diagram_rendered` pairing; fenced
   Mermaid blocks inside `kind: markdown` files need nothing additional —
   any `history/vNNN/` snapshot of the markdown renders them natively.

## Proposal: canonical-architecture-diagram-to-mermaid

### Target specification files

- SPECIFICATION/spec.md

### Summary

Re-state the §"Contract + reference implementations architecture" →
"Canonical architecture diagram" paragraph for Mermaid: the canonical
diagram is maintained as Mermaid source embedded as a fenced block in the
repo README's Architecture section, with no rendered-artifact pairing; the
Phase-6 doctor drift-check scope narrows to escape-hatch PlantUML pairings
only.

### Motivation

The paragraph currently mandates PlantUML source + rendered SVG "maintained
by review" with a Phase-6 drift-check to keep the pairing in lockstep. Under
Mermaid the pairing does not exist for this diagram: the fenced source IS
what renders, on GitHub and in most viewers, so the drift class the check
was designed for vanishes. The conversion of the existing
`contract-and-reference-implementations.{plantuml,svg}` is tracked as
work-item livespec-iiv3 (Wave 0c) and executes after this revise.

### Proposed Changes

1. Replace the "Canonical architecture diagram" paragraph body with: the
   canonical architecture diagram is maintained as **Mermaid source embedded
   as a fenced block in the repo README's Architecture section** (a
   standalone `.mmd` source file MAY additionally exist if other documents
   reference it). The README rendering IS the rendered form — no paired
   rendered artifact exists or is required. Phase 6 graduates the diagrams
   into the SPECIFICATION template; its doctor drift-check covers ONLY
   escape-hatch PlantUML `diagram_source`/`diagram_rendered` pairings (a
   Mermaid syntax lint MAY be added as a CI nicety but is not a contract
   requirement).

## Proposal: locked-vendored-libs-paragraph-separation

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Cosmetic rider (memo livespec-bhwnuk item 1, v104-introduced): in §"Locked
vendored libs", insert the missing blank line before the paragraph beginning
"The cross-repo work-item dependency machinery (`livespec_runtime.cross_repo`)
is deliberately absent from this set", so Markdown stops rendering it as part
of the preceding `typing_extensions` bullet.

### Motivation

The v104 replacement paragraph was appended directly after the
`typing_extensions` list item without a separating blank line; Markdown
therefore renders the standalone paragraph as a continuation of that bullet,
attributing the cross-repo-machinery statement to the `typing_extensions`
entry. One-line whitespace fix; no semantic change.

### Proposed Changes

1. Insert a blank line between the `typing_extensions` bullet and the "The
   cross-repo work-item dependency machinery…" paragraph in §"Locked
   vendored libs".

## Proposal: restate-commit-and-merge-discipline-citations

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Cosmetic rider (memo livespec-bhwnuk item 2, pre-existing): restate the two
path-form citations `non-functional-requirements.md §"Constraints → Commit
and merge discipline"` (in §"Pre-commit step ordering"'s lefthook narration
and in §"Plugin versioning"'s release-mapping paragraph) as the exact heading
form `non-functional-requirements.md §"Commit and merge discipline"`.

### Motivation

No heading with the literal text "Constraints → Commit and merge discipline"
exists; the actual structure is an H3 "Commit and merge discipline" under the
H2 "Constraints". The arrow path-form is the same citation family the v104
near-miss fixes normalized elsewhere; §"Reference discipline" requires
citations to use the exact heading text so reference-checking stays
mechanical.

### Proposed Changes

1. In the lefthook commit-msg narration (the `check-conventional-commits`
   sentence) and in the release-please rebase-merge sentence, replace
   `§"Constraints → Commit and merge discipline"` with `§"Commit and merge
   discipline"` (file reference unchanged).
