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

## What the daemon injects at threshold

When a tracked session's **remaining context** falls to or below its threshold
(`ctx_threshold`, default 50%) AND the pane is in a verified idle-input state,
the daemon records an **injection stamp** (an epoch-seconds timestamp in the
sidecar `~/.livespec-overseer-stamps.json`, keyed by `(repo, topic)`) and then
**bracketed-pastes** this wrap-up message once (re-sent once more only if
context keeps dropping):

```
Your context is now under {N}%. Wrap up for a clean session restart:
 1. Update {handoff} so a FRESH session can resume from it alone
    (read-first chain present, concrete next action, resume command printed).
 2. Stop every background sub-agent and subprocess you started.
 3. ONLY when genuinely at a clean stopping point with the handoff ready,
    WRITE the ready marker (do not merely print it), then stop:
        sha256sum {handoff} | cut -d' ' -f1 > {repo}/plan/{topic}/.overseer-ready
 If instead you are blocked on a human decision, write:
        echo "<one-line summary>" > {repo}/plan/{topic}/.overseer-blocked
```

`{N}` is the track's threshold; `{handoff}` is the absolute handoff path;
`{repo}`/`{topic}` build the marker paths. The exact string lives in
`supervisor.py`'s `WRAPUP_TEMPLATE`; keep this block and that constant in sync
if either changes.

## What a tracked session must WRITE

Two marker files, both under `<repo>/plan/<topic>/`:

- **`.overseer-ready`** — write this ONLY when genuinely at a clean stopping
  point with the handoff already updated. Its contents MUST be the SHA-256 hex
  digest of the on-disk `handoff.md`, exactly as `sha256sum <handoff> | cut -d'
  ' -f1` produces it. Writing the marker is the session's certification "I am
  done; a fresh session can resume from this handoff alone." **Write the file —
  do not merely print the command.**
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
2. the `.overseer-ready` marker file **exists**;
3. its **mtime is strictly newer than the injection stamp** — proving it is from
   this round, not a stale marker from a prior wrap-up; AND
4. its stripped **contents equal the SHA-256 hex of the current on-disk
   `handoff.md`** — proving the session actually updated the handoff before
   certifying.

Any missing or unreadable file makes the check **False** (fail-closed). Because
the marker is written only after the handoff update and hash-matches it, a
restart always resumes from an updated handoff; because the daemon **deletes the
marker** as it restarts, a marker can never re-trigger. The restart is
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
