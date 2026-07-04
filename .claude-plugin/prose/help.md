# help

Harness-neutral driving prose for the `help` operation, per
`SPECIFICATION/spec.md` §"Contract + reference implementations
architecture": this artifact is the core-owned LLM-facing half of the
operation. `help` has no backing CLI — the response is composed by
the LLM in narration, no CLI invocation, no JSON. Drivers bind this
prose to their runtime; nothing in this file names any specific agent
runtime's tools or command namespace.

Explain what livespec does at a high level and route the user to
the right operation for their intent.

## When to run

- The user invokes the help operation, says "what can livespec do",
  "how do I use livespec", or asks for an overview of livespec
  capabilities.
- The user describes a goal (e.g., "I want to start a spec"
  or "I want to file a change") and is unsure which
  operation to invoke.

## Steps

1. **Brief overview.** Explain in 1-2 sentences:
   "livespec is an LLM-mediated specification toolchain.
   You author natural-language specifications, and livespec's
   operations govern the workflow: seeding the initial spec,
   filing proposed changes, critiquing, revising into version
   snapshots, running validation checks, and ranking the
   next spec-side action."

2. **Route to the right operation.** Map the user's goal to
   one of:
   - **seed** — start a brand-new spec in an empty project.
     The operation walks a 3-question pre-seed dialogue
     (template, sub-specs?, intent), then generates and
     writes the initial `SPECIFICATION/` tree plus
     auto-captured seed proposed-change.
   - **propose-change** — file a proposed change against an
     existing spec. Lands at
     `<spec-target>/proposed_changes/<topic>.md`.
   - **critique** — file a critique-style proposed-change
     (delegates to propose-change with `-critique`
     reserve-suffix appended).
   - **revise** — process all pending proposed-changes with
     per-proposal accept/modify/reject decisions, cut a new
     history/vNNN/ snapshot.
   - **doctor** — validate the main spec + each sub-spec tree:
     the static structural-invariant phase plus the LLM-driven
     objective and subjective phases.
   - **prune-history** — destructively collapse old
     `history/vNNN/` snapshots into a single
     `PRUNED_HISTORY.json` marker. Requires explicit user
     invocation; the LLM MUST NOT auto-activate this
     operation.
   - **next** — rank the most-ripe next spec-side action
     (revise, propose-change, critique, prune-history, or
     none) over the current `proposed_changes/` and
     `history/` state, emitting structured JSON. Use when
     unsure what spec-side work to do next.

3. **Pointer to per-operation CLI help.** Mention that each
   operation's backing CLI supports `-h` / `--help` (e.g.,
   running the seed CLI named in config with `--help`) for
   the CLI flag details.

## Post-CLI

No CLI invocation; no post-step LLM-driven phase.

## Failure handling

No CLI exit codes — this operation is pure LLM narration. If
the user asks about a capability the installed version does
not carry, say so directly and point at the nearest
currently-available behavior.
