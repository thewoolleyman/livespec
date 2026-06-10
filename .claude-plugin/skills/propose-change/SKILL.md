---
name: propose-change
description: File a proposed change against an existing livespec specification, landing it under <spec-root>/proposed_changes/<topic>.md. Invoked by /livespec:propose-change, "propose a change to the spec", or when the user wants to record a spec amendment that the next /livespec:revise pass will accept or reject.
allowed-tools: Bash, Read, Write
---

# propose-change — Claude Code binding

This file is the thin Claude Code binding for the `propose-change`
operation. The complete harness-neutral driving prose is the core
artifact at `${CLAUDE_PLUGIN_ROOT}/prose/propose-change.md` —
`../../prose/propose-change.md` relative to this SKILL.md (the
relative layout is identical in the flattened installed cache and in
`--plugin-dir .` dev mode). FIRST read that prose file in full, then
execute it end-to-end, binding its harness-neutral vocabulary to this
runtime as follows.

## Runtime bindings

- **"run the propose-change CLI named in config" / "invoke the
  propose-change CLI"** — invoke the reference wrapper via the Bash
  tool with explicit argv:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/propose_change.py" <topic> --findings-json <path> [--author <id>] [--reserve-suffix <text>] [--spec-target <path>] [--project-root <path>]
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
- **"the revise / critique / seed operation"** — the
  `/livespec:revise`, `/livespec:critique`, `/livespec:seed` skills
  in this plugin.
- **"the doctor prose (`prose/doctor.md`)"** — read
  `${CLAUDE_PLUGIN_ROOT}/prose/doctor.md` and follow it (the
  LLM-driven post-step phase runs under `doctor/SKILL.md`'s
  bindings).
- **"core's `livespec/schemas/` package"** — resolves at runtime to
  `${CLAUDE_PLUGIN_ROOT}/scripts/livespec/schemas/`.
