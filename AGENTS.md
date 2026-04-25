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
| `bootstrap/` | Throwaway scaffolding driving plan execution (state files + Claude Code skill). |
| `.claude/plugins/livespec-bootstrap/` | Symlink to `bootstrap/.claude-plugin/`; makes the bootstrap skill auto-discoverable to Claude Code. |
| `tmp/` | Empty working directory from earlier passes; deleted by Phase 0. |

## How to make progress

Invoke the bootstrap skill:

```
/livespec-bootstrap:bootstrap
```

It reads `bootstrap/STATUS.md`, finds your current phase + sub-step
in the plan, presents the next action, and gates every advancement on
explicit user confirmation. It also has built-in drift-correction
sub-flows (halt-and-revise for pre-Phase-6 PROPOSAL changes;
propose-change for post-Phase-6 SPECIFICATION changes) so you do not
need to remember the revision procedure manually.

If the slash command is not in your menu, run `/reload-plugins` to
pick up the symlinked plugin. If that does not help, fall back to
plain language: "Follow the skill at
`bootstrap/.claude-plugin/skills/bootstrap/SKILL.md` to drive bootstrap
execution."

After modifying SKILL.md, run `/reload-plugins` to refresh.

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
| Bootstrap skill prose | `bootstrap/.claude-plugin/skills/bootstrap/SKILL.md` |
| Per-version PROPOSAL.md snapshots | `brainstorming/approach-2-nlspec-based/history/vNNN/` |

## After bootstrap completes

Phase 11 (cleanup) of the plan removes:

- This `AGENTS.md` file at repo root
- The `.claude/plugins/livespec-bootstrap/` symlink (and the
  `.claude/plugins/` parent directory if empty)

The `bootstrap/` and `brainstorming/` directories themselves stay in
place as historical reference, but nothing in the production app
(`.claude-plugin/`, `SPECIFICATION/`, `dev-tooling/`, `tests/`,
`pyproject.toml`, `justfile`, `lefthook.yml`, etc.) references them.
