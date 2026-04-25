# bootstrap/ orientation

Throwaway scaffolding for executing the livespec bootstrap plan. The
production app does not depend on anything in this directory.

After the layout fix in commit history (the marketplace+plugin
content moved out of `bootstrap/`), this directory contains ONLY the
state files plus this orientation. The plugin contents themselves
live at `.claude/plugins/livespec-bootstrap/`; the marketplace
manifest lives at `.claude-plugin/marketplace.json` (repo root).
Phase 11 cleanup removes those two locations; this directory stays
in place as historical reference.

## Files (in this directory)

| File | Purpose |
|---|---|
| `STATUS.md` | Current phase, sub-step, last completed exit criterion, next action, last commit. |
| `open-issues.md` | Append-only-with-status-mutation log of plan / PROPOSAL drift. |
| `decisions.md` | Append-only log of executor judgment calls during phase work. |
| `AGENTS.md` | This file. |

## Related files (outside this directory)

| Path | Purpose |
|---|---|
| `.claude-plugin/marketplace.json` | Repo-root marketplace manifest declaring the `livespec-bootstrap` plugin. Auto-discovered by Claude Code. |
| `.claude/plugins/livespec-bootstrap/.claude-plugin/plugin.json` | Plugin manifest. |
| `.claude/plugins/livespec-bootstrap/skills/bootstrap/SKILL.md` | Skill prose driving plan execution. The full behavior contract — phase loop, drift-correction sub-flows, state-file formats — lives here. |

## How the skill is exposed to Claude Code

Claude Code auto-discovers `marketplace.json` at the standard
repo-root location `.claude-plugin/marketplace.json`. The
marketplace's `plugins[]` entry uses a string-typed `source`
field pointing at `./.claude/plugins/livespec-bootstrap` (the
plugin's directory). The plugin's manifest lives at
`.claude/plugins/livespec-bootstrap/.claude-plugin/plugin.json`;
its skill at
`.claude/plugins/livespec-bootstrap/skills/bootstrap/SKILL.md`.
This layout matches the working reference at
`~/workspace/openbrain/.claude-plugin/marketplace.json` +
`~/workspace/openbrain/.claude/plugins/openbrain/`.

Earlier attempts at symlinks under `.claude/plugins/` and at a
non-default marketplace path with `extraKnownMarketplaces` in
`.claude/settings.json` both failed; the openbrain-style layout is
what works.

**One-time setup per machine.** On workspace trust, Claude Code
auto-loads the marketplace; `/reload-plugins` (or restart) makes
the plugin available. If `/livespec-bootstrap:bootstrap` doesn't
appear after `/reload-plugins`, run
`/plugin install livespec-bootstrap@livespec-marketplace` then
`/reload-plugins` again.

## Don't

- **Hand-edit `STATUS.md`, `open-issues.md`, or `decisions.md`.**
  The bootstrap skill is the only writer; manual edits get
  overwritten on the next invocation. If you need to record
  something, invoke the skill and use the "Report an issue first"
  or "Record a decision first" branch.
- **Reference anything in `bootstrap/` from production code paths**
  (`.claude-plugin/plugin.json`, `dev-tooling/`, `tests/`,
  `SPECIFICATION/`). The bootstrap scaffolding is a closed system
  removed from the production app at Phase 11.

## Do

- Invoke `/livespec-bootstrap:bootstrap` to start or continue
  execution. The skill drives every sub-step.
- Read `STATUS.md` directly if you just want to see where you are
  without invoking the skill.
- Read `open-issues.md` to see what drift has been logged across
  prior sessions.

## After bootstrap completes

Phase 11 removes `.claude/plugins/livespec-bootstrap/` and
`.claude-plugin/marketplace.json`. This directory itself stays in
place as historical reference. The skill's slash command stops
working once those are gone; that's intentional — the production
app uses its own `/livespec:*` slash commands instead.
