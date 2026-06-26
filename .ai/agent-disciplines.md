# Agent disciplines — cross-cutting quick reference

Progressively-disclosed detail for `AGENTS.md` §"Agent-instruction `.ai/`
convention". Read this when **ending a session** or before applying a
**cross-cutting discipline**. Each discipline's AUTHORITATIVE detail lives in the
named `AGENTS.md` section (or spec section); this file is the at-a-glance index
plus the one rule that has no other home — the session-end standing-handoff print
rule.

## Session-end standing-handoff print rule

When a session advanced a **standing-handoff track** — a `prompts/<name>.md`
that declares itself a refresh-each-session handoff — the session's closing
summary MUST print the exact command that resumes it:

```
run prompts/<name>.md
```

Never leave the next session to rediscover its entry point. This operationalizes
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
- **1Password secret-wrapper** — beads/Dolt/tenant-`mysql` access runs only under
  a recognized `with-<id>-env.sh` wrapper (fleet tenants: `with-livespec-env.sh`);
  secrets are probe-only (`printenv NAME | wc -c`, never echo a value) and never
  committed. Detail: `AGENTS.md` §"Beads runtime prerequisites" and §"Git and
  cross-repo working discipline".
- **No local memory** — durable, non-ephemeral agent guidance routes to
  `AGENTS.md` or a referenced `.ai/<topic>.md`, NEVER to the harness-private
  per-session local-memory store (`~/.claude/projects/<slug>/memory/*.md`), which
  is ephemeral, per-user, and invisible to other agents and runtimes. Detail:
  `SPECIFICATION/contracts.md` §"Fleet agent-instruction core".
