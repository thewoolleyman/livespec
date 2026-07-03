# Agent disciplines — cross-cutting quick reference

Progressively-disclosed detail for `AGENTS.md` §"Agent-instruction `.ai/`
convention". Read this when **ending a session** or before applying a
**cross-cutting discipline**. Each discipline's AUTHORITATIVE detail lives in the
named `AGENTS.md` section; this file is the at-a-glance index plus the one rule
that has no other home — the session-end standing-handoff print rule.

## Session-end standing-handoff print rule

When a session advanced a **standing-handoff track** — a refresh-each-session
handoff, i.e. a plan thread's `plan/<topic>/handoff.md` — the session's closing
recap MUST end by printing the exact resume command **verbatim, as the LAST
line of the recap** (nothing after it):

```
/livespec-orchestrator-beads-fabro:plan <topic>
```

Print it **verbatim and last, every time** — never paraphrased, never buried
mid-summary, never omitted, and never with trailing prose after it. Never leave
the next session to rediscover its entry point. This operationalizes
`SPECIFICATION/non-functional-requirements.md` §"Planning Lane guidance" → "No
shadow ledger" ("a session's closing summary names the exact command that
launches the next session") at the agent-instruction layer. If the session
advanced the track materially, also refresh the handoff file itself (and the
ledger state it points at) before printing the resume command.

## Cross-cutting disciplines index

Each entry names the discipline and points at its authoritative detail — read the
named section before acting; do not rely on this summary alone.

- **TDD red-green-replay** — every product `.py` change rides a two-step
  single-commit ritual (Red stages the test alone and must fail; Green amends the
  impl and must pass). Docs/spec/config changesets are exempt and use
  `chore(...)`/`docs(...)` subjects. Detail: `AGENTS.md` §"Red-Green-Replay commit
  protocol".
- **Worktree → PR → merge → cleanup** — every tracked-file change happens in a
  dedicated `~/.worktrees/<repo>/<branch>` worktree, never on the primary
  checkout; merge through a PR with the repo's rebase-merge discipline, then
  remove the worktree and refresh the primary. Detail: `AGENTS.md` §"Repository
  mutation protocol".
- **Hooks are load-bearing; never `--no-verify`** — use `mise exec -- git …` so
  the lefthook/commit-refuse hooks fire; on a hook failure, fix the cause or halt
  and surface it — never bypass. Detail: `AGENTS.md` §"Repository mutation
  protocol".
- **No local memory** — durable, non-ephemeral agent guidance routes to
  `AGENTS.md` or a referenced `.ai/<topic>.md`, NEVER to the harness-private
  per-session local-memory store (`~/.claude/projects/<slug>/memory/*.md`), which
  is ephemeral, per-user, and invisible to other agents and runtimes. Detail:
  `AGENTS.md` §"Agent-instruction `.ai/` convention".
