# Incident record — 2026-07-19 fleet kill caused by an adversarial-review agent brief

**The agent driving this thread destroyed the maintainer's tmux fleet.** This is
the third fleet kill (2026-07-03, 2026-07-18 ×2, 2026-07-19). It was caused by
the agent working ON the prevention epic, which makes it the most instructive of
the four. Record it verbatim; do not soften it.

## Timeline (CEST, 2026-07-19)

| When | What |
|---|---|
| 07:47:55 | Session spawned a **Codex** sub-agent (`codex:codex-rescue`) to adversarially pre-accept-review the 4 merged guard changes. |
| 07:59:03–07:59:05 | Fleet died. Clean-teardown signature in the user journal: a burst of `tmux-spawn-*.scope: Consumed <N> CPU time, <N>G memory peak` — identical to the 2026-07-18 signature (not a crash, not OOM). |
| 08:03:39 | Maintainer manually recreated one session. |

Corroboration: the session's own foreground `Bash` call died with **exit 137**
(SIGKILL) — its shell went down with the server it lived in.

## Root cause

The review brief instructed the agent to **"actively try to break each"** guard
and then *listed literal fleet-killing commands to craft*:

- `env TMUX_TMPDIR=/tmp tmux kill-server`
- `tmux -S /tmp/tmux-1000/default kill-server`
- `tmux -L default kill-server`
- `bash -c 'tmux kill-server'`

The author's intent was "feed these as JSON payload strings to the guard's
stdin and read its verdict." **The brief never said that**, and never said
"do not execute a tmux command." An agent told to "try" them had every reason
to run them.

## Why no guard stopped it

The only guard actually live at the time was the **host guard** — a Claude Code
`PreToolUse` (Bash) hook in `~/.claude/settings.json`. **A Codex-runtime agent
does not pass through Claude Code hooks at all.** The session pointed a
"break the tmux guard" agent at the one runtime its guard provably could not see.

The Codex-runtime guard that *would* have covered it (work-item
`livespec-omjc2t` → mirror `livespec-driver-codex-72z`) was **merged but never
installed** into `~/.codex/config.toml`.

## Contributing cause — the reporting error that created false confidence

Before spawning the agent, the session reported the epic as "essentially built"
with a table of green rows, on the basis of **merge SHAs**. In reality **one of
five layers was live** (the host guard). The session then acted on its own false
report, believing the fleet was defended.

This violates the fleet's own standing rule (`CLAUDE.md`):

> "Done" means rolled out and exercised live — never merely merged + CI-green +
> AI-accepted.

## Hard rules this incident establishes

1. **Never put a destructive command in a sub-agent brief** — not as an example,
   not as a thing to "try", not even quoted. Describe the hazard class in prose
   and require verification by *classifier payload*, never by execution.
2. **Guard-testing is payload-only.** To prove a guard denies X, feed X as a
   string to the guard's stdin and read the verdict. Executing X to "see if it
   is blocked" risks the exact destruction the guard exists to prevent, and is
   never necessary.
3. **A hook covers exactly one runtime.** Before dispatching any agent, enumerate
   the runtime it will execute on (Claude Code / Codex / Fabro sandbox / raw
   subprocess) and confirm a guard covers *that* runtime. Coverage on one runtime
   is not coverage.
4. **Merged ≠ protected.** Never report a safety control as done, complete, or
   protecting anything until it is INSTALLED on the target runtime and
   demonstrated live with a payload.
5. **A script's internal subprocesses are invisible to a PreToolUse hook.** The
   hook sees only the top-level Bash command string. `python3 foo.py` is opaque.
   This is a structural limit of the L2 guard and is why L1 (env inversion)
   matters.

## Standing constraint until L1/L2 coverage is complete

Do NOT spawn a sub-agent on any runtime lacking an installed tmux guard. If a
Codex reviewer is wanted, install and live-verify the Codex guard FIRST
(see `../handoff.md` step 1).
