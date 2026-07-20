---
name: overseer
description: >-
  Keep multiple parallel livespec tracks moving via a TWO-PANE model: a
  deterministic top-pane daemon (`overseerd`) that watches every tracked tmux
  session's context %, injects an ESCALATING wrap-up at threshold, and
  atomically restarts a session ONLY once that session declares itself `ready`
  (exit + `claude --dangerously-skip-permissions -n <topic>` + re-kick from
  `plan/<topic>/handoff.md`) — THE CARDINAL RULE: the daemon NEVER restarts a
  session that has not declared itself ready, because only the session knows
  whether it is safe to kill; one that declares nothing is REPORTED as not
  responding and left alone — and this THIN bottom pane, the interactive Claude
  overseer, which starts the daemon, manages the discovery-driven auto-managed
  track list via a JSONL topic↔tmux mapping (`add`/`remove`/`unassign`/`start`),
  and RELAYS the tracks the daemon reports as non-blocking text naming the tmux
  session + pane to go to. NOTIFY, NEVER BLOCK: a question may only be asked by
  the actor that OWNS the decision, so the overseer never raises a blocking
  prompt for a TRACK's decision (answer that in the track's own pane); it prompts
  only for decisions it owns (add/remove/unassign/start, threshold). The list is
  discovered from each watched repo's `plan/` dir; declaration is OUT-OF-BAND on
  the filesystem — ONE `.overseer-state` file valued `ready` / `blocked: <reason>`
  / `winding-down` — never pane text. The daemon never auto-spawns a session for
  an UNASSIGNED plan (first launch is deliberate) and never force-kills any
  session. The overseer does NO track work, never polls tracked sessions on a
  timer, never hand-codes. LOCAL-ONLY to this repo and usable only from it — a
  PERMANENT, human-supervised ALTERNATE to autonomous mode (not a stopgap): not
  part of the plugin, spec, template, or fleet, and not synced.
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

## Requirements — Linux and tmux (a DECLARED requirement, not a soft preference)

The overseer runs on **Linux with tmux**, and that is a deliberate product
decision rather than an unfinished portability story:

- **Linux**, because the session readers parse `/proc/<pid>/…` to join a live
  Claude or Codex process to its tmux pane. **macOS has no `/proc` at all** —
  absent, not merely shaped differently — so there is nothing to read.
- **tmux**, because every acting mechanic (capture, paste, respawn, split)
  shells out to a real tmux.

The host boundary is deliberately **NOT abstracted**: no `psutil`, no per-OS
shims, no terminal-multiplexer abstraction. That option was weighed and rejected
as speculative generality. If you need macOS, that reopens the decision on its
own evidence — it is not smuggled in as a seam.

**How it behaves on an unsupported host.** `overseerd` REFUSES to start and
names exactly which precondition failed, rather than failing several ticks deep
inside whichever reader touched the host first:

```
overseer[SURFACE]: refusing to start: unsupported host — tmux is not on PATH —
every acting mechanic drives a real tmux (the overseer declares Linux + tmux as
a REQUIREMENT and deliberately does not abstract the host boundary)
```

The check runs BEFORE every other startup gate, so an unsupported host is
reported ahead of (say) an ungitignored `tmp/overseer/` — you are never sent to
fix the wrong thing first.

---

## The two-pane model

Two panes in the overseer's own tmux window:

- **TOP pane = the daemon** (`overseerd`, which runs the `supervisor.py` daemon
  logic) — a stdlib Python process that both *acts* and *renders the table*. No
  LLM, no tokens. It gets **2/3 of the window height**, because it is the surface
  that answers "what needs my attention?". Every ~10s it
  discovers plans, joins the JSONL mapping, reads each tracked session's live
  pane + its one state file, injects escalating wrap-ups, restarts the sessions
  that have declared themselves `ready`, reports the ones that have not, and
  reprints the live `Status · Topic · tmux · Ctx% · Repo` table (re-rendered
  from live captures each tick, so it can never freeze on a stale snapshot) —
  followed by the **`NEEDS YOU` block** (below).
- **BOTTOM pane = this interactive Claude overseer** (thin) — starts the daemon,
  takes plain-text commands to manage the track list, and ANSWERS THE
  MAINTAINER'S QUESTIONS from the daemon's log. It does NO track work, and it is
  **NOT a status display** (see "The table is state; the log is history" below).

## The table is state; the log is history — NEVER answer the first from the second

**THE STALENESS RULE (maintainer-declared 2026-07-14): the bottom pane must never
present itself as a live view of what needs attention.** You are an LLM. You print
text ONCE, and from that instant it is a frozen transcript that ages silently while
the fleet moves on. The bottom pane once printed "two tracks want you" and sat there
while both were resolved minutes later — the maintainer read a dead report as current.
This is the *frozen-snapshot* failure the design already fixed **for the top pane**
(re-render every tick, stamp it) and never applied here.

So the two surfaces have strictly separate jobs, and you must not confuse them:

| Question | Surface | Why |
|---|---|---|
| **"What needs attention *right now*?"** | the **top pane's `NEEDS YOU` block** | rebuilt every tick from live captures, so a track the maintainer resolves DISAPPEARS from it; costs no tokens, so it can refresh forever |
| **"What *happened*, and *when*?"** | **`tmp/overseer/daemon.log`** — read it and answer | an append-only event history; the thing an LLM is actually good for |

- **Point the maintainer at the top pane** for current state. Do not re-render the
  table into your transcript "for convenience" — that manufactures a second, decaying
  copy of a surface that is already correct and free.
- **If you DO state anything about current state** (they asked you directly, or you
  ran `list`), you MUST **timestamp it and label it a point-in-time read**, and say the
  top pane is the live one. An unstamped status claim from this pane is the bug.
- **Never** answer "what needs attention?" by tailing the log. The log is *history*:
  it records that a track *entered* a condition, never that it is *still in* it.

**All semantic judgment lives in the tracked session's own LLM**, expressed
out-of-band via its ONE state file; the daemon only pattern-matches deterministic
tmux signals and that file.

> **THE CARDINAL RULE (maintainer-declared 2026-07-14): the daemon NEVER restarts
> a session that has not declared itself `ready`.** A session's own `ready`
> declaration is the SOLE authorization for a restart — the daemon never infers it
> from a timer, from idleness, or from how low the context has fallen. **"Idle +
> settled" is NOT "at a safe stopping point"**: a session can be idle while a
> background build runs, while a sub-agent works, or while it waits on a human in
> another pane. Only the session knows, so only the session may say so. A session
> that declares nothing is **reported to you as not responding and left alone** —
> that is a bug in the SESSION, never a licence for the daemon to guess. (This
> replaced a previously-shipped timer-based force-restart, which was a severe bug.)

The session declares itself by writing ONE line to ONE file
(`<repo>/tmp/overseer/<topic>/.overseer-state`), valued `ready`,
`blocked: <one-line reason>`, or `winding-down` (the "I heard you, wrapping up
now" ACK). See `marker-protocol.md`.

---

## Starting the daemon + adopting sessions (run the bootstrap FIRST)

**The FIRST thing you do when `/overseer` starts is run the bootstrap** — do NOT
hand-craft any tmux command, and do NOT target another session by name. This
script is invoked BY the skill (you, via the Bash tool), never typed by a human at
a terminal: it splits the daemon pane beside the SAME Claude session that ran
`/overseer` and that session resumes in the bottom pane — it does NOT launch
Claude, so running it from a bare shell would leave a bare-shell bottom pane. From
your interactive (BOTTOM) pane — the Claude session where `/overseer` is running —
run:

```bash
.claude/skills/overseer/overseer-start
```

That one command (a self-invokable `uv` script) does everything deterministically:

0. **Verifies it is running under Claude Code** via `$CLAUDECODE` (set in every
   Claude Code Bash-tool shell). If unset it prints a refusal pointing back to
   `/overseer` and exits non-zero WITHOUT splitting — so a stray hand-run from a
   plain terminal fails loudly instead of leaving a daemon pane + bare-shell bottom
   pane. (This is why it is skill-invoked-only; it is not a standalone launcher.)
1. **Detects your own pane** via `$TMUX_PANE`, which this Claude session inherits.
   If `$TMUX_PANE` is unset it prints `not inside a tmux pane` and exits non-zero —
   only then is the session genuinely not in tmux; start it inside a tmux session
   and re-run. (Do NOT improvise a tmux check — this is the ONE authority.)
2. **Splits YOUR OWN window** to create the daemon **TOP pane** running
   `overseerd`, keeping focus on your (bottom) pane. It targets `$TMUX_PANE` only,
   so the daemon pane always lands in *this* window — never in a separate session.
   It is idempotent (tags the pane `overseer-daemon`; re-running won't stack panes).
3. **Adopts existing Claude sessions.** It reads Claude Code's own session
   registry (`~/.claude/sessions/<pid>.json`, which carries each live session's
   display `name` + `cwd`), joins each to its tmux session by PID, and auto-tracks
   any whose `cwd` is inside a fleet repo AND whose `name` is an active plan topic
   — mapping each to the tmux session holding it. The match key is that registry
   `name`, NOT the tmux session name and NOT the `#{pane_title}` terminal title
   (which drifts to a task summary), and NOT a screen-scrape (the old input-box
   border vanished whenever a prompt was up). This also runs **every daemon tick**,
   so a session that was mid-prompt, renamed, or launched later is picked up within
   one interval. Codex sessions aren't in Claude's registry, so they're not adopted
   yet (a known gap).

- The daemon's **stdout is the live table** in the top pane (it clears + re-renders
  each tick). Each data row is **color-coded by status** so the operator scans by hue:
  green = working, yellow = idle / waiting on a human / low on context, red = broken
  (`session-gone` / `not-claude`), default (white/gray) = `unassigned`. (Color is
  TTY-only, so a piped `list` stays plain.) Its **stderr → `tmp/overseer/daemon.log`**
  — the channel this bottom pane reads to relay blocked/danger alerts. `overseer-start`'s
  own progress (pane created, sessions adopted) prints to its stderr as it runs.
- `overseerd` takes one optional argument, **`--warn-percent N`** — the
  daemon-wide default remaining-context % at which the FIRST wrap-up fires
  (default **50**). `overseer-start` accepts the same `--warn-percent N` and
  threads it into the `overseerd` launch command
  (`.claude/skills/overseer/overseerd --warn-percent N 2> tmp/overseer/daemon.log`).
  `N` is an int in `[1, 99]`; a per-track `ctx_threshold` override in the mapping
  still wins over this default. Aside from `--warn-percent`, `overseerd` watches
  the whole fleet with the fixed store/stamp paths and the default loop interval,
  and does not auto-recover dead sessions at startup (surface-only: it never
  auto-spawns; re-launching a mapped-but-dead session is a deliberate `start` —
  below). Path discovery is self-contained, so it works from any cwd.
- **Escalating, spam-proof wrap-ups.** Once a track drops to/below the warn
  threshold the daemon injects the wrap-up ONCE, then once more each time
  remaining crosses a lower 10%-band (40, 30, 20, 10) — each band at most once.
  The message **sharpens** with the band: a SUGGESTION to start wrapping up above
  30% remaining, an insistent "STOP AND WIND DOWN NOW" at 30 / 20 / 10. With the
  old force-restart gone, this escalation is the daemon's ONLY lever. The crossed
  bands + the round timestamp are tracked in a DURABLE sidecar, so a daemon restart
  never re-spams a band already sent; multiple bands crossed in one tick coalesce
  into a single message. Re-warns STOP as soon as the session acknowledges with
  `winding-down` (the daemon never keystrokes into a session that is actively
  wrapping up), and the round resets on a restart so the bands can fire again in
  the next round.

**The watch-set + the list.** The daemon watches every repo named in
`~/.livespec-overseer-repos.json` that has a local checkout with a `plan/` dir,
with no per-run override. The declaration is `{"repos": ["<checkout>", ...]}`,
parsed leniently so `//` comments are allowed beside an entry. For each
watched repo it discovers `plan/*/` (excluding `plan/archive/**`) and shows
**one row per unarchived plan topic** — including plans with **no session**
(status `unassigned`, flagged ready to start). The row's tmux, Ctx%, and
lifecycle status come from the JSONL mapping ⋈ the live pane. Table statuses you
will see:

| Status | Meaning |
|---|---|
| `unassigned` | a discovered plan with no session — startable, never auto-started |
| `idle` | at an empty prompt with nothing for the daemon to do (context unknown, or above threshold but waiting on a human / already declared) |
| `idle-with-context-left` | idle above the wind-down threshold, not waiting on a human, undeclared — sent ONE keep-going nudge; the daemon marks it and clears the mark when it works again |
| `working` | busy — actively generating, or a live background shell under its pane |
| `settling` | the pane is present but not yet a verified idle state; wait |
| `warned` | at/below the warn threshold, wrap-up injected, nothing declared yet |
| `winding-down` | the session ACKed the wrap-up and is wrapping up; re-warns suppressed |
| `danger` | at/below **20%** remaining with **nothing declared** — reported loudly, **never acted on** |
| `restarting` | the session declared `ready`; the daemon is respawning + re-kicking it |
| `blocked:human` | a structured gate on the pane, or a `blocked: <reason>` declaration |
| `session-gone` | the mapped tmux session no longer exists AND no live Claude session for the topic is running |
| `live-outside-tmux` | the mapped tmux session is gone, but a live Claude session for this topic is running in a NON-tmux terminal (e.g. a bare SSH shell) — alive and working, but the daemon cannot capture/inject/respawn it. **Informational, not an alarm** (not in `NEEDS YOU`) |
| `not-claude` | the mapped pane is not a live Claude in that repo — never keystroked |

A `danger` row is a **report, not a decision the daemon will make for you**: the
overseer will not restart an undeclared session, so a `danger` track sits there
until a human acts. See "Your job as the bottom pane" below.

### The `NEEDS YOU` block — the answer to "what needs attention?"

Under the table the daemon prints the rows a human must actually go act on —
`blocked:human`, `danger`, `session-gone`, `not-claude`, and any malformed state file —
each with **labeled coordinates** (`topic: … | tmux: … | repo: …`) and its jump command:

```
NEEDS YOU (1):
  ! topic: autonomous-mode | tmux: livespec-autonomous-mode | repo: livespec — blocked:human — waiting on a cost-gate decision
      jump: tmux switch-client -t livespec-autonomous-mode
```

The coordinates are labeled so the operator never has to guess which unlabeled token is
the plan topic, which is the tmux session to jump to, and which is the repo.

…and, when the fleet is clean, `NEEDS YOU: nothing — every tracked session is healthy.`

`unassigned` rows are deliberately excluded: a discovered plan with no session is
*startable*, not *stuck*, and there are dozens of them — they were burying the handful
of rows that genuinely wanted the operator, which is why this block exists. It refreshes
with the tick, so a resolved track vanishes from it on its own.

### The window-name badge

The daemon also badges the attention count onto its tmux **window name** (`overseer` →
`overseer(2!)`), pinning it with `automatic-rename off`. This is the ONLY overseer
surface visible **without looking at the overseer window** — tmux renders the window name
in the status bar of whatever session the maintainer is attached to, so a track that wants
them is noticed while they are heads-down elsewhere. It clears back to `overseer` when
nothing needs attention (a badge that could not clear would just be one more stale
indicator).

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
  session. The tmux id is derived automatically: the **bare plan topic**, or
  `<repo-slug>-<topic>` (single dash) only when that topic collides across watched
  repos. The handoff and resume line default to the plan's `handoff.md`.
  Replaces any existing row for that `(repo, topic)`.
- **`remove --repo <repo> --topic <topic>`** / **`unassign --repo <repo> --topic
  <topic>`** — drop the mapping row (synonyms). The plan reverts to `unassigned`;
  the tmux session is **never force-killed** — surface-only.
- **`start --repo <repo> --topic <topic>`** — the **SURFACE-ONLY, user-initiated
  launch**: create the tmux session if missing, launch
  `claude --dangerously-skip-permissions -n <topic>` in the repo, paste the resume
  line, and map it. **The daemon NEVER auto-spawns a session for an unassigned
  plan** — the FIRST launch of a plan is a deliberate act (the maintainer, via
  you). An already-tracked session is restarted automatically, but ONLY once it
  declares itself `ready` (the cardinal rule above). Pass
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
- **Watch-set** — always `~/.livespec-overseer-repos.json`. To bring another
  repo under watch, add its checkout path to that file's `repos` array; there is
  no per-run repo override. Declaring a repo that has no session assigned yet is
  the normal case, not an error — that is how an `unassigned` plan becomes
  visible in the first place.

---

## Your job as the bottom pane

1. **Start the daemon** in the top pane (above) and confirm the table renders.
2. **Manage the track list** — take the maintainer's natural-language request
   (`list` / `add` / `remove` / `unassign` / `start`), resolve the repo + topic
   (prompt for whichever is omitted, recommend-first), and run the matching
   subcommand with `--repo` / `--topic`. Adding a plan puts it under the daemon's
   watch; `start` launches a session for it (deliberately, never automatically).
3. **ANSWER FROM THE LOG — as text, never as a blocking prompt.** `tmp/overseer/daemon.log`
   is the daemon's **event history**, and knowing it is a core part of your job: it is how
   you answer "why did that track restart?", "when did X block?", "has the daemon been
   injecting wrap-ups?". Its format:

   ```
   2026-07-14T08:47:32Z overseer: <diagnostic>              # routine daemon bookkeeping
   2026-07-14T08:47:32Z overseer[SURFACE]: <alert>          # something the operator may care about
   ```

   - Every line is **ISO-8601 timestamped** — so you can always answer *when*.
   - `overseer:` lines are diagnostics (adopted a session, auto-linked, voided a stale
     declaration, archive-GC'd a row, restarted a track).
   - `overseer[SURFACE]:` lines are operator alerts. A **track-scoped** one names the plan
     topic, its repo, the tmux **session** and **pane**, and a copy-pasteable
     `tmux switch-client -t <session>` jump command. A **daemon-level** one (failed paste,
     respawn failure, singleton-lock refusal, gitignore refusal) has no track coordinates.
   - Alerts are **EDGE-TRIGGERED**: one line when a track *enters* a condition (or its
     reason changes), **not** one per tick. So a line means "this started happening at
     that time" — it does **NOT** mean the track is still in that state now. To know
     whether it *still* is, read the top pane's `NEEDS YOU` block. (Alerts used to repeat
     every tick, which buried the history under thousands of identical lines *and* invited
     exactly the stale-report bug above.)
   - The log is truncated when the daemon starts, so it covers the current daemon's life.

   Three kinds of track alert concern you:
   - **`blocked:human`** — a tracked session hit a structured gate (permission
     prompt / picker) or declared `blocked: <reason>`. The daemon never keystrokes
     into it and never restarts it.
   - **`danger`** — a track is at/below ~20% context left and has declared
     **nothing**. The daemon **reports it and does nothing else**: it will NOT
     restart a session that has not declared itself ready. Relay it as "this track
     is not responding to the wrap-up protocol; a human must go look at it," with
     its session + pane + jump command. (It is a **defect in that session** — it was
     told, escalatingly, exactly what to write.)
   - **malformed state file** — the session wrote a value that is not one of
     `ready` / `blocked` / `winding-down`. It is treated as **no declaration** and
     reported; relay it the same way.

   **NOTIFY, NEVER BLOCK — this is a hard rule.** A question may only be asked by
   the actor that **OWNS** the decision. A tracked session's decision belongs to
   that session and is **already displayed in its own pane**, so you MUST NOT
   re-ask it here: **never raise `AskUserQuestion` (or any blocking prompt) for a
   track's decision.** Relay it as plain, non-blocking text — with the session,
   pane, and jump command — and let the maintainer answer **in the tracked
   session's own pane**. (This is not a style preference: re-asking created a
   duplicate surface. The maintainer answered in the tracked pane, the overseer's
   modal stayed blocking forever, and the whole console wedged on it — a single
   point of failure.) It self-heals: the daemon re-derives `blocked:human` from the
   live pane each tick, so once the human answers in the tracked pane, the alert
   simply stops.

   Include an explicit recommendation in plain language with each relayed track, and
   **stamp anything you say about current state** (see the staleness rule above).
   Reading this log when re-engaged or when the maintainer checks in is not
   timer-polling — you never poll the tracked sessions themselves, and you never put
   yourself on a timer to re-render a table the top pane already renders for free.
4. **Supervise, don't do.** You manage the list and relay; the daemon does the
   mechanics; each tracked session's own LLM does its track work in its own
   context and declares its state in its one state file.

---

## Maintainer-owned gates — ask ONLY about decisions YOU own

**The ownership test comes first, before any question of style:** a question may
only be asked by the actor that **OWNS** the decision, and you must **never block
on a question you do not own**.

- **You OWN it** → a clickable `AskUserQuestion` is correct: add / remove /
  unassign / start a track, a warn-threshold change, your own exit gate, or an
  irreversible / outward-facing action of YOURS the maintainer has not
  pre-authorized. Nobody else can answer these, so asking is the only way they get
  answered.
- **A TRACK owns it** → **never** `AskUserQuestion`. The tracked session's own
  question is already up in its own pane; relay it as non-blocking text with the
  session, pane, and jump command, and let the maintainer answer it **there**. This
  covers `blocked:human`, a `danger` non-responder, a malformed state file, and any
  decision that belongs to the track's own work (a `groom` cut, a backlog promotion
  or `pending-approval` approval, a `/livespec:*` spec ratification, that track's
  irreversible actions). Re-asking any of these here duplicates a surface that
  already exists — and the duplicate blocks.

Within what you DO own: decide-and-inform beats ask-and-wait for anything
reversible or clearly within established intent — make the call and tell the
maintainer what you did; keep genuine gates to an explicit recommendation, plain
language, ONE clickable picker at a time. And **never freeze the loop on any one
track** — the daemon keeps the other tracks moving regardless; report and let the
rest continue.

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
  session (the bare topic, or `<repo-slug>-<topic>` on a cross-repo collision) is
  gone, relaunch it with a deliberate `start --repo <repo> --topic <topic>` (which
  recreates the tmux session, relaunches `claude -n <topic>`, and pastes the resume
  line). **`--repo` MUST be the full absolute path** (`/data/projects/livespec`),
  never the bare slug — see the restart-learnings note in `AGENTS.md`.
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
- **Maintainer-interaction style — for the decisions YOU own.** One clear,
  CLICKABLE choice at a time (`AskUserQuestion`), plain language, no jargon,
  recommended option first; define every domain term inside the question. Never
  dump a prose wall of decisions — walk the maintainer through them one by one; say
  the plain-language bottom line first, then detail. **For a decision a TRACK owns,
  do not use a picker at all** — relay it as non-blocking text naming the session,
  pane, and jump command (see "Maintainer-owned gates" above).

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
- **`marker-protocol.md`** (beside this file) — the escalating wrap-up + the ONE
  state-file contract: the cardinal rule, what the daemon injects at each band,
  the three values a tracked session may WRITE (`ready` / `blocked: <reason>` /
  `winding-down`), and what the restart interlock validates.

---

## This skill is local-only and permanent

It lives at `.claude/skills/overseer/` in *this* repo and is usable **only from
this repo**. It is **not** part of the livespec plugin, the spec, the copier
template, or any fleet-propagated surface — do not add it to manifests,
conformance checks, or other repos. It is a **permanent, human-supervised
alternate to autonomous mode** (the Beads/Dolt + Fabro Dispatcher), not a stopgap
awaiting replacement: the two coexist as standing peers (see the callout near the
top of this file). Maintain it in place — keep it thin, keep it correct.
