---
name: livespec-implementation-beads:plan
description: Manage beads issues for implementation work — create new issues for untracked implementation gaps, triage existing issues, set priorities and dependencies, and commit the beads export view as a reviewable planning commit. Surfaces untracked gaps to the user before creating issues. Invoked by /livespec-implementation-beads:plan, "plan implementation work", "manage beads issues", or after a refresh-gaps run reveals new untracked gaps.
---

# plan

You are running an interactive planning session that maintains
implementation-gap-tied beads issues for the
`livespec-implementation` workflow. The user drives every
state-changing `bd` write; you persist state via noninteractive
`bd` commands and the `dev-tooling/implementation/plan.py`
automation, but ONLY after per-issue and per-dep-edge consent.

## Spec contract (verbatim)

From `SPECIFICATION/non-functional-requirements.md` §Spec
§"Repo-local implementation workflow":

> `plan` — manages beads issues for implementation work,
> including creating new beads issues for untracked
> implementation gaps and triaging existing issues. Surfaces
> untracked gaps to the user before creating issues; commits
> the beads export view as a reviewable planning commit.

## Hard rules (non-functional-requirements.md §Constraints §"Beads invariants")

1. **Issue prefix.** All new issues use the `li-` prefix.
   `bd init` was run with `--prefix li`; `bd create` honors the
   prefix automatically.
2. **Gap-id ↔ beads-label, exactly one.** Every gap id from
   `implementation-gaps/current.json` MUST correspond to exactly
   one beads issue across all statuses. Gap-tied issues carry
   the `gap-id:gap-NNNN` label (`-l gap-id:gap-NNNN`); plan.py's
   `--create` mode attaches it automatically. Run
   `just implementation::check-gap-tracking` after each batch.
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

## Consent rules (cross-reference: li-1f5 Item 4)

Every state-changing bd write on the user's behalf REQUIRES
explicit per-write consent. The plan skill realizes this for
the two writes it issues:

- **Per-issue consent.** Before any `bd create`, surface the
  proposed issue (gap id, title, fix-hint, depends_on) and ask
  the user to confirm. Multiple gaps → ask per gap, not per
  batch ("OK to create all 5?" is NOT consent — the user must
  see and approve each one).
- **Per-dep-edge consent.** When a gap names predecessors in
  `depends_on`, surface the proposed `bd dep add <new> <pred>`
  and ask per edge before issuing it.

The user MAY pre-authorize a batch ("create all of these")
explicitly, but the default is per-issue confirmation. Don't
assume batch authorization from earlier in the session.

## Canonical invocation

The plan workflow is split between an automation step (plan.py
mechanically files the issues) and a dialogue step (you, the
agent, surface candidates and collect consent before invoking
the automation).

**List untracked gaps** (read-only on bd):

```
just implementation::plan
```

Equivalent direct invocation:

```
uv run python3 dev-tooling/implementation/plan.py
```

Default mode emits a JSON array of untracked gap entries to
stdout (gaps in `current.json` whose `gap-id:gap-NNNN` label
is not yet attached to any beads issue across all statuses).

**File one or more issues** (after per-issue consent):

```
uv run python3 dev-tooling/implementation/plan.py --create gap-NNNN [gap-NNNN ...]
```

Each named gap id is filed as a `bd create -t task -p 2 -l
gap-id:gap-NNNN --json` issue with title and description from
the gap blueprint. After creation, predecessors named in the
gap's `depends_on` field are wired via `bd dep add <new-issue>
<predecessor-issue>` for every predecessor that already has a
tracking issue. Already-tracked gaps are silently skipped
(idempotent).

**File every untracked gap** (rarely the right choice — the
batch case usually wants per-gap consent):

```
uv run python3 dev-tooling/implementation/plan.py --create-all
```

## Workflow

1. Run `just implementation::refresh-gaps` if the report is
   stale (or doesn't exist). The plan workflow needs an
   accurate `current.json` to identify untracked gaps.
2. Run `just implementation::plan` to surface the untracked
   gaps. Read the result.
3. **For each untracked gap, surface to the user**: gap id,
   title, fix-hint, depends_on. Ask whether to file it.
4. **For each `depends_on` predecessor**: surface the proposed
   `bd dep add` edge. Ask whether to file it.
5. Once the user confirms, run
   `plan.py --create gap-NNNN [...]` for the approved gaps.
   plan.py emits one log line per `bd create` and per
   `bd dep add` for transcript clarity.
6. Run `just implementation::check-gap-tracking` and confirm
   the 1:1 invariant still holds.
7. Stage `.beads/issues.jsonl` (auto-exported) and commit with
   a Conventional Commits subject like
   `chore(beads): file li-NNN — <one-line summary>` (single
   issue) or
   `chore(beads): plan li-N..li-M — <theme>` (batch). The
   commit goes through the chained lefthook gates normally.

## Triage workflows (non-create)

The plan skill also covers triage of existing issues. Closing
gap-tied issues with `--resolution fix` is the `implement`
skill's responsibility, NOT this skill's; non-fix closures
(wontfix / spec-revised / duplicate / no-longer-applicable)
ARE in scope here.

| Goal | Command | Consent? |
| --- | --- | --- |
| Re-prioritise an issue | `bd update <id> --priority <0-4>` | Per-update. |
| Re-title an issue | `bd update <id> --title "..."` | Per-update. |
| Defer an issue | `bd defer <id> --until "<date>"` | Per-update. |
| Add a `blocks` dep | `bd dep add <blocked> <blocker>` | Per-edge. |
| Close (non-fix reason) | `bd close <id> --reason "<why>"` | Per-close. |
| Reopen | `bd update <id> --status open` | Per-update. |
| Add a label | `bd update <id> --add-label <label>` | Per-update. |

Priorities: `0` = critical, `1` = high, `2` = normal (default),
`3` = low, `4` = backlog.

## Pattern source

Open Brain's `plan` skill is the canonical reference for this
workflow. Differences:

- Issue prefix: `li-` (livespec) vs. `ob-` (Open Brain).
- Gap-report path: `implementation-gaps/current.json`
  (livespec) vs. `current-specification-drift.json`
  (Open Brain).
