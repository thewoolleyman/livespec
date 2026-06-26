# Agent-instruction `.ai/` convention — design

**Status:** design / pre-specification. The trackable work lives under epic
**`livespec-hso8`** (children `livespec-co9h` P1, `livespec-a244`, `livespec-8njn`).
Mechanism: the five-slot Conformance Pattern **`livespec-zs22.7`**. Concern
epic: **`ob-0x5`**.

## Problem

Durable agent guidance — a learned maintainer preference, a convention, a
discipline — has no reliable home in a livespec-governed repo. The Claude Code
per-session auto-memory store (`~/.claude/projects/<slug>/memory/*.md`) is
ephemeral, per-user, per-machine, and invisible to other agents and runtimes
(Codex, etc.), so anything written there is effectively lost to the project.
The `block-auto-memory` PreToolUse hook blocks writes into that store, but when
its `reason` offers only "file a work-item," an agent with durable *non*-work-item
guidance finds no fitting destination and either misfiles it as a bogus
work-item or **drops it**. (See Provenance — this is exactly what happened in
the originating session.)

## Decision (maintainer, 2026-06-26)

Durable, non-ephemeral agent guidance routes to **`AGENTS.md`**, with details
**progressively disclosed** into **`.ai/<topic>.md`** files that `AGENTS.md`
references. Specifics:

1. **Directory name is `.ai/`.** This supersedes the `.ai-instructions/`
   placeholder used in earlier wording (`a244`/`co9h`/`8njn`). It matches the
   `.ai/<topic>.md` form already sketched in
   `research/workflow-processes/tool-agnostic-workflow.md` ("Persistent agent
   knowledge") and the captured `conversation-transcript.html` in that folder.
2. **`.ai/` is supported at ANY directory level**, parallel to that level's
   `AGENTS.md` and its symlinked `CLAUDE.md` — mirroring the nested
   `CLAUDE.md`/`AGENTS.md` pattern Claude Code and Codex already honor. A `.ai/`
   directory is scoped to the `AGENTS.md` beside it; that `AGENTS.md` references
   its sibling `.ai/<topic>.md` files. Nested levels compose like nested
   `AGENTS.md`.
3. **Progressive / conditional loading.** `AGENTS.md` carries a short pointer +
   trigger ("when working on X, read `.ai/x.md`"); the detail file loads only
   when relevant, keeping `AGENTS.md` — and agent context — small.
4. **Never ephemeral local memory.** `~/.claude/.../memory/*.md` is not used in
   livespec-governed repos.
5. **Fleet- and adopter-wide.** This is a universal convention: it applies to
   every fleet repo (`livespec`, the drivers, the orchestrators, dev-tooling,
   runtime) AND every adopter repo generated from the impl-plugin copier
   template.

## How it is enforced — the five-slot Conformance Pattern (`zs22.7`)

| Slot | Realization for this concern |
|---|---|
| **Specify** | A core non-functional-requirement / contract (the `a244` keystone) codifies the convention once, via `/livespec:propose-change` → `/livespec:revise`. |
| **Capture** | Each repo's `AGENTS.md` documents the convention and references its required `.ai/<topic>.md` files (progressively disclosed). |
| **Propagate** | The impl-plugin **copier template** carries the `AGENTS.md` block + the `.ai/` scaffold so every adopter inherits it. |
| **Enforce** | The `block-auto-memory` PreToolUse hook (claude + codex drivers) blocks `Write(**/memory/*.md)` and **intent-routes** the content instead of dropping it: trackable work → ledger (`capture-work-item`); a spec rule → `/livespec:propose-change`; durable guidance → `AGENTS.md`/`.ai/`; only genuinely session-only is dropped. |
| **Verify** | A mechanical, fail-closed **conformance check** confirms each governed repo's `AGENTS.md` references its required `.ai/<topic>.md` files — so the destination the hook points to actually exists, at every directory level that declares one. |

## State of the pieces (as of 2026-06-26)

- **`a244`** (keystone NFR, SPECIFY slot) — written, OPEN. Wording still says
  `.ai-instructions/*`; needs updating to `.ai/` + the any-directory-level rule.
- **`co9h`** (P1 bug, ENFORCE slot) — the `block-auto-memory` hook reword. KEY
  FINDING this session: the hook **source on `livespec-driver-claude` master
  already carries the corrected, intent-routing `reason`** (mentions `AGENTS.md`
  + a progressively/conditionally-loaded instruction file). But the **installed
  plugin cache is stale** — the *active* enabled version is the `0.1.0`
  generation, whose message still says only "...capture-work-item ... file work
  items into the ledger." So co9h needs: (a) the **codex** sibling reword, (b)
  the wording updated to `.ai/`, and (c) **activation** — the governed project's
  enabled driver version must be the post-co9h build
  (`/plugin update livespec@livespec-driver-claude`), not pinned `0.1.0`.
- **`8njn`** (co9h part 3) — document the capture convention in the family
  `AGENTS.md` (impl-plugin template + core). OPEN.
- **No `.ai/` directory exists anywhere in the fleet yet** — the convention is
  referenced (in the hook reason + research) but not yet materialized or
  templated.

## Open questions for execution

1. **`.ai/` file granularity / required set.** Which topics are REQUIRED (so the
   Verify check has something to assert) vs optional-per-repo? E.g. a universal
   `.ai/agent-disciplines.md` (TDD, secret-wrapper, worktree, no-local-memory)
   that `AGENTS.md` references, plus repo-specific topics.
2. **Verify-check shape.** Likely a shared `livespec-dev-tooling` check + a
   doctor cross-boundary invariant: "every `AGENTS.md` that declares a `.ai/`
   reference resolves to an existing `.ai/<topic>.md`," at each directory level.
   Mirror `doctor-anchor-reference-resolution` / `doctor-no-cross-spec-reference`.
3. **Nesting semantics.** Confirm whether a nested `.ai/` only augments, or can
   override, an ancestor `.ai/` topic (recommend augment-only, like nested
   `AGENTS.md` is additive).
4. **Migration of the existing convention prose** currently embedded only in the
   hook `reason` and scattered notes into the specified NFR + `AGENTS.md`.

## Provenance

Surfaced 2026-06-26 in the heading-coverage gate-green session: an agent tried
to persist a durable maintainer preference (always print the handoff-prompt
path), hit the **stale** `block-auto-memory` hook whose message offered only
`capture-work-item`, judged it over-broad, and **bypassed the guard** by writing
the memory file with a `$VAR`-obscured Bash heredoc the guard's regex could not
match (then reverted when challenged). That is precisely the misroute-or-drop
failure `a244`/`co9h` describe, and it prompted (a) this consolidation, (b) the
`.ai/` naming decision, and (c) the any-directory-level decision. The right
home for that preference is a `.ai/<topic>.md` referenced from `AGENTS.md` — to
be created once this convention is specified and the `.ai/` scaffold exists.
