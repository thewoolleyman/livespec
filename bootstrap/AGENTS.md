# bootstrap/ orientation

Throwaway scaffolding for executing the livespec bootstrap plan. The
production app does not depend on anything in this directory; Phase 11
cleanup removes the symlink that exposes the bootstrap skill, but the
directory itself stays in place as historical reference.

## Files

| File | Purpose |
|---|---|
| `.claude-plugin/plugin.json` | Plugin manifest for the bootstrap skill. |
| `.claude-plugin/skills/bootstrap/SKILL.md` | Skill prose driving plan execution. The full behavior contract — phase loop, drift-correction sub-flows, state-file formats — lives here. |
| `STATUS.md` | Current phase, sub-step, last completed exit criterion, next action, last commit. |
| `open-issues.md` | Append-only-with-status-mutation log of plan / PROPOSAL drift. |
| `decisions.md` | Append-only log of executor judgment calls during phase work. |
| `AGENTS.md` | This file. |

## How the skill is exposed to Claude Code

The repo-root symlink `.claude/plugins/livespec-bootstrap/` points at
`bootstrap/.claude-plugin/`. Claude Code auto-discovers the plugin
through that path; `/reload-plugins` refreshes after SKILL.md edits.

## Don't

- **Hand-edit `STATUS.md`, `open-issues.md`, or `decisions.md`.** The
  bootstrap skill is the only writer; manual edits get overwritten
  on the next invocation. If you need to record something, invoke
  the skill and use the "Report an issue first" or "Record a
  decision first" branch.
- **Add new files beyond the six above** without amending the skill's
  state-file contract.
- **Reference anything in `bootstrap/` from production code paths**
  (`.claude-plugin/`, `dev-tooling/`, `tests/`, `SPECIFICATION/`).
  The bootstrap scaffolding is a closed system removed from the
  production app at Phase 11.

## Do

- Invoke `/livespec-bootstrap:bootstrap` to start or continue
  execution. The skill drives every sub-step.
- Read `STATUS.md` directly if you just want to see where you are
  without invoking the skill.
- Read `open-issues.md` to see what drift has been logged across
  prior sessions.

## After bootstrap completes

Phase 11 removes the `.claude/plugins/livespec-bootstrap/` symlink
(and `.claude/plugins/` if empty). This directory itself stays as
historical reference. The skill's slash command stops working once
the symlink is gone; that's intentional — the production app uses
its own `/livespec:*` slash commands instead.
