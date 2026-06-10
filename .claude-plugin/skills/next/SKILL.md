---
name: next
description: Rank the next spec-side action (revise, propose-change, critique, prune-history, or none) over the current `<spec-target>/proposed_changes/` and `<spec-target>/history/` state, emitting structured JSON. Invoked by /livespec:next, "what should I work on next on the spec side", or as a primitive composed by a cross-repo loop driver.
allowed-tools: Bash
---

# next — Claude Code binding

This file is the thin Claude Code binding for the `next` operation.
The complete harness-neutral driving prose is the core artifact at
`${CLAUDE_PLUGIN_ROOT}/prose/next.md` — `../../prose/next.md`
relative to this SKILL.md (the relative layout is identical in the
flattened installed cache and in `--plugin-dir .` dev mode). FIRST
read that prose file in full, then execute it end-to-end, binding its
harness-neutral vocabulary to this runtime as follows.

## Runtime bindings

- **"run the next CLI named in config" / "invoke the next CLI"** —
  invoke the reference wrapper via the Bash tool with explicit argv:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/next.py" [--spec-target <path>] [--project-root <path>]
  ```

- **"surface the nudge" / "ask the user to confirm"** —
  conversational turns in this session.
- **"a cross-repo loop driver"** — in the livespec repo itself this
  is the project-local `/livespec-orchestrate` skill
  (`.claude/skills/livespec-orchestrate/SKILL.md`; non-contract
  working tooling). When that driver (or any other skill) invokes
  this skill, skip the prose's Step 1 nudge.
