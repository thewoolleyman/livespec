---
name: livespec-implementation-beads:plan
description: Manage beads issues for implementation work — create new issues for untracked implementation gaps, triage existing issues, set priorities and dependencies, and commit the beads export view as a reviewable planning commit. Surfaces untracked gaps to the user before creating issues. Invoked by /livespec-implementation-beads:plan, "plan implementation work", "manage beads issues", or after a refresh-gaps run reveals new untracked gaps.
---

# plan

You are running an interactive planning session that maintains
implementation-gap-tied beads issues for the
`livespec-implementation` workflow. The user drives; you persist
state via noninteractive `bd` commands.

## Spec contract (verbatim)

From `SPECIFICATION/non-functional-requirements.md` §Spec
§"Repo-local implementation workflow":

> `plan` — manages beads issues for implementation work, including
> creating new beads issues for untracked implementation gaps and
> triaging existing issues. Surfaces untracked gaps to the user
> before creating issues; commits the beads export view as a
> reviewable planning commit.

## Hard rules (non-functional-requirements.md §Constraints §"Beads invariants")

1. **Issue prefix.** All new issues use the `li-` prefix.
   `bd init` was run with `--prefix li`; `bd create` honors this
   automatically.
2. **Gap-id ↔ beads-label, exactly one.** Every gap id from
   `implementation-gaps/current.json` MUST correspond to exactly
   one beads issue across all statuses. When you create a
   gap-tied issue, attach the gap id as a label
   (`-l gap-id:gap-NNNN` or `--labels +gap-id:gap-NNNN`). Run
   `just implementation::check-gap-tracking` after planning to
   confirm the invariant holds.
3. **Dolt is source-of-truth.** NEVER hand-edit
   `.beads/issues.jsonl`. NEVER run manual JSONL import/export
   as ordinary workflow. The `bd config set export.auto true`
   auto-exports the JSONL view after each write; commit that
   view as part of the planning commit.
4. **Noninteractive only.** Forbidden: `bd edit` (opens
   `$EDITOR`). Use `bd create`, `bd update <id> --description "..."`,
   `bd update <id> --status ...`, `bd dep add`, `bd close`, etc.
   Pass `--json` when output informs a follow-up command.
5. **Hooks already chained.** `core.hooksPath = .beads/hooks/`,
   templates managed by `dev-tooling/implementation/setup-beads.sh`
   chain lefthook FIRST + bd SECOND with exit-status preserved.
   You don't have to do anything special at commit time.

## bd command repertoire (noninteractive only)

| Goal | Command |
| --- | --- |
| List open issues | `bd list --status open --json` |
| Show one issue | `bd show <id> --json` |
| Find unblocked work | `bd ready --json` |
| Create freeform issue | `bd create "<title>" -t task -p <0-4> -d "<desc>"` |
| Create gap-tied issue | `bd create "<title>" -t task -p <n> -d "<desc>" -l gap-id:gap-NNNN` |
| Add a `blocks` dep | `bd dep add <blocked-id> --type blocks <blocker-id>` |
| Update title / desc | `bd update <id> --title "..."` / `--description "..."` |
| Re-prioritise | `bd update <id> --priority <0-4>` |
| Set status (e.g. `blocked`) | `bd update <id> --status blocked` |
| Close (non-fix reason) | `bd close <id> --reason "<closure_summary>"` |
| Reopen | `bd update <id> --status open` |
| Add a label retroactively | `bd update <id> --labels +<label>` |

Priorities: `0` = critical, `1` = high, `2` = normal (default),
`3` = low, `4` = backlog.

## Workflow

1. Read `implementation-gaps/current.json` (run `refresh-gaps`
   first if the file is stale or missing).
2. For each `gaps[].id` not yet labelled on any beads issue,
   surface it to the user with the gap's title + spec_refs +
   fix_hint. Confirm before creating.
3. Run `bd create` for each confirmed gap with the `gap-id:`
   label. Establish `bd dep add` edges where the gap depends on
   another (e.g. Python automation depends on schema being
   authored).
4. After all writes, run
   `just implementation::check-gap-tracking` and confirm green.
5. Stage `.beads/issues.jsonl` (the auto-exported view) and
   commit with a Conventional Commits subject like
   `chore(beads): plan li-N..li-M for current implementation
   gaps`. The commit goes through the chained lefthook gates
   normally.

Closing gap-tied issues with `--resolution fix` is the
`implement` skill's responsibility, NOT this skill's.
Non-fix closures (wontfix / spec-revised / duplicate /
no-longer-applicable) are in scope here.

## Manual fallback (current state)

The Python automation at
`dev-tooling/implementation/plan.py` is itself a tracked
implementation gap and may not exist at the time you read this.
Until it does, run the workflow above by hand using the bd
commands directly.
