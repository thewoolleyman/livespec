---
name: livespec-implementation-beads:implement
description: Drive issue-based implementation work. Surface ready issues to the user, ask which to claim, do the gap-closing work (Red→Green code cycle, doc edit, config change, etc.), verify the gap is closed by re-running refresh-gaps, then close the beads issue with resolution:fix and the required audit fields. Invoked by /livespec-implementation-beads:implement, "implement next gap", or "work the bd ready queue".
---

# implement

You are running the work-execution skill for the
`livespec-implementation` workflow. You surface ready beads
issues to the user, ask which to claim, do the work, verify it
closed the linked implementation gap, and close the issue with
proof.

## Spec contract (verbatim)

From `SPECIFICATION/non-functional-requirements.md` §Spec
§"Repo-local implementation workflow":

> `implement` — drives issue-based implementation work.
> Verifies completed gap-tied issues by re-running
> `refresh-gaps` and confirming the gap no longer appears
> before closing the beads issue with `resolution:fix` and
> audit notes.

And from §Constraints:

> Closing a gap-tied beads issue with `resolution:fix` MUST
> re-run `livespec-implementation:refresh-gaps` (or
> `just implementation:refresh-gaps`) and confirm the gap no
> longer appears in `implementation-gaps/current.json`. If the
> gap remains, the issue MUST NOT be closed as fixed.
>
> Each closed issue MUST carry the following audit fields:
> - **Gap id** — the `id` value from
>   `implementation-gaps/current.json` when the issue was
>   created.
> - **Evidence of fix** — specification section + implementation
>   evidence the gap was closed.
> - **Verification run id** — the `run_id` UUID from the
>   verifying `refresh-gaps` invocation's structlog output.
> - **Verification timestamp** — UTC ISO-8601 timestamp of the
>   verifying refresh-gaps run.

## Hard rules

- **Per-claim user consent.** NEVER auto-claim a `bd ready`
  issue. The agent surfaces candidates; the user picks. See
  the workflow §1-§3 below for the exact flow. This rule
  exists because session 2026-05-10 observed the agent
  parsing "pick the next leaf-level issue" as autonomous
  instructions and claiming li-0d0 without confirmation.
- **All bd writes are noninteractive.** NEVER `bd edit`
  (opens `$EDITOR`). The implement.py automation uses argv-list
  subprocess calls; manual fallback uses the same.
- **Mandatory verification re-run.** The beads issue MUST NOT
  be closed with `--resolution fix` until the gap-id is gone
  from `implementation-gaps/current.json`. The implement.py
  `--close` mode runs refresh-gaps as a subprocess and
  hard-refuses if the gap-id remains.
- **Code-commit discipline.** See §Code-change discipline
  below.

## Code-change discipline

- **Conventional Commits** subjects (`feat:` / `fix:` /
  `chore:` / `refactor:` / `docs:` / `test:` / `build:` /
  `ci:` / `style:` / `perf:` / `revert:`) — enforced by
  `just check-conventional-commits` in the commit-msg hook.
- **For `feat:` and `fix:` commits**, the v034 D2-D3
  Red→Green replay contract applies:
  - Red commit stages exactly one new test file + zero impl;
    the commit-msg hook runs the test, confirms it fails, and
    writes `TDD-Red-*` trailers (test-file SHA-256, output
    SHA-256, captured-at).
  - Green amend stages the impl; the commit-msg hook re-runs
    pytest, confirms the same test now passes, verifies the
    test-file SHA-256 matches the Red trailer, and writes
    `TDD-Green-*` trailers.
  - If the test must change between Red and Green, reset the
    Red commit and redo it with the final test content.
    Don't try to amend the test mid-cycle.
- **Other commit types (chore, docs, refactor, etc.)** are
  exempt from Red→Green replay — single commit is fine.
- **Direct commits to master are forbidden.** Work on a
  feature branch, push, open a PR, auto-merge with
  `gh pr merge --auto --rebase`. Branch protection enforces
  this server-side too.

## Canonical invocation

The implement workflow uses
`dev-tooling/implementation/implement.py` for the mechanical
verify-and-close flow; the agent owns the dialogue
(surfacing, consent, code edits).

**Surface ready issues** (read-only on bd):

```
just implementation::implement
```

Equivalent direct invocation:

```
uv run python3 dev-tooling/implementation/implement.py
```

Default mode runs `bd ready --json` and emits the result to
stdout. The agent reads this, surfaces it to the user, and
asks which issue to work on.

**Verify-and-close a completed issue**:

```
uv run python3 dev-tooling/implementation/implement.py \
  --close LI-ID \
  --gap GAP-NNNN \
  --evidence "<one-paragraph evidence-of-fix>"
```

This:

1. Subprocesses `dev-tooling/implementation/refresh_gaps.py`
   to regenerate `implementation-gaps/current.json`.
2. Hard-refuses if the named gap-id still appears in
   `gaps[].id`.
3. Composes the four-field audit notes (gap id, evidence,
   `run_id` from `inspection.run_id`, timestamp from
   `generated_at`).
4. Runs `bd update LI-ID --notes <audit> --add-label
   resolution:fix`.
5. Runs `bd close LI-ID --reason "<one-liner>"`.

## Workflow

1. Run `just implementation::implement` to read `bd ready
   --json`.
2. **Surface the ready candidates to the user** as a compact
   list: id, priority, gap-id label (if any), title. Include
   a one-line scope-feel for each (small/medium/large effort,
   if known).
3. **Ask the user which issue to claim.** Do NOT auto-pick
   based on priority, dependent-count, lower-id heuristics, or
   any other criterion. The user picks; you wait.
4. After the user confirms a specific issue, claim it:
   `bd update <id> --status in_progress` (or `bd update <id>
   --claim`, which atomically sets the assignee + status).
5. Do the work. For code changes, follow the Red→Green
   discipline above. For docs / config / refactor changes,
   single commit is fine.
6. Run `implement.py --close LI-ID --gap GAP-NNNN --evidence
   "..."`. The script will refuse if the gap-id is still
   present. If it refuses: continue working; do NOT bypass.
7. Run `just implementation::check-gap-tracking` to confirm
   the gap-id ↔ beads-label exactly-once invariant still
   holds. Closed issues retain their gap-id labels — the
   invariant only requires exactly-one issue per CURRENT gap
   (the now-closed issue's label doesn't count against the
   current state).
8. Stage `.beads/issues.jsonl` (auto-exported) and
   `implementation-gaps/current.json` (refreshed by the
   close), commit with a Conventional Commits subject like
   `chore(beads): close li-NNN — gap-NNNN verified gone (<one-liner>)`,
   push, open PR, auto-merge.

## Non-fix closures

If during work you discover the issue isn't actually a gap
(spec revised, duplicate of another issue, won't-fix), use
`bd close <id> --reason "<closure_summary>"` (no
`--resolution fix`). The `plan` skill is the better-suited
surface for these non-fix closures, but `implement` may
handle them inline if they surface mid-work.

## Pattern source

Open Brain's `implement` skill is the canonical reference
for this workflow. Differences:

- Issue prefix: `li-` (livespec) vs. `ob-` (Open Brain).
- Gap-report path: `implementation-gaps/current.json`
  (livespec) vs. `current-specification-drift.json`
  (Open Brain).
- Audit-fields phrasing: livespec uses `Verification run_id`
  / `Verification timestamp`; Open Brain uses
  `Drift run_id` / `Drift timestamp`.
