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
You only have {N}% of your context remaining. Wrap up for a clean session restart:
 1. Get your OWN work to a clean, resumable stopping point — your session owns its
    handoff and everything under plan/; the overseer never touches those.
 2. Stop every background sub-agent and subprocess you started.
 3. ONLY when genuinely at a clean stopping point, WRITE the ready marker (do not
    merely print it), then stop:
        mkdir -p {marker_dir} && : > {marker_dir}/.overseer-ready
 If instead you are blocked on a human decision, write:
        mkdir -p {marker_dir} && echo "<one-line summary>" > {marker_dir}/.overseer-blocked
```

`{N}` is the session's CURRENT remaining-context percent; `{marker_dir}` is
`<repo>/tmp/overseer/<topic>/`. The exact string lives in `supervisor.py`'s
`WRAPUP_TEMPLATE`; keep this block and that constant in sync if either changes.

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
daemon never keystrokes into a blocked track and never restarts it.

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
