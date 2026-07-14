# Agent disciplines — cross-cutting quick reference

Progressively-disclosed detail for `AGENTS.md` §"Agent-instruction `.ai/`
convention". Read this when **ending a session** or before applying a
**cross-cutting discipline**. Each discipline's AUTHORITATIVE detail lives in the
named `AGENTS.md` section (or spec section); this file is the at-a-glance index
plus the rules that have no other home — the session-end standing-handoff path
rule and the overseer / long-running-coordinator discipline.

## Session-end standing-handoff path rule

When a session advanced a **standing-handoff track** — a refresh-each-session
handoff, i.e. a plan thread's `plan/<topic>/handoff.md` — the session's closing
recap MUST end by printing the exact handoff path **verbatim, as the LAST line
of the recap** (nothing after it):

```
plan/<topic>/handoff.md
```

Print the path **verbatim and last, every time** — never paraphrased, never
buried mid-summary, never omitted, and never with trailing prose after it. The
path is the runtime-neutral resume anchor: Claude Code, Codex, and a human can
all open the same file, while slash-command or skill-invocation syntax is
runtime-specific. Mention a runtime-specific invocation earlier in the recap
only when it is valid for the current runtime and helpful; never make it the
last-line standing-handoff anchor.

This operationalizes `SPECIFICATION/non-functional-requirements.md` §"Planning
Lane guidance" → "No shadow ledger" ("a session's closing summary names the
exact command that launches the next session") at the agent-instruction layer by
treating the committed handoff file as the portable launch point. If the session
advanced the track materially, also refresh the handoff file itself (and the
ledger state it points at) before printing the handoff path.

## Planning-lane continuation rule

A plan thread's handoff is executable coordination, not a suggestion to stop.
When a resumed handoff names a next action, execute that action automatically
unless the user explicitly asked only for status, review, or analysis. This
includes chaining to another livespec-orchestrator operation such as `groom`,
`capture-work-item`, `propose-change`, or `drive` when the handoff names it.

Do not stop merely because a handoff file was refreshed, validated, committed,
or merged. Keep going until the active operation is genuinely blocked, the
thread closes, the work reaches a handoff-rotation boundary, or the user's
newest message redirects the session. For a planning thread, `groom` stays in
the maintainer-side planning lane and is not factory-dispatched; ready
implementation work that `groom` produces is what routes to the factory.

When the maintainer asks to **land** an instruction, plan artifact, or code
change, "land" means the full repository mutation protocol has completed:
branch work is merged to the owning repository's `master`, the primary checkout
has been fast-forwarded to the merged `origin/master`, temporary worktrees and
branches have been removed, and the primary checkout is verified clean on
`master`. Opening a PR, pushing a branch, or leaving the primary checkout behind
remote `master` is not landed.

## Maintainer-gated actions are prompts, not blockers

When a resumed handoff names a maintainer-gated action, do not treat that state
as blocked or inactive. Treat it as the next actionable step that requires an
explicit maintainer confirmation before execution.

The agent MUST:

1. State the recommended action first.
2. Explain the blast radius in plain language.
3. Provide the exact command or operation that would run.
4. Ask for confirmation before executing.
5. Offer defer/inspect alternatives only after the recommendation.

A final recap must not say "nothing to do" while a maintainer-gated action
remains. The correct state is "ready for maintainer confirmation."

## Overseer / long-running-coordinator discipline

A long-running **manual coordinator** — an overseer session that dispatches and
watches several other sessions (the local `.claude/skills/overseer/SKILL.md`
tool) — degrades unless it actively keeps ITSELF lean. These rules are the
hard-won failures of the manual overseer; hold them whenever one session
coordinates others, overseer skill or not:

- **Rotate the role before ~50% context — don't hoard it to exhaustion.** The
  coordinator role is fully resumable from its durable handoff
  (`plan/<topic>/handoff.md`): refresh that handoff and hand the role to a FRESH
  session, which resumes lean via the handoff path. There is no reason to drive
  a coordinator to 80%+ and autocompact — that is the concrete failure these
  rules exist to prevent.
- **Close every spawned background session before handing off.** Before
  offering a handoff, pause, or session exit, TERMINATE every background
  sub-agent and subprocess this session spawned — `TaskStop` each named agent
  by name, and stop any `run_in_background` shells. Their durable state
  (worktrees, committed branches, the ledger) survives the process being
  stopped, so nothing is lost. A hand-off that leaves live background
  sessions/subprocesses running is INCOMPLETE — it blocks the maintainer from
  exiting the session; verify none remain before declaring the handoff done.
  (Maintainer-declared 2026-07-06, after an overseer paused a track with five
  sub-agents still running and the session could not be exited.)
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
- **Auto-enable-merge opt-out for review-before-merge dispatches.** Every fleet
  impl-plugin repo carries `.github/workflows/auto-enable-merge.yml`, which
  auto-merges (rebase) any non-draft, un-`do-not-merge`-labeled PR authored by
  the maintainer allowlist or the release-please App on a `release-please--`
  branch the moment CI goes green — deliberate, load-bearing autonomy (it keeps
  the release train and factory unattended) and never to be disabled to obtain
  a review gate. When you dispatch a manual implementer PR you intend to review
  BEFORE it merges — e.g. a factory-repair PR the broken factory cannot carry
  itself — the dispatch brief MUST instruct the sub-agent to open the PR as
  DRAFT or apply the `do-not-merge` label; otherwise a green PR merges before
  the overseer can review it (observed 2026-07-05: a fabro-fix PR auto-merged
  pre-review, shipping a regression a follow-up release corrected).

**Why this matters.** The manual overseer is being retired precisely because a
single coordinator's context does not scale across a long multi-track rollout —
so a manual coordinator MUST rotate-and-delegate or it degrades into
ineffectiveness. The same constraint binds any future long-running
multi-session coordination, whatever drives it.

## Tracked-session discipline — the overseer wrap-up contract

This binds YOU when your session is a **track** supervised by the overseer daemon
(`.claude/skills/overseer/`) — i.e. you are running a plan thread and a wrap-up
message is pasted into your pane at a context threshold. It is the other half of
the contract; the daemon's half is `marker-protocol.md`.

- **You are restarted ONLY when YOU declare yourself `ready` — and that is the
  cardinal rule, not a courtesy.** The daemon NEVER restarts a session that has not
  declared itself ready, because a timer cannot know whether you are safe to kill:
  "idle + settled" is not "at a safe stopping point" (you can be idle while a
  background build runs, while a sub-agent works, or while you wait on a human in
  another pane). Only YOU know. When you declare `ready` and stop, the daemon
  respawns your pane into a fresh session and hands it exactly one prompt:
  `read <repo>/plan/<topic>/handoff.md and follow it`.
- **Write exactly ONE of THREE values to ONE file, always.** The file is
  `<repo>/tmp/overseer/<topic>/.overseer-state` (never anything under `plan/`); its
  first line is one of:
  - `winding-down` — the ACK: "I got the wrap-up and am wrapping up now." **Write
    this IMMEDIATELY on receiving the wrap-up, before anything else.** It stops the
    daemon re-warning you while you wrap up.
  - `ready` — "I am at a clean stopping point; restart me." This is the ONLY thing
    that restarts you.
  - `blocked: <one-line reason>` — "I need a human decision I cannot make myself."
    The track is reported to the maintainer (who answers **in your pane**) and is
    never restarted.

  The normal sequence is therefore TWO writes: `winding-down` on arrival, then
  `ready` (or `blocked: …`) when you actually stop. A value that is none of the
  three is treated as **no declaration** and reported as malformed.
- **`plan/<topic>/handoff.md` is the ONLY artifact you hand forward.** Never leave
  your resume state in a scratchpad file, a `/tmp` path, or this transcript — the
  next session inherits NONE of it. If your real pending work has drifted from what
  the handoff says, **REWRITE the handoff**. That file is yours to own; the overseer
  never reads or writes it.
- **Declining to declare does NOT buy you a reprieve — it wedges your own track.**
  You will not be killed; you will be **reported to a human as not responding**, and
  your track will then **sit there** until a person intervenes. That is a chore you
  handed to the maintainer and a defect in YOU: you were told, escalatingly, exactly
  what to write. Declaring is mandatory.
- **Never reason your way out of declaring.** A session once did exactly that: it
  judged the resume line pointed at a stale handoff (because it had stashed its live
  handoff in a scratchpad), refused to write anything, explained itself in prose, and
  stopped — wedging its track idle at 13%. The right move was to rewrite the handoff
  and declare `ready`. If the resume path looks wrong, FIX THE HANDOFF; the state
  file is not the place to register an objection.
- **Stop your background work first.** Terminate every sub-agent and
  `run_in_background` shell you started BEFORE declaring `ready` — their durable
  state (worktrees, branches, the ledger) survives, and a restart with live
  background processes is an incomplete handoff. (A live background shell also reads
  as BUSY to the daemon, so it would not restart you anyway.)

(Maintainer-declared 2026-07-14. The refusal above wedged a live track, and the
first fix — a timer-based force-restart of any stalled idle session — was itself a
severe bug: the daemon cannot know whether an idle session is safe to kill, so it
must never guess. The authorization is yours alone; this discipline is what makes
you exercise it.)

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

## The Fabro factory is a shared concurrency surface — never gate on other runs

The Fabro factory is a **shared, multi-tenant execution surface built to run
many runs at once**. Other, unrelated runs living in it — a run parked idle at
0% CPU, one blocked awaiting a human, another session's `fabro server` /
`livespec-console-beads-fabro serve` cockpit, a tmux session driving the
orchestrator — are its NORMAL operating state, NOT a conflict. Their presence
MUST NOT stop, pause, or gate your own dispatch, golden-master, or accept: just
proceed and run yours alongside them. The host is provisioned for it (18 cores,
94 GiB RAM) and Fabro multiplexes runs by design (e.g. the golden-master already
falls back to `HOST_PUBLISH_PORT` so its in-container `fabro` never contends with
a host `fabro` server holding the same port).

**Do not conflate this with the anti-clobber git discipline — they are different
axes:**

- **Persistent shared STATE is protected.** Never force-push or rewrite another
  session's branch, reap its worktree during an active dispatch, or edit the
  tracked files it is mid-commit on. (`AGENTS.md` §"Git and cross-repo working
  discipline".)
- **The factory's shared COMPUTE is meant to be shared.** The fabro server, the
  docker daemon, the sandbox images, host CPU/RAM — running your own independent
  run on them touches no other session's persistent state, so it needs no
  deference and no permission.

The handoff caveat "re-check for a LIVE dispatch before editing that repo"
belongs to the STATE axis: it guards against conflicting file edits/commits in a
repo, NOT against launching an independent run in the factory. A self-contained
dispatch / golden-master / accept edits no tracked files and is always safe to
run concurrently.

**And never re-ask an already-authorized action on account of factory
occupancy.** Once the maintainer has picked or authorized an action, discovering
that something unrelated is also running is not new information that warrants a
second confirmation — proceed. Surface a factory observation only when it is a
genuine resource-exhaustion breach (the resource health check's job), never
merely "another run is present."

(Maintainer-declared 2026-07-14, after a session refused to run an
already-authorized local golden-master because an unrelated, idle, human-blocked
`livespec-dev-tooling` run was parked in the factory — and re-asked a question
the maintainer had already answered.)

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
- **Tracked-session wrap-up contract (overseer)** — if the overseer daemon pastes
  a wrap-up into your pane, you are restarted ONLY when you declare yourself
  `ready`; the daemon never restarts an undeclared session (only you know whether
  you are safe to kill). ACK immediately with `winding-down`, then write exactly one
  of `ready` / `blocked: <reason>` / `winding-down` to the ONE state file
  `<repo>/tmp/overseer/<topic>/.overseer-state`. `plan/<topic>/handoff.md` is the
  ONLY artifact the fresh session inherits (never a scratchpad) — if the resume path
  looks stale, REWRITE the handoff; never withhold the declaration to register an
  objection. Declaring nothing does not kill you and does not save you: it gets you
  reported to a human as not responding and wedges your own track. Detail: this file
  §"Tracked-session discipline — the overseer wrap-up contract" and
  `.claude/skills/overseer/marker-protocol.md`.
- **Factory-dispatch over inline implementation** — ready, factory-safe impl
  work-items are dispatched via `/livespec-orchestrator-beads-fabro:orchestrate`
  (Codex/Fabro sandbox), never hand-coded inline in Claude; inline Claude is for
  planning / `groom` / spec-side / maintainer-gated exits only. Better code AND
  spares Claude quota. Detail: this file §"Factory-dispatch over inline
  implementation".
- **The Fabro factory is a shared concurrency surface** — other unrelated runs in
  the factory (even idle or human-blocked ones, another session's `fabro server`
  or console cockpit) are its normal state and MUST NOT gate your own
  dispatch/golden-master/accept; that is a different axis from the anti-clobber
  rule, which protects persistent shared state (branches, worktrees, files), not
  multiplexed factory compute. Never re-ask an already-authorized action because
  unrelated work is running. Detail: this file §"The Fabro factory is a shared
  concurrency surface — never gate on other runs".
