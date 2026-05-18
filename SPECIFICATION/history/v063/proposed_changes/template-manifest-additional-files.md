---
topic: template-manifest-additional-files
author: claude-opus-4-7
created_at: 2026-05-17T14:36:24Z
---

## Proposal: Template manifest for additional spec files (markdown sub-files, diagram source, rendered output)

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

Extend the template format with an explicit per-file manifest so spec_root MAY contain files beyond the closed set the livespec template implicitly fixes today. The manifest MUST declare each file's kind (markdown, diagram_source, or diagram_rendered) and per-kind behavior governs heading-coverage applicability, LLM-context inclusion, and history-snapshot scope. Rendering of diagram_source to diagram_rendered SHOULD occur during /livespec:revise via a project-declared render command (in .livespec.jsonc); livespec MUST NOT vendor renderers or runtimes. The built-in livespec template stays at its current five-file opinion; a separate livespec-with-diagrams template uses the mechanism to add PlantUML support.

### Motivation

Two real-world needs are not supported today: (1) breaking a large spec file into textual sub-files for readability, and (2) including diagrams as first-class spec content. PlantUML and Mermaid sources are textual and LLM-readable, so they qualify as spec content rather than mere human aids — forcing every team that wants a sequence diagram to fork the whole template imposes a real tax. The current implicit five-file set is enforced in two places: dev-tooling/checks/heading_coverage.py:54-60 hardcodes the file tuple, and the livespec template's seed prompt lists the six output files inline. There is no extension point in template.json today (template_config.schema.json declares only template_format_version, spec_root, and optional doctor extension hooks). The proposal adds the mechanism in core while keeping the opinion (which files belong in a default livespec spec) inside templates — preserving livespec's opinionated default while making richer file structures a first-class extension path rather than a fork-the-whole-skill-bundle obligation.

### Proposed Changes

### Manifest mechanism in core; default opinion stays in templates

The `template.json` schema (`.claude-plugin/scripts/livespec/schemas/template_config.schema.json`) MUST be extended with a new `spec_files` object mapping spec-target-relative paths to per-file declarations. Each declaration MUST carry a `kind` field with one of three values: `markdown`, `diagram_source`, or `diagram_rendered`. A `diagram_rendered` entry MUST also carry a `derived_from` field naming the `diagram_source` path it was rendered from.

Example shape:

```jsonc
{
  "template_format_version": 2,
  "spec_root": "SPECIFICATION/",
  "spec_files": {
    "spec.md":                    { "kind": "markdown" },
    "contracts.md":               { "kind": "markdown" },
    "constraints.md":             { "kind": "markdown" },
    "non-functional-requirements.md": { "kind": "markdown" },
    "scenarios.md":               { "kind": "markdown" },
    "README.md":                  { "kind": "markdown" },
    "diagrams/architecture.puml": { "kind": "diagram_source" },
    "diagrams/architecture-auth-flow.svg":  { "kind": "diagram_rendered", "derived_from": "diagrams/architecture.puml" },
    "diagrams/architecture-data-model.svg": { "kind": "diagram_rendered", "derived_from": "diagrams/architecture.puml" }
  }
}
```

The built-in `livespec` template MUST keep its current opinion — its manifest declares only the five existing markdown files plus `README.md`. A separate `livespec-with-diagrams` template SHOULD ship as the canonical example of using the mechanism to add diagram support.

### Per-kind behavior

The three `kind` values govern three orthogonal axes:

- **Markdown-shaped checks** (heading-coverage and similar): MUST apply only to files of `kind: markdown`. Files of `kind: diagram_source` or `kind: diagram_rendered` MUST be exempt.
- **LLM-context inclusion** (critique, doctor LLM-driven phases, propose-change context): MUST include `markdown` and `diagram_source` files (LLMs can read PlantUML/Mermaid semantically). MUST NOT include `diagram_rendered` files (opaque to LLMs and frequently oversized).
- **History snapshots** (`history/vNNN/` materialization during revise): MUST include all three kinds. Rendered files are required in history because viewing an old revision in a browser MUST render correctly — markdown references like `![](diagrams/auth-flow.svg)` would otherwise produce broken images, defeating the human-readable audit trail.

This bloat cost in `history/` is accepted as the price of human-readable history. The source-only-in-history alternative was considered and rejected.

### Rendering contract

Livespec MUST NOT vendor rendering binaries (no bundled `plantuml.jar`, no Java-runtime detection, no Graphviz dependency). The render command MUST be declared in `.livespec.jsonc` (the project-level config), keyed by source kind:

```jsonc
{
  "template": "livespec-with-diagrams",
  "render_commands": {
    "diagram_source": ["plantuml", "-tsvg", "-o", "{output_dir}", "{source}"]
  }
}
```

The render command MUST run with `cwd` set to the project root. Livespec MUST substitute `{source}` (project-root-relative path to the changed source file) and `{output_dir}` (the directory containing the source — so rendered files sit next to source and the relative reference path `![](diagrams/foo.svg)` is structurally valid in `spec_root/`, `history/vNNN/`, with no path rewriting).

The `livespec-with-diagrams` template's `README.md` and `CLAUDE.md` MUST state the external requirement ("this template requires PlantUML to be installed; here is the install recipe per OS"). Livespec itself MUST NOT detect or attempt to install the renderer.

### Where rendering happens in the lifecycle

Proposal documents under `proposed_changes/<topic>.md` MUST remain prose write-ups of intended changes; they MUST NOT become tree-shaped patches. `/livespec:revise` is the skill that materializes new spec versions, and rendering MUST integrate there: after revise writes updated diagram source, it MUST invoke the configured render command, and only after the render succeeds MAY it snapshot the full result (markdown + source + rendered) to `history/vNNN/`. propose-change itself MUST NOT render.

### Transactional revise semantics

If the render command exits non-zero, revise MUST fail the entire revision and leave `spec_root/` untouched. No half-applied state — markdown edits committed but rendering failed — is permitted. The recommended flow is: stage all changes to a working location → run render → only on full success, commit edits and snapshot to history.

### PlantUML multi-diagram-per-file accommodation

One `.puml` source MAY contain multiple `@startuml ... @enduml` blocks that each render to a separate SVG. The manifest accommodates this by allowing multiple `diagram_rendered` entries to share a single `derived_from` source. The spec-author convention SHOULD be to name `@startuml` blocks (e.g., `@startuml auth-flow`) so prose references like "see the `auth-flow` sequence in `architecture.puml`" navigate cleanly for both LLM and human readers.

### Doctor check: source/rendered drift

A new static doctor check SHOULD warn when a `diagram_rendered` file's content does not match a fresh re-render of its `derived_from` source, or (cheaper) when the rendered file's mtime predates the source's. This catches the case where someone edits diagram source manually outside the revise flow and forgets to re-render.

### Heading-coverage rewiring

`dev-tooling/checks/heading_coverage.py` currently hardcodes the five-file tuple `_TREE_ROOT_NLSPEC_FILES` (lines 54-60). It MUST instead consult the active template's manifest and apply only to files of `kind: markdown`. This is a correctness change, not added complexity — the current check implicitly assumes every spec file is markdown, which the manifest extension reveals as wrong rather than introducing.

### Schema versioning

`template_config.schema.json` MUST bump from v1 to v2. v1 templates SHOULD continue to load (their implicit file set treated as a manifest of `kind: markdown` entries for the well-known files); v2 templates MUST declare `spec_files` explicitly. No breaking change to existing forks is introduced.

### Trust boundary worth naming

A render command in `.livespec.jsonc` is arbitrary shell that revise WILL execute. This is the same trust boundary as any project-config file in a Claude Code workflow (the user already trusts their own project's config), but the contracts MUST state it explicitly so the surface is not silently introduced.

### Explicitly rejected alternatives (captured for the design record)

- **Bundling `plantuml.jar` and Java detection in livespec core** — rejected as a real toolchain commitment (JRE + Graphviz install burden) masquerading as "include the dependencies."
- **Restructuring `proposed_changes/` from flat prose files to tree-shaped patches** — rejected; the proposal document is a prose write-up of intent, not a file-by-file diff. Revise materializes the patch from the prose.
- **Source-only-in-history (rendered artifacts gitignored or excluded from snapshots)** — rejected because old revisions MUST render correctly for human readers; the bit-for-bit reconstructibility from source plus pinned renderer was judged over-engineering for a natural-language spec tool.
- **`diagram_rendered` as a general spec-file kind admitting hand-authored SVG** — out of scope for this proposal. The default contract treats `diagram_source` as PlantUML/Mermaid-style textual diagram description and `diagram_rendered` as opaque rendered output produced by the render command. Hand-authored raster-export SVG is a human aid and SHOULD live outside `spec_root/`.
