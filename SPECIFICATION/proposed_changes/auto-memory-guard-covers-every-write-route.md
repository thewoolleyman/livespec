---
topic: auto-memory-guard-covers-every-write-route
author: claude-opus-5-5
created_at: 2026-10-18T16:10:41Z
---

## Proposal: Claude auto-memory redirect covers every write route

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Widen the Claude Code Driver's PreToolUse auto-memory redirect from the Write tool alone to every route an agent session uses to write a memory file: Write, Edit, MultiEdit, and Bash commands that write into an agent memory directory. The intent-routing reason is unchanged except that its durable-guidance route names the progressive-disclosure shape explicitly: a short AGENTS.md entry pointing at a .ai/<topic>.md file that holds the content.

### Motivation

On 2026-10-18 a session in the governed project livespec-orchestrator-beads-fabro wrote two notes into ~/.claude/projects/<slug>/memory/ with `cat >>` and `sed`, and no guard refused either. The installed Driver hook (livespec-driver-claude v0.10.0) is registered on Write only, exactly as this clause ratifies, so Edit, MultiEdit and every shell write reach the memory store unguarded. Fifty-two notes accumulated that way across five governed projects on one host. The earlier verification livespec-driver-claude-vxy7io correctly found the hook conformant, because the clause itself pins the Write-only registration. The same file's Fleet agent-instruction core section already says the memory store is NEVER the home for durable guidance in a governed member; this change makes the hook enforce that statement on every write route. Plan: livespec-driver-claude plan block-auto-memory-coverage, epic livespec-driver-claude-22yt6u.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"Driver-shipped hooks", in the bullet **PreToolUse auto-memory redirect**, replace the sentence beginning "Registered on the `Write` tool; the effective matcher is `Write(**/memory/*.md)`" and its parenthetical with the following, leaving the rest of the bullet unchanged:

> Registered on the `Write`, `Edit`, and `MultiEdit` tools and on the `Bash` tool. For a file tool the hook acts when the target file's immediate parent directory is `memory` and the filename ends in `.md` (the Claude Code auto-memory layout, `~/.claude/projects/<slug>/memory/*.md`). For `Bash` the hook MUST deny a command that it POSITIVELY identifies as writing a file into an agent memory directory — the Claude Code layout above or the Codex local-memory store `~/.codex/memories/` — judging each `;`, `&&`, `||` and pipeline segment, and the payload of a `sh -c` / `bash -c` / `env` wrapper. The write forms the hook MUST recognise are a NON-EXHAUSTIVE minimum the Driver MAY widen and MUST NOT narrow: output redirection (`>`, `>>`, including a here-document redirected into such a path), `tee`, an in-place editor (`sed -i`, `perl -i`), a `cp`, `mv`, `install`, `ln`, `touch`, `truncate`, or `dd of=` whose destination lies in such a directory, and an inline interpreter program (`python3 -c`, `perl -e`, `node -e`) whose text names such a path together with a write-mode open. A command that only reads such a directory (`cat`, `grep`, `ls`, `head`, `find` without `-delete` or `-exec`) MUST NOT be denied, and removing a note (`rm`) MUST NOT be denied, because removal is how a migrated note is discharged. A write whose destination path the guard cannot read from the command text (a path computed at runtime, or assembled by a script file) is a STATED LIMIT of this guard, not a defect; the fail-open discipline still applies, so the hook MUST pass through on any failure and acts only on a POSITIVE identification.

In the same bullet, replace the durable-guidance route "durable non-work-item agent guidance (a learned preference, convention, or discipline) routes to the member's `AGENTS.md` or a referenced progressively-disclosed `.ai/<topic>.md` file per §\"Fleet agent-instruction core\"" with:

> durable non-work-item agent guidance (a learned preference, convention, or discipline) routes to a short discoverable entry in the member's `AGENTS.md` that points at a progressively-disclosed `.ai/<topic>.md` file holding the content, or to `AGENTS.md` alone when the guidance is itself short, per §"Fleet agent-instruction core"

The deny reason MUST be identical across the file-tool and `Bash` routes.

## Proposal: Codex auto-memory-write guard covers shell writes

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Extend the Codex Driver's required auto-memory-write guard from manual apply_patch, Edit and Write calls to shell commands, using the same write-form recognition the Claude redirect now uses, and cover the Claude Code memory layout as well as the Codex store, since a Codex session can write either.

### Motivation

The Codex Driver ships block_auto_memory.py on Write, Edit and apply_patch only (livespec-driver-codex livespec/hooks/hooks.json, measured 2026-10-18), so a Codex shell command writes into ~/.codex/memories/ or ~/.claude/projects/<slug>/memory/ unguarded, the same bypass the Claude Driver has. The clause should state the shell route for both runtimes symmetrically. Plan: livespec-driver-claude plan block-auto-memory-coverage, epic livespec-driver-claude-22yt6u.

### Proposed Changes

In `SPECIFICATION/contracts.md`, in the paragraph **Codex auto-memory-write guard (required).**, replace "it MUST intercept a tool call that would write a file into the Codex local-memory store (`~/.codex/memories/`) — a manual `apply_patch` / `Edit` / `Write` whose target path is under that store —" with:

> it MUST intercept a tool call that would write a file into an agent memory directory — the Codex local-memory store (`~/.codex/memories/`) or the Claude Code auto-memory layout (`~/.claude/projects/<slug>/memory/*.md`) — whether a manual `apply_patch` / `Edit` / `Write` whose target path is under such a directory, or a shell command the guard POSITIVELY identifies as writing into one, recognised by the same NON-EXHAUSTIVE minimum write forms, read and removal allowances, and stated limits as the Claude auto-memory redirect in §"Driver-shipped hooks" —

The remainder of the paragraph, including the KNOWN LIMITATION about background-generated memories and the fail-open discipline, MUST remain unchanged.
