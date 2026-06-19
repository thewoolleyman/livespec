---
name: livespec-next
description: Use when the user invokes `/livespec:next`, says `livespec next`, or asks for the next spec-side livespec action.
---

# livespec-next

This is a Codex runtime adapter for the livespec `next` operation.
It is not the operation's behavior source of truth.

When this skill is triggered:

1. Resolve the repository root as the current working tree.
2. Read `.claude-plugin/prose/next.md` completely.
3. Follow that prose exactly for behavior, routing, failure handling, and user-facing output.
4. When the prose calls for the next CLI, invoke `.claude-plugin/scripts/bin/next.py` from this repository with explicit argv.
5. For the default repository invocation, pass `--project-root <repo-root>`, `--spec-target <repo-root>/SPECIFICATION`, `--limit 5`, and `--offset 0` unless the user or prose selects different valid inputs.
6. Do not copy, summarize as a substitute for, or restate operation behavior from the prose in this adapter.
