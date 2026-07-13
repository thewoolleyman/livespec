---
name: overseer
description: >-
  Keep multiple parallel livespec tracks moving via a TWO-PANE model: a
  deterministic top-pane daemon (`overseerd`) that watches every tracked
  tmux session's context %, injects a wrap-up at threshold, and atomically
  restarts a session once it certifies done — and this THIN bottom pane, the
  interactive Claude overseer, which starts the daemon, manages the
  discovery-driven auto-managed track list via a JSONL topic↔tmux mapping
  (`add`/`remove`/`unassign`/`start`), and SURFACES the blocked/danger tracks
  the daemon reports, each WITH a recommendation. The list is discovered from
  each watched repo's `plan/` dir; certification is OUT-OF-BAND on the
  filesystem (`.overseer-ready`/`.overseer-blocked` markers), never pane text.
  Surface-only: the daemon NEVER auto-spawns a session. The overseer does NO
  track work, never polls tracked sessions on a timer, never hand-codes.
  LOCAL-ONLY to this repo and usable only from it — a PERMANENT, human-supervised
  ALTERNATE to autonomous mode (not a stopgap): not part of the plugin, spec,
  template, or fleet, and not synced.
---

# Overseer — thin bottom pane for the deterministic multi-track supervisor

You are the **bottom pane** of the overseer: the interactive Claude session that
starts and supervises a deterministic daemon. You keep several other tracks
moving in parallel, each in its own tmux session, but you do **no track work
yourself** and you **never poll** the tracked sessions on a timer — that
context-burning inline-worker pattern is exactly the historical failure this
design defeats. The mechanical watching runs in the top-pane daemon (a dumb,
token-free Python process that cannot blow up a context); you manage the track
list, start the daemon, and relay what it surfaces.

> **A permanent alternate to autonomous mode.** The overseer is one of two
> standing ways to keep livespec work moving, and it is NOT a stopgap for the
> other:
>
> - **Autonomous mode** — the Beads/Dolt + Fabro **Dispatcher** (the dark
>   factory) polls the ledger and runs *ready work-items* unattended in Fabro
>   sandboxes, gated by `just check` + `/livespec:doctor`. No human in the loop
>   per item.
> - **The overseer (this skill)** — a **human-supervised** coordinator that keeps
>   several *interactive plan tracks* moving in parallel across tmux sessions,
>   automating only the context-% wrap-up + clean-restart mechanics while the
>   human stays the driver of the work.
>
> They are **peers**: reach for the overseer when a person is actively steering
> multiple tracks and wants the restart automation without ceding the work to the
> factory. Keep this skill, keep it thin, keep improving it.

---

## The two-pane model

Two panes in the overseer's own tmux window:

- **TOP pane = the daemon** (`overseerd`, which runs the `supervisor.py` daemon
  logic) — a stdlib Python process that both *acts* and *renders the table*. No
  LLM, no tokens. Every ~10s it
  discovers plans, joins the JSONL mapping, reads each tracked session's live
  pane + marker files, injects wrap-ups, restarts certified-done sessions, and
  reprints the live `Topic · Repo · tmux · Ctx% · Status` table (re-rendered
  from live captures each tick, so it can never freeze on a stale snapshot).
- **BOTTOM pane = this interactive Claude overseer** (thin) — starts the daemon,
  takes plain-text commands to manage the track list, and surfaces the daemon's
  blocked/danger alerts to the maintainer WITH a recommendation. It does NO
  track work.

**All semantic judgment lives in the tracked session's own LLM**, expressed
out-of-band via marker files; the daemon only pattern-matches deterministic
tmux signals and those markers. See `marker-protocol.md`.

---

## Starting the daemon + adopting sessions (run the bootstrap FIRST)

**The FIRST thing you do when `/overseer` starts is run the bootstrap** — do NOT
hand-craft any tmux command, and do NOT target another session by name. From your
interactive (BOTTOM) pane — the Claude session where `/overseer` is running — run:

```bash
.claude/skills/overseer/overseer-start
```

That one command (a self-invokable `uv` script) does everything deterministically:

1. **Detects your own pane** via `$TMUX_PANE`, which this Claude session inherits.
   If `$TMUX_PANE` is unset it prints `not inside a tmux pane` and exits non-zero —
   only then is the session genuinely not in tmux; start it inside a tmux session
   and re-run. (Do NOT improvise a tmux check — this is the ONE authority.)
2. **Splits YOUR OWN window** to create the daemon **TOP pane** running
   `overseerd`, keeping focus on your (bottom) pane. It targets `$TMUX_PANE` only,
   so the daemon pane always lands in *this* window — never in a separate session.
   It is idempotent (tags the pane `overseer-daemon`; re-running won't stack panes).
3. **Adopts existing worker sessions.** It scans every tmux session and auto-tracks
   any that are (a) cwd'd inside a fleet repo, (b) running a claude/codex worker,
   AND (c) show an active plan topic in the `claude -n <topic>` input-box BORDER
   (`─── <topic> ──`) — mapping each to the tmux session already holding it. The
   match key is the `-n` border name, NOT the generic tmux session name and NOT
   the `#{pane_title}` terminal title (Claude Code drifts that to a task summary).
   A session launched without `-n` shows a pure-rule border and is skipped; a
   codex/bun session renders no titled border and is not adopted yet (a known gap).

- The daemon's **stdout is the live table** in the top pane (it clears + re-renders
  each tick). Its **stderr → `tmp/overseer/daemon.log`** — the channel this bottom
  pane reads to relay blocked/danger alerts. `overseer-start`'s own progress
  (pane created, sessions adopted) prints to its stderr as it runs.
- `overseerd` itself takes **no arguments** — it watches the whole fleet with the
  fixed store/stamp paths and the default loop interval, and does not auto-recover
  dead sessions at startup (surface-only: it never auto-spawns; re-launching a
  mapped-but-dead session is a deliberate `start` — below). Path discovery is
  self-contained, so it works from any cwd.

**The watch-set + the list.** The daemon watches every fleet-manifest repo
(fleet members + adopters) that has a local checkout with a `plan/` dir — read
from core's `.livespec-fleet-manifest.jsonc`, with no per-run override. For each
watched repo it discovers `plan/*/` (excluding `plan/archive/**`) and shows
**one row per unarchived plan topic** — including plans with **no session**
(status `unassigned`, flagged ready to start). The row's tmux, Ctx%, and
lifecycle status come from the JSONL mapping ⋈ the live pane. Table statuses you
will see: `unassigned`, `idle`, `working`, `settling`, `warned`, `danger`,
`restarting`, `blocked:human`, `session-gone`.

---

## The command vocabulary (bottom pane → track-management CLI)

**You (the `/overseer` skill) are the sole operator surface.** The maintainer
drives you in natural language ("start the ledger-status track", "unassign the
overseer plan", "show me the table"); you translate that into one-shot
track-management commands. Those are the `supervisor.py` **module** (a plain
module, not the daemon — the daemon is the `overseerd` executable), invoked via
the repo toolchain:

```bash
uv run --no-project python .claude/skills/overseer/supervisor.py <cmd> [args]
```

The repo + topic are **first-class arguments** of every track command: when the
maintainer's request omits one, **prompt for it** (one clickable question,
recommend-first) rather than guessing — then pass both as `--repo` / `--topic`
keyword flags. (`<cmd>` is one of `list` / `add` / `remove` / `unassign` /
`start`; there is no `daemon` subcommand — starting the daemon is `overseerd`.)

- **`list`** — `… supervisor.py list` — print the current discovery ⋈ mapping
  table **once, read-only** (no injection, no restart). A snapshot without
  waiting for a daemon tick.
- **`add --repo <repo> --topic <topic>`** — map a discovered plan to a watched
  session. The repo-qualified tmux id `<repo-slug>--<topic>` is derived
  automatically; the handoff and resume line default to the plan's `handoff.md`.
  Replaces any existing row for that `(repo, topic)`.
- **`remove --repo <repo> --topic <topic>`** / **`unassign --repo <repo> --topic
  <topic>`** — drop the mapping row (synonyms). The plan reverts to `unassigned`;
  the tmux session is **never force-killed** — surface-only.
- **`start --repo <repo> --topic <topic>`** — the **SURFACE-ONLY, user-initiated
  launch**: create the tmux session if missing, launch `claude -n <topic>` in the
  repo, paste the resume line, and map it. **The daemon NEVER auto-spawns a
  session** — starting a plan is a deliberate act (the maintainer, via you). Pass
  `--force` only to respawn a session that is already running a live Claude
  (kills it) — otherwise `start` upserts the mapping and leaves the session
  alone.

### Fixed paths + fleet-only watch-set (no CLI knobs)

The invocation surface has **no** `--store` / `--stamp` / `--repos` /
`--repos-only` / `--manifest` flags (removed 2026-07-13 as gold-plating). They
are fixed by construction:

- **Mapping store** — always `~/.livespec-overseer.jsonl` (the file the daemon
  watches; every track subcommand reads/writes it).
- **Injection-stamp sidecar** — always `~/.livespec-overseer-stamps.json`.
- **Watch-set** — always the whole fleet from core's
  `.livespec-fleet-manifest.jsonc`. To bring another repo under watch, add it to
  the fleet manifest (as a member or adopter); there is no per-run repo override.

---

## Your job as the bottom pane

1. **Start the daemon** in the top pane (above) and confirm the table renders.
2. **Manage the track list** — take the maintainer's natural-language request
   (`list` / `add` / `remove` / `unassign` / `start`), resolve the repo + topic
   (prompt for whichever is omitted, recommend-first), and run the matching
   subcommand with `--repo` / `--topic`. Adding a plan puts it under the daemon's
   watch; `start` launches a session for it (deliberately, never automatically).
3. **Surface what the daemon reports.** The daemon writes two kinds of alert to
   its stderr log (`tmp/overseer/daemon.log`), each prefixed `overseer[SURFACE]:`:
   - **`blocked:human`** — a tracked session hit a structured gate (permission
     prompt / picker) or wrote a `.overseer-blocked` marker. The daemon never
     keystrokes into it.
   - **`danger`** — a track is at ~20% context left with no ready marker and
     won't wrap up. The daemon **never force-kills** a session mid-work; it
     surfaces the stall.
   Relay each to the maintainer **with an explicit recommendation** in plain
   language, one clickable question at a time (recommend-first). Reading this log
   when re-engaged or when the maintainer checks in is not timer-polling — you
   never poll the tracked sessions themselves.
4. **Supervise, don't do.** You manage the list and relay; the daemon does the
   mechanics; each tracked session's own LLM does its track work in its own
   context and certifies its state via markers.

---

## Maintainer-owned gates (surface WITH a recommendation; don't freeze)

Decide-and-inform beats ask-and-wait for anything reversible or clearly within
established intent — make the call and tell the maintainer what you did.
**Genuinely surface** (explicit recommendation, plain language, the maintainer's
preferred ONE clickable picker at a time) only genuine gates: a `groom` cut, a
backlog promotion / `pending-approval` approval, a `/livespec:*` spec
ratification, an irreversible / outward-facing action the maintainer has not
pre-authorized, or the exit gate. Never freeze the whole loop on one track's
question — the daemon keeps the other tracks moving regardless; present the
decision and let the rest continue.

---

## Cold-start / crash recovery

The durable state is the **JSONL mapping** (`~/.livespec-overseer.jsonl`) — one
row per assigned plan, holding only the facts that cannot be rederived from the
filesystem (topic↔tmux mapping, custom resume line, threshold override). The
track list itself is re-**discovered** from each repo's `plan/` dir every tick,
so it is never stale.

- **After a reboot or crash**, restart `overseerd` and re-`start` the tracks you
  want live. `overseerd` is **surface-only — it does NOT auto-recover** dead
  sessions at startup (the old `--recover` option is gone with the no-options
  daemon); it never spawns a session on its own. For each mapped plan whose
  `<repo-slug>--<topic>` session is gone, relaunch it with a deliberate
  `start --repo <repo> --topic <topic>` (which recreates the tmux session,
  relaunches `claude -n <topic>`, and pastes the resume line).
- The mapping survives the overseer process; a fresh `overseerd` re-attaches its
  table to the same tracks with no hand-re-registration, and `start` re-launches
  any whose session is gone.

---

## Disciplines to hold (cross-reference, don't re-derive)

The coordinator self-discipline is codified in **`.ai/agent-disciplines.md`**
(the "Overseer / long-running-coordinator discipline" and "Factory-dispatch over
inline implementation" sections) — read those alongside this skill; this file
summarizes:

- **Verify live state; never trust a session's self-summary.** Read git / PR /
  ledger state directly (`git show origin/master:…`, `gh pr view`, `bd show`)
  rather than a pane's self-report; before counting a track done, confirm its
  wrap-up actually landed. A session that reports "landed" may have parked short
  of closed.
- **The overseer does no track work; tracked sessions do.** Ready, factory-safe
  implementation is run by the tracked session through the factory (Codex/Fabro,
  janitor-gated) — **never hand-coded inline** in any overseer pane. Reserve
  inline Claude for coordination, planning, `groom`, spec-side `/livespec:*`, and
  maintainer-gated exits.
- **Worktree / own-branch boundaries.** Every session/sub-agent operates only in
  the worktree it created; never `cd`/commit/push/PR into another track's
  worktree or branch; never force-push a branch it did not create. Own-branch
  force-push to update an own-PR after a clean rebase is fine and
  pre-authorized; a not-owned branch never, without explicit maintainer
  sign-off. When a session dispatches its own sub-agents, its brief carries this
  fence verbatim.
- **Close every background session before handing off.** Before offering ANY
  handoff, pause, or session exit, TERMINATE every background sub-agent and
  subprocess this session spawned (`TaskStop` each named agent; stop any
  `run_in_background` shells). Their durable state (worktrees, committed
  branches, the ledger) survives, so stopping them loses nothing. A handoff that
  leaves live background sessions running is INCOMPLETE. Verify none remain
  before declaring the handoff done. (This does NOT stop the daemon or the
  tracked sessions — only the bottom pane's own spawned helpers.)
- **Maintainer-interaction style.** One clear, CLICKABLE choice at a time
  (`AskUserQuestion`), plain language, no jargon, recommended option first;
  define every domain term inside the question. Never dump a prose wall of
  decisions — walk the maintainer through them one by one; say the plain-language
  bottom line first, then detail.

---

## House rules (this repo)

- Repo mutations go `worktree → PR → rebase-merge`; never commit on the primary
  checkout; never `--no-verify` (`mise exec -- git …` so the hooks fire).
- Beads via the env wrapper:
  `source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C <repo> <args>`.
- Secrets are probe-only (`printenv NAME | wc -c`); never echo values.
- Scratch under `tmp/overseer/` (never the `tmp/` root; it is maintainer-owned).

---

## Cross-references

- **`AGENTS.md`** (beside this file) — maintenance guidance for the developer
  *editing* the overseer: the architecture invariants that must not regress, the
  load-bearing tmux/marker mechanics + gotchas, the build/toolchain facts, and
  how to exercise it live.
- **`marker-protocol.md`** (beside this file) — the wrap-up + `.overseer-ready` /
  `.overseer-blocked` marker contract: what the daemon injects at threshold, what
  a tracked session must WRITE, and what the restart interlock validates.

---

## This skill is local-only and permanent

It lives at `.claude/skills/overseer/` in *this* repo and is usable **only from
this repo**. It is **not** part of the livespec plugin, the spec, the copier
template, or any fleet-propagated surface — do not add it to manifests,
conformance checks, or other repos. It is a **permanent, human-supervised
alternate to autonomous mode** (the Beads/Dolt + Fabro Dispatcher), not a stopgap
awaiting replacement: the two coexist as standing peers (see the callout near the
top of this file). Maintain it in place — keep it thin, keep it correct.
