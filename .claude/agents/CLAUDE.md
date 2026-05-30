# `.claude/agents/` — custom subagent definitions

Claude Code custom subagent definitions for the livespec family. Each
file is a YAML-frontmatter + Markdown-system-prompt definition that the
Layer 3 orchestrator (`/livespec-orchestrate`) selects via `agentType`
when dispatching mutating work into a family repo.

| File | Agent | Purpose |
|---|---|---|
| `livespec-implementer.md` | `livespec-implementer` | Dispatch executor — self-manages a secondary worktree, does the work, commits per the target repo's rules, opens + arms a PR, reports the PR number. |

Why these exist: the standing dispatch contract (worktree discipline,
the Red-Green-Replay commit ritual, `mise exec -- git`, never
`--no-verify` / `core.bare true`, the PR handoff) lives in the agent
definition ONCE, so per-dispatch briefs shrink to "implement
work-item X in repo Y" plus a one-line binding-rules handoff. This is
the whole point of epic `li-dispatch-agents` — kill the per-dispatch
re-derivation tax.

Design discipline: the agent prompt POINTS AT each repo's canonical
`AGENTS.md` (and the commit-hook reject messages) rather than becoming
a competing source of truth. It carries only the must-not-violate
distillation; AGENTS.md wins on any disagreement.
