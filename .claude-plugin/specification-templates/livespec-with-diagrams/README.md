# livespec-with-diagrams template

The diagram-seeding variant of the built-in `livespec` template,
per `SPECIFICATION/spec.md` §"Template manifest". The variant is
**Mermaid-first**: it seeds diagram conventions and an example
fenced `mermaid` block into the template's spec files, and uses
the v2 `spec_files` manifest's `diagram_source` /
`diagram_rendered` mechanism ONLY for the PlantUML escape hatch.

## Diagram conventions

- **Mermaid for common types.** Sequence, class, state, ER,
  flowchart/dependency, and light C4 diagrams are authored as
  fenced ` ```mermaid ` blocks inside the `kind: markdown` spec
  files. They need NO manifest entries, NO render command, and
  NO history special-casing — they are markdown content and
  follow the markdown file's lifecycle (GitHub, most markdown
  previewers, and LLMs all read them natively).
- **PlantUML escape hatch for the rest.** Diagram types Mermaid
  lacks first-class support for (deployment, timing, object,
  mind map, rich C4/sprites) live as textual PlantUML sources
  under `diagrams/` (`kind: diagram_source`) with rendered SVG
  outputs (`kind: diagram_rendered`, `derived_from` naming the
  source). `/livespec:revise` re-renders the SVG whenever a
  revise pass writes updated source.

## When to choose this template

Pick this template when your specification benefits from inline
architecture / sequence / state diagrams alongside the prose. If
your project doesn't need seeded diagram conventions, use the
built-in `livespec` template instead — Mermaid fenced blocks
work identically there; this variant only adds the seeded
conventions, the starter blocks, and the escape-hatch wiring.

## External renderer requirement (escape hatch only)

Mermaid fenced blocks need no renderer. The PlantUML escape
hatch ships starter source (`diagrams/example.plantuml`, a
deployment diagram — a type Mermaid lacks) and its rendered SVG
(`diagrams/example.svg`). Re-rendering on `revise` requires a
working `plantuml` binary on `PATH`. livespec does NOT install,
detect, or recommend the renderer (no bundled renderers); each
project using the escape hatch is responsible for making the
renderer available in its dev environment and CI.

- **Ubuntu / Debian:** `sudo apt-get install -y plantuml`
- **macOS (Homebrew):** `brew install plantuml`
- **Other platforms:** download `plantuml.jar` from
  <https://plantuml.com/download> and create a shell wrapper
  that invokes `java -jar /path/to/plantuml.jar "$@"`.

### Project configuration

Once `plantuml` is on `PATH`, declare the render command in your
project's `.livespec.jsonc`:

```jsonc
{
  "template": "livespec-with-diagrams",
  "render_commands": {
    "diagram_source": ["plantuml", "-tsvg", "-o", "{output_dir}", "{source}"]
  }
}
```

Per `SPECIFICATION/contracts.md` §".livespec.jsonc
render-commands shape", `{source}` substitutes the
project-root-relative path of the changed source file and
`{output_dir}` substitutes the directory containing the source.
The render command runs with `cwd` at the project root; non-zero
exit fails the revise transactionally.

## Manifest contents

The shipped `template.json` (`template_format_version: 2`)
declares:

- six NLSpec markdown files: `spec.md`, `contracts.md`,
  `constraints.md`, `non-functional-requirements.md`,
  `scenarios.md`, `README.md` (all `kind: markdown`; fenced
  Mermaid blocks live inside these)
- one starter PlantUML escape-hatch source at
  `diagrams/example.plantuml` (`kind: diagram_source`)
- its rendered output at `diagrams/example.svg`
  (`kind: diagram_rendered`,
  `derived_from: diagrams/example.plantuml`)

Replace the starter diagrams with your project's actual ones.
Add or remove `spec_files` entries as needed; the manifest is
the source of truth for which files participate in
heading-coverage (markdown only), LLM-context inclusion
(markdown plus diagram_source), and history snapshots (all
three kinds).
