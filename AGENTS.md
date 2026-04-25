# Repo orientation for AI sessions

This repo is **livespec** — a Claude Code plugin for governing a
living natural-language specification — currently in **bootstrap
mode**. Read this file in any fresh session before doing work; it
tells you where to start and what NOT to do.

## Status: bootstrapping

The repo is being bootstrapped into a working livespec plugin via the
plan at
[`brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`](brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md).
Until bootstrap completes, the production layout — `.claude-plugin/`,
`SPECIFICATION/`, `dev-tooling/`, `tests/`, `pyproject.toml`,
`justfile`, etc. — does NOT exist. The repo currently contains:

| Directory / file | Purpose |
|---|---|
| `brainstorming/` | Frozen design and process artifacts (PROPOSAL.md v022, the bootstrap plan, companion docs, version history). |
| `prior-art/` | External-source reference material with permalinks. |
| `bootstrap/` | Throwaway scaffolding state files (`STATUS.md`, `open-issues.md`, `decisions.md`, `AGENTS.md`). |
| `.claude-plugin/marketplace.json` | Repo-root marketplace manifest declaring the `livespec-bootstrap` plugin. Auto-discovered by Claude Code. |
| `.claude/plugins/livespec-bootstrap/` | The bootstrap plugin contents (`.claude-plugin/plugin.json` + `skills/bootstrap/SKILL.md`). |
| `tmp/` | Empty working directory from earlier passes; deleted by Phase 0. |

## How to make progress

### One-time setup per machine (~30 seconds)

Claude Code does not auto-register a local marketplace from a
committed `marketplace.json`; it has to be added explicitly. Run
these four commands once per machine:

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

### Then invoke the bootstrap skill

```
/livespec-bootstrap:bootstrap
```

It reads `bootstrap/STATUS.md`, finds your current phase + sub-step
in the plan, presents the next action, and gates every advancement on
explicit user confirmation. It also has built-in drift-correction
sub-flows (halt-and-revise for pre-Phase-6 PROPOSAL changes;
propose-change for post-Phase-6 SPECIFICATION changes) so you do not
need to remember the revision procedure manually.

After modifying SKILL.md, run `/reload-plugins` to refresh without
restarting the session.

### Fallback if plugin discovery is still failing

If `/livespec-bootstrap:bootstrap` is not in your menu after the
one-time setup above, fall back to plain language: "Follow the
skill at `.claude/plugins/livespec-bootstrap/skills/bootstrap/SKILL.md`
to drive bootstrap execution." The skill prose is self-contained
and will work without slash-command discovery.

## Hard rules during bootstrap

- **Do NOT execute phase work ad-hoc.** Route every sub-step through
  the bootstrap skill so progress, decisions, and discovered drift
  land in the persistent log files (`bootstrap/STATUS.md`,
  `bootstrap/open-issues.md`, `bootstrap/decisions.md`).
- **Do NOT hand-edit files under `brainstorming/` after Phase 0.**
  Plan §3's cutover principle binds. If you discover drift, route
  through the skill's "Report an issue first" gate; the
  halt-and-revise sub-flow handles formal `vNNN` revisions properly.
- **Do NOT hand-edit the bootstrap state files.** The skill is the
  only writer for `STATUS.md`, `open-issues.md`, and `decisions.md`.
  Manual edits get overwritten on the next invocation.

## Where to find things

| You want | Location |
|---|---|
| The plan being executed | `brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` |
| The frozen specification design | `brainstorming/approach-2-nlspec-based/PROPOSAL.md` (v022) |
| Python style discipline | `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md` |
| Outstanding deferred items | `brainstorming/approach-2-nlspec-based/deferred-items.md` |
| NLSpec discipline rubric | `brainstorming/approach-2-nlspec-based/livespec-nlspec-spec.md` |
| Goals / non-goals | `brainstorming/approach-2-nlspec-based/goals-and-non-goals.md` |
| Current bootstrap status | `bootstrap/STATUS.md` |
| Open drift logged across sessions | `bootstrap/open-issues.md` |
| Executor judgment-call log | `bootstrap/decisions.md` |
| Bootstrap skill prose | `.claude/plugins/livespec-bootstrap/skills/bootstrap/SKILL.md` |
| Per-version PROPOSAL.md snapshots | `brainstorming/approach-2-nlspec-based/history/vNNN/` |

## After bootstrap completes

Phase 11 (cleanup) of the plan removes:

- This `AGENTS.md` file at repo root
- The `.claude/plugins/livespec-bootstrap/` directory (and the
  `.claude/plugins/` parent if empty)
- The `.claude-plugin/marketplace.json` file

The `bootstrap/` and `brainstorming/` directories themselves stay in
place as historical reference, but nothing in the production app
(`.claude-plugin/`, `SPECIFICATION/`, `dev-tooling/`, `tests/`,
`pyproject.toml`, `justfile`, `lefthook.yml`, etc.) references them.

After Phase 11, optionally run
`/plugin uninstall livespec-bootstrap@livespec-marketplace` in
Claude Code to remove the locally-installed plugin state too (not
strictly required, since the marketplace registration is gone).
