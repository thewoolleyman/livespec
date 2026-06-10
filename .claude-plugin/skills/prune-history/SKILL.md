---
name: prune-history
description: Destructively prune old vNNN/ snapshots from <spec-root>/history/ to bound history size. Requires explicit user invocation (model-driven invocation is disabled). Invoked only via /livespec:prune-history or an explicit "prune the livespec history" request from the user.
allowed-tools: Bash, Read, Write
disable-model-invocation: true
---

# prune-history — Claude Code binding

This file is the thin Claude Code binding for the `prune-history`
operation. The complete harness-neutral driving prose is the core
artifact at `${CLAUDE_PLUGIN_ROOT}/prose/prune-history.md` —
`../../prose/prune-history.md` relative to this SKILL.md (the
relative layout is identical in the flattened installed cache and in
`--plugin-dir .` dev mode). FIRST read that prose file in full, then
execute it end-to-end, binding its harness-neutral vocabulary to this
runtime as follows.

The prose's requirement that "every Driver MUST configure its runtime
so model-driven self-invocation is disabled" is realized in this
binding by the `disable-model-invocation: true` frontmatter above:
the LLM MUST NOT invoke this skill on its own initiative; only an
explicit user request triggers it.

## Runtime bindings

- **"run the prune-history CLI named in config" / "invoke the
  prune-history CLI"** — invoke the reference wrapper via the Bash
  tool with explicit argv:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/prune_history.py" [--project-root <path>]
  ```

- **"confirm with the user" / "surface" / "narrate"** —
  conversational turns in this session (the AskUserQuestion tool or
  plain narration, as appropriate).
- **"read `<file>`"** — the Read tool.
- **"the doctor prose (`prose/doctor.md`)"** — read
  `${CLAUDE_PLUGIN_ROOT}/prose/doctor.md` and follow it.
