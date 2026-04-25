# livespec

A Claude Code plugin for governing a living natural-language
specification — seeding it, proposing changes, critiquing, revising,
validating, and versioning.

## Status

**Bootstrapping.** The project is being bootstrapped into a working
plugin via the plan at
[brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md](brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md).
Until bootstrap completes, the production layout
(`.claude-plugin/plugin.json`, `SPECIFICATION/`, `dev-tooling/`,
`tests/`, `pyproject.toml`, etc.) does NOT exist yet — only the
brainstorming artifacts and the bootstrap scaffolding.

See [AGENTS.md](AGENTS.md) for full repo orientation, especially if
you are an AI session.

## One-time setup (per machine)

To make the bootstrap skill discoverable, register and install the
local marketplace + plugin in Claude Code. Run these four commands
once:

```
/plugin marketplace add ./.claude-plugin/marketplace.json
/plugin marketplace update livespec-marketplace
/plugin install livespec-bootstrap@livespec-marketplace
/reload-plugins
```

When `/plugin install` asks where to install, choose
**repo-scoped (project scope)** — the plugin is throwaway scaffolding
specific to this repo and is removed at Phase 11 cleanup.

After this setup, future `/reload-plugins` invocations pick up
SKILL.md edits without re-installing.

## Driving the bootstrap

Once the plugin is installed, invoke:

```
/livespec-bootstrap:bootstrap
```

The skill reads `bootstrap/STATUS.md`, finds your current phase + sub-step
in the plan, presents the next action, and gates every advancement on
explicit user confirmation. It also handles drift correction — if you
discover that the plan or PROPOSAL.md needs corrections during
execution, the skill walks you through a formal `vNNN/` revision (pre-
Phase-6) or a dogfooded propose-change/revise cycle against
`SPECIFICATION/` (post-Phase-6).

## After bootstrap completes

Phase 11 (cleanup) removes `.claude/plugins/livespec-bootstrap/`,
`.claude-plugin/marketplace.json`, and the repo-root `AGENTS.md`. The
`bootstrap/` and `brainstorming/` directories themselves stay in place
as historical reference. The production app uses its own `/livespec:*`
slash commands and does not reference any of the bootstrap scaffolding.
