# bootstrap/ orientation

Throwaway scaffolding for executing the livespec bootstrap plan. The
production app does not depend on anything in this directory; Phase 11
cleanup removes the symlink that exposes the bootstrap skill, but the
directory itself stays in place as historical reference.

## Files

| File | Purpose |
|---|---|
| `.claude-plugin/plugin.json` | Plugin manifest for the bootstrap skill. |
| `.claude-plugin/marketplace.json` | Local marketplace manifest declaring this plugin to Claude Code's discovery mechanism. |
| `.claude-plugin/skills/bootstrap/SKILL.md` | Skill prose driving plan execution. The full behavior contract — phase loop, drift-correction sub-flows, state-file formats — lives here. |
| `STATUS.md` | Current phase, sub-step, last completed exit criterion, next action, last commit. |
| `open-issues.md` | Append-only-with-status-mutation log of plan / PROPOSAL drift. |
| `decisions.md` | Append-only log of executor judgment calls during phase work. |
| `AGENTS.md` | This file. |

## How the skill is exposed to Claude Code

Two committed files coordinate plugin discovery:

- `bootstrap/.claude-plugin/marketplace.json` declares
  `livespec-marketplace` containing the `livespec-bootstrap`
  plugin (a directory-source plugin at the marketplace root).
- `.claude/settings.json` registers
  `extraKnownMarketplaces.livespec-marketplace` pointing at
  `./bootstrap/.claude-plugin` and pre-enables the plugin via
  `enabledPlugins["livespec-bootstrap@livespec-marketplace"]:
  true`.

**One-time setup per machine.** Claude Code prompts the user to
trust the workspace and add the marketplace on a fresh clone; the
user must then run
`/plugin install livespec-bootstrap@livespec-marketplace` once
to install the plugin into local Claude Code state. After that,
`/reload-plugins` refreshes after SKILL.md edits without
re-installing.

Symlinks under `.claude/plugins/` were tried in an earlier commit
and **do not work** — Claude Code's plugin loader does not follow
symlinks for project-local discovery. The marketplace mechanism
above is the documented supported approach.

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

Phase 11 removes the `livespec-marketplace` and
`livespec-bootstrap@livespec-marketplace` keys from
`.claude/settings.json` (or the whole file if no other settings
exist by then). This directory itself stays as historical
reference. The skill's slash command stops working once the
marketplace registration is gone; that's intentional — the
production app uses its own `/livespec:*` slash commands instead.
