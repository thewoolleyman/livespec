# Handoff — the overseer never restarts a session that has not declared itself ready

**LATEST (2026-07-17): Codex tracks are FULL CITIZENS — shipped, merged, and live.**
PR #1308 (commits `31fb34cb` + `c1aed0a4`) retired monitor-only: a Codex track now gets
the escalating wrap-up AND is auto-restarted on its own `ready` via
`codex resume --dangerously-bypass-approvals-and-sandbox <id>` (never the claude command).
Proven live on a throwaway Codex TUI, wired-functions live-exercised, both Fable reviews
clean (no blockers), daemon respawned onto the merged code and the new Codex gate
detection confirmed live. The `livespec-overseer` daemon (top pane) is running this code
as of 2026-07-17 21:11. See OPEN decision #1 and known-defects #1–#3 below (all RESOLVED),
and `research/codex-ctx-and-restart-evidence.md` §"2026-07-17". The cardinal rule and the
5 must-not-regress properties were independently re-verified intact.

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

**Codex detection is BUILT, WIRED, adversarially reviewed, and PROVEN LIVE. The row
taxonomy is settled.** Everything below "Standing operational notes" is reference.

### FIRST: land PR #1296, then RESPAWN THE DAEMON

- **PR #1296** (`feat/overseer-codex-session-discovery`) was OPEN at hand-off, rebased
  clean on master, 246 beside-tests green, auto-merge armed. **Confirm it merged.** It is
  the whole Codex feature. If it did not merge, read its CI failure — do NOT rebuild it.
- **Then respawn the daemon.** It keeps whatever code it started with, so the Codex rows
  stay `unassigned` until it restarts. Command is in Standing operational notes below.
  (It was respawned 2026-07-17 onto the session-gone fixes; it does NOT yet carry #1296.)

### The state of things (2026-07-16/17)

**MERGED:** #1291 (§4 corrections) · #1293 (exited-to-shell) · #1295 (tmux=None + void
outlived `blocked:`) · #1298 (handoff) · #1299 (deleted `not-claude`).

**The row taxonomy is now settled, maintainer-declared — do not re-litigate it:**

| status | means |
|---|---|
| `unassigned` | we have **NEVER** seen a session for this plan |
| `session-gone` | it **WAS** assigned to something; now it is in no tmux. Red, in NEEDS YOU |
| `live-outside-tmux` | a live Claude for the topic runs with NO tmux pane — alive but unmanageable |

- **Neither names a tmux session** (`tmux=None`). The daemon lists PLANS, not panes: a
  tmux name reaches the table only as a mapping row's column value, and naming a bare
  terminal (`livespec1`) was the original complaint.
- **The MAPPING ROW is the memory of "we have ever seen it"** — that is the ONLY thing
  separating the two states, so a dead mapping is **KEPT, never pruned**. (I built pruning
  first; the maintainer reversed it. Pruning would erase the evidence and silently demote
  a died-on-us track to look like one that never started.)
- **`not-claude` is DELETED. Do not reintroduce it.** It was the identity gate's return
  value leaking into the UI — it named a check's output, not anything an operator needs.
  The gate itself is unchanged and still guards every act.

### Codex detection — what shipped (PR #1296)

`codex_sessions.py` (the Codex twin of `claude_sessions`) + the `supervisor.py` wiring.
Proven live on the real fleet, both tracks the maintainer named:

```
BEFORE: unassigned  rop-sweep-library-checks     —                     —
        unassigned  rop-sweep-consumer-cleanup   —                     —
AFTER:  idle        rop-sweep-library-checks     livespec-dev-tooling  66%   (TUI 66%)
        idle        rop-sweep-consumer-cleanup   livespec3             38%   (TUI 38%)
```

**The join is exact, not a heuristic:** a codex process holds its own rollout file OPEN,
and the FILENAME embeds the session id → `session_index.jsonl` → `thread_name` = the plan
topic; `/proc/<pid>/cwd` = the repo. `resolve_tmux_session` was already runtime-agnostic.

**Five things that MUST NOT regress** (each pinned by a test; each cost real effort):

1. **Identity is PANE-scoped, not session-scoped** (`_is_codex_track` takes `target`).
   Adversarial review found that session-scoping let ANY codex in a Claude track's tmux
   session (e.g. `codex resume <topic>` spawned from that session's own Bash tool)
   reclassify the live CLAUDE track as monitor-only — silently killing its wrap-up, its
   NOT-RESPONDING alert and its restart, invisible in NEEDS YOU. Worst failure possible.
   Identity needs BOTH the exact session-map hit AND the target pane's own command.
2. **`start` fails closed on PROOF OF DEATH** (`if not signals.pane_is_shell(cmd)`), not
   on "is it a live Claude?". The old test knew one runtime, so a live codex pane (`bun`)
   failed it and got respawn-KILLED. Enumerating live runtimes does not scale; demand a
   shell.
3. **Ctx comes from each runtime's OWN statusline** — `parse_ctx_remaining` matches BOTH
   `Ctx: N% left` (Claude) and `Context N% left` (Codex). An earlier cut computed Codex's
   ctx from rollout `token_count` events and was WRONG by 2-4 points (62 vs 66, 36 vs 38)
   because it reimplemented codex-rs's private occupancy formula (~12k baseline, reasoning
   excluded). **Never reintroduce a local occupancy formula.** `codex_sessions.py` now
   never reads a rollout body at all.
4. **A Codex track is MONITOR-ONLY and is NEVER restarted with the claude command.**
   `_do_restart` runs `claude --dangerously-skip-permissions -n <topic>`; aimed at a codex
   pane it destroys the session. `test_an_ADOPTED_codex_track_declaring_ready_is_never_restarted`
   is the guard — **verified to have teeth by sabotage** (disable the gate, it goes red).
   Its predecessor went VACUOUS when Codex was wired and passed for the old reason; if you
   change this area, re-sabotage to confirm the guard still bites.
5. **Identity derives; nothing is stored.** No `runtime` field on the mapping. The pane
   command for a codex pane is **`bun`** (the launcher; the codex binary is its child) and
   `bun` matches any bun app — `pane_is_codex` is deliberately loose and MUST NEVER gate
   alone.

### OPEN — maintainer decisions (do NOT self-resolve)

1. **Codex restartable, or monitor-only? — RESOLVED 2026-07-17: FULL CITIZEN, shipped
   (PR #1308, merged; commits `31fb34cb` + `c1aed0a4`).** Monitor-only is RETIRED. A Codex
   track now receives the escalating wrap-up AND is auto-restarted on its own `ready` via
   `codex resume --dangerously-bypass-approvals-and-sandbox <session-id> "<kick>"`
   (`_do_codex_restart` / `_codex_launch_command`) — NEVER the claude command (the one
   destructive bug, pinned by a sabotage-verified guard). The autonomy flag is the codex
   twin of the Claude path's `--dangerously-skip-permissions` (maintainer-chosen full
   bypass). Proven live first on a throwaway Codex TUI (`codex resume` reattaches the SAME
   session — rollout id preserved → re-adoptable — and auto-submits the kick), then the
   wired functions live-exercised, then the daemon respawned onto the merged code and the
   new Codex gate detection confirmed live (`codex-yolo-sandbox` correctly reported
   `blocked:human` at a `›` picker). Two independent Fable reviews: no blockers. See
   `research/codex-ctx-and-restart-evidence.md` §"2026-07-17".
2. **Does `vps-info` belong in the fleet?** It has `plan/dolt-backup-missing-secret/` but
   is absent from `.livespec-fleet-manifest.jsonc`, so it is unwatched. **Independently: a
   live Claude session there is `waiting` on the human right now** (`tmux switch-client -t
   vps-info`), invisible to the fleet view. Note its session is named `vps-info-7e`, not
   the topic — so registering the repo alone would NOT adopt it.

### OPEN — known defects (defects #1–#3 RESOLVED by the full-citizen change 2026-07-17)

1. **RESOLVED (PR #1308).** ~~The codex `ready` alert arm is effectively DEAD CODE~~ — the
   wrap-up now reaches codex (the `elif is_codex:` monitor-only branch is gone), so it
   writes the injection stamp and `ready_valid` becomes reachable for a codex track; its
   `ready` now drives a real `codex resume` restart, not a plain `idle`.
2. **RESOLVED (PR #1308).** ~~Doc/code contradiction (ctx read "lets a Codex track receive
   the wrap-up" but monitor-only means it never does)~~ — a Codex track NOW receives the
   wrap-up, so the claim is true; the passenger-runs-to-exhaustion behaviour is retired.
3. **RESOLVED (PR #1308).** ~~AGENTS.md stale vs shipped code~~ — audited against the
   shipped code (Fable-reviewed): the `not_claude` node/paragraphs/TOCTOU/colour bullet are
   corrected (deleted-status), the Codex-ctx section rewritten (statusline, not the removed
   `rollout_ctx_remaining`), and the `adopt_sessions` docstring fixed (codex IS adopted).
   The `--warn-percent`/"four modules" pre-existing inaccuracies were fixed too.
4. **Two codex sessions in one tmux session (STILL OPEN):** `codex_by_tmux_session` keeps
   first-by-pid, so the second shadows the first → that track silently loses ctx +
   monitoring. Safe, but a monitoring outage.
5. **`recover_missing_sessions` is Claude-only (STILL OPEN, now DOCUMENTED):** startup
   recovery re-launches the CLAUDE command, so a codex track that died while the daemon was
   DOWN would be recreated as claude (rollout orphaned) — non-destructive (only ABSENT
   sessions are recreated), unavoidable under runtime-derived-live (a dead codex has no
   live rollout id at recovery). Documented in the `recover_missing_sessions` docstring; a
   real fix needs a codex-session-store lookup by `thread_name`. While the daemon is UP the
   per-tick restart path DOES dispatch by runtime.
6. **The beside-tests now touch the REAL `/proc` and `~/.codex`** via default kwargs in
   adopt/refresh. Deterministic today (tmp cwds cannot match fleet repos), but a real host
   coupling in a unit suite.
7. **`livespec-p9s0`** (ledger, P1, NOT overseer): the cross-repo wiring check reads
   siblings' LOCAL clones, so a stale clone flaps phantom drift. Hit live this session and
   worked around by fast-forwarding the clone.

### Method notes worth keeping

- **The beside-tests are the ONLY gate on this folder.** Always
  `uv run pytest .claude/skills/overseer/ -q` before pushing.
- **Sabotage your safety tests.** Both times a guard mattered here it was verified by
  breaking the thing it guards and watching it go red. One guard was silently vacuous and
  only sabotage revealed it.
- **Adversarial review earns its keep on this daemon.** Three independent Fable reviewers
  refuted the Codex work twice and produced the ctx numbers; every finding above with
  "adversarial review" attached was something the author (me) missed.

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
