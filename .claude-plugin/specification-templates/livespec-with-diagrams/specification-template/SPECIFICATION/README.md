# `<intent-derived-title>` — specification overview

This `SPECIFICATION/` directory holds the living specification
for the project, governed by `livespec`'s propose-change/revise
loop. The `livespec-with-diagrams` template ships six spec files
plus a `diagrams/` escape-hatch directory plus the
`proposed_changes/` and `history/` machinery:

- `spec.md` — primary source surface (project intent, top-level
  architecture).
- `contracts.md` — wire-level / CLI-level interfaces.
- `constraints.md` — architecture-level constraints whose
  violation an end user could observe (runtime, language,
  dependencies, etc.).
- `non-functional-requirements.md` — dev-environment,
  repository-tooling, build/test, and contributor-workflow
  invariants that are NOT visible at the user-facing surface.
- `scenarios.md` — Gherkin acceptance scenarios.
- `README.md` (this file) — overview + entry-point.
- `diagrams/` — PlantUML escape-hatch diagram sources plus
  their rendered SVG outputs (see "Diagram conventions").

## Conventions

- Every spec file uses BCP 14 / RFC 2119 normative language for
  requirements (`MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`,
  `MAY`, `OPTIONAL`).
- `scenarios.md` uses the Gherkin keyword convention with each
  step on its own line (preceded and followed by a blank line)
  so every step renders as its own Markdown paragraph under
  GitHub-Flavored Markdown. No fenced code blocks for Gherkin
  steps.
- Cross-file references use the GitHub-flavored anchor form
  `[link text](relative/path.md#section-name)`.

## Diagram conventions

Mermaid is the standard diagram format. Common diagram types
(sequence, class, state, ER, flowchart/dependency, light C4)
are authored as fenced `mermaid` blocks inside the markdown
spec files — they are markdown content, follow the markdown
file's lifecycle, and need no manifest entry or render command.

PlantUML is the escape hatch, ONLY for diagram types Mermaid
lacks first-class support for (deployment, timing, object,
mind map, rich C4/sprites). Escape-hatch diagrams live as
`diagrams/<name>.plantuml` sources (`kind: diagram_source` in
the template manifest) with rendered SVG outputs
(`kind: diagram_rendered`); `/livespec:revise` re-renders them
via the `render_commands` entry in `.livespec.jsonc` whenever
their sources change. The starter
`diagrams/example.plantuml` → `diagrams/example.svg` pair shows
the mechanism with a deployment diagram.

## Lifecycle

Mutations to this `SPECIFICATION/` flow through
`/livespec:propose-change` → `/livespec:revise` (or its
`/livespec:critique` delegation surface). Hand-edits outside
the propose-change loop are caught by the doctor static phase's
`out-of-band-edits` check and surfaced as findings.

## History

Past versions live under `history/v001/` through `history/vN/`.
`prune-history` (when invoked) consolidates older versions into
a `PRUNED_HISTORY.json` marker preserving the audit trail.
