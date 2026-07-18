# Prevention design — mechanical, multi-level

Goal: make it structurally impossible (not merely forbidden) for a
dispatched agent to destroy the maintainer's live tmux fleet, and make
any residual destruction cheap to recover from. Incident basis:
`incident-2026-07-18.md`. Design principle: **defense in depth, with
the deepest level removing the shared resource rather than guarding
it** — each level works even if every level above it fails.

The levels, deepest first:

## L1 — Exposure inversion: agents never see the maintainer's socket

The root enabler is that every dispatched agent shares the
maintainer's default tmux socket namespace (`/tmp/tmux-1000/`), so a
"clean up tmux" impulse anywhere lands on the fleet server. Invert it:

- **Overseer-spawned sessions and dispatched-agent environments export
  `TMUX_TMPDIR=<agent-scoped dir>`** (e.g. `/tmp/tmux-agents-1000/` or
  a per-dispatch scratch dir), set where panes/sandboxes are created
  (the overseer's spawn path in `livespec` `.claude/skills/overseer/`,
  and the Fabro sandbox env in `livespec-orchestrator-beads-fabro`).
  With that env in place, even a bare `tmux kill-server` from an agent
  resolves to an agent-scoped server — worst case it kills other
  agents' scratch servers, never the fleet.
- Note the b3 kill used `TMUX_TMPDIR=/tmp` explicitly, which would
  pierce this level — that's what L2 is for. L1 converts the common
  accidental case into a no-op.
- Repos: `livespec` (overseer spawn), `livespec-orchestrator-beads-fabro`
  (dispatcher/sandbox env).

## L2 — Command guard: a hook that refuses fleet-killing tmux commands

A PreToolUse (Bash) hook that DENIES, with an explanatory message, any
agent command matching the hazard class:

- `tmux … kill-server` without an explicit `-L <name>`/`-S <path>`
  scoping to a non-default socket;
- `TMUX_TMPDIR=` assignments resolving to the default namespace
  (`/tmp` or `/tmp/tmux-<uid>`) combined with a tmux invocation;
- `pkill/killall` targeting `tmux`.

The deny message tells the agent the safe alternative (private `-L`
socket) so the work continues instead of stalling. Placement:

- **Immediate, host-local**: the maintainer's user-scope hooks
  (`~/.claude/settings.json`) so every Claude session on the host is
  covered today, regardless of repo.
- **Durable, fleet-distributed**: the Driver plugins' bundled hooks —
  `livespec-driver-claude` (Claude runtime) and the equivalent guard
  for `livespec-driver-codex` (Codex runtime), since Codex agents run
  on the same host and socket namespace.
- The hook must NOT block scoped scratch usage (`tmux -L lc_e2e_…
  kill-server` is fine) — the guard denies default-socket destruction,
  not tmux use.

## L3 — Harness socket-scoping + structural check (console repo)

- Fix `livespec-console-beads-fabro/crates/console-cli/tests/support/mod.rs`
  so every tmux invocation passes a private socket (`-L
  lc_e2e_<pid>-<nonce>`, or `TMUX_TMPDIR=<per-run scratch>`): launch
  paths at 139–152 / 419–434, cleanup at 137/251/417, `resolve_tmux()`
  at 264–291. CI's container isolation stays as belt-and-braces, but
  host runs become safe.
- Add a repo check (the console repo's enforcement suite) failing any
  test/harness code that invokes tmux without socket scoping, so the
  property is enforced, not remembered.

## L4 — Recovery resilience: a kill costs a minute, not hours

Today recovery is the maintainer noticing and manually retyping the
fleet from shell history (16:49 kill → 19:18 rebuild). Make the fleet
self-healing:

- A systemd **user** unit (host-local, `~/.config/systemd/user/`) that
  keeps the overseer tmux session alive (`tmux new -A -D -s
  livespec-overseer` with `Restart=on-failure`), so a killed server
  re-establishes the anchor session immediately.
- The overseer already persists the topic↔tmux mapping
  (`~/.livespec-overseer.jsonl`); a `recreate-fleet` step (overseer
  daemon or a small script the unit invokes) can relaunch tracked
  sessions from it.
- The investigation's live instrumentation (`tmux-death-canary`
  systemd user unit + `tmux-sigtrace` bpftrace unit, files under
  `tmp/tmux-death-investigation/`) stays armed until L1+L2 land, then
  stands down.

## L5 — Instruction propagation (supplementary prose)

Prose failed alone, but it still shapes agent behavior before a hook
has to fire:

- Promote the `vps-info/AGENTS.md:654` prohibition into the
  dispatch-brief boilerplate (the overseer/dispatcher brief templates)
  so every dispatched subagent carries it verbatim: never touch the
  default tmux socket; always create scratch servers with `-L`; never
  `kill-server` without `-L`/`-S`.
- Add the same rule to the AGENTS.md of the repos whose agents drive
  tmux (`livespec`, `livespec-console-beads-fabro`).

## Explicitly out of scope for this thread

- The tmux 3.5a `clients_calculate_size` NULL-deref upstream report
  (separate small item; harness workaround: avoid `window-size manual`
  on detached scratch servers).
- The ~14:00 load-saturation stall (separate investigation if it
  recurs).
- Swap addition (memory was not a factor in these kills).

## Sequencing

L2-host (user-scope hook, minutes of work, covers everything today) →
L3 harness fix + check → L1 env inversion (overseer + dispatcher) →
L4 resilience unit → L2-driver durable hooks → L5 prose propagation.
The thread's epic tracks one child work-item per level per repo.
