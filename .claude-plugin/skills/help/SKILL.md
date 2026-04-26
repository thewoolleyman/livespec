---
name: help
description: Explain what livespec does and route the user to the right sub-command (seed, propose-change, critique, revise, doctor, prune-history). Invoked by /livespec:help, "what can livespec do", or when the user asks for an overview of livespec capabilities.
allowed-tools: Read
---

# help

Explain what livespec does at a high level and route the user to
the right sub-command for their intent. There is no Python
wrapper for `help` — the response is composed by the LLM in
narration, no `bin/*.py` invocation, no JSON.

## When to invoke

- The user types `/livespec:help`, says "what can livespec do",
  "how do I use livespec", or asks for an overview of livespec
  capabilities.
- The user describes a goal (e.g., "I want to start a spec"
  or "I want to file a change") and is unsure which
  sub-command to invoke.

## Steps

1. **Brief overview.** Explain in 1-2 sentences:
   "livespec is an LLM-mediated specification toolchain.
   You author natural-language specifications, and livespec's
   sub-commands govern the workflow: seeding the initial spec,
   filing proposed changes, critiquing, revising into version
   snapshots, and running structural-invariant checks."

2. **Route to the right sub-command.** Map the user's goal to
   one of:
   - **seed** (`/livespec:seed`) — start a brand-new spec in
     an empty project. The skill walks a 3-question pre-seed
     dialogue (template, sub-specs?, intent), then generates
     and writes the initial `SPECIFICATION/` tree plus
     auto-captured seed proposed-change.
   - **propose-change** (`/livespec:propose-change`) — file a
     proposed change against an existing spec. Lands at
     `<spec-target>/proposed_changes/<topic>.md`.
   - **critique** (`/livespec:critique`) — file a critique-
     style proposed-change (delegates to propose-change with
     `-critique` reserve-suffix appended).
   - **revise** (`/livespec:revise`) — process all pending
     proposed-changes with per-proposal accept/modify/reject
     decisions, cut a new history/vNNN/ snapshot.
   - **doctor** (`/livespec:doctor`) — run static-invariant
     checks across the main spec + each sub-spec tree.
   - **prune-history** (`/livespec:prune-history`) — collapse
     old version snapshots per the configured retention rule
     (Phase 7 adds the wrapper; not available in Phase 3
     minimum-viable).

3. **Pointer to per-sub-command help.** Mention that each
   sub-command's wrapper supports `-h` / `--help` (e.g.,
   `bin/seed.py --help` via Bash) for the CLI flag details.

## Post-wrapper

No wrapper invocation; no post-step LLM-driven phase.

## Failure handling

No wrapper exit codes — this skill is pure LLM narration. If
the user asks about a sub-command not yet implemented (e.g.,
`prune-history` in Phase 3), redirect them to "Phase 7 adds
this wrapper; for now, the spec tree is append-only".

## Phase 3 minimum-viable scope

This is bootstrap prose; Phase 7 widens to the full
per-sub-command dispatch + intent-recognition flow per
`skill-md-prose-authoring`.
