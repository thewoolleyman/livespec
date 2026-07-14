# Overseer wrap-up + marker protocol

This is the contract between the overseer **daemon** (`supervisor.py`, the top
pane) and a **tracked session** (a Claude Code session running a plan thread in
some repo). It defines the wrap-up message the daemon injects at a context
threshold and the two **out-of-band marker files** a tracked session writes to
certify its state. `supervisor.py`'s `WRAPUP_TEMPLATE` /
`wrapup_message()` and `signals.py`'s `ready_marker_valid()` /
`blocked_marker()` are the authoritative implementations; this doc is the
single conceptual source they share, and the reference a tracked session's own
`handoff.md` points at.

## Why markers, not printed text

A pane's text stream **cannot** carry a trustworthy "the session asserts X now"
signal. The injected instruction is echoed back into the transcript, the model
quotes tokens while narrating, output scrolls above the visible capture, and
long lines wrap — any of which turns a printed sentinel into a **false match**
(adversarial review, 2026-07-12, blockers #1–#4). So certification is
**out-of-band, on the filesystem**: a file write cannot be forged by
prompt-echo, cannot scroll off, and cannot line-wrap. Pane scraping is retained
ONLY for the busy / idle / gate signals, where a false positive is safe (it
merely suppresses action). See the "The certification protocol" section of
`design.md`.

## The overseer NEVER touches `plan/`

The overseer touches only its **config** (the mapping store, the injection-stamp
sidecar, the fleet manifest) and **temp files** (`<repo>/tmp/overseer/<topic>/`).
It NEVER reads, writes, or hashes anything under a session's `plan/<topic>/` tree
— the handoff and all plan-thread files are the **session's own workflow**. The
overseer enumerates `plan/*/` DIRECTORIES to discover tracks and *points* a
resume line at the conventional `plan/<topic>/handoff.md`, but it never opens it.
Because the markers live under `tmp/` (gitignored), the overseer never dirties a
tracked tree; the daemon `git check-ignore`-validates each watched repo's
`tmp/overseer/` at startup and refuses to run if any is not ignored.

## What the daemon injects at threshold

When a tracked session's **remaining context** falls to or below its threshold
(`ctx_threshold`, default 50%) AND the pane is in a verified idle-input state,
the daemon records an **injection stamp** (an epoch-seconds timestamp in the
sidecar `~/.livespec-overseer-stamps.json`, keyed by `(repo, topic)`) and then
**bracketed-pastes** this wrap-up message:

```
You only have {N}% of your context remaining. Wrap up for a clean session restart.

You WILL be restarted. That is automatic and NOT conditional on your cooperation.
When you stop, this pane is respawned into a fresh session handed exactly ONE prompt:
    read {handoff} and follow it
So {handoff} is the ONLY thing the next session inherits. Do NOT leave your resume
state anywhere else (a scratchpad file, this transcript) — it will be LOST. If your
real pending work has drifted from what that file says, REWRITE that file to
describe the actual next step.

 1. Bring your OWN work to a clean, resumable stopping point, and UPDATE {handoff}
    to match. Your session owns its handoff and everything under plan/; the overseer
    never reads or writes those.
 2. Stop every background sub-agent and subprocess you started.
 3. Then WRITE the ready marker (do not merely print it) and stop:
        mkdir -p {marker_dir} && : > {marker_dir}/.overseer-ready
    It certifies you are done, and restarts you IMMEDIATELY.
 If instead you are blocked on a HUMAN decision you cannot make yourself, write this
 one instead and stop — a blocked track is surfaced to the human, never auto-restarted:
        mkdir -p {marker_dir} && echo "<one-line summary>" > {marker_dir}/.overseer-blocked

Write ONE of the two markers. Declining to write either does NOT prevent the restart —
it only means you get force-restarted later, from a handoff you never refreshed.
```

`{N}` is the session's CURRENT remaining-context percent; `{marker_dir}` is
`<repo>/tmp/overseer/<topic>/`; `{handoff}` is `<repo>/plan/<topic>/handoff.md`.
The exact string lives in `supervisor.py`'s `WRAPUP_TEMPLATE`; keep this block and
that constant in sync if either changes.

**Why the message names the handoff and states the restart is unconditional.** A
tracked session once REFUSED to write either marker: its real pending work had
drifted away from what `plan/<topic>/handoff.md` said (it had stashed the live
handoff in a scratchpad file), so it reasoned that certifying would resume the next
session from a stale document — and it stopped, un-certified, wedging its track idle
at 13% **forever**. Both halves of that failure are now closed: the daemon
force-restarts a stalled track regardless (see below), and this message tells the
session plainly that (a) the restart is coming either way and (b) the handoff is the
ONLY artifact it can hand forward — so the correct response to drift is to **rewrite
the handoff**, never to withhold the marker. Naming the handoff path is still
POINTING at it, exactly as the resume line does; the overseer never opens it.

## What a tracked session must WRITE

Two marker files, both under `<repo>/tmp/overseer/<topic>/` (the repo's gitignored
temp dir — NEVER under `plan/`):

- **`.overseer-ready`** — write this ONLY when genuinely at a clean stopping
  point. Its **contents do not matter** (presence + a fresh mtime are the whole
  signal); an empty file is fine. Writing the marker is the session's
  certification "I am done; restart me." **Write the file — do not merely print
  the command.** How the session prepared its own handoff / plan files is its own
  business; the overseer does not inspect it.
- **`.overseer-blocked`** — write this instead when the session has stopped on a
  **human decision** it cannot make itself. Its contents are a one-line summary
  of what is blocked. Presence (not content) is the signal, so even an empty
  file reads as blocked.

Stop after writing the marker. The daemon acts on it on its next tick.

**Writing ONE of the two is MANDATORY — "neither" is not a valid outcome.** A
session may choose *which* marker fits (done → `.overseer-ready`; needs a human →
`.overseer-blocked`), but it may not decline both. Declining does not veto the
restart; it only forfeits the session's say in *when* and *from what*: the daemon
force-restarts a stalled track anyway, from a handoff the session chose not to
refresh. And because the fresh session inherits **only**
`plan/<topic>/handoff.md`, a session whose real pending work has drifted from that
file must **rewrite the file** — never stash its resume state in a scratchpad and
withhold the marker.

## What `ready_marker_valid` validates (the restart interlock)

The daemon restarts a tracked session (atomic `respawn-pane -k` → wait for the
fresh Claude TUI → paste the resume line → delete the marker) ONLY when the
`.overseer-ready` marker passes ALL of these deterministic checks
(`signals.ready_marker_valid`):

1. an **injection stamp exists** for this round (there was a wrap-up to respond
   to) — without one there is no round to certify;
2. the `.overseer-ready` marker file **exists**; AND
3. its **mtime is strictly newer than the injection stamp** — proving it is from
   this round, not a stale marker from a prior wrap-up.

Presence + freshness only — the marker's **contents are not inspected**, because
the handoff (and everything under `plan/`) is the session's own business, which
the overseer must never read or hash. Any missing or unreadable file makes the
check **False** (fail-closed). Because the daemon **deletes the marker** as it
restarts, a marker can never re-trigger. The restart is
additionally gated on no busy markers and a verified idle-input pane. This is
the out-of-band certification that defeats the pane-echo problem — blockers
#1–#4 all dissolve here.

The `.overseer-blocked` marker has no hash interlock: presence alone flips the
track to `blocked:human` in the table and is surfaced to the bottom pane; the
daemon never keystrokes into a blocked track and never restarts it — a human gate
is the ONE thing that suppresses the force-restart below.

## The restart is NON-NEGOTIABLE — the marker is a fast path, not a veto

The `.overseer-ready` interlock above buys an **immediate** restart. Withholding it
does **not** buy a reprieve. A warned session that stalls **idle** at or below the
danger line (`DANGER_CTX_REMAINING`, 20% remaining) without ever certifying — it
refused, crashed, ran out of context, or autocompacted — is **FORCE-restarted** once
it has been continuously idle-stalled for `_STALL_RESTART_GRACE`
(`supervisor._danger_or_force_restart`). Both paths then run the identical mechanics:

    respawn-pane -k -c <repo> 'claude --dangerously-skip-permissions -n <topic>'
      → wait for the fresh Claude TUI (#{pane_current_command})
      → bracketed-paste + verify-submit:  read <repo>/plan/<topic>/handoff.md and follow it
      → clear the round (marker + injection stamp + notified bands)

`--dangerously-skip-permissions` is required for the resumed session to run
**autonomously**; without it the fresh session stalls on its first permission prompt.

This REPLACED the original "danger → surface to the human, NEVER force-kill"
behavior, which wedged a real track idle at 13% forever. **It is not a mid-work
kill.** The force-restart is reachable only from the idle branch of the state
machine, so the pane is already proven not-busy, *settled* (two captures apart),
identity-gated Claude, not at a structured gate, and not `.overseer-blocked`. A busy
pane is `working` and is never touched; a human-gated pane is `blocked:human` and is
never restarted. `respawn-pane -k` replaces the **process** — every file, worktree,
and commit on disk survives. The stall clock resets the instant the session resumes
work, so only a genuine, continuous stall accrues toward the grace.

## Handoffs may adopt the `.overseer-blocked` convention

A tracked session's own `handoff.md` MAY bake in "when you stop to ask the human
a question, write `.overseer-blocked` with a one-line reason" so a
prose-question stop is detected airtight rather than showing as plain `idle` in
the table. This is optional: the restart interlock stays safe regardless,
because a restart requires the `.overseer-ready` marker, which a blocked session
never writes.

## Pointers

- `design.md` — the "The certification protocol" and "Context-% reading"
  sections carry the full rationale and the anchored, fail-closed context parse.
- `SKILL.md` — the bottom-pane interactive overseer contract that starts the
  daemon and surfaces what it reports.
- `AGENTS.md` — maintenance guidance for editing the overseer.
