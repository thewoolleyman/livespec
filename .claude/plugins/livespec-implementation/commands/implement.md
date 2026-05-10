---
description: Drive issue-based implementation work — pull a leaf-level issue from `bd ready`, do Red→Green code cycle, verify the gap is closed, then close the beads issue with audit fields
allowed-tools: Skill, Bash, Read, Write, Edit, Grep, Glob, AskUserQuestion
---

Invoke the `implement` skill (per
`.claude/plugins/livespec-implementation/skills/implement/SKILL.md`)
to drive a single round of issue-based implementation work.

Workflow:

1. `bd ready --json` — pick the next leaf-level issue with no
   unmet `bd dep` blockers. Prefer lower issue ids first.
2. `bd update <id> --status in-progress` to claim the work.
3. Do the work. For code changes, follow v034 Red→Green
   discipline: red commit (test only), green amend (impl).
4. Run `just implementation::refresh-gaps` (or invoke the
   refresh-gaps skill manually if the Python automation isn't
   ready yet). Capture the `run_id` from the structlog output.
5. Inspect `implementation-gaps/current.json` and confirm the
   gap-id you were working on is GONE. If it still appears,
   the fix is incomplete — continue working; do NOT close.
6. Once verified gone, close the issue with `bd close <id>
   --resolution fix --note "<audit fields>"`. The audit note
   MUST include: the gap-id, evidence of fix (spec section +
   impl evidence), the verification refresh-gaps run_id, and
   the verification timestamp (UTC ISO-8601).
7. Run `just implementation::check-gap-tracking` to confirm
   the 1:1 invariant still holds.

For non-fix closures (wontfix / spec-revised / duplicate /
no-longer-applicable), use `bd close <id> --reason
<closure_summary>` instead — no refresh-gaps re-verification
needed.

Per the consent rules: `bd close` invocations and the
accompanying commits require explicit user confirmation.
