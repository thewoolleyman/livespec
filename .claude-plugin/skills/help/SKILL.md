---
name: help
description: Explain what livespec does and route the user to the right sub-command (seed, propose-change, critique, revise, doctor, prune-history). Invoked by /livespec:help, "what can livespec do", or when the user asks for an overview of livespec capabilities.
allowed-tools: Read
---

# help — Claude Code binding

This file is the thin Claude Code binding for the `help` operation.
The complete harness-neutral driving prose is the core artifact at
`${CLAUDE_PLUGIN_ROOT}/prose/help.md` — `../../prose/help.md`
relative to this SKILL.md (the relative layout is identical in the
flattened installed cache and in `--plugin-dir .` dev mode). FIRST
read that prose file in full, then execute it end-to-end, binding its
harness-neutral vocabulary to this runtime as follows.

## Runtime bindings

- **"the seed / propose-change / critique / revise / doctor /
  prune-history / next operation"** — the corresponding
  `/livespec:<name>` skill in this plugin; route the user to the
  slash command by that name.
- **"running the seed CLI named in config with `--help`"** — e.g.
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/seed.py" --help` via
  the Bash tool (same pattern for every other operation's wrapper
  under `${CLAUDE_PLUGIN_ROOT}/scripts/bin/`).
