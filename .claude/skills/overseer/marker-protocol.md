# Overseer wrap-up + state-declaration protocol

This is the contract between the overseer **daemon** (`supervisor.py`, the top
pane) and a **tracked session** (a Claude Code session running a plan thread in
some repo). It defines the wrap-up message the daemon injects at a context
threshold and the ONE **out-of-band state file** a tracked session writes to
declare what it wants done with it. `supervisor.py`'s `wrapup_message()` (built
from `_WRAPUP_SUGGEST_HEAD` / `_WRAPUP_INSIST_HEAD` / `_WRAPUP_BODY`) and
`signals.py`'s `read_state()` / `valid_token()` / `ready_valid()` are the
authoritative implementations; this doc is the single conceptual source they
share, and the reference a tracked session's own `handoff.md` points at.

(The file is still named `marker-protocol.md` for its existing cross-references.
There is no longer a *marker* — a file whose mere presence is the signal. There
is one **state file** carrying one of three **values**; see "Why ONE file with a
value" below.)

## THE CARDINAL RULE — the daemon never restarts a session that has not declared itself ready

**A tracked session is restarted ONLY when it declares `ready`.** That
declaration is the sole authorization. The daemon never infers readiness — not
from idleness, not from a timer, not from how low the context has fallen.

The reason is not politeness, it is correctness: **a timer cannot know whether a
session is safe to kill.** "Idle + settled" is NOT "at a safe stopping point" — a
session can be idle while a background build runs, while a sub-agent works, or
while it waits on a human in another pane. Only the session knows, so only the
session may say so.

A session that declares **nothing** is **reported to the human as not
responding** and is otherwise **left alone**. That is a bug in the SESSION (it
was told, escalatingly, exactly what to write) — never a licence for the daemon
to guess on its behalf.

This REPLACES the previously-shipped timer-based **force-restart** of an idle
stalled session, which was a severe bug: it killed sessions the daemon had no way
to prove were safe to kill. It is gone from the code (there is no
`_STALL_RESTART_GRACE`, no `danger_idle_since`, no force path in `evaluate`).
Maintainer-declared 2026-07-14.

The restart **mechanics** are unchanged (see "The restart mechanics" below); only
the **trigger** changed: it is now solely the session's own `ready` declaration.

## Why a file, not printed text

A pane's text stream **cannot** carry a trustworthy "the session asserts X now"
signal. The injected instruction is echoed back into the transcript, the model
quotes tokens while narrating, output scrolls above the visible capture, and
long lines wrap — any of which turns a printed sentinel into a **false match**
(adversarial review, 2026-07-12, blockers #1–#4). So the declaration is
**out-of-band, on the filesystem**: a file write cannot be forged by
prompt-echo, cannot scroll off, and cannot line-wrap. Pane scraping is retained
ONLY for the busy / idle / gate signals, where a false positive is safe (it
merely suppresses action). See the "The certification protocol" section of
`design.md`.

## Why ONE file with a value, not two presence-markers

The protocol used to be two files — `.overseer-ready` and `.overseer-blocked` —
whose **presence** was the whole signal. Both are GONE. Two files carried a
built-in ambiguity: nothing stopped **both** existing at once, and which one won
was incidental rather than designed. One file with a **value** makes that state
unrepresentable — a file holds exactly one first line, so a session declares
exactly one thing.

A **malformed** value (a typo, an invented token) is **surfaced** to the operator
and treated as **no declaration at all** — fail-closed, so a typo can never
restart anything (`signals.valid_token`; the row `note` reads
`BAD state file: '<token>'`).

## The overseer NEVER touches `plan/`

The overseer touches only its **config** (the mapping store, the injection-stamp
sidecar, the fleet manifest) and **temp files** (`<repo>/tmp/overseer/<topic>/`).
It NEVER reads, writes, or hashes anything under a session's `plan/<topic>/` tree
— the handoff and all plan-thread files are the **session's own workflow**. The
overseer enumerates `plan/*/` DIRECTORIES to discover tracks and *points* a
resume line at the conventional `plan/<topic>/handoff.md`, but it never opens it.
Because the state file lives under `tmp/` (gitignored), the overseer never
dirties a tracked tree; the daemon `git check-ignore`-validates each watched
repo's `tmp/overseer/` at startup and refuses to run if any is not ignored.

## What the daemon injects at threshold — an ESCALATING wrap-up

When a tracked session's **remaining context** falls to or below its threshold
(`ctx_threshold`, default 50%) AND the pane is in a verified idle-input state,
the daemon records an **injection stamp** (an epoch-seconds timestamp in the
sidecar `~/.livespec-overseer-stamps.json`, keyed by `(repo, topic)`) and then
**bracketed-pastes** the wrap-up message.

It fires **once per 10%-band** — the threshold itself, then each lower band
(40 / 30 / 20 / 10) — and each band fires **at most once per round**, durably
(the notified-band set lives in the same sidecar, so a daemon restart never
re-spams a band it already sent). With the force-restart gone, **this escalation
is the only lever the daemon has**, so it must actually sharpen: the message is a
**suggestion** above `_INSIST_AT` (30% remaining) and an **insistent shut-down
demand** at 30 / 20 / 10.

The **suggestion** head (remaining > 30%):

```
You are down to {n}% of your context. Please start wrapping up for a clean session
restart — do it now, while you still have room to do it properly.
```

The **insistent** head (remaining ≤ 30%):

```
STOP AND WIND DOWN NOW. You have only {n}% of your context left. Finish what is in
flight, do not start anything new, and shut down — you are close to the point where
you can no longer hand off cleanly.
```

Both are followed by the same body:

```
You WILL be restarted — but ONLY when YOU say so. The overseer never kills a session
that has not declared itself ready. When you stop, this pane is respawned into a fresh
session handed exactly ONE prompt:
    read {handoff} and follow it
So {handoff} is the ONLY thing the next session inherits. Do NOT leave your resume state
anywhere else (a scratchpad file, this transcript) — it will be LOST. If your real
pending work has drifted from what that file says, REWRITE that file.

Declare your state by writing ONE line to the single state file
{state_file} — one of exactly these three values:

    winding-down                  I got this message and am wrapping up now.
    ready                         I am at a clean stopping point — restart me.
    blocked: <one-line reason>    I need a human decision I cannot make myself.

ACKNOWLEDGE FIRST, right now, before anything else:
    mkdir -p {marker_dir} && echo winding-down > {state_file}

Then:
 1. Bring your OWN work to a clean, resumable stopping point, and UPDATE {handoff} to
    match. Your session owns its handoff and everything under plan/; the overseer never
    reads or writes those.
 2. Stop every background sub-agent and subprocess you started.
 3. Declare done, and stop:
        echo ready > {state_file}

`ready` is the ONLY thing that restarts you. If you write nothing at all, you are NOT
restarted and NOT killed — you are reported to the human as not responding, and your
track sits there until a person intervenes. Do not do that to them: write the file.
```

`{n}` is the session's CURRENT remaining-context percent (re-filled on every
re-warn, so each escalation reflects the live value); `{marker_dir}` is
`<repo>/tmp/overseer/<topic>/`; `{state_file}` is that directory's
`.overseer-state`; `{handoff}` is `<repo>/plan/<topic>/handoff.md`. The exact
strings live in `supervisor.py`'s `_WRAPUP_SUGGEST_HEAD` / `_WRAPUP_INSIST_HEAD`
/ `_WRAPUP_BODY`; keep this block and those constants in sync if either changes.

**Why the message names the handoff and says the restart needs the session's own
word.** A tracked session once refused to declare anything: its real pending work
had drifted away from what `plan/<topic>/handoff.md` said (it had stashed the
live handoff in a scratchpad file), so it reasoned that declaring done would
resume the next session from a stale document — and it stopped, undeclared,
wedging its track idle at 13%. So the message now says plainly that the handoff
is the ONLY artifact it can hand forward, and that the correct response to drift
is to **rewrite the handoff**, never to withhold the declaration. It also states
the other half honestly — no `ready`, no restart — because that is now true, and
a session that is told an untruth ("you will be restarted regardless") will
reason its way around it. Naming the handoff path is still POINTING at it,
exactly as the resume line does; the overseer never opens it.

## What a tracked session must WRITE

ONE file — `<repo>/tmp/overseer/<topic>/.overseer-state` (the repo's gitignored
temp dir, NEVER under `plan/`). Its **first non-empty line** is `<token>` or
`<token>: <detail>`, and there are exactly **three legal tokens**:

- **`ready`** — "I am at a clean stopping point; restart me." **This is the SOLE
  restart authorization.** It counts only if its mtime is **newer than this
  round's injection stamp** (see the interlock below). Write it — do not merely
  print the command.
- **`blocked: <one-line reason>`** — "I need a human decision I cannot make
  myself." The track is **surfaced** to the operator, with its tmux coordinates,
  and is **never restarted and never keystroked into**.
- **`winding-down`** — the ACK: "I got the wrap-up and am wrapping up now."
  **Write this IMMEDIATELY on receiving the wrap-up, before anything else.** A
  **fresh** ACK suppresses further re-warns, so the daemon never keystrokes into
  a session that is actively wrapping up. A **stale** one (older than
  `_ACK_STALE_AFTER`, 900 seconds) resumes the escalation and re-reports the
  track — but it STILL never authorizes the daemon to act. The ACK buys patience,
  not an indefinite stall.

The normal sequence is therefore **two writes**: `winding-down` the moment the
wrap-up lands, then `ready` (or `blocked: …`) when the session actually stops.
The daemon acts on the file on its next tick.

**Declaring is MANDATORY — "nothing" is not a valid outcome.** A session chooses
*which* value fits; it may not decline all three. Declining does not buy a
reprieve and does not buy a restart either: the track is reported to the human as
NOT RESPONDING and then **sits there**, wedged, until a person intervenes. The
session is not killed — it has simply broken its own track and handed a chore to
a human. And because the fresh session inherits **only**
`plan/<topic>/handoff.md`, a session whose real pending work has drifted from
that file must **rewrite the file** — never stash its resume state in a
scratchpad and withhold the declaration.

## What `ready_valid` validates (the restart interlock)

The daemon restarts a tracked session ONLY when the state file passes ALL of
these deterministic checks (`signals.ready_valid`):

1. an **injection stamp exists** for this round (there was a wrap-up to respond
   to) — without one there is no round to declare against;
2. the state file's token is **exactly `ready`**; AND
3. its **mtime is strictly newer than the injection stamp** — proving the
   declaration is from this round, not a stale one from a prior wrap-up.

Any absent, unreadable, or other-valued file makes the check **False**
(fail-closed). Beyond the token, the file's contents are not inspected — no
handoff hash — because the handoff (and everything under `plan/`) is the
session's own business, which the overseer must never read or hash. The daemon
**deletes the state file** as it restarts (`_clear_state`, which also clears the
round's stamp + notified bands), so a declaration can never re-trigger. The
restart is additionally gated on: no busy markers (including no live background
shell under the pane's process), a verified idle-input pane, a **settled** pane
(two captures compared), and a process-identity check that the pane really is our
Claude in our repo.

**Stale-declaration voiding.** If a session declares `ready` and then **resumes
work**, the daemon voids the (now false) declaration rather than restarting it
later: on a busy or blocked tick, a `ready` older than `_MARKER_VOID_GRACE` (120
seconds) is cleared. Younger ones survive, because the declaring turn's own tail
(final streaming + stop hooks) legitimately keeps the pane busy for a while right
after the file is written.

## The restart mechanics (unchanged — only the trigger changed)

Once, and only once, the session has declared `ready`, the daemon runs:

    respawn-pane -k -c <repo> 'claude --dangerously-skip-permissions -n <topic>'
      → wait for the fresh Claude TUI (poll #{pane_current_command})
      → bracketed-paste + verify-submit:  read <repo>/plan/<topic>/handoff.md and follow it
      → clear the round (state file + injection stamp + notified bands)

`--dangerously-skip-permissions` is required for the resumed session to run
**autonomously**; without it the fresh session stalls on its first permission
prompt. The abrupt `respawn-pane -k` is safe **precisely because of the
declaration**: the session asserted it is at a clean stopping point. And
`respawn-pane -k` replaces the **process** — every file, worktree, branch, and
commit on disk survives it. Every tmux step is a hard gate: if the respawn fails
or the pane never becomes a live Claude, the daemon surfaces the failure and
**keeps** the `ready` declaration so the next tick retries, rather than silently
destroying it.

## Notify, never block — the overseer relays, the tracked pane answers

**A question may only be asked by the actor that OWNS the decision.** A tracked
session's decision belongs to that session and is already displayed in **its own
pane**; the overseer must never re-ask it. So every track the daemon reports —
`blocked:human`, a non-responding `danger` track, a malformed state file — is
relayed to the operator as **non-blocking text**, never as a blocking prompt
(`AskUserQuestion`), and the operator answers **in the tracked session's own
pane**.

Because the overseer never prompts on a track's behalf, the alert line is the
operator's ONLY handover — so it is self-sufficient: every track-scoped alert
(`Supervisor._alert`) names the plan **topic**, its **repo**, the tmux
**session** and **pane** holding it, and a copy-pasteable jump command
(`tmux switch-client -t <session>`). A bare `repo::topic` told the operator WHAT
was stuck but not WHERE to go.

This self-heals: the daemon re-derives `blocked:human` from the live pane each
tick, so when the human answers in the tracked pane, the alert simply stops.
(Overseer-OWNED decisions — add / remove / unassign / start a track, a threshold
— are a different matter: nobody else can answer them, so a clickable question is
correct there. See `SKILL.md`.)

## Handoffs may adopt the `blocked:` convention

A tracked session's own `handoff.md` MAY bake in "when you stop to ask the human
a question, write `blocked: <one-line reason>` to the state file" so a
prose-question stop is detected airtight rather than showing as plain `idle` in
the table. This is optional: the restart interlock stays safe regardless, because
a restart requires a fresh `ready`, which a blocked session never writes.

## Pointers

- `design.md` (beside the plan at `plan/overseer-rewrite/`) — the "Notify, never
  block + the cardinal rule" section carries the current design; "The
  certification protocol" and "Context-% reading" carry the original rationale
  and the anchored, fail-closed context parse.
- `SKILL.md` — the bottom-pane interactive overseer contract that starts the
  daemon and relays what it reports.
- `AGENTS.md` — maintenance guidance for editing the overseer.
- `.ai/agent-disciplines.md` (repo root) §"Tracked-session discipline — the
  overseer wrap-up contract" — the same contract stated from the TRACKED
  SESSION's side.
