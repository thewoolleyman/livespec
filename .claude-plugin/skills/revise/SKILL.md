---
name: revise
description: Walk the user through accepting or rejecting each pending proposed change in <spec-root>/proposed_changes/, then snapshot the result as a new <spec-root>/history/vNNN/ revision. Invoked by /livespec:revise, "revise the livespec", or "process pending proposed changes".
allowed-tools: Bash, Read, Write
---

# revise — Claude Code binding

This file is the thin Claude Code binding for the `revise` operation.
The complete harness-neutral driving prose is the core artifact at
`${CLAUDE_PLUGIN_ROOT}/prose/revise.md` — `../../prose/revise.md`
relative to this SKILL.md (the relative layout is identical in the
flattened installed cache and in `--plugin-dir .` dev mode). FIRST
read that prose file in full, then execute it end-to-end, binding its
harness-neutral vocabulary to this runtime as follows.

## Runtime bindings

- **"run the revise CLI named in config" / "invoke the revise
  CLI"** — invoke the reference wrapper via the Bash tool with
  explicit argv:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/revise.py" --revise-json <path> --post-step-doctor [--author <id>] [--spec-target <path>] [--project-root <path>]
  ```

- **"run the template-resolution CLI"** — via the Bash tool:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/resolve_template.py"
  ```

- **"run `python -m livespec_dev_tooling.workflow_checks.no_stale_revise_branches`"**
  (prose Step 3.5) — via the Bash tool against the project root.
- **"ask the user" / "confirm with the user" / "surface" /
  "narrate" / the per-proposal confirmation dialogue** —
  conversational turns in this session (the AskUserQuestion tool or
  plain narration, as appropriate).
- **"read `<file>`" / "list `<dir>`"** — the Read tool (or Bash
  `ls`). **"write `<file>`"** — the Write tool.
- **"the propose-change / critique operation"** — the
  `/livespec:propose-change`, `/livespec:critique` skills in this
  plugin.
- **"the doctor prose (`prose/doctor.md`)"** — read
  `${CLAUDE_PLUGIN_ROOT}/prose/doctor.md` and follow it (the
  LLM-driven post-step phase runs under `doctor/SKILL.md`'s
  bindings).
- **"invoke the active impl plugin's `capture-impl-gaps`
  front-end"** (prose Step 13(e)) — invoke
  `/<plugin-namespace>:capture-impl-gaps --since-version <prior-vN>
  --spec-target <spec-target> --project-root <project-root>` via the
  skill-namespace dispatch, where `<plugin-namespace>` is the value
  of `implementation.plugin` in `.livespec.jsonc`.
- **"core's `livespec/schemas/` package"** — resolves at runtime to
  `${CLAUDE_PLUGIN_ROOT}/scripts/livespec/schemas/`.
