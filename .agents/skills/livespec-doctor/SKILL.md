---
name: livespec-doctor
description: Use when the user invokes `/livespec:doctor`, says `livespec doctor`, or asks Codex to check or validate a livespec specification.
---

# livespec-doctor

This is a Codex runtime adapter for the livespec `doctor` operation.
It is not the operation's behavior source of truth.

When this skill is triggered:

1. Resolve the repository root as the current working tree.
2. Read `.claude-plugin/prose/doctor.md` completely.
3. Follow that prose exactly for behavior, routing, failure handling, and user-facing output.
4. When the prose calls for the static doctor CLI, invoke `.claude-plugin/scripts/bin/doctor_static.py` from this repository with explicit argv.
5. For a non-mutating CLI-help proof, invoke `.claude-plugin/scripts/bin/doctor_static.py --help`.
6. Do not copy, summarize as a substitute for, or restate operation behavior from the prose in this adapter.
