---
name: seed
description: Author the initial natural-language specification for a new project, populating the chosen template's spec_root layout. Invoked by /livespec:seed, "seed a livespec spec", "set up a livespec", or when starting a brand-new spec in an empty SPECIFICATION/ tree.
allowed-tools: Bash, Read, Write
---

# seed — Claude Code binding

This file is the thin Claude Code binding for the `seed` operation.
The complete harness-neutral driving prose is the core artifact at
`${CLAUDE_PLUGIN_ROOT}/prose/seed.md` — `../../prose/seed.md`
relative to this SKILL.md (the relative layout is identical in the
flattened installed cache and in `--plugin-dir .` dev mode). FIRST
read that prose file in full, then execute it end-to-end, binding
its harness-neutral vocabulary to this runtime as follows.

## Runtime bindings

- **"run the seed CLI named in config" / "invoke the seed CLI"** —
  invoke the reference wrapper via the Bash tool with explicit argv:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/seed.py" --seed-json <path> [--project-root <path>]
  ```

- **"run the template-resolution CLI"** — via the Bash tool:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/resolve_template.py" --project-root . --template <chosen>
  ```

- **"ask the user" / "confirm with the user" / "surface" /
  "narrate"** — conversational turns in this session (the
  AskUserQuestion tool or plain narration, as appropriate).
- **"read `<file>`"** — the Read tool. **"write `<file>`"** — the
  Write tool.
- **"the propose-change / critique / revise operation"** — the
  `/livespec:propose-change`, `/livespec:critique`,
  `/livespec:revise` skills in this plugin.
- **"the doctor prose (`prose/doctor.md`)"** — read
  `${CLAUDE_PLUGIN_ROOT}/prose/doctor.md` and follow it (the
  LLM-driven post-step phase runs under `doctor/SKILL.md`'s
  bindings).
- **"core's `livespec/schemas/` package"** — resolves at runtime to
  `${CLAUDE_PLUGIN_ROOT}/scripts/livespec/schemas/`.
