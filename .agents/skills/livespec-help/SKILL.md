---
name: livespec-help
description: Use when the user invokes `/livespec:help`, says `livespec help`, or asks how to use livespec in this repository.
---

# livespec-help

This is a Codex runtime adapter for the livespec `help` operation.
It is not the operation's behavior source of truth.

When this skill is triggered:

1. Resolve the repository root as the current working tree.
2. Read `.claude-plugin/prose/help.md` completely.
3. Follow that prose exactly for behavior, routing, failure handling, and user-facing output.
4. Do not invoke a wrapper CLI; the core help prose defines this operation as narration-only.
5. Do not copy, summarize as a substitute for, or restate operation behavior from the prose in this adapter.
