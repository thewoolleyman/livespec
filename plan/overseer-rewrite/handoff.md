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
`STATE_*` incl. `STATE_IDLE_WITH_CONTEXT_LEFT` / `_DAEMON_TOKENS`, `TrackState`),
`supervisor.py` (`wrapup_message` + the two escalation heads, `idle_nudge_message` +
`_nudge_idle_with_context` / `_write_idle_nudge_state` / `_clear_idle_nudge_state`,
`_live_session_outside_tmux`, `_elide` + `_MAX_NOTE_IN_TABLE` / `_MAX_REASON_IN_ALERT`,
`_alert`, `_alert_non_responder`, `_clear_state`, and `_do_restart` — which has exactly
ONE caller, guarded by `elif ready:`), beside-tests (**209 green**).

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

## Shipped 2026-07-16 (all merged to master + live-exercised)

Three daemon improvements landed this day, each restarted into the live
`livespec-overseer` daemon and exercised against the real fleet:

- **idle-with-context-left nudge (PR #1282).** A session idle ABOVE its wind-down
  threshold, not waiting on a human, undeclared → the daemon sends ONE "keep going, do
  not stop with context left" nudge and stamps a daemon-written `idle-with-context-left`
  marker (the FIRST daemon-authored token), edge-triggered and self-clearing when the
  session goes non-idle. The cardinal rule is intact — the marker gates a text nudge,
  never a respawn. **Live evidence:** `nudged idle-with-context-left …::codex-factory-
  telemetry (ctx 58% > threshold 50%)` fired on a real fleet session; marker written then
  auto-cleared when it resumed. See `marker-protocol.md` §"The keep-going nudge",
  `AGENTS.md` invariant 9.
- **live-outside-tmux (PR #1286).** A mapped tmux session gone BUT a live Claude registry
  session for the topic running OUTSIDE tmux (a bare SSH shell) → the informational
  `live-outside-tmux` (`_live_session_outside_tmux`), NOT the alarming `session-gone`, and
  kept out of `NEEDS YOU`. **Live evidence:** `fabro-ci-image-factoring` showed
  `live-outside-tmux` while its SSH session was alive, and correctly fell back to
  `session-gone` once that session exited.
- **Note elision on every surface (PR #1286).** A session wrote a 705-byte `blocked:`
  reason that blew up the Status column (sized to its widest cell) and dumped into the
  alert + `NEEDS YOU`. `_elide` flattens + truncates the note at all three sites: the
  table Status cell (`_MAX_NOTE_IN_TABLE`, 48) and the `NEEDS YOU` line + `_alert`
  daemon.log line (`_MAX_REASON_IN_ALERT`, 160). Full reason stays in the pane the jump
  command points at. See `AGENTS.md` render bullet.

## Resume command

**The redesign, the display / detection-accuracy fixes, and the 2026-07-16 trio above are
complete, merged, and live-exercised.** The daemon in the `livespec-overseer` top pane
was respawned onto master carrying all of them (2026-07-16). The ONE open ENGINEERING
item is **Codex detection — now BUILD-READY** (design below); pick it up in a fresh
focused session.

### NEXT = Codex detection — BUILD-READY design (de-risked 2026-07-16)

The daemon cannot see a Codex session: it discovers the plan (shows `unassigned`) but
cannot map the running Codex session to it. The previous note called the topic↔session
join "the hard part … no clean join." **That is now SOLVED** — the join is clean and
exact (verified live 2026-07-16), so this is ready to build. Do it as its own focused
session (a new worktree/PR), not inline.

**The clean join (verified live):** a running codex process holds its rollout file OPEN,
and the rollout filename embeds the session id, which `session_index.jsonl` maps to the
`thread_name` = the plan topic.

1. Enumerate running codex processes (`/proc/<pid>/comm == "codex"`; the binary is
   `…/@openai/codex-linux-x64/…/bin/codex --dangerously-bypass-approvals-and-sandbox`).
2. `/proc/<pid>/cwd` → the repo; scan `/proc/<pid>/fd/` for the open
   `rollout-<ts>-<id>.jsonl` → extract `<id>`.
3. `<id>` → `~/.codex/session_index.jsonl` → `thread_name`. (The rollout file's first
   payload also carries `cwd`, as a cross-check.)
4. If `thread_name` matches a discovered `plan/<topic>/` in that repo → adoptable.
5. Walk `<pid>` up to a tmux pane PID → the tmux session (reuse
   `claude_sessions.resolve_tmux_session`).

Verified: pid in `livespec-dev-tooling` → open rollout id `019f6a11` → thread_name
`rop-sweep-library-checks` → real `plan/rop-sweep-library-checks/`; likewise
`rop-sweep-consumer-cleanup` in `livespec-orchestrator-beads-fabro`. Some threads are
`"Codex Companion Task: …"` (sub-agent / one-shot codex runs), NOT plan topics — those
simply fail step 4 and are correctly ignored, so the companion-task noise filters itself.

**The four signals — what v1 needs:**

1. **Adoption (NEW).** A `codex_sessions.py` mirroring `claude_sessions.py`:
   `read_live_codex_sessions(...) -> [CodexSession(pid, cwd, thread_name)]` composing the
   pid→open-fd→id→thread_name join, and a `map_codex_sessions` joining to tmux (reuse
   `resolve_tmux_session`). Then `Supervisor.adopt_codex_sessions` (or fold into
   `adopt_sessions`): for each live codex session whose `thread_name` is an ACTIVE plan
   topic in a fleet repo and not already mapped → append a mapping that RECORDS THE
   RUNTIME (claude vs codex) so `evaluate` can branch (see §4).
2. **Identity gate (CHANGE).** `_pane_is_managed_claude` / `signals.pane_is_claude` accept
   only `node`/`claude`. Add a Codex identity (`pane_is_codex` → `bun`/`codex`) and let the
   gate accept the mapped session's runtime — a Codex-mapped session whose pane is
   `bun`/`codex` is valid, not `not-claude`.
3. **Busy (MOSTLY DONE).** The process-tree shell-walk (`has_active_subshell`) is the
   runtime-agnostic FALLBACK the daemon already uses when `claude_status is None` — exactly
   the Codex case (Codex is not in Claude's registry). Likely already fires for a busy
   codex; VERIFY live (a codex running a tool spawns subprocesses).
4. **Ctx% + restart (SAFETY-CRITICAL).** Codex has no `Ctx: N% left` statusline →
   `parse_ctx_remaining` returns unknown → no wrap-up, no ctx-band (fail-closed, fine).
   **The restart path MUST be gated Claude-only.** `_do_restart` launches
   `claude --dangerously-skip-permissions -n <topic>`; running that against a Codex pane
   would replace the codex session with a claude one — destructive and wrong. A Codex track
   is MONITOR-ONLY: the `ready` branch of `evaluate` must NOT reach `_do_restart` for a
   codex-runtime track. Gate on the mapping's runtime marker, and TEST it explicitly (a
   Codex track that declares `ready` must NOT restart). This is the one place a bug is
   dangerous — get it right.

**A Codex track** then adopts and shows `working` / `idle` / `blocked:human` like a Claude
track (busy via the shell-walk; `blocked:` via the state file if the codex session writes
one — the idle-nudge's `blocked:` escape already applies). It never gets the wrap-up (ctx
unknown) and is NEVER restarted.

**Code + tests + docs:** new `codex_sessions.py` + beside-tests; `supervisor.py` changes
(adopt, identity gate, restart gate) + beside-tests; `AGENTS.md` (a Codex-adoption
invariant + the monitor-only restart gate) and `SKILL.md`. Beside-tests are the ONLY gate:
`uv run pytest .claude/skills/overseer/ -q`. **Secrets caution:** rollout `.jsonl` files
contain session content — read only the filename (for the id) and the first payload's
`cwd`; never dump rollout bodies.

### Standing operational notes (NOT open tasks)

- **A running daemon must be restarted to pick up new code.** `overseerd` is long-lived in
  the top pane and keeps whatever code it started with. As of 2026-07-16 it was respawned
  onto master carrying the idle-nudge + live-outside-tmux + note-elision trio — do not
  restart it just because you read this line. (Restart is `respawn-pane -k` on the daemon
  pane with `.claude/skills/overseer/overseerd 2>> tmp/overseer/daemon.log`; the stderr
  redirect is REQUIRED — `_log`/`_surface` write to stderr, and the bottom pane reads that
  daemon.log.)
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
