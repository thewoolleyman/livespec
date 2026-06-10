---
name: critique
description: Critique an existing livespec specification or a pending proposed change, surfacing ambiguities, contradictions, and missing rules as findings the user can act on. Invoked by /livespec:critique, "critique the livespec spec", or "find issues in the spec".
allowed-tools: Bash, Read, Write
---

# critique — Claude Code binding

This file is the thin Claude Code binding for the `critique`
operation. The complete harness-neutral driving prose is the core
artifact at `${CLAUDE_PLUGIN_ROOT}/prose/critique.md` —
`../../prose/critique.md` relative to this SKILL.md (the relative
layout is identical in the flattened installed cache and in
`--plugin-dir .` dev mode). FIRST read that prose file in full, then
execute it end-to-end, binding its harness-neutral vocabulary to this
runtime as follows.

## Runtime bindings

- **"run the critique CLI named in config" / "invoke the critique
  CLI"** — invoke the reference wrapper via the Bash tool with
  explicit argv:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/critique.py" --findings-json <path> [--author <id>] [--spec-target <path>] [--project-root <path>]
  ```

- **"run the template-resolution CLI"** — via the Bash tool:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/resolve_template.py"
  ```

- **"ask the user" / "confirm with the user" / "surface" /
  "narrate"** — conversational turns in this session (the
  AskUserQuestion tool or plain narration, as appropriate).
- **"read `<file>`"** — the Read tool. **"write `<file>`"** — the
  Write tool.
- **"the revise / propose-change operation"** — the
  `/livespec:revise`, `/livespec:propose-change` skills in this
  plugin.
- **"the doctor prose (`prose/doctor.md`)"** — read
  `${CLAUDE_PLUGIN_ROOT}/prose/doctor.md` and follow it (the
  LLM-driven post-step phase runs under `doctor/SKILL.md`'s
  bindings).
- **"core's `livespec/schemas/` package"** — resolves at runtime to
  `${CLAUDE_PLUGIN_ROOT}/scripts/livespec/schemas/`.
