# Agent disciplines — cross-cutting quick reference

Progressively-disclosed detail for `AGENTS.md` §"Agent-instruction `.ai/`
convention". Read this when **ending a session** or before applying a
**cross-cutting discipline**. Each discipline's AUTHORITATIVE detail lives in the
named `AGENTS.md` section (or spec section); this file is the at-a-glance index
plus the rules that have no other home — the session-end standing-handoff print
rule and the overseer / long-running-coordinator discipline.

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

## Overseer / long-running-coordinator discipline

A long-running **manual coordinator** — an overseer session that dispatches and
watches several other sessions (the local `.claude/skills/overseer/SKILL.md`
tool) — degrades unless it actively keeps ITSELF lean. These rules are the
hard-won failures of the manual overseer; hold them whenever one session
coordinates others, overseer skill or not:

- **Rotate the role before ~50% context — don't hoard it to exhaustion.** The
  coordinator role is fully resumable from its durable handoff
  (`plan/<topic>/handoff.md`): refresh that handoff and hand the role to a FRESH
  session, which resumes lean via the resume command. There is no reason to drive
  a coordinator to 80%+ and autocompact — that is the concrete failure these
  rules exist to prevent.
- **Never park ready work behind a "my context is heavy" rationale.** Track work
  runs in each tracked session's OWN context; kicking or re-engaging a track
  costs the coordinator only ~3 cheap `tmux` calls. The coordinator's context
  budget is IRRELEVANT to whether ready work should move. Keep every ready track
  moving, re-engage at boundaries, and surface only real blockers.
- **Keep the coordinator lean by construction.** Capture session panes with
  `tail` (`tmux capture-pane -p | tail -30`), never full dumps. Delegate heavy
  authoring, migrations, and handoff-file writes to sub-agents — their context,
  not the coordinator's. Keep status updates terse: a one-line tick per routine
  event, full detail only at milestones and blockers.

**Why this matters.** The manual overseer is being retired precisely because a
single coordinator's context does not scale across a long multi-track rollout —
so a manual coordinator MUST rotate-and-delegate or it degrades into
ineffectiveness. The same constraint binds any future long-running
multi-session coordination, whatever drives it.

## Factory-dispatch over inline implementation

The fleet is built around a **dark factory**: ready, factory-safe implementation
work-items are dispatched through `/livespec-orchestrator-beads-fabro:orchestrate`
(`run --action impl:<work-item-id>`), which runs the Red→Green build factory-side
in a **Codex/Fabro sandbox**, gated by the janitor (`just check` +
`/livespec:doctor`). **Do NOT hand-code ready implementation inline in a Claude
session** — that is the inline-overseer anti-pattern this fleet is actively
deleting (the work-item-lifecycle epic's exit gate removes the local overseer
skill for exactly this reason). Dispatching is not just cleaner: it produces
better code AND spends **Codex** quota instead of **Claude** quota.

Holds for **ad-hoc work AND anything routed via the `plan` skill**:

- **Ad-hoc / freeform impl** (a bug, refactor, or tactical task you would
  otherwise start coding) → file it as a work-item and dispatch via
  `orchestrate`; do not open an editor and hand-write it.
- **`plan`-routed impl** — when a planning thread matures a piece into ledger
  work, that work is **factory-dispatched**; the planning session itself never
  hand-codes the implementation.
- **Trust `orchestrate`** — it owns the Dispatcher/Fabro mechanics. Never invoke
  Fabro directly or pre-inspect `.fabro/`; if a repo or item is not factory-safe,
  `orchestrate` says so.

**Stays in Claude (NOT factory-dispatched):** the planning thread itself,
`groom` (the maintainer-owned cut), spec-side `/livespec:*` lifecycle, host-only
self-machinery, and maintainer-gated exits. Everything that is ready,
factory-safe *implementation* goes through the factory. Authoritative detail:
the orchestrator's `SPECIFICATION/contracts.md` §"Dispatcher admission, WIP cap,
and post-merge acceptance" and its `prose/plan.md` routing.

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
- **Overseer / long-running-coordinator self-discipline** — a manual coordinator
  that dispatches and watches other sessions MUST rotate its own role before
  ~50% context, never park ready work behind its own context budget, and stay
  lean by `tail`-capturing panes and delegating heavy authoring to sub-agents.
  Detail: this file §"Overseer / long-running-coordinator discipline" and the
  local `.claude/skills/overseer/SKILL.md`.
- **Factory-dispatch over inline implementation** — ready, factory-safe impl
  work-items are dispatched via `/livespec-orchestrator-beads-fabro:orchestrate`
  (Codex/Fabro sandbox), never hand-coded inline in Claude; inline Claude is for
  planning / `groom` / spec-side / maintainer-gated exits only. Better code AND
  spares Claude quota. Detail: this file §"Factory-dispatch over inline
  implementation".
