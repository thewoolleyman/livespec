# `<intent-derived-title>` — specification overview

This `SPECIFICATION/` directory holds the living specification
for the project, governed by `livespec`'s propose-change/revise
loop. The `livespec-with-diagrams` template ships six spec files
plus the `proposed_changes/` and `history/` machinery:

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

Mermaid is the standard and default diagram format. Diagram
types (sequence, class, state, ER, flowchart/dependency, C4, and
the rest) are authored as fenced `mermaid` blocks inside the
markdown spec files — they are markdown content, render natively
wherever markdown is viewed, follow the markdown file's
lifecycle, and need no manifest entry or render command.

If a diagram genuinely needs a tool Mermaid lacks (rare), render
it with an alternate tool such as PlantUML or Graphviz OUTSIDE
livespec and commit the resulting image alongside the markdown
that references it; livespec treats it as an opaque asset and
does not manage it.

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
