# Agent disciplines — cross-cutting quick reference

Progressively-disclosed detail for `AGENTS.md` §"Agent-instruction `.ai/`
convention". Read this when **ending a session** or before applying a
**cross-cutting discipline**. Each discipline's AUTHORITATIVE detail lives in the
named `AGENTS.md` section; this file is the at-a-glance index plus the one rule
that has no other home — the session-end plan resume rule.

## Session-end plan resume rule

When a session advanced a **plan** — a Planning Lane record whose
`plan/<slug>/epic.md` is the write-once anchor for ledger epic identity — the
session's closing recap MUST end by printing the exact resume command
**verbatim, as the LAST line of the recap** (nothing after it):

```
/livespec-orchestrator-beads-fabro:plan <topic>
```

Print it **verbatim and last, every time** — never paraphrased, never buried
mid-summary, never omitted, and never with trailing prose after it. Never leave
the next session to rediscover its entry point. This operationalizes
`SPECIFICATION/non-functional-requirements.md` §"Planning Lane guidance" at the
agent-instruction layer: mutable supervisor state and handoff entries are
append-only, attributed ledger entries, while research evidence in git is
preserved as write-once plan material. If the session advanced the plan
materially, append the needed ledger entry before printing the resume command;
do not create or refresh a live `plan/<slug>/handoff.md`.

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
