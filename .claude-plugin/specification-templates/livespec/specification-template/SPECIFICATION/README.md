# `<intent-derived-title>` — specification overview

This `SPECIFICATION/` directory holds the living specification
for the project, governed by `livespec`'s propose-change/revise
loop. The `livespec` template ships five spec files plus the
`proposed_changes/` and `history/` machinery:

- `spec.md` — primary source surface (project intent, top-level
  architecture).
- `contracts.md` — wire-level / CLI-level interfaces.
- `constraints.md` — architecture-level constraints (runtime,
  language, dependencies, etc.).
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
