---
name: doctor
description: Run the doctor checks against a livespec spec tree — the static phase (structural failures) plus the LLM-driven objective and subjective phases — surfacing findings as JSON or as a per-finding user dialogue. Invoked by /livespec:doctor, "run livespec doctor", or "check the spec for invariants", and as the post-step LLM-driven phase from every wrapper-having sub-command.
allowed-tools: Bash, Read
---

# doctor — Claude Code binding

This file is the thin Claude Code binding for the `doctor` operation.
The complete harness-neutral driving prose is the core artifact at
`${CLAUDE_PLUGIN_ROOT}/prose/doctor.md` — `../../prose/doctor.md`
relative to this SKILL.md (the relative layout is identical in the
flattened installed cache and in `--plugin-dir .` dev mode). FIRST
read that prose file in full, then execute it end-to-end, binding its
harness-neutral vocabulary to this runtime as follows.

When another `/livespec:*` skill delegates here for the post-step
LLM-driven phase only, follow the prose's "Post-CLI" section: skip
the static-phase Steps 1-4 and proceed from Step 5.

## Runtime bindings

- **"run the doctor CLI named in config" / "invoke the doctor
  CLI"** — invoke the reference wrapper via the Bash tool with
  explicit argv:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/doctor_static.py" [--project-root <path>]
  ```

- **"run the template-resolution CLI"** — via the Bash tool:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/resolve_template.py" --template <name>
  ```

- **"ask the user" / "prompt the user" / "surface" / "narrate" /
  the per-finding dialogue** — conversational turns in this session
  (the AskUserQuestion tool or plain narration, as appropriate).
- **"read `<file>`" / "inspect the stdout JSON"** — the Read tool
  (or Bash `cat` for captured output).
- **"invoke the critique operation"** — the `/livespec:critique`
  skill in this plugin.
- **"the calling operation's prose"** — the delegating
  `/livespec:*` skill's binding + its `prose/<name>.md` artifact.
