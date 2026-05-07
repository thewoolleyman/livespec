# livespec

A Claude Code plugin for governing a living natural-language
specification — seeding, proposing changes, critiquing, revising,
validating, and versioning.

## Install

```
/plugin marketplace add thewoolleyman/livespec
/plugin install livespec@livespec
```

After install, restart Claude Code (or run `/reload-plugins`).
The seven slash commands below become available with the
`livespec:` namespace prefix.

## Slash commands

- `/livespec:seed` — author the initial natural-language spec
- `/livespec:propose-change` — file a proposed change against the spec
- `/livespec:critique` — surface issues in the spec
- `/livespec:revise` — accept or reject pending proposed changes
- `/livespec:doctor` — run static + LLM-driven validation
- `/livespec:prune-history` — collapse old `history/vNNN/` entries
- `/livespec:help` — overview + routing to the right sub-command

## Dogfooding (editing the plugin source in this repo)

Two paths:

- **Live-reload mode** (daily dev): launch Claude Code with
  `claude --plugin-dir .` from the repo root. The plugin loads
  directly from the local source; edits to `.claude-plugin/skills/<name>/SKILL.md`
  and `.claude-plugin/scripts/...` are picked up via `/reload-plugins`
  without re-installing.
- **Marketplace install path** (verifies the published flow):
  use the install commands above (or
  `/plugin marketplace add ./.claude-plugin/marketplace.json`
  for the local marketplace variant). Either copies the plugin
  into `~/.claude/plugins/cache/` and does NOT live-reload — run
  `/plugin update livespec@livespec` to pull changes after editing.

## More

- See [AGENTS.md](AGENTS.md) for repo orientation.
- See [SPECIFICATION/](SPECIFICATION/) for the live livespec specification (dogfooded).
- See [archive/](archive/) for bootstrap-process history.
