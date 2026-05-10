---
description: Manage beads issues for implementation-gap work — surface untracked gaps, create gap-tied issues with consent, set dependencies, commit the export view
allowed-tools: Skill, Bash, Read, Write, Edit, AskUserQuestion
---

Invoke the `plan` skill (per
`.claude/plugins/livespec-implementation/skills/plan/SKILL.md`)
to manage beads issues for implementation work.

Workflow:

1. Read `implementation-gaps/current.json` (run
   `/livespec-implementation:refresh-gaps` first if the file is
   stale or missing).
2. For each `gaps[].id` not yet labelled on any beads issue,
   surface it to the user with the gap's title + spec_refs +
   fix_hint. Confirm BEFORE creating.
3. Run `bd create` for each confirmed gap with the
   `gap-id:gap-NNNN` label. Establish `bd dep add` edges per
   the gap's `depends_on` list.
4. After all writes, run
   `just implementation::check-gap-tracking` and confirm green.
5. Stage `.beads/issues.jsonl` (the auto-exported view) and
   commit with a Conventional Commits subject like
   `chore(beads): plan li-N..li-M for current implementation gaps`.

All `bd create` calls require explicit per-issue user consent.
No batch-filing. No urgency-framing in the ask.
