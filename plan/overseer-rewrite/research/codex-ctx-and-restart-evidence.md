# Research — Codex Ctx% IS readable and restart IS possible (evidence for two §4 corrections)

**Date:** 2026-07-16. **Method:** direct inspection of the live machine (`~/.codex/`,
`/proc/<pid>/`, `codex --help`) against a real 2-day-old Codex TUI session (pid 1682090,
cwd `/data/projects/openbrain`, tmux session `openbrain`).

## Scope — what this does and does NOT touch

The BUILD-READY design in `handoff.md` §"NEXT = Codex detection" stands: its pid→open-fd→
rollout-id→`thread_name` join is correct (this investigation derived the identical join
independently, on different sessions — see "Corroboration" below), and its signal-1/2/3
plan is unchanged by anything here.

This document corrects **only §4 (Ctx% + restart)**, which reaches two conclusions the
live evidence contradicts. Both corrections *expand* what a Codex track can do; neither
weakens the §4 safety gate, which is right and must stay (see "The safety gate is
correct").

## Correction 1 — Ctx% does NOT require the statusline

§4 says: *"Codex has no `Ctx: N% left` statusline → `parse_ctx_remaining` returns unknown
→ no wrap-up, no ctx-band (fail-closed, fine)"*, and concludes a Codex track *"never gets
the wrap-up (ctx unknown)"*.

The premise (no statusline) is true; the conclusion does not follow. Ctx% is available
from the **rollout file the design already opens** — the same file it reads for the id and
the first payload's `cwd`. The rollout carries a `token_count` event stream (773 of them in
the sampled session), each with:

```json
{"type": "token_count",
 "info": {"last_token_usage": {"total_tokens": 165818},
          "model_context_window": 258400}}
```

So `ctx_left% = 1 − last_token_usage.total_tokens / model_context_window` → **35.8% left**
on the sampled session. Reading the LAST such record gives the current figure.

This is not a workaround — it is a *better* source than the Claude path: an authoritative
number read from a file, versus a regex over rendered terminal text that a repaint can
mangle.

**Why this matters:** the escalating wrap-up is the daemon's core lever now that nothing is
force-killed. Under §4 as written, a Codex track is a passenger — visible in the table but
never nudged, so it silently runs to exhaustion and wedges exactly the way the original
overseer bug did. With ctx readable, a Codex track can receive the wrap-up and declare
`ready`/`winding-down` like any other, and the whole protocol applies to it unchanged.

**Metadata only.** `last_token_usage` and `model_context_window` are counters in an event
envelope, not conversation content — consistent with §4's secrets caution (never dump
rollout bodies). An implementation should parse `token_count` payloads and ignore all
other record types.

## Correction 2 — restart is possible; "never restarted" is stronger than needed

§4 concludes a Codex track *"is NEVER restarted"*, treating monitor-only as intrinsic.

It is not intrinsic — it is a property of the *command*, and Codex has a direct analogue:

```
codex resume [SESSION_ID] [PROMPT]
    SESSION_ID: "Session id (UUID) or session name. UUIDs take precedence if it parses."
    PROMPT:     "Optional user prompt to start the session"
```

So the restart mechanic maps cleanly:

```
codex resume <topic> "read <repo>/plan/<topic>/handoff.md and follow it"
```

This is in two ways *cleaner* than the Claude path:

- The kick is an **argument**, so no `send-keys` paste and no paste-race.
- `resume` reattaches the **same named session**, so the `thread_name` — hence
  adoptability — survives the restart by construction. (`claude -n <topic>` creates a
  fresh session instead.)

`archive` / `delete` / `unarchive` likewise accept "id or session name", confirming names
are first-class in Codex, not an incidental label.

**This does not make monitor-only wrong for v1** — a smaller blast radius on a
load-bearing daemon is a legitimate scope call, and it is the maintainer's to make. The
correction is narrower: monitor-only should be recorded as a **v1 scope decision with a
known exit**, not as a permanent property of Codex tracks.

## The safety gate is correct — keep it exactly as §4 has it

§4's core safety point is right and this research reinforces it: `_do_restart` launches
`claude --dangerously-skip-permissions -n <topic>`, and running that against a Codex pane
would replace the codex session with a claude one — destructive and wrong. **The `ready`
branch must not reach the current `_do_restart` for a codex-runtime track, and that must be
tested explicitly.**

The correction is about what comes *after* the gate. Rather than the gate meaning "codex →
never restart", the durable shape is **runtime-dispatched restart**: the gate selects the
restart command for the track's runtime (`claude -n <topic>` + paste vs `codex resume
<topic> "<kick>"`), and v1 may simply leave the codex arm unimplemented. That keeps today's
safety identical while not baking "never" into the design.

The cardinal rule is already runtime-agnostic and needs no change: never restart without a
`ready` declaration, which a Codex session writes to the same
`<repo>/tmp/overseer/<topic>/.overseer-state` path.

## Corroboration of the landed join (independent, different sessions)

Derived independently before the design landed, on different sessions than the ones §4
cites — so the join is now confirmed twice, on disjoint evidence:

- pid 1682090 → fd → `rollout-2026-07-12T06-19-39-019f548d-….jsonl` → uuid `019f548d-…`
  → `session_meta.cwd = /data/projects/openbrain` (matching `/proc/1682090/cwd`),
  `originator: codex-tui`, `thread_source: user`.
- `originator: codex-tui` is an additional identity cross-check available from the rollout
  side, corroborating signal 2's `bun`/`codex` process gate.

Two facts worth having alongside §4's companion-task note:

- **The index is sparse: only 67 of 259 rollout files appear in `session_index.jsonl`** —
  because only *named* sessions are indexed. An unnamed session carries no topic anywhere
  (the sampled session's rollout contains the string `thread_name` **zero** times). §4's
  step 4 already fails such sessions closed, so this costs nothing — but it means Codex
  adoption, like Claude's, *depends on a naming convention* (`claude -n <topic>`'s
  equivalent). Worth stating as a precondition rather than discovering later.
- **The companion/real split is 38/31**, not overwhelmingly companion: the 31 real names
  include `autonomous-mode`, `ledger-status-conformance`, `console-specification-drafting`,
  `cloud-local-memory-cleanup`, plus §4's two `rop-sweep-*`.
