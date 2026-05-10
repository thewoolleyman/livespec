---
description: Refresh the implementation-gap report by comparing SPECIFICATION/ against the repo
allowed-tools: Skill, Bash, Read, Write, Edit, Grep, Glob
---

Invoke the `refresh-gaps` skill (per
`.claude/plugins/livespec-implementation/skills/refresh-gaps/SKILL.md`)
to walk `SPECIFICATION/` and the repository's implementation,
tests, tooling, and workflow state; derive the current
implementation-gap report; and write it to
`implementation-gaps/current.json`.

After the report is written, run `just implementation::check-gaps`
to validate the file against its schema. Surface any schema
errors to the user.

This skill is read-only with respect to `SPECIFICATION/` and
MUST NOT create or close beads issues. For issue triage, use
`/livespec-implementation:plan` after this command completes.
