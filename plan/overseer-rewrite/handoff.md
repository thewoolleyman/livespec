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

## Row-correctness audit (2026-07-16) — every daemon line verified against ground truth

The maintainer reported `livespec1` as broken ("it doesn't even have an active claude but
it has data in its line") and asked that **every** line's status be double-checked. All 6
non-`unassigned` rows were verified against ground truth (`#{pane_current_command}` + the
Claude registry). **Two real bugs, both fixed; one false alarm, corrected.**

| Row | Daemon said | Ground truth | Verdict |
|---|---|---|---|
| autonomous-mode | `working` 68% | pane `claude`, registry `busy` | correct |
| **fabro-ci-image-factoring** | **`not-claude`, tmux=livespec1** | **bare `zsh`, no live Claude** | **BUG — fixed** |
| ledger-status-conformance | `working (background shell)` | pane `claude`, registry `shell` | correct |
| **overseer-rewrite** | `working` + `blocked:` note | pane `claude`, registry `busy` | **BUG — stale note, fixed** |
| **codex-credential-broker** | `working` + `blocked:` note | pane `claude`, registry `busy` | same bug |
| codex-factory-telemetry | `working`, ctx `—` | pane `claude`, registry `busy` | **NOT a bug — see below** |

**Bug 1 — an exited-to-shell track (PR #1293, merged; PR #1295).** `not-claude` was
designed as the identity GATE for acts and is correct as that, but its answer was reused
as the row STATUS — conflating "our Claude EXITED to a bare shell" (the ordinary end of
every track) with "the mapping points at a FOREIGN pane" (a real mis-mapping). It also
skipped the live-outside-tmux fallback (wired only into the missing-tmux-session branch),
hiding a Claude alive outside tmux behind an alarm. Both no-managed-pane paths now route
through `_no_managed_pane_row`, and such a row reports **`tmux=None`** — the cell asserts
*the tmux session HOLDING this track*, and there is none (maintainer-declared: "it
shouldn't display the session name; the session doesn't exist in that panel anymore").
`not-claude` narrows to the foreign-pane case and deliberately KEEPS naming its session
(that pane is what the operator must inspect) — pinned so the rule cannot be over-applied.

**Bug 2 — an outlived `blocked:` declaration (PR #1295).** Nothing retired a `blocked:`:
`_clear_state` runs only on the daemon's OWN restart path, so a pane replaced out-of-band
inherits its predecessor's declaration (this very track rendered a reason written by a
session that no longer existed), and the dead reason later fires a false `blocked:human`.
Now voided when the session is GENERATING past the RB1 grace — an observation (it is
producing tokens) not a semantic judgment. See `AGENTS.md` §"Stale-`blocked` voiding" for
the two bounds that MUST NOT be widened (`generating` ≠ `busy`; the grace).

**The false alarm — `Ctx: —` is NOT a daemon bug.** A one-shot
`supervisor.py list` renders `—` for a track whose ctx the DAEMON shows fine (it read 83%
at the same moment). `_effective_ctx` keeps the last-known ctx in **per-instance**
`_inject[key].last_ctx`, so a FRESH process has no history and renders `—` until it reads
the statusline itself. Nothing is wrong; do not "fix" it. Read ctx from the running
daemon's table, not from a one-shot `list`.

## Resume command

**The redesign, the display / detection-accuracy fixes, the 2026-07-16 trio above, and the
row-correctness audit are complete, merged, and live-exercised.** PR #1293 (released
0.15.1) and **PR #1295 (tmux=None + the `blocked:` void) are both MERGED to master**.

**⚠ FIRST ACTION: RESPAWN THE DAEMON.** It is long-lived and keeps whatever code it
started with, so it still carries PRE-#1293/#1295 code — until it is respawned the table
keeps showing the old wrong rows (a `not-claude` row naming a dead `livespec1`, stale
`blocked:` notes on working rows). The respawn command is in Standing operational notes;
it was left to the maintainer because it kills the console's own top pane.

The ONE open ENGINEERING item is **Codex detection** — its READ LAYER IS BUILT (PR #1296);
only the `supervisor.py` wiring remains. See the next section, which carries an ORDERING
CONSTRAINT you must read before touching the identity gate.

### NEXT = Codex detection — the READ IS BUILT; only the WIRING remains

**Status 2026-07-16/17: the whole `codex_sessions.py` read layer is built, tested, and
live-exercised (PR #1296).** What remains is a PURE `supervisor.py` change — no further
primitives are needed. Read this sub-section first; the original design below it is
still correct but describes the read as unbuilt.

**Already built and merged/queued (PR #1296)** — `.claude/skills/overseer/codex_sessions.py`
+ 26 beside-tests, every host coupling injected:

| function | what it gives you |
|---|---|
| `read_live_codex_sessions()` | `[CodexSession(pid, name, cwd, session_id)]` — `name` IS the plan topic |
| `map_codex_sessions(pane_pid_to_session)` | `[(tmux_session, name, cwd)]` — **the exact triple `claude_sessions.map_named_sessions` emits**, so ONE adopt path serves both runtimes |
| `codex_by_tmux_session(pane_pid_to_session)` | `{tmux_session: CodexSession}` — **the per-tick map to key everything off**; twin of `_claude_status` / `status_by_tmux_session` |
| `rollout_ctx_remaining(path)` | remaining-% as `int \| None` — **the same shape `signals.parse_ctx_remaining` returns**, so it drops into the same slot |
| `proc_pids_of_comm` / `proc_cwd` / `proc_fd_targets` / `open_rollout_id` / `rollout_id` / `read_thread_names` | the injectable pieces |

Live, right now, on the real host — these two are `unassigned` today and adoptable the
moment the wiring lands:

```
tmux='livespec-dev-tooling'  name='rop-sweep-library-checks'    ctx=62% left
tmux='livespec3'             name='rop-sweep-consumer-cleanup'  ctx=36% left   <-- PAST the 50% line
```

**`rop-sweep-consumer-cleanup` is already past the wind-down line and getting no wrap-up.**
That is the concrete cost of leaving this unwired, and the reason Ctx% mattered.

#### THE ORDERING CONSTRAINT — read before touching the identity gate

**Today's state is already SAFE, and the danger is INTRODUCED by step 2.** The identity
gate (`_pane_is_managed_claude`) rejects a codex pane, so a Codex track reads `not-claude`
and returns BEFORE the busy / ready branches — it can never reach `_do_restart`. The
moment the gate ACCEPTS codex panes, a Codex track that declares `ready` flows into
`_do_restart` and is respawned with `claude --dangerously-skip-permissions -n <topic>`,
which REPLACES the codex session with a claude one. Destructive.

⇒ **Accepting codex panes and refusing to restart them are INSEPARABLE and MUST land in
the same commit**, with the refusal tested (a Codex track that declares `ready` must not
be restarted as claude). Never land adoption or the gate change alone.

**The guard for this is ALREADY WRITTEN and green** (PR #1296,
`test_a_codex_pane_is_never_restarted_even_when_it_declares_ready`). It asserts the
INVARIANT — no respawn, no paste — never the mechanism, so it must keep passing through
your change via the NEW runtime-aware restart gate rather than via the `not-claude` return
that happens to catch it today. It is verified to have TEETH: widening the identity gate
to accept `bun` (exactly your change) turns it RED, because the daemon really does respawn
the codex pane. **If it goes red while you wire, that is the destructive bug, not a stale
test — do not edit the test to make it pass.**

#### Wiring notes that will save the next session time

- **Derive the runtime; do NOT add a stored `runtime` field to the mapping.** A codex
  pane's `#{pane_current_command}` is **`bun`, NOT `codex`** (verified live: tmux reports
  the pane's foreground process, which is the `bun` launcher; the vendored codex binary is
  its CHILD). So a `pane_is_codex` keyed on `bun` would false-positive on any bun app.
  **`codex_by_tmux_session` already solves this** — membership in that per-tick map IS the
  exact answer (a session is in it only because a real codex process holding a real
  rollout resolved to that tmux session this tick), and the same lookup hands you the
  `CodexSession` for ctx. Hold it in a `self._codex` field refreshed in `build_rows`,
  mirroring `_refresh_claude_status` / `_claude_status` exactly. Live, exact,
  self-correcting, no schema change, nothing to migrate. Proven live:

  ```
  livespec3                 pane_cmd='bun'     is_codex=True    <-- a pane check would miss/over-match
  livespec2                 pane_cmd='claude'  is_codex=False
  livespec-autonomous-mode  pane_cmd='claude'  is_codex=False
  ```
- **`adopt` should take the triple, not grow a branch.** `map_codex_sessions` deliberately
  emits `claude_sessions.map_named_sessions`'s shape: extract the common body of
  `adopt_sessions` and feed it both sources, so the two runtimes cannot drift.
- **Companion tasks filter themselves.** `Codex Companion Task: …` names fail the "is this
  an ACTIVE plan topic?" test — no filter needed anywhere.
- **Busy needs nothing new.** `has_active_subshell` is the runtime-agnostic fallback the
  daemon already uses when `claude_status is None` — exactly the Codex case. VERIFY live.
- **Ctx** — feed `rollout_ctx_remaining` in where `parse_ctx_remaining` is used for a codex
  track (same `int | None` contract, so `_effective_ctx` and every band work unchanged).
  The rollout path is `open_rollout_id`'s source fd; keep the ~5 ms tail read per tick.
- **The one open MAINTAINER decision (do NOT self-resolve):** should a Codex track be
  **restartable**, or **monitor-only**, in v1? The cardinal rule already answers the
  safety half runtime-agnostically — never restart without a `ready` declaration, which a
  Codex session writes to the same `.overseer-state`. `codex resume <topic> "<kick>"`
  makes restart genuinely possible (it takes the kick as an ARGUMENT — no `send-keys`
  paste — and reattaches the SAME named session, so adoptability survives). Monitor-only's
  only argument is a smaller blast radius. Was asked and NOT yet answered; until it is,
  build monitor-only and SURFACE a ready Codex track (notify-never-block) rather than
  restarting it.

The original design follows; it remains accurate except that it records the read as
unbuilt and Ctx%/restart as unavailable (both corrected above and in `research/`).

### The original BUILD-READY design (de-risked 2026-07-16)

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
4. **Ctx% + restart (SAFETY-CRITICAL).** **The restart path MUST be gated Claude-only.**
   `_do_restart` launches `claude --dangerously-skip-permissions -n <topic>`; running that
   against a Codex pane would replace the codex session with a claude one — destructive and
   wrong. The `ready` branch of `evaluate` must NOT reach the CURRENT `_do_restart` for a
   codex-runtime track. Gate on the mapping's runtime marker, and TEST it explicitly (a
   Codex track that declares `ready` must NOT restart it as claude). This is the one place a
   bug is dangerous — get it right.

   **Two corrections to this item's earlier reading — see
   `research/codex-ctx-and-restart-evidence.md` for the live evidence.** Both EXPAND what a
   Codex track can do; neither weakens the gate above, which stands as written.

   - **Ctx% IS readable — it does not need the statusline.** True: Codex renders no
     `Ctx: N% left`, so `parse_ctx_remaining` finds nothing. But ctx comes from the ROLLOUT
     FILE THIS DESIGN ALREADY OPENS: its `token_count` events carry
     `last_token_usage.total_tokens` + `model_context_window`, so
     `ctx_left% = 1 − total_tokens / model_context_window` (verified: 35.8% left on a live
     session). Read the LAST such record. This is a BETTER source than the Claude path — a
     number from a file, not a regex over rendered terminal text. It matters because the
     wrap-up is the daemon's core lever now that nothing is force-killed: a wrap-up-less
     Codex track is a passenger that runs to exhaustion and wedges exactly like the original
     bug. With ctx readable, a Codex track gets the escalation and declares
     `ready`/`winding-down` like any other. (`token_count` payloads are counters, not
     conversation content — parse those, ignore every other record type, per the secrets
     caution below.)
   - **Restart is POSSIBLE, so monitor-only is a v1 SCOPE CALL, not a property of Codex.**
     `codex resume [SESSION_ID] [PROMPT]` takes *"Session id (UUID) or session name"* plus an
     optional prompt, so the analogue is
     `codex resume <topic> "read <repo>/plan/<topic>/handoff.md and follow it"` — cleaner
     than the Claude path twice over: the kick is an ARGUMENT (no `send-keys` paste, no
     paste-race), and `resume` reattaches the SAME named session so `thread_name` (hence
     adoptability) survives by construction. The durable shape is therefore
     **runtime-dispatched restart** — the gate SELECTS the command for the track's runtime —
     with v1 free to leave the codex arm unimplemented. Identical safety today, without
     baking "never" into the design.

   **Precondition worth stating up front:** the index is sparse — only **67 of 259** rollout
   files appear in `session_index.jsonl`, because only NAMED sessions are indexed; an
   unnamed session carries no topic anywhere. Step 4 already fails those closed, so it costs
   nothing, but it means Codex adoption depends on a naming convention exactly as Claude's
   does via `claude -n <topic>`.

**A Codex track** then adopts and shows `working` / `idle` / `blocked:human` like a Claude
track (busy via the shell-walk; `blocked:` via the state file if the codex session writes
one — the idle-nudge's `blocked:` escape already applies). Per the corrections above it CAN
get the wrap-up (ctx is readable from the rollout); whether v1 also restarts it is the open
scope call — until that arm exists, it is never restarted.

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
