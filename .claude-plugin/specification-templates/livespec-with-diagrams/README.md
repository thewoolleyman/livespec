# livespec-with-diagrams template

The PlantUML-supporting variant of the built-in `livespec` template.
Adds a `diagrams/` subdirectory under the spec root for textual
diagram sources (PlantUML) plus their rendered outputs (SVG), wired
through the v2 `spec_files` manifest so livespec's lifecycle treats
diagrams as first-class spec content: included in LLM context,
snapshotted into history, and re-rendered by `revise` whenever
their sources change.

## When to choose this template

Pick this template when your specification benefits from inline
architecture / sequence / state diagrams alongside the prose. The
diagram source is what livespec reads for LLM context (PlantUML is
text and LLM-readable); the rendered SVG is what humans see when
viewing the spec in a browser or markdown previewer.

If your project doesn't need diagrams, use the built-in `livespec`
template instead — it carries the same six NLSpec markdown files
without the renderer-install commitment.

## External renderer requirement

This template ships starter diagram source (`diagrams/example.plantuml`)
and its rendered SVG (`diagrams/example.svg`). Re-rendering on
`revise` requires a working `plantuml` binary on `PATH`. Per
livespec's non-vendoring constraint
(`SPECIFICATION/constraints.md` §"No bundled renderers"), livespec
does NOT install, detect, or recommend the renderer. Each project
using this template is responsible for ensuring the renderer is
available in its dev environment and CI.

### Install per OS

- **Ubuntu / Debian:** `sudo apt-get install -y plantuml`
- **macOS (Homebrew):** `brew install plantuml`
- **Other platforms:** Download the `plantuml.jar` from
  <https://plantuml.com/download> and create a shell wrapper that
  invokes `java -jar /path/to/plantuml.jar "$@"`.

The system `plantuml` is preferred over the GraalVM-native
release distributed via GitHub: at the time of writing, the
native build on Linux fails with an AWT linker error
(`No awt in java.library.path`) absent a separate freetype/AWT
stub install. The traditional `plantuml.jar` + JRE path is the
operational default.

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

Per `SPECIFICATION/contracts.md` §".livespec.jsonc render-commands
shape", `{source}` substitutes the project-root-relative path of
the changed source file and `{output_dir}` substitutes the
directory containing the source. The render command runs with
`cwd` at the project root; non-zero exit fails the revise
transactionally.

## Manifest contents

The shipped `template.json` declares:

- six NLSpec markdown files: `spec.md`, `contracts.md`,
  `constraints.md`, `non-functional-requirements.md`,
  `scenarios.md`, `README.md` (all `kind: markdown`)
- one starter PlantUML source at `diagrams/example.plantuml`
  (`kind: diagram_source`)
- the rendered output at `diagrams/example.svg` (`kind:
  diagram_rendered`, `derived_from: diagrams/example.plantuml`)

Replace the starter diagram with your project's actual architecture
diagrams. Add or remove `spec_files` entries as needed; the manifest
is the source of truth for which files participate in
heading-coverage (markdown only), LLM-context inclusion (markdown
plus diagram_source), and history snapshots (all three kinds).
