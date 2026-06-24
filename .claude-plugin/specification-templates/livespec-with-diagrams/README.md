# livespec-with-diagrams template

The diagram-seeding variant of the built-in `livespec` template,
per `SPECIFICATION/spec.md` §"Template manifest". It seeds Mermaid
diagram conventions and an example fenced `mermaid` block into the
template's spec files. It differs from the built-in `livespec`
template ONLY in that seeded content; its `spec_files` manifest is
the same markdown-only set.

## Diagram conventions

**Mermaid is livespec's standard and default diagram format.**
Diagram types (sequence, class, state, ER, flowchart/dependency,
C4, and the rest) are authored as fenced ` ```mermaid ` blocks
inside the `kind: markdown` spec files. They need NO manifest
entries, NO render command, and NO history special-casing — they
are markdown content that GitHub, IDEs, and markdown previewers
render natively and that LLMs read natively, and they follow the
markdown file's lifecycle.

## When to choose this template

Pick this template when your specification benefits from inline
architecture / sequence / state diagrams alongside the prose and
you want the Mermaid conventions and an example block already
seeded. If you don't need the seeded conventions, use the built-in
`livespec` template instead — Mermaid fenced blocks work
identically there; this variant only adds the seeded conventions
and the starter block.

## Alternate diagram tools

If a diagram genuinely needs a tool Mermaid lacks (rare), render it
with an alternate tool such as PlantUML or Graphviz OUTSIDE livespec
and commit the resulting image alongside the markdown that
references it (e.g., `![](diagrams/foo.svg)`). livespec treats the
image as an opaque committed asset — it does NOT detect, recommend,
install, invoke, or otherwise manage any external diagram tool. The
image is preserved across revisions by the whole-tree history
snapshot (per `SPECIFICATION/spec.md` §"Template manifest" →
"Lifecycle participation").

## Manifest contents

The shipped `template.json` (`template_format_version: 2`) declares
the six NLSpec markdown files — `spec.md`, `contracts.md`,
`constraints.md`, `non-functional-requirements.md`, `scenarios.md`,
`README.md` — all `kind: markdown`; fenced Mermaid blocks live
inside these. `markdown` is the only file kind. A project that wants
a different file set materializes a custom template that owns and
edits its own `template.json`.
