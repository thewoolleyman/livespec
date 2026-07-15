# Handoff — the overseer never restarts a session that has not declared itself ready

**Status (2026-07-14): the CURRENT design.** It SUPERSEDES the "non-negotiable
force-restart" that briefly shipped earlier the same day (PRs #1219 / #1221) — that
force-restart was itself a **severe bug** and has been removed. **HOLD on archive still
stands.** **Owning session:** livespec core, "overseer-rewrite".

## THE CARDINAL RULE

**The daemon NEVER restarts a session that has not declared itself `ready`.**

A timer cannot know whether a session is safe to kill. **"idle + settled" is NOT "at a
safe stopping point"**: a session can sit at an empty prompt while a background build
runs, while a sub-agent works, or while it waits on a human in another pane. Only the
session knows — so only the session may authorize the restart.

A session that declares nothing is **reported** to the human as not responding and is
**left alone**. That is a bug in the SESSION, never a licence for the daemon to guess.

The restart *mechanics* remain fully automatic and unchanged — `respawn-pane -k` →
`claude --dangerously-skip-permissions -n <topic>` → paste `read
<repo>/plan/<topic>/handoff.md and follow it`. Only the *trigger* changed: it is now
solely the session's own declaration.

## What went wrong (the history, so it is not repeated)

1. **The original wedge.** A session at 13% refused to write a marker (its real handoff
   was stashed in a scratchpad, so it judged the resume path stale) and sat idle
   forever. A real bug — but the correct fix was the *wrap-up text*: tell the session
   the handoff is the ONLY artifact it hands forward, so drift is fixed by REWRITING it.
2. **The overcorrection (removed).** A timer-based force-restart was layered on top: a
   warned track idle at the danger line for 90s was killed and relaunched. This
   **guessed** that idle meant safe. It was proven unsafe almost immediately — a session
   with a live `Bash(run_in_background)` build reads exactly like an idle one, so the
   force-restart would `respawn-pane -k` it and destroy the running work. That was only
   the *first* such case; there is no reliable way for the daemon to enumerate the rest.
   Maintainer-declared a **severe bug**; removed.

If you ever find yourself re-adding `_danger_or_force_restart`, `_STALL_RESTART_GRACE`,
or `danger_idle_since` — stop. That is this bug returning.

## The ONE tri-state indicator file

`.overseer-ready` + `.overseer-blocked` are **gone**. Two presence-markers carried a
built-in ambiguity: nothing stopped BOTH existing, and their precedence was incidental
rather than designed. There is now **one file with a VALUE**, which makes the ambiguity
unrepresentable — writing one value REPLACES the other.

`<repo>/tmp/overseer/<topic>/.overseer-state`; the first non-empty line is `<token>` or
`<token>: <detail>`:

| value | meaning | daemon |
|---|---|---|
| `ready` | at a clean stopping point — restart me | **the SOLE restart authorization** (and only if its mtime is newer than this round's injection stamp) |
| `blocked: <one-line reason>` | needs a human decision the session cannot make | surfaced with coordinates; never restarted, never keystroked |
| `winding-down` | ACK: got the wrap-up, wrapping up now | a FRESH ack suppresses re-warns (never keystroke into a session already wrapping up); a STALE one (older than `_ACK_STALE_AFTER`, 900s) resumes escalation but STILL never authorizes an act |

A malformed/typo'd token is **surfaced** and treated as no declaration (fail-closed) —
never silently ignored, never read as readiness.

## Escalating wrap-up (the lever, now that nothing is force-killed)

Fires once per 10% band, durably (50/40/30/20/10):

- **50 / 40 — suggestion:** *"You are down to N% of your context. Please start wrapping up…"*
- **30 / 20 / 10 — insistent:** *"STOP AND WIND DOWN NOW…"* (`_INSIST_AT = 30`)

Re-sending identical text five times is repetition, not escalation; with no
force-restart, this escalation IS the lever, so it must actually sharpen.

## Notify, never block (the wedged-console bug)

**A question may only be asked by the actor that OWNS the decision, and the overseer
must never block on a question it does not own.**

The interactive bottom pane used to relay a *tracked session's* blocked-gate as its own
`AskUserQuestion` modal. That duplicated the decision surface: the maintainer answered
in the tracked session's own pane, and the overseer's modal stayed blocking forever —
wedging the entire console (a single point of failure for the whole fleet view).

- **Track decisions** → the tracked session owns them and already displays them in its
  own pane. The overseer reports them as **non-blocking text** and never re-asks.
- **Overseer-owned decisions** (`add` / `remove` / `unassign` / `start`) →
  `AskUserQuestion` is still fine; nobody else can answer them.

This self-heals: the daemon re-derives `blocked:human` from the live pane every tick, so
when the human answers in the tracked pane the alert simply stops.

**Every track alert now names WHERE to act** — plan topic, repo, tmux **session**,
**pane**, and a copy-pasteable `tmux switch-client -t <session>` jump command.
`repo::topic` alone said WHAT was stuck but not WHERE to go.

## Where the code lives

`.claude/skills/overseer/` — `signals.py` (`state_path`, `read_state`, `ready_valid`,
`STATE_*`, `TrackState`), `supervisor.py` (`wrapup_message` + the two escalation heads,
`_alert`, `_alert_non_responder`, `_clear_state`, and `_do_restart` — which has exactly
ONE caller, guarded by `elif ready:`), beside-tests (**164 green**).

**The beside-tests are the ONLY gate on this folder** — it sits outside every product
gate (ruff / pyright / coverage / import-linter all exclude it; `just check` never
collects it), so a broken change here merges green with nothing having exercised it.
ALWAYS run before pushing:

```bash
uv run pytest .claude/skills/overseer/ -q
```

## Rolled out and live-exercised (2026-07-14)

The running daemon carries this code and was exercised against the real fleet:

- `blocked:human` alerts now render with their coordinates, e.g.
  `autonomous-mode (livespec) — blocked on human: structured gate on pane — answer it IN
  THAT PANE [tmux session 'livespec-autonomous-mode' pane %66] — jump: tmux switch-client
  -t livespec-autonomous-mode` — a NON-BLOCKING report, so the console cannot wedge on it.
- The escalating wrap-up was delivered to this very track at the 50% band, and this
  session ACKed with `winding-down` and then declared `ready` — the protocol dogfooded
  end-to-end by the session that wrote it.

## Resume command

**The redesign + the display and detection-accuracy fixes are complete, merged, and
live-exercised.** The daemon in the `livespec-overseer` top pane runs current code
(respawned onto master `00d26ef`, 2026-07-15). The ONE open ENGINEERING item is Codex
detection.

### NEXT = Codex detection (the one open feature)

The daemon cannot see a Codex session at all: it discovers the plan (shows `unassigned`)
but cannot map the running Codex session to it. This is deeper than adoption — FOUR daemon
signals assume Claude, and Codex needs each:

1. **Adoption.** `adopt_sessions` reads Claude's registry (`~/.claude/sessions/<pid>.json`:
   name→topic, cwd→repo, pid→tmux). Codex is not there. Codex DOES keep a store
   (`~/.codex/sessions/`, `~/.codex/session_index.jsonl`), and a live codex process's cwd
   is readable via `/proc/<pid>/cwd` — BUT the index's `thread_name` values are
   `"Codex Companion Task: …"`, NOT plan topics like `shell-logic-hardening`. So there is
   **no clean topic↔session join** the way Claude's registry `name` gives one. That is the
   hard part to design (candidate: manual `add` targeting the bare session; or a
   cwd+recency heuristic; or a Codex-side naming convention).
2. **Identity gate.** `_pane_is_managed_claude` accepts only `node`/`claude`; Codex is
   `bun`/`codex`, so a mapped Codex session reads `not-claude`. Needs a `pane_is_codex`
   and a Codex-aware identity so it shows as a tracked Codex session.
3. **Busy.** Already covered — the process-tree shell-walk (`has_active_subshell`) is the
   runtime-agnostic FALLBACK used precisely when there is NO Claude registry entry (Codex).
4. **Ctx% + restart.** Codex's statusline is not `Ctx: N% left` (ctx reads unknown → no
   wrap-up), and restart is `claude -n <topic>` — a Codex session must be MONITORED-ONLY
   (never restarted with the claude command).

Recommendation: scope this as its own focused piece (a plan thread), not a quick patch.

### Standing operational notes (NOT open tasks)

- **A running daemon must be restarted to pick up new code.** `overseerd` is long-lived in
  the top pane and keeps whatever code it started with. As of 2026-07-15 it already carries
  master `00d26ef` — do not restart it just because you read this line.
- **The console BOTTOM pane remedy** (if its interactive Claude exits to a bare `zsh`):
  run `claude --dangerously-skip-permissions` in it, then `/overseer` — `overseer-start` is
  idempotent on the `overseer-daemon` pane title, so it will not double-start the daemon.
  Do NOT run it while the console is already up.

### Related work-item (NOT overseer)

- **`livespec-p9s0`** (livespec core ledger, P1) — the pin "staleness" root cause: the
  cross-repo wiring check reads a sibling's LOCAL clone `HEAD` (not `origin`, no fetch), so
  stale local clones under `/data/projects/` flap the check with drift that does not exist
  on `origin/master`. Decide the durable fix (read the canonical branch fetched; and/or
  keep local clones fresh; and the orphaned-repo angle). Not an overseer change.

## The protocol, dogfooded a second time (2026-07-14)

This session WAS the restart. The previous `overseer-rewrite` session declared `ready`;
the daemon restarted it on that declaration ALONE (`overseer: restarted
/data/projects/livespec::overseer-rewrite (pane %1)`) and `_clear_state` wiped the file.
Re-verified while resuming, so a future reader need not re-derive it:

- **No "nothing to resume" restart loop is possible.** `ready_valid` requires an
  injection stamp *from this round*, so a fresh session that declares `ready` with no
  wrap-up pending is never restarted. Declaring readiness is always safe.
- **Notify-never-block is holding live.** The restored console relayed both blocked
  tracks as NON-BLOCKING text with full coordinates (repo, tmux session, pane, jump
  command) and raised no `AskUserQuestion` on any track's behalf.

## Detection-accuracy bug fixes (2026-07-15)

Three live bugs found while the maintainer exercised the fleet, all in the daemon's
session-detection signals. All fixed; the beside-tests pin each.

1. **`NEEDS YOU` coordinates were unlabeled.** The block printed `autonomous-mode
   (livespec)` — named WHAT was stuck but the tmux session to jump to had to be inferred.
   Fixed: each row now leads with `topic: … | tmux: … | repo: …` (PR #1258, merged).

2. **False-idle: a session running an in-process sub-agent read as `idle`.** The busy
   check was `is_busy(pane) or has_active_subshell(pane)`. A Task-tool sub-agent runs
   INSIDE the `claude`/`node` process — it spawns no descendant shell (so the shell-walk
   misses it) and need not repaint the pane (so `is_busy` misses it). Fix: fold Claude's
   own registry `status: "busy"` (from `~/.claude/sessions/<pid>.json`) into the busy
   check.

3. **False-working: a lingering background `sleep`/poll shell masked an at-prompt
   session as `working (background shell)`.** `has_active_subshell` flags ANY descendant
   shell; a backgrounded `sleep 120` is a descendant shell but not real work. Fix: for an
   adopted Claude session, its registry `status` GOVERNS — when Claude reports
   `idle`/`waiting` the shell-walk is ignored for that session.

The unifying fix (bugs 2+3): **Claude's registry `status` is the authoritative busy
signal for an adopted Claude session** — more accurate than the process-tree shell-walk
(catches sub-agents) and less over-broad (ignores trivial background shells). The
shell-walk stays as the runtime-agnostic FALLBACK for Codex (not in Claude's registry).
Its original job — blocking a force-restart of a live background build — is moot now that
the cardinal rule forbids restart without a `ready` declaration.

4. **Correction (`shell` status): the first cut of the bug-2/3 fix was incomplete.** It
   folded only `status: "busy"` into the busy check and made every other status IGNORE the
   shell-walk — which then mis-read a session at the prompt with a live
   `Bash(run_in_background)` command (Claude reports `status: "shell"`) as **idle**.
   Surfaced live on `autonomous-mode` (a running `drive.py` dispatch) and
   `livespec-orchestrator-beads-fabro`. Root-cause fix: the registry status is
   AUTHORITATIVE and its full vocabulary maps cleanly —
   `_CLAUDE_BUSY_STATUSES = {"busy", "shell"}` are working, `idle`/`waiting` are not; the
   process-tree shell-walk is IGNORED for an adopted Claude session and kept ONLY as the
   Codex fallback. See `AGENTS.md` §"Load-bearing mechanics" (the registry-`status` and
   background-shell bullets).
