---
name: livespec-implementation-beads:implement
description: Drive issue-based implementation work. Pull a leaf-level issue from `bd ready`, do the gap-closing work (Red→Green code cycle, doc edit, config change, etc.), verify the gap is closed by re-running refresh-gaps, then close the beads issue with resolution:fix and the required audit fields. Invoked by /livespec-implementation-beads:implement, "implement next gap", or "work the bd ready queue".
---

# implement

You are running the work-execution skill for the
`livespec-implementation` workflow. You pull the next ready
beads issue, do the work, verify it closed the linked
implementation gap, and close the issue with proof.

## Spec contract (verbatim)

From `SPECIFICATION/non-functional-requirements.md` §Spec
§"Repo-local implementation workflow":

> `implement` — drives issue-based implementation work. Verifies
> completed gap-tied issues by re-running `refresh-gaps` and
> confirming the gap no longer appears before closing the beads
> issue with `resolution:fix` and audit notes.

And from §Constraints:

> Closing a gap-tied beads issue with `resolution:fix` MUST
> re-run `livespec-implementation:refresh-gaps` (or
> `just implementation:refresh-gaps`) and confirm the gap no
> longer appears in `implementation-gaps/current.json`. If the
> gap remains, the issue MUST NOT be closed as fixed.
>
> Each closed issue MUST carry the following audit fields:
> - **Gap id** — the `id` value from
>   `implementation-gaps/current.json` when the issue was created.
> - **Evidence of fix** — specification section + implementation
>   evidence the gap was closed.
> - **Verification run id** — the `run_id` UUID from the
>   verifying `refresh-gaps` invocation's structlog output.
> - **Verification timestamp** — UTC ISO-8601 timestamp of the
>   verifying refresh-gaps run.

## Hard rules

- ALL bd writes are noninteractive. NEVER `bd edit`.
- The verification re-run of `refresh-gaps` is MANDATORY. The
  beads issue MUST NOT be closed with `--resolution fix` until
  the gap-id is gone from `implementation-gaps/current.json`.
- Code commits follow the standard livespec discipline:
  - Conventional Commits subjects (`feat:` / `fix:` / `chore:` /
    `refactor:` etc.) — enforced by
    `just check-conventional-commits` in commit-msg hook.
  - For `feat:` and `fix:` commits, the v034 D2-D3 Red→Green
    replay contract applies (Red commit stages exactly one new
    test file + zero impl; Green amend stages the impl). Other
    types (chore, docs, refactor) are exempt.
  - Direct commits to master are forbidden — work on the
    bootstrap or a feature branch; PR + rebase-merge to master.

## Workflow

1. `bd ready --json | jq` — pick the next leaf-level issue with
   no unmet `bd dep` blockers. Prefer lower issue ids first
   (earlier issues set up context for later ones).
2. `bd update <id> --status in-progress` to claim the work.
3. Do the work. For code changes, follow the v034 Red→Green
   discipline: red commit (test only), green amend (impl), then
   any chore/refactor follow-ups as separate commits.
4. Run `just implementation::refresh-gaps` (or invoke the
   `refresh-gaps` skill manually if the Python automation isn't
   ready yet). Capture the `run_id` from the structlog output.
5. Inspect `implementation-gaps/current.json` and confirm the
   gap-id you were working on is GONE. If it still appears:
   - The fix is incomplete. Continue working; do NOT close.
   - Optionally update the beads issue's description with the
     remaining work.
6. Once verified gone, close the issue:
   ```
   bd close <id> --resolution fix --note "$(cat <<'EOF'
   Gap id: gap-NNNN
   Evidence: <spec section + impl evidence>
   Verification run_id: <UUID from refresh-gaps>
   Verification timestamp: <UTC ISO-8601>
   EOF
   )"
   ```
7. Run `just implementation::check-gap-tracking` to confirm the
   1:1 invariant still holds (closed issues retain their
   gap-id labels — the invariant only requires exactly-one
   issue per CURRENT gap).

## Non-fix closures

If during work you discover the issue isn't actually a gap (spec
revised, duplicate of another issue, won't-fix), use
`bd close <id> --reason "<closure_summary>"` (no `--resolution
fix`). The `plan` skill is the better-suited surface for these
non-fix closures, but `implement` may handle them inline if
they surface mid-work.

## Manual fallback (current state)

The Python automation at
`dev-tooling/implementation/implement.py` is itself a tracked
implementation gap and may not exist at the time you read this.
Until it does, run the workflow above by hand using the bd
commands directly + manual `refresh-gaps` (per the
`refresh-gaps` SKILL.md "Manual fallback" section).
