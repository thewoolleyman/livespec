# Overseer — maintenance guide (for the developer editing it)

This is guidance for **editing the overseer**, not for running it. It is a
DIFFERENT document from `SKILL.md`:

- `SKILL.md` = the overseer **at runtime** ("when invoked, do X").
- this file = guidance for the developer **changing** the overseer ("when you
  change X, preserve invariant Y, watch gotcha Z, verify via W").

The overseer is a **deterministic multi-track supervisor**: a stdlib-Python
daemon (`supervisor.py`, the top pane) that watches parallel livespec plan
tracks across tmux sessions, plus a thin interactive Claude bottom pane
(`SKILL.md`). The daemon acts and renders a live table; it holds NO semantic
judgment. Every "am I done / blocked?" decision is made by the tracked
session's own LLM and expressed out-of-band on the filesystem — ONE state file
(`<repo>/tmp/overseer/<topic>/.overseer-state`) holding one of three values
(`ready` / `blocked: <reason>` / `winding-down`); the daemon only pattern-matches
deterministic tmux signals and that file.

## Why it exists / history

Two prior failure modes shaped this design, and they MUST NOT recur:

1. **Inline-worker context blowup.** A session ran the overseer window as an
   inline worker (did the track work itself), blew up its own context, and
   autocompacted. → The mechanics now run in a dumb, token-free Python process
   that cannot blow up a context; the interactive pane stays thin.
2. **Frozen top-pane snapshot.** A `/clear` does not kill tmux panes, so a prior
   overseer's dashboard kept rendering an hours-old "everything idle" snapshot
   while nothing was live. → The table is re-rendered from live captures every
   tick (and time-stamped), so it can never freeze on a stale snapshot.

Status: **PERMANENT** — a human-supervised alternate to autonomous mode (the
Beads/Dolt + Fabro Dispatcher / dark factory), not a stopgap awaiting a
replacement. The two are standing peers: autonomous mode runs *ready work-items*
unattended through the ledger; the overseer keeps *interactive plan tracks*
moving in parallel under a human driver, automating only the context-% wrap-up +
restart mechanics. Maintain it in place. **LOCAL-ONLY and unsynced:** it lives
under `.claude/skills/overseer/` in this repo only and is usable only from it. Do
NOT add it to the plugin, the spec, the copier template, fleet manifests,
conformance checks, or any other repo.

## The evaluate() state machine

`Supervisor.evaluate(track)` re-classifies each tracked session **from scratch
every tick** into exactly one status. Its only inputs are the pane capture, the
parsed `Ctx: N% left`, Claude's registry `status`, and the out-of-band
`.overseer-state` file (`ready` / `blocked` / `winding-down`, all
**session-written**). It is a **precedence cascade** — the FIRST matching guard
wins — not a persistent FSM: a session moves between statuses only by changing
those inputs (its own work, its own declaration, its context dropping). The
per-state side-effects (after the `·`) and the `(act)` guard fire ONLY when
`act=True` (the daemon loop); the read-only `list` path (`act=False`) classifies
without acting.

```mermaid
stateDiagram-v2
    direction TB

    [*] --> tick
    state "evaluate(track) — one tick" as tick

    tick --> unassigned: is_unassigned
    tick --> cGone: no managed pane (gone / foreign / shell)
    tick --> cBusy: live and ours

    state cGone <<choice>>
    cGone --> live_outside_tmux: live Claude, no tmux
    cGone --> session_gone: no live Claude

    state cBusy <<choice>>
    cBusy --> working: busy
    cBusy --> cGate: not busy

    state cGate <<choice>>
    cGate --> blocked_human: gate or 'blocked'
    cGate --> cIdle: neither

    state cIdle <<choice>>
    cIdle --> settling: not idle-prompt
    cIdle --> cStream: empty idle prompt

    state cStream <<choice>>
    cStream --> working: still streaming (act)
    cStream --> cReady: settled

    state cReady <<choice>>
    cReady --> restarting: fresh 'ready'
    cReady --> cCtx: no valid ready

    state cCtx <<choice>>
    cCtx --> cBand: eff_ctx ≤ threshold
    cCtx --> cRoom: above threshold

    state cRoom <<choice>>
    cRoom --> idle_ctx_left: free to continue
    cRoom --> idle: Claude 'waiting' / prior declaration

    state cBand <<choice>>
    cBand --> winding_down: fresh ACK
    cBand --> danger: eff_ctx ≤ 20
    cBand --> warned: otherwise

    working: working  ·  voids stale ready + blocked
    blocked_human: blocked:human  ·  alerts operator
    settling: settling  ·  wait, re-read next tick
    restarting: restarting  ·  _do_restart (ONLY path; runtime-dispatched claude/codex)
    warned: warned  ·  injects escalating wrap-up
    danger: danger  ·  alerts NOT RESPONDING, never restarts
    winding_down: winding-down  ·  ACK, stop re-warning
    idle_ctx_left: idle-with-context-left  ·  one keep-going nudge
    live_outside_tmux: live-outside-tmux  ·  unmanaged, not an alarm

    note right of idle_ctx_left
      One "keep going" nudge per idle episode. The daemon WRITES the
      idle-with-context-left marker to edge-trigger the nudge (its only
      self-authored token) and clears it when the session next goes
      non-idle, re-arming a later episode. A session genuinely waiting on
      a human writes `blocked: &lt;reason&gt;` instead.
    end note

    note right of restarting
      THE CARDINAL RULE: a respawn is reachable ONLY via a fresh
      session-written 'ready'. The daemon never infers it from
      idleness, a timer, or how low ctx has fallen.
    end note
```

Every branch is a leaf: the tick ends there and the next tick re-enters
`evaluate()` from the top. The cross-tick lifecycle a session actually walks is
`working → … → warned` (daemon injects the wrap-up) `→ winding-down` (session
ACKs) `→ restarting` (session declares `ready`) `→` a fresh `working` after the
respawn — each arrow driven by the SESSION's own declaration, never a daemon
guess. `unassigned` / `session_gone` / `live_outside_tmux` are structural pre-checks
(no live managed pane to read); `settling` is a one-tick "wait and re-read". The
diagram is drawn Claude-first, but **a Codex track is a full citizen
(maintainer-declared 2026-07-17)** and flows through the SAME branches with
runtime-appropriate mechanics: `is_codex_idle_input` (not Claude's `❯` box) drives its
`idle`, the wrap-up and keep-going nudge are pasted with a Codex submit-verify (the pane
goes busy, not an emptied `❯` box), and `restarting` dispatches to `codex resume <id>`
rather than the claude launch command (see invariant 7 and the load-bearing mechanics).
The `cGone` choice splits the no-managed-pane case: when there
is no pane the daemon can drive but a live Claude registry session for the topic is
running with NO tmux pane (a bare SSH shell), the row is the informational
`live-outside-tmux` (alive, but the daemon cannot capture/inject/respawn it) — NOT
the alarming `session-gone`, and it is kept out of the `NEEDS YOU` block. A live
session that resolves to a DIFFERENT tmux session stays `session-gone` (re-mapping
is a separate concern; `_live_session_outside_tmux`).

**`cGone` is reached THREE ways, and they must answer identically
(`_no_managed_pane_row`; 2026-07-16).** The mapped tmux session is gone; OR it survives
but its Claude **exited to a bare shell** (the ordinary end of a track's life); OR the
mapping points at a genuinely FOREIGN pane (another program, a Claude in a different
repo). All three are the same fact about the track — no pane the daemon can drive — so
all three route through the one helper (`session-gone`, or `live-outside-tmux` when a
live session for the topic runs with no tmux pane); only tmux housekeeping differs.
**`not_claude` is DELETED (maintainer-declared 2026-07-17: "What the hell is
not-claude?").** It was the identity gate's return value leaking into the UI — it named a
check's output, not anything an operator needs — and it made a bare terminal (`livespec1`)
look like a tracked pane. Do NOT reintroduce it. The identity gate (`_pane_is_managed`,
covering BOTH runtimes) is unchanged and still governs every ACT — the change was purely
what the operator is TOLD, never a relaxation; a shell / foreign pane is still never
pasted into. **Why it mattered:** reporting an exited-to-shell track as `not-claude` left
finished tracks sitting red in `NEEDS YOU` claiming a live tmux mapping (found live
2026-07-16: `fabro-ci-image-factoring` → `livespec1`, a bare zsh), and it skipped the
live-outside-tmux fallback entirely — hiding a Claude alive outside tmux behind an alarm.

Reading notes: `threshold` = the track's `ctx_threshold` override, else the
daemon-wide `warn_percent` (default 50). A malformed `.overseer-state` token is
surfaced as a row note and treated as **no declaration** (fail-closed) — it never
authorizes an ACT (restart / injection), though it is not inert: the `BAD state file`
note puts the row in `NEEDS YOU`, and (being a non-null `declared`) it suppresses the
keep-going nudge on an idle-above-threshold session, which then renders plain `idle`
(both the safe direction). Two act-only guards are folded for clarity: `cStream →
working` (drawn) skips a tick when an "idle" frame is still streaming, and an
identical post-settle identity re-check (not drawn) routes a pane that has
exited to a shell to `settling` (a one-tick "the pane changed under us"; the next
tick re-enters at the top gate and renders the settled `session-gone`). The `cRoom`
choice guards the
`idle-with-context-left` nudge: an idle session ABOVE threshold reaches it, and
takes the `idle_ctx_left` leg only when it is not `waiting` on a human and has
made no declaration of its own (or already carries the marker — so the nudge is
sent once, not every tick); otherwise it is a plain `idle` leaf. See invariant 9
for the marker's edge-triggered lifecycle.

## Architecture invariants that must not regress

1. **The supervisor owns mechanics only.** Semantic judgment ("am I done / am I
   blocked?") stays in the tracked session's LLM, expressed via the **out-of-band
   state file** — NEVER inferred from printed pane text (prompt-echo, model
   quotation, scroll, and line-wrap all corrupt pane text; see the adversarial
   review). If you ever find yourself parsing a "the session says it's done"
   sentinel out of a pane capture, stop — that is the exact anti-pattern the
   state-file protocol replaced.

   **The overseer NEVER touches files under `plan/`.** It touches ONLY its own
   config (the mapping store, the injection-stamp sidecar, the watch-set declaration)
   and temp files (`<repo>/tmp/overseer/<topic>/`). A session's `handoff.md` and
   everything else under `plan/<topic>/` is the SESSION's own workflow — the
   overseer never reads, writes, or hashes it. Discovery enumerates `plan/*/`
   DIRECTORIES only; the resume line *points* the session at the conventional
   `plan/<topic>/handoff.md` but never opens it; markers live under `tmp/`, never
   `plan/`. The daemon `git check-ignore`-validates each watched repo's
   `tmp/overseer/` at startup (`Supervisor.unignored_tmp_repos`) and REFUSES to
   run if any is not gitignored, so a marker can never dirty a tracked tree. If
   you ever add code that opens, writes, or stats a FILE under `plan/`, stop —
   that violates this invariant.
2. **The overseer stays thin.** The interactive bottom pane never does track
   work inline and never polls the tracked sessions from the Claude pane on a
   timer. Watching is the daemon's job.
3. **Surface-only for UNASSIGNED plans.** The daemon NEVER auto-spawns a session
   for a plan that has none. Launching a plan is a deliberate act (`start`,
   user-initiated); a discovered plan with no session shows as `unassigned`,
   flagged ready to start — never started automatically. This scopes the FIRST
   launch ONLY. It is a DIFFERENT rule from invariant 7 (which governs whether an
   ALREADY-TRACKED session may be restarted, and answers: only on its own `ready`
   declaration). Neither one licenses the other: "surface-only" is not a reason to
   ignore a `ready` declaration, and invariant 7 is not a reason to spawn a
   session for an unassigned plan.
4. **Discovery-driven list; JSONL = mapping only.** The track list is
   re-discovered from each watched repo's `plan/*/` every tick. The JSONL store
   (`~/.livespec-overseer.jsonl`) holds ONLY facts that cannot be rederived from
   the filesystem (topic↔tmux mapping, custom resume line, threshold override).
   Do NOT regress to a hand-maintained plan list.
5. **Cross-repo by construction; sessions are named after the BARE plan topic
   (maintainer-declared 2026-07-19).** Rows are repo-scoped, but a tmux session is
   named after its **bare plan topic** (`registry.tmux_id` → `<topic>`), because
   that is the name the operator reads and navigates by — NOT the old
   repo-qualified `<repo-slug>--<topic>`. A repo prefix is added ONLY on a genuine
   cross-repo collision — when the SAME topic exists in ≥2 watched repos
   (`registry.colliding_topics`, computed from discovery) — and then as
   `<repo-slug>-<topic>` with a **single** dash (the double-dash form is retired).
   tmux session names are global while topics are unique only per repo, so the
   single-dash prefix disambiguates exactly the clashing topics and nothing else.
   The collision set is recomputed each tick and cached on `self._colliding` (set at
   the top of `build_rows`, before adopt / auto_link / evaluate), and threaded into
   every session-name derivation (`_session_of`, `auto_link`) plus the CLI
   (`_cli_colliding` for `add` / `start`) so a session is named identically wherever
   it is derived. Never hardcode `/data/projects/livespec`. The daemon's per-tick
   `auto_link` links a live session to a discovered plan ONLY when the derived
   session (bare topic, or `<slug>-<topic>` on collision) exists AND its
   `#{pane_current_path}` resolves inside the row's repo — the cwd check, not the
   name, is what prevents two repos sharing a topic from cross-linking.
6. **Two-pane bootstrap + `adopt` (the `/overseer` startup, 2026-07-13).** The
   skill runs the `overseer-start` executable FIRST — and ONLY the skill does:
   it is skill-invoked (by Claude's Bash tool), never a standalone launcher, and
   does NOT start Claude (it splits the daemon pane beside the SAME Claude session
   that ran `/overseer`, which then resumes in the bottom pane). So it REFUSES
   before splitting unless `$CLAUDECODE` is set (the marker Claude Code exports in
   every Bash-tool shell) — a hand-run from a plain terminal would otherwise leave
   a daemon pane + a bare-shell bottom pane (no Claude), the exact broken state
   that guard prevents. It (a) detects the skill's OWN pane via `$TMUX_PANE`
   (Claude Code inherits it — do NOT re-derive tmux membership by hand; that
   improvisation is what falsely reported "not inside a tmux window" and grabbed a
   separate session), (b) splits THAT window
   (`tmuxio.split_window_top` targeting `$TMUX_PANE`, idempotent via a pane titled
   `overseer-daemon`) to run `overseerd` in a TOP pane while focus stays on the
   bottom pane, and (c) runs `Supervisor.adopt_sessions`. **`adopt` matches each
   live Claude session's registry `name`** — NOT the tmux session name (those are
   generic: `livespec`, `livespec1`), NOT the `#{pane_title}` terminal title
   (Claude DRIFTS it to a task summary), and NOT a screen-scrape of the input-box
   border (which vanishes whenever the pane shows a prompt — the failure that
   retired the border scrape). Claude Code writes each session's display `name` +
   `cwd` (+ live `status`) to `~/.claude/sessions/<pid>.json`; the maintainer's
   sessions run `claude --dangerously-skip-permissions` and are renamed at runtime,
   so the name is ONLY in that registry, never argv. `claude_sessions.py` reads the
   registry (keeping live PIDs — alive AND `/proc` start-time == recorded
   `procStart`, defeating PID reuse) and joins each to its tmux session by walking
   the claude PID up to a tmux pane PID (`tmuxio.pane_pid_sessions`). A session is
   adopted when its registry `cwd` is in a fleet repo AND its `name` is an ACTIVE
   discovered topic there; registry membership already proves it is a Claude
   process, so there is no worker-command guard. **Adopt runs EVERY tick** (in
   `build_rows(act=True)`), not just at bootstrap — so a session that was mid-prompt,
   renamed, or launched later is picked up within one interval (the fix for "the
   daemon never re-adopted after the prompt cleared"). It maps to the bare session
   name (`tmux == session`), never double-adds, and — distinct from invariant 5's
   `auto_link`, which links only the `registry.tmux_id` session the daemon itself
   launches (the bare topic, or `<repo-slug>-<topic>` on a cross-repo collision).
   **Codex sessions ARE adopted the same tick, through the
   SAME code path** (`adopt_sessions` sums `claude_sessions.map_named_sessions(...)` +
   `codex_sessions.map_codex_sessions(...)`, both emitting the `(tmux, name, cwd)` triple)
   — they are not in Claude's registry, but `codex_sessions.py` supplies the equivalent
   join (see the next bullet). (Per-session pane reads —
   `pane_id`/`pane_current_command`/`pane_current_path` — go through `list-panes`, not the
   flaky-for-detached-sessions `display-message`.)

   **Codex session discovery (`codex_sessions.py`; 2026-07-16).** The Codex twin of
   `claude_sessions`, returning the same `pid` / `name` (= the plan topic) / `cwd`
   shape so adoption can treat both runtimes uniformly. Codex keeps no pid-keyed
   registry, which is why this looked like the hard part — but a running codex
   process **holds its own rollout file OPEN**, and the rollout FILENAME embeds the
   session id, which `session_index.jsonl` maps to the `thread_name`:
   `pid --comm=="codex"--> /proc/<pid>/fd/* --> rollout-<ts>-<id>.jsonl --> id
   --index--> thread_name`, with `/proc/<pid>/cwd` giving the repo. **Exact, not a
   heuristic** — no cwd+recency guessing. `claude_sessions.resolve_tmux_session` is
   already runtime-agnostic and joins the pid to its tmux session unchanged.
   Load-bearing details, each pinned by a beside-test:
   - **Only NAMED sessions are indexed** (67 of 259 rollouts, live) — an unnamed
     session carries no topic anywhere and is dropped. Codex adoption depends on a
     naming convention exactly as Claude's does via `claude -n <topic>`. This is the
     one real precondition; it is not a defect to engineer around.
   - **`comm == "codex"`, and an open rollout is REQUIRED.** The `bun` launcher is
     the codex process's PARENT and holds NO rollout fd, so the fd requirement
     excludes it structurally.
   - **No `procStart` liveness check is needed** (unlike Claude's registry, whose
     files outlive their process): the pid came from a `/proc` scan this instant and
     must still hold an open rollout — a fd cannot go stale.
   - **`Codex Companion Task: …` threads are NOT filtered here** (38 of 69 index
     records) — they fail the "is this an ACTIVE plan topic?" test at adoption, so
     the noise filters itself and the module stays a pure, dumb join with no policy.
   - **The join NEVER reads a rollout's contents** — rollouts are full session
     transcripts. `codex_sessions.py` needs only the filename + `/proc`; it opens NO
     rollout body at all. (Keep it that way — see the Ctx% note.)

   **Codex Ctx% comes from the STATUSLINE, NOT the rollout (2026-07-16, corrected).**
   Codex renders `Context N% left` in its statusline (verified live) — its OWN computed
   number — and `signals.parse_ctx_remaining` reads it exactly as it reads Claude's
   `Ctx: N% left` (`_CTX_RE` matches BOTH forms), so Codex needs NO ctx code of its own.
   An earlier cut computed ctx from the rollout's `token_count` events
   (`rollout_ctx_remaining`) and was **WRONG by 2–4 points** against Codex's own display,
   because it reimplemented codex-rs's private occupancy formula (subtracts a ~12k
   baseline, excludes reasoning tokens) — an internal that drifts with any Codex release.
   That function was REMOVED; `codex_sessions.py` reads no rollout body. **Never
   reintroduce a local occupancy formula.** This matters because the escalating wrap-up is
   the daemon's ONLY lever now that nothing is force-killed — and a Codex track now
   RECEIVES that wrap-up (and is restarted on `ready`) as a full citizen; it is no longer
   a monitor-only passenger (see invariant 7 and the load-bearing mechanics below).
7. **THE CARDINAL RULE — never restart a session that has not declared itself
   `ready` (maintainer-declared 2026-07-14).** The session's own `ready`
   declaration in its state file (`signals.ready_valid`) is the **SOLE**
   authorization for a restart, and `Supervisor._do_restart` has exactly ONE
   caller: the `ready` branch of `evaluate`. The daemon NEVER infers readiness —
   not from idleness, not from a timer, not from how low the context has fallen.

   **Why this is a correctness rule, not a courtesy.** A timer cannot know whether
   a session is safe to kill. **"Idle + settled" is NOT "at a safe stopping
   point"**: a session can be idle while a background build runs, while a sub-agent
   works, or while it waits on a human in another pane. Only the session knows, so
   only the session may authorize the restart. A session that declares NOTHING is
   **reported to the human as not responding** (`_alert_non_responder`) and
   otherwise **left alone** — that is a bug in the SESSION (which was told,
   escalatingly, exactly what to write), never a licence for the daemon to guess.

   **This REPLACED a previously-shipped invariant that said the opposite.** An
   earlier version of this list asserted the auto-restart was NON-NEGOTIABLE and
   that a warned track stalling idle at the danger line was **FORCE-restarted**
   after a grace (`_danger_or_force_restart` / `_STALL_RESTART_GRACE` /
   `_InjectState.danger_idle_since`). That was a **severe bug** — the daemon killed
   sessions it had no way to prove were safe to kill — and all of it is **deleted
   from the code**. If you find yourself re-adding a timer, a grace, or any
   daemon-side judgment that ends in a respawn, STOP: you are reintroducing it.

   The restart **mechanics** are unchanged and still required — only the **trigger**
   moved to the session's declaration. `_do_restart` is **RUNTIME-DISPATCHED**
   (`is_codex` selects the arm); the Claude arm is:

   - **(a) exit + restart** — the ATOMIC `respawn-pane -k` (kill the pane's process
     and launch the new one in a single tmux op), NOT a `/exit` followed by a scrape
     for the shell prompt. The `❯` glyph is ambiguously BOTH the Claude idle prompt
     and the zsh prompt, so a mis-timed "the shell is back" would type into the
     still-live session.
   - **(b) `claude --dangerously-skip-permissions -n <topic>`** — BOTH flags are
     required (`Supervisor._launch_command`). Without
     `--dangerously-skip-permissions` the fresh session stalls on its first
     permission prompt and the restart is NOT autonomous, which defeats the whole
     mechanism; `-n <topic>` re-assigns the session name from the plan topic.
   - **(c) the resume line** — `read <repo>/plan/<topic>/handoff.md and follow it`,
     bracketed-pasted AND verify-submitted once the fresh TUI is up
     (`default_resume` + `_submit_prompt`). A `claude "<prompt>"` argv only
     PRE-FILLS the box without submitting — which is why the resume line is pasted
     after launch rather than passed on the command line. **The submit is
     SELF-HEALING (R1, 2026-07-18):** a freshly-respawned TUI can DROP the Enter
     while still drawing its welcome screen, leaving the fresh session live but idle
     with the resume UN-submitted (proven live 2026-07-17 — fabro / autonomous-mode /
     overseer-rewrite each stranded this way, autonomous-mode for 9h until a human
     pressed Enter). So `_do_restart` waits for the box to render first
     (`_await_input_box`) and, if the submit STILL does not land, does NOT clear the
     `ready` marker or log success — it marks a round-scoped `resume_pending`
     (`registry.set_resume_pending`) and alerts. The next tick's `evaluate` intercepts
     the still-open round BEFORE the busy/idle cascade and retries the SUBMIT ONLY
     (`_resend_enter` — re-send Enter, NEVER a re-respawn, so it can never escalate to
     a kill; a fresh `ready` is still the sole respawn trigger), closing the round only
     once the box clears or the pane goes busy. The stranded row stays a NEEDS-YOU
     report (`_RESUME_PENDING_NOTE`) until it resumes. See invariant 7's B5 discipline:
     "is the fresh Claude up?" and "did the resume submit?" are now SEPARATE facts —
     conflating them (the old `_clear_state` + "restarted" log on a failed submit) is
     the exact discarded-marker bug this replaced.

   **The Codex arm (`_do_codex_restart`) is the ONE place the destructive bug lives,
   and the dispatch is what prevents it.** `claude -n <topic>` aimed at a codex pane
   would REPLACE the codex session with a claude one; so a Codex track respawns
   `codex resume --dangerously-bypass-approvals-and-sandbox <session-id> "<resume line>"`
   (`_codex_launch_command`) instead — NEVER the claude command. The
   `--dangerously-bypass-approvals-and-sandbox` flag is the codex twin of the Claude arm's
   REQUIRED `--dangerously-skip-permissions` (maintainer-declared 2026-07-17): without it
   the resumed session uses codex's default INTERACTIVE approval and stalls at a `› 1.`
   approval picker on its first tool call, so the restart is not hands-off (codex documents
   the flag as "solely for externally-sandboxed environments", which this local-only host
   is). It is otherwise SIMPLER than the Claude arm (proven live 2026-07-17): `codex resume`
   takes the kick as an ARGUMENT and AUTO-SUBMITS it, so there is no separate paste (no
   `_submit_prompt`) and no fresh-TUI submit race; and it resumes by the exact UUID, which
   reattaches the SAME rollout so the `thread_name` — hence adoptability — survives by
   construction. The await polls `pane_is_codex` (`_await_pane`) not `pane_is_claude`, and
   the round is closed (`_clear_state`) only after the await CONFIRMS the codex pane came up
   — a failed respawn or await keeps the `ready` marker so the restart retries (B5, pinned
   by the codex marker-kept tests). The sabotage-verified guard test
   (`…never_issues_the_claude_command`) pins that the routing holds; if you touch this
   area, re-sabotage (route codex → the claude command) and confirm it goes red.

   **Reboot recovery is RUNTIME-DISPATCHED (defect #5, 2026-07-18).** `recover_missing_sessions`
   (startup only) no longer always launches the claude command. A dead codex process is absent
   from the live `self._codex` map (no rollout fd at cold start), so the runtime is derived from
   the PERSISTENT codex index instead — `session_index.jsonl` SURVIVES the session's death. If
   the track's TOPIC names a session there (`codex_sessions.latest_session_for_thread_name`, the
   most-recent by `updated_at`), the track is CODEX: `_recover_codex_track` resumes the SAME
   rollout via `codex resume <id>` (option c) when it still exists on disk
   (`codex_sessions.rollout_exists`), else skips + surfaces (option b) — NEVER mis-recreating it
   as claude (rollout-orphaning). A topic absent from the index is a Claude track and recovers as
   before. The `session_exists` gate still means only a genuinely ABSENT session is recreated, so
   no live session is killed. Verified live 2026-07-18: `codex resume` reattached a 26-day-old
   session with its thread_name intact (so the daemon re-adopts it); the reverse-index + rollout
   gate resolve correctly against the real `~/.codex`; the latest-by-`updated_at` pick is
   unambiguous (distinct timestamps per id in real index data). Two interstitials seen live and
   both self-healing (a `› N.` gate → `blocked:human` → operator clears): codex's directory-trust
   prompt appears only for a repo codex has NOT trusted — in recovery `track.repo` is where the
   codex session originally ran, so it is already trusted and the resume is clean; and the
   working-dir picker appears only when the pane cwd ≠ the session's recorded cwd — recovery sets
   cwd to `track.repo`, which matches. See the `recover_missing_sessions` docstring.

   The abrupt kill is safe **because of** the declaration: the session asserted it
   is at a clean stopping point, and `respawn-pane -k` replaces the PROCESS — every
   file, worktree, and commit on disk survives it.

   **With the force-restart gone, the ESCALATION is the only lever.** So it has to
   actually sharpen: `wrapup_message` sends a SUGGESTION above `_INSIST_AT` (30%
   remaining) and an insistent "STOP AND WIND DOWN NOW" at 30 / 20 / 10. Re-sending
   identical text five times is repetition, not escalation. If you touch the wrap-up
   text, keep that gradient — it is load-bearing now.
8. **Notify, never block (maintainer-declared 2026-07-14).** **A question may only
   be asked by the actor that OWNS the decision, and the overseer must NEVER block
   on a question it does not own.** A tracked session's decision belongs to that
   session and is already displayed in ITS pane; re-asking it in the interactive
   bottom pane created a duplicate surface — the maintainer answered in the tracked
   session's pane, the overseer's modal stayed blocking, and the whole console
   wedged on it (a single point of failure). So:

   - **Track decisions → non-blocking TEXT.** The bottom pane relays
     `blocked:human`, a non-responding `danger` track, and a malformed state file as
     reported text; the operator answers **in the tracked session's own pane**. It
     NEVER raises `AskUserQuestion` on a track's behalf.
   - **Overseer-OWNED decisions → `AskUserQuestion` is still right** (add / remove /
     unassign / start a track, a threshold) — nobody else can answer those.
   - **It self-heals.** `blocked:human` is re-derived from the live pane every tick,
     so when the human answers in the tracked pane the alert simply stops. Nothing
     needs to be dismissed.
   - **Therefore every track-scoped alert MUST name WHERE to act.** Because the
     overseer never prompts on a track's behalf, the alert line is the operator's
     ONLY handover, so it must be self-sufficient: plan topic, repo, tmux SESSION,
     PANE, and a copy-pasteable `tmux switch-client -t <session>` jump command. That
     is what `Supervisor._alert` guarantees — route EVERY new track-scoped alert
     through it, never a bare `_surface` with an f-string of `repo::topic` (which
     told the operator WHAT was stuck but not WHERE to go). `_surface` remains for
     DAEMON-level notices with no track coordinates (a failed paste retry, a
     respawn failure, the singleton-lock refusal, the gitignore refusal).
9. **ONE state file with a VALUE — never two presence-markers.** The declaration is
   `<repo>/tmp/overseer/<topic>/.overseer-state`, whose first non-empty line is
   `<token>` or `<token>: <detail>`. There are **three SESSION-written tokens**
   (`ready`, `blocked`, `winding-down` — `signals.STATE_TOKENS`) plus **one
   DAEMON-written token** (`idle-with-context-left` — `signals._DAEMON_TOKENS`);
   `signals.valid_token` accepts either set. The predecessor pair
   `.overseer-ready` + `.overseer-blocked` is GONE: two presence-markers carried a
   built-in ambiguity — nothing stopped BOTH existing, and their precedence was
   incidental rather than designed. One file with a value makes that state
   unrepresentable. A malformed/typo'd token is **surfaced** and treated as **no
   declaration** (fail-closed, `signals.valid_token`); do not "helpfully" coerce or
   fuzzy-match it. If you ever add a second signal file, stop — you are re-creating
   the ambiguity this collapsed.

   **`idle-with-context-left` is the ONE token the daemon writes to itself, and it
   never authorizes a restart.** It is a marker, not a declaration: when a session
   goes idle while still ABOVE the wind-down threshold and is not waiting on a human
   (and has made no `ready`/`blocked`/`winding-down` declaration of its own), the
   daemon sends exactly ONE "keep going, don't stop with context left" nudge and
   stamps this token so it does not re-nudge every tick. **The nudge fires ONLY after
   the session has been CONTINUOUSLY idle for at least `_IDLE_NUDGE_AFTER` (1 hour;
   maintainer-declared 2026-07-18: it was "too aggressive, TOO SOON" and interrupted
   sessions merely between turns).** The continuous-idle clock is in-memory
   (`_InjectState.idle_since`), stamped on the first cleanly-idle tick (empty prompt AND
   not busy — `busy` folds in Claude's registry `busy`/`shell`, so a sub-agent or
   background command resets it) and cleared the moment the session is non-idle; a daemon
   restart resets it, which only ever DELAYS a nudge (the safe direction). The row still
   reads `idle-with-context-left` immediately (descriptive, not an attention status); only
   the keystroke waits for the 1-hour floor. It is EDGE-TRIGGERED: the
   nudge fires once per idle episode, and the daemon CLEARS the token the moment the
   session goes non-idle again (busy / gate / blocked branches call
   `_clear_idle_nudge_state`), re-arming a fresh nudge for a later episode. The
   clear only unlinks the file when it still holds `idle-with-context-left`, so it
   can never clobber a session's own `ready`/`blocked`/`winding-down`. This is NOT a
   crack in the cardinal rule (invariant 7): the marker gates a text NUDGE, never a
   respawn — the sole restart trigger is still a session-written `ready`. The
   nudge's own text tells the session it may instead write `blocked: <reason>` if it
   is genuinely waiting on a human (the escape hatch for a YOLO-mode session that can
   only say so in prose).
10. **The DAEMON owns "what needs attention"; the bottom pane must never be a status
    display (maintainer-declared 2026-07-14).** Current state is rendered ONLY by the
    daemon — the table plus its `NEEDS YOU` block (`Supervisor._attention_lines`,
    `needs_attention`, `ATTENTION_STATUSES`) — because that render is rebuilt from live
    captures every tick and costs no tokens, so it *cannot* go stale and *can* refresh
    forever. An LLM pane can do neither: it prints text ONCE, and that text then ages
    silently.

    **This is the frozen-snapshot failure (history #2) recurring in the other pane.** The
    bottom pane printed "two tracks want you", went idle, and kept showing it while both
    were resolved minutes later; the maintainer acted on a dead report. The original fix
    (re-render each tick + stamp it) had only ever been applied to the top pane.

    The split that resolves it — and that you must not blur:

    - **The table is STATE** (what is true *now*; self-correcting — a resolved track
      disappears from the block on the next tick).
    - **The log is HISTORY** (`tmp/overseer/daemon.log`; what happened and *when*). The
      bottom pane SHOULD know it and its format — answering questions from it is its job
      (maintainer 2026-07-14: "it should still know about the log and its format so it can
      answer questions with its data"). What it must not do is answer *"what needs
      attention?"* from it.

    Consequences that are load-bearing, not cosmetic:

    - **Every log line is timestamped** (`_log` / `_surface` prefix `_iso_now()`) — a
      history you cannot date cannot answer "when?".
    - **Track alerts are EDGE-TRIGGERED** (`_alert`'s `_alerted` dict; re-armed in
      `evaluate` when the row goes healthy). Re-emitting an unchanged alert every tick
      buried the history under thousands of identical lines (a track blocked overnight →
      ~3,000) *and* made `tail`ing the log look like a current-state read, which is the
      bug. If you make alerts repeat per-tick again, you have reintroduced it.
    - **The badge must be able to CLEAR.** `_refresh_window_name` drops back to `overseer`
      when the count is 0 — a badge that could only be set would be one more stale
      indicator.
    - **`unassigned` is not attention.** It is startable, not stuck, and it outnumbers the
      real rows ~10:1; including it re-buries the signal.

    If you find yourself putting the bottom pane on a timer to keep it fresh, STOP: that
    burns tokens forever to duplicate a surface that is already correct and free, and it
    walks back into history #1 (the context-blowing inline worker). The answer is fewer
    LLM refreshes, not more.

## Load-bearing mechanics + gotchas

- **Pane sizing + the window badge (`tmuxio.set_pane_height_percent` / `rename_window`).**
  The daemon pane gets **2/3** of the window (`overseer-start`'s
  `_DAEMON_PANE_HEIGHT_PERCENT = 66`) because it carries the table + `NEEDS YOU` block —
  the surfaces that answer "what needs my attention?"; the bottom pane is a command
  prompt and needs less. `overseer-start` normalizes the stack (`select_layout_even`)
  and THEN resizes, resolving the daemon pane **by title** (`pane_by_title`) so the
  idempotent re-run path — where the pane already existed and its id was never held —
  resizes it too. Percentage sizes (`resize-pane -y 66%`) are a real tmux feature
  (verified on 3.5a), so the split survives a terminal resize without recomputing rows.
  **`rename_window` MUST also set `automatic-rename off`** — tmux otherwise re-derives a
  window's name from its foreground command on the next tick and silently overwrites the
  badge; pinning is part of renaming, not an optional extra.
- **Row color is a TTY-only, whole-LINE affordance (`_row_color` / `_STATUS_COLOR`;
  2026-07-15).** `render` tints each DATA row by its raw status so the operator scans
  the list by hue — green = actively working (`working`/`winding-down`/`restarting`/
  `settling`), yellow = idle (`idle`/`idle-with-context-left`) / waiting on a human
  (`blocked:human`) / low on context (`warned`/`danger`), red = broken
  (`session-gone` — `not-claude` is DELETED, no longer a status), default (uncolored,
  terminal white/gray) = `unassigned`, `live-outside-tmux` (informational — alive but
  unmanaged, deliberately NOT tinted so it reads as neither healthy nor broken), and any
  other unmapped status. Two invariants keep it
  safe: (a) the ANSI codes wrap the **already-padded whole line**, never a cell, so the
  column widths — still computed on plain-text `len` — stay aligned; and (b) color is
  emitted **only to a TTY** (`render` gates on `out.isatty()`), so a piped
  `supervisor.py list` and the beside-tests' plain `StringIO` get NO escape codes and
  every `row.split()` assertion stays valid. The header + separator are never tinted.
  If you add a status token, add it to `_STATUS_COLOR` too (an unmapped status is legal
  — it just renders in the default color).
- **Session-authored notes are ELIDED on EVERY surface (`_elide`; 2026-07-16).** A note
  is SESSION-authored free text — a `blocked:` reason or the live-outside-tmux detail —
  that can be arbitrarily long AND multi-line, and a raw 705-byte `blocked:` value once
  blew the whole Status column out (the table sizes each column to its widest cell) and
  broke row alignment. `_elide` flattens the note to one line (`" ".join(split())`,
  collapsing newlines) and truncates with an ellipsis, applied at THREE call sites so no
  surface can be overrun: the table Status cell (`_MAX_NOTE_IN_TABLE`, 48 — tightest,
  because the column width is load-bearing), and the `NEEDS YOU` block line + the
  edge-triggered `_alert` daemon.log line (both `_MAX_REASON_IN_ALERT`, 160 — a longer
  preview, since the FULL reason is in the tracked pane the line's jump command points
  at). Never render `row.note` raw onto any surface — route it through `_elide`.
- **`command tmux` semantics (`tmuxio.py`).** Every tmux call is
  `subprocess.run([...], shell=False)` with an argv LIST — no shell is spawned,
  so a user's zsh `tmux` function shim is bypassed (the `command tmux` effect).
  Never build a shell string for word-splitting.
- **Bracketed paste, never line-by-line.** Multi-line payloads (the wrap-up, the
  resume line) go in via `load-buffer -` + `paste-buffer -p` so the receiving
  Claude TUI takes the whole blob as ONE pasted input that cannot fragment into
  separate submitted prompts. `send-keys -l` typing a multi-line payload would
  fragment it — do not.
- **Bracketed-paste submission (`_submit_prompt`) — verified-submit loop, RUNTIME-AWARE.**
  Paste (`load-buffer` + `paste-buffer -p`, single- or multi-line, atomic — never type a
  payload key-by-key), then re-send `Enter` until submission is CONFIRMED, up to
  `_SUBMIT_MAX_ENTERS`. Verified live (2026-07-13): on a STEADY idle session a single
  `Enter` submits; but a freshly-`respawn`-ed session is often still drawing its
  welcome/news screen when the first `Enter` arrives and DROPS it, leaving the payload
  un-submitted. The verify loop fixes that (an extra `Enter` on an already-empty prompt is
  a harmless no-op). The confirm signal is **runtime-specific** (`expect_codex`) because
  the two TUIs render differently: **Claude** confirms on the empty `❯` box returning
  (`signals.input_box_ready`); **Codex** confirms on the pane going BUSY
  (`signals.is_busy` — Codex's `esc to interrupt` / `Working …`), because Codex has no
  `❯` box and its empty box shows a grey rotating PLACEHOLDER indistinguishable from typed
  text in an ANSI-stripped capture, so "box cleared" is not usable; "the model started
  responding" is (verified live 2026-07-17, busy within ~1s of Enter). This is NOT the old
  `send-keys -l` key-by-key collapse — the paste is always atomic; it is submit TIMING.
- **Codex idle / gate detection is STRUCTURAL, and its own (`signals.is_codex_idle_input`
  / `codex_prompt_present`; 2026-07-17).** A Codex track is a full citizen that gets the
  wrap-up pasted in and is restarted on `ready`, so its idle read must be as safe as
  Claude's `is_idle_input`, not the coarse "not busy". Codex idle = a `›` input line above
  its statusline (`… · Context N% left · …`), not busy, and NOT a picker — so a booting
  pane or a Codex approval/directory-trust picker is never keystroked into. That picker
  uses a `›` cursor (`› 1.`), NOT Claude's `❯`, which is why `is_structured_gate`'s cursor
  regex accepts BOTH glyphs (`[❯›]`); reverting it to `❯`-only lets a wrap-up paste into
  the Codex chooser (sabotage-verified by `test_a_codex_approval_gate_suppresses_the_wrapup`).
- **Anchored, fail-closed Ctx% parse (`signals.parse_ctx_remaining`).** Scan only
  the last FEW non-empty pane rows (`_CTX_TAIL_ROWS`), ANSI-stripped, taking the
  LAST `Ctx: N% left` match. The statusline is the SECOND-to-last row — a footer
  hint (`⏵⏵ …` / `? for shortcuts`) renders BELOW it (verified live 2026-07-13) —
  so reading only the LAST row misses `Ctx:` entirely. NEVER scan the whole
  capture — page content (including the overseer design doc itself) contains
  `Ctx: N% left` and would yield a false reading; the small bound keeps that
  anti-false-match intent. No match ⇒ **unknown**, which keeps the last known
  value and NEVER counts as a threshold crossing. This is the one coupling: if
  the statusline stops emitting `Ctx: N% left`, ctx reads unknown and the daemon
  degrades safely (the table shows a dash).
- **Busy detection (`signals.is_busy` + the daemon's settled-delta).** The live
  TUI (verified 2026-07-13) renders NO persistent busy string while streaming
  tokens — the input box looks idle and the response accumulates above it — so
  single-capture markers are insufficient. `signals.is_busy` fires on the real
  active-generation spinner (`✻ … (… · Ns · ↓ tokens)` / `(running … hook…)`),
  `esc to interrupt` (older layouts), and `Waiting for N background`; it
  deliberately does NOT fire on the lingering completed-turn summary
  (`✻ Brewed for 25s`). Because streaming shows no spinner in the captured
  region, the daemon ALSO runs a two-capture **settled-delta**
  (`Supervisor._pane_settled`) before injecting/restarting an apparently-idle
  track: two captures `_SETTLE_DELAY` apart that DIFFER ⇒ actively working ⇒
  treated as `working` and skipped. Over-firing busy is the SAFE direction.
- **Claude registry `status` is AUTHORITATIVE for an adopted Claude session
  (`claude_sessions.status_by_tmux_session`; 2026-07-15).** Claude Code writes a live
  `status` into each session's registry file (`~/.claude/sessions/<pid>.json`), and its
  four values map cleanly onto the daemon's model — recomputed each tick into
  `Supervisor._claude_status` (`{tmux_session: status}`) by `_refresh_claude_status`, read
  in `evaluate`, and matched against `_CLAUDE_BUSY_STATUSES = {"busy", "shell"}`:
  - **`busy`** — actively generating, OR running an in-process sub-agent (Task tool). A
    sub-agent spawns NO descendant shell and need not repaint the pane, so
    `has_active_subshell` AND `is_busy` both miss it — but Claude reports `busy`, so the
    daemon marks it `working` (note `"sub-agent (Claude busy)"`). [fixed false-idle]
  - **`shell`** — at the prompt with a live `Bash(run_in_background)` command. This is
    Claude's OWN, accurate background-work signal → `working (background shell)`. [fixed
    the autonomous-mode false-idle: a real background dispatch mis-read as idle]
  - **`waiting`** — at a gate/prompt for the human. **`idle`** — nothing pending. Neither
    is busy; the session falls through to the gate/idle branches.
  For an adopted session the daemon therefore **IGNORES the process-tree shell-walk
  entirely** and trusts `status`: it is strictly better than the walk, which both MISSED
  sub-agents (false-idle) and false-fired on lingering/transient shells that Claude was
  not actually using (false-`working (background shell)` on a session sitting at a user
  prompt). Getting this right took two iterations — the first fix folded only `busy` in
  and made everything else ignore the shell, which then mis-read a genuine `shell`-status
  background dispatch as idle; the authoritative-`status` model (this bullet) is the
  root-cause fix.
- **Background-shell detection (`claude_sessions.has_active_subshell`) — the
  runtime-agnostic FALLBACK, Codex-only.** A descendant shell (`sh`/`bash`/`zsh`/…) under
  the pane process marks a session busy ONLY for a session with NO Claude registry entry
  (`claude_status is None` — Codex). It is the only busy signal that covers Codex. Its
  ORIGINAL job — blocking a force-restart of a live `Bash(run_in_background)` build — is
  moot now that the cardinal rule forbids restart without a `ready` declaration; for
  Claude the `shell` status supersedes it exactly and more accurately. The `/proc` readers
  (`proc_children`/`proc_comm`) are injected (`children_of`/`comm_of`) so the beside-tests
  fake them. When it is the SOLE reason a track isn't idle, the row `note` is
  `"background shell"`.
- **Idle-input detection (`signals.is_idle_input`).** The real idle prompt is an
  EMPTY `❯` between two horizontal rule lines (`────…`), statusline + hint below
  — NOT a `╭─╮` box with `? for shortcuts` (verified live 2026-07-13). Detect
  that structural shape (glyph/hint-independent); require the prompt EMPTY so the
  daemon never injects over existing input; gate with not-busy + not-gate.
- **State-file declaration (`signals.read_state` / `valid_token` /
  `ready_valid`).** The ONE state file lives at
  `<repo>/tmp/overseer/<topic>/.overseer-state` (the repo's gitignored temp dir —
  NEVER under `plan/`); its first non-empty line is `<token>` or
  `<token>: <detail>`. The restart interlock (`ready_valid`) fires ONLY when: an
  injection stamp exists for this round, the token is **exactly `ready`**, AND its
  mtime is strictly newer than that stamp (this round, not a stale declaration).
  Beyond the token, **contents are NOT inspected** (no handoff hash): the handoff
  and everything under `plan/` is the session's own business, which the overseer
  must never read or hash. Any missing/unreadable/other-valued file ⇒ False
  (fail-closed). The daemon writes the injection stamp BEFORE pasting the wrap-up
  (so a subsequent declaration has `mtime > stamp`) and DELETES the file as it
  restarts (`_clear_state` — so a declaration can never re-trigger). **`ready` is
  the SOLE restart authorization — never reshape this into "the daemon may decide
  for itself"** (invariant 7). The full contract is in `marker-protocol.md`; keep
  it and `supervisor.py`'s `_WRAPUP_SUGGEST_HEAD` / `_WRAPUP_INSIST_HEAD` /
  `_WRAPUP_BODY` in sync.
- **Self-healing resume-submit (`registry.set_resume_pending` / `read_resume_pending`,
  `_resend_enter`; R1, 2026-07-18).** The restart respawns the fresh session and pastes the
  resume line, but a freshly-respawned TUI can DROP the Enter while still drawing its
  welcome screen — the fresh session then sits live but IDLE with an un-run handoff
  (proven live 2026-07-17 four times in one day; autonomous-mode stranded 9h). The OLD code
  cleared the `ready` marker and logged "restarted" anyway, so the daemon never retried.
  Now `_do_restart` separates two facts it used to conflate — "is the fresh Claude up?"
  (await) and "did the resume submit?" (the Enter): on a FAILED submit it keeps the marker
  + stamp, marks a round-scoped `resume_pending` flag on the injection-stamp dict, and
  alerts (no clean "restarted" log). The next tick's `evaluate` sees `resume_pending` and
  intercepts BEFORE the busy/idle cascade — a box holding the un-submitted resume reads as
  "not idle" and would otherwise fall to `settling` and never retry. The retry branches on
  the BOX STATE, NOT on `busy` (review SF3): an empty box means the resume left the box
  (submitted / never pasted) → close the round; a box holding text means the Enter dropped →
  re-send Enter ONLY (`_resend_enter`, NEVER a re-paste, NEVER a re-respawn). `busy` is NOT a
  "submitted" signal — a fresh session can be busy for SessionStart-hook reasons unrelated to
  the resume, so a `busy` shortcut would false-close the round. And a fresh TUI that comes up
  on a PICKER is never keystroked (review SF4): both `_do_restart` and the retry branch check
  `is_structured_gate` first and report `blocked:human`, keeping the round open until the
  human clears the gate. **The re-respawn stays gated on a fresh `ready` alone**,
  so the retry can never escalate to a `respawn-pane -k` (the loop-safety property the
  Codex-#2 reasoning protected; pinned by `test_submit_retry_never_kills_the_fresh_session`
  and `test_idle_pane_with_resume_pending_closes_the_round_instead_of_respawning`). The flag
  is round-scoped by construction: `clear_injection_stamp` (round close) and
  `write_injection_stamp` (fresh round) both drop it, so it can never outlive its round.
  Codex never sets it (`codex resume` auto-submits its kick, no separate paste). Harden:
  `_await_input_box` waits for the box to render before the FIRST paste so most restarts
  never need the retry at all.
- **Claude identity gate `topic in names` parity + stale-mapping re-point
  (`_pane_is_managed_claude`, `_claude_names`, `registry.repoint_tmux`; R2, 2026-07-18).**
  The Codex gate is pane-scoped (`_is_codex_track` requires `live.name == topic`); the
  Claude gate checked only process + cwd, so a generic reused tmux window (`livespec1`…
  cycled across topics) the store mapped to topic A but now running topic B's Claude —
  SAME repo — passed the gate and got A's wrap-up injected into B, then a `ready`
  respawn-KILLED B as A. The gate now ALSO requires a live Claude named for THIS topic to be
  present in the pane's tmux session (`self._claude_names`, from `names_by_tmux_session` —
  the SET of ALL live Claude names in that tmux session, so a HELPER Claude sharing the
  session cannot shadow the track's own name and flap it to `session-gone`; review SF5). It
  is POSITIVE-mismatch only: reject only when the tmux session has live Claude names but NOT
  this topic's; an UNKNOWN tmux session (empty set — registry miss, or a direct-`evaluate`
  test that did not populate the map) preserves the prior process+cwd gate — fail-soft, so a
  transient miss never flaps a live track to `session-gone`. Do NOT widen this to "reject
  unless proven `topic in names`" (that reintroduces the flap). Separately,
  `adopt_sessions` now RE-POINTS a stale mapping: when a topic's live named session resolves
  to a tmux session different from the store's `tmux` field, it rewrites the row
  (`repoint_tmux`, idempotent + guarded so a steady-state tick never touches the store)
  instead of freezing the binding — the "re-mapping is a separate concern" the old code
  deferred was the concern.
- **Stale-`ready` voiding (`_void_if_stale` + `_MARKER_VOID_GRACE`).** A session
  that declares `ready` and then RESUMES work must not be restarted on that (now
  false) declaration. So on a busy/blocked tick a `ready` OLDER than
  `_MARKER_VOID_GRACE` (120s) is cleared. Younger ones SURVIVE deliberately: the
  declaring turn's own tail (final text streaming + stop hooks) legitimately keeps
  the pane busy for a while right after the write, and voiding on ANY busy would
  destroy every legitimate declaration before the pane ever went idle (RB1).
- **Stale-`blocked` voiding (`_void_stale_blocked`; 2026-07-16).** Nothing else retires a
  `blocked:`. `_clear_state` runs only on the daemon's own restart path, so a pane replaced
  OUT-OF-BAND (a hand-restarted session, a `/clear`) INHERITS its predecessor's declaration
  — found live: a fresh `overseer-rewrite` session rendered `working (awaiting maintainer
  next-step decision — Codex…)`, a reason written by a session that no longer existed. Left
  alone the dead reason also fires a false `blocked:human` the moment the session goes idle.
  So a `blocked:` is voided when the session is **GENERATING** and the declaration is past
  `_MARKER_VOID_GRACE`. **This is not the daemon judging semantics (invariant 1):** it does
  not guess the session is unblocked, it observes that the session is PRODUCING TOKENS,
  which is incompatible with waiting for an answer. Two bounds, each pinned by a test —
  widen neither:
  - **`generating`, not merely `busy`.** Busy via a live `Bash(run_in_background)` command
    alone (Claude `shell`) means the session is AT ITS PROMPT and may legitimately be
    awaiting a human while a build runs → never voided, however old. Only a real generation
    spinner (`is_busy`) or Claude `busy` (generating / in-process sub-agent) qualifies.
  - **The same RB1 grace as `ready`.** The declaring turn's own final text streams 10–60s
    AFTER the write, so a young declaration must survive its own busy tail.
  An IDLE blocked session is never touched: it keeps its declaration and keeps alerting
  until the session itself retracts it. Note the note-default coupling — `note` defaults to
  the blocked reason, so the void runs BEFORE the note is derived and the note is re-derived
  after; the reason only ever reached a `working` row via the spinner path anyway (the
  shell / sub-agent branches overwrite the note), which is exactly the provably-stale case.
- **The `winding-down` ACK (`_ACK_STALE_AFTER`).** A FRESH `winding-down` (≤ 900s
  old) suppresses further wrap-up injections — the daemon must never keystroke into
  a session that is actively wrapping up — and shows as the `winding-down` row
  status. A STALE one resumes the escalation and re-reports the track (an ACK must
  not become an infinite stall), but it STILL never authorizes an act: only `ready`
  does.
- **Reporting a non-responder (`_alert_non_responder`).** This is the WHOLE response
  to a session that declared nothing at/below `DANGER_CTX_REMAINING` (20%): say so,
  loudly, with the tmux coordinates to go fix it — and do nothing else. It is a
  DEFECT REPORT about that session (it got an escalating wrap-up telling it exactly
  what to write), not a chore for the operator to work around. The fix is to make
  the session honour the protocol; it is NEVER to have the daemon guess on its
  behalf.
- **State precedence** (`evaluate`, top to bottom). `working` and `blocked:human`
  are evaluated FIRST, so an injection/keystroke is suppressed while a pane is busy
  (including a live background shell) or showing a structured gate (permission
  prompt / picker) — never keystroke into a gate. Then `settling` / identity
  re-check, then `restarting` (a fresh `ready`), then the threshold branch
  (`winding-down` on a fresh ACK, else `danger` at/below 20%, else `warned`), else
  the idle branch. `restarting` is checked BEFORE `warned`: a fresh `ready` means the
  session already declared it is done, so it supersedes any re-warn. The idle branch
  itself splits: an idle session still ABOVE threshold, not `waiting` on a human, and
  carrying no session declaration (or already holding the marker) becomes
  `idle-with-context-left` and gets ONE keep-going nudge; anything else is plain
  `idle` (see invariant 9 for the marker lifecycle).
- **Atomic restart via `respawn-pane -k`, proven by `#{pane_current_command}`.**
  Restart replaces the pane's process in one step (`respawn-pane -k -c <repo>
  'claude --dangerously-skip-permissions -n <topic>'`) — NEVER `/exit` then
  screen-scrape a shell prompt. The `❯` glyph is ambiguously BOTH the Claude idle
  prompt and the zsh prompt, so a mis-timed "shell is back" could type `claude …`
  into the still-live session. Wait for the fresh TUI by polling
  `#{pane_current_command}` → `node`/`claude` (`signals.pane_is_claude`), never by
  scraping `❯`. There is exactly ONE restart path and its abrupt kill is safe
  because of the DECLARATION: the session itself asserted it is at a clean stopping
  point, and the kill destroys only the PROCESS (files, worktrees, branches, and
  commits on disk survive). Every tmux step is a hard gate: a failed respawn, or a
  pane that never becomes a live Claude, SURFACES and returns WITHOUT clearing the
  round — the `ready` declaration is preserved and the restart retried, never
  silently destroyed.
- **`claude --dangerously-skip-permissions -n <topic>`** is the launch command
  (`_launch_command`), and BOTH flags are load-bearing.
  `--dangerously-skip-permissions` makes the restarted session AUTONOMOUS — without
  it the fresh session stalls on its first permission prompt and the auto-restart
  silently accomplishes nothing (invariant 7b). `-n <topic>` sets the session's
  display name in the prompt box, the `--resume` picker, AND the terminal title
  (which tmux surfaces) — a cleaner equivalent of typing `/rename`. The resume line
  is then pasted as the first prompt (a `claude "<prompt>"` argv only pre-fills, no
  auto-submit — which is why it is pasted after launch, not passed on the command
  line). Related `claude` flags to know: `--session-id` and `--resume`.

## Build / toolchain facts

- **Stdlib-only Python, host-only.** No third-party imports; six modules
  (`registry.py`, `signals.py`, `tmuxio.py`, `supervisor.py`, plus the session
  readers `claude_sessions.py` and `codex_sessions.py`) plus beside-tests.
  Precedent for host-only Python under `.claude/`:
  `.claude/hooks/livespec_footgun_guard.py`. Stdlib-only is now **load-bearing
  for the invocation surface too**: the `overseerd` executable carries a
  `#!/usr/bin/env -S uv run --script --no-project` shebang, so it runs with an
  isolated interpreter and **no dependencies** — a third-party import would break
  the shebang launch (there is no project sync to satisfy it).
- **Invocation surface (daemon vs module split; 2026-07-13).** Two homes:
  - **`overseerd`** — the dedicated daemon **executable** (uv shebang above +
    `chmod +x`). Run it with NO subcommands; its ONE option is `--warn-percent N`
    (an int in [1, 99], the daemon-wide default wind-down threshold — a per-track
    `ctx_threshold` override still wins; `overseer-start` threads it through). It calls
    `supervisor.run_daemon()`, which watches the whole fleet. It pins its own dir
    onto `sys.path` so `import supervisor` (and supervisor's siblings) resolve
    from any cwd. This is the ONLY thing the `/overseer` skill launches in the top
    pane.
  - **`supervisor.py`** — a **plain module** (NO shebang, NOT executable). It
    holds the `Supervisor` logic + `run_daemon()` + the one-shot track-management
    CLI (`list` / `add` / `remove` / `unassign` / `start`, `--repo` / `--topic`
    keyword flags). It carries NO `daemon` subcommand (a dedicated executable has
    no business being a subcommand of a track CLI). The skill invokes it as
    `uv run --no-project python .claude/skills/overseer/supervisor.py <cmd>` — a
    module invoked from the skill, never a supported bare `python3` path.
  Beyond `--warn-percent`, there are **no config knobs**: store
  (`~/.livespec-overseer.jsonl`) and injection-stamp
  (`~/.livespec-overseer-stamps.json`) paths are hard-coded via the `registry`
  defaults, and the watch-set is read from `~/.livespec-overseer-repos.json`
  (an absolute `$HOME` path, so it works from any cwd AND from any install
  location — it is deliberately NOT derived from the module's own position,
  which is what previously pinned this package to
  `<core>/.claude/skills/overseer/`) — no `--store` / `--stamp` / `--repos` / `--repos-only` /
  `--manifest`, and `overseerd` takes no `--interval` / `--once` / `--recover`
  (surface-only: no startup auto-recovery). The `Supervisor` dataclass keeps
  `store_path` / `stamp_path` / `watch_repos` / `manifest_path` injectable, but
  **only the beside-tests inject them** (they redirect `registry.DEFAULT_STORE_PATH`
  for CLI isolation) — neither `overseerd` nor the module CLI exposes them.
- **Outside the product STYLE gates; inside the TEST gate.** The beside-tests run
  in `just check` (see the next bullet). Everything else — lint, types, coverage,
  import contracts — still excludes the folder, by four concrete config facts (the
  design's "PR #1109 / dev-tooling `.claude/` universe exemption" labels are
  paraphrase for these). Bringing each of those inside is tracked as its own
  decision in `plan/overseer-productization/`:
  - **ruff** — `pyproject.toml` `[tool.ruff].extend-exclude` names
    `.claude/skills/overseer/**` (ruff's repo-wide scan is the one gate whose
    denylist must name the path; precedent `.claude/hooks/**`).
  - **pyright** — `[tool.pyright].include` lists only `.claude-plugin/scripts`
    and `dev-tooling`; the overseer folder is omitted, so it is never
    type-checked.
  - **coverage** — pytest's `testpaths = ["tests"]` means the coverage-bearing
    product suite never collects the beside-tests, so `fail_under = 100` does not
    apply to these modules. `check-overseer` collects them under their own target
    WITHOUT `--cov`, precisely so that stays true.
  - **import-linter** — `root_packages = ["livespec"]`; these modules are not
    part of the `livespec` package, so no import contract touches them.
  - The dev-tooling shared checks read their scope from
    `livespec_dev_tooling.config` (`source_tree_prefixes` /
    `target_dirs`), none of which include `.claude/skills/` — so
    `check-claude-md-coverage` and the style checks never reach here.
- **The beside-tests ARE a product gate — `just check-overseer` is a literal
  member of the `just check` aggregate, so pre-commit, pre-push, and CI all run
  them.** This reverses the folder's earlier "outside the product gates, the
  discipline lives in the developer's hands" design. That design was wrong in
  practice: a broken overseer change merged green with NOTHING having exercised
  its behavior, more than once. The beside-tests are hermetic (FakeTmux, a fake
  `/proc`, seam-injected Codex discovery) and the whole suite runs in seconds, so
  there was never a real cost to wiring them in. Run them directly while
  iterating:

  ```bash
  uv run pytest .claude/skills/overseer/ -q
  ```

  (`conftest.py` puts the folder on `sys.path` so `import registry` / `import
  signals` / `import tmuxio` resolve when pytest collects the beside-tests.)
  They need their own justfile target because pytest's `testpaths = ["tests"]`
  never collects them; the target runs WITHOUT coverage, since these modules are
  scoped out of the `fail_under = 100` gate. Lint (ruff), types (pyright), and
  coverage remain scoped out of this folder — bringing those inside the gates is
  the rest of the `plan/overseer-productization/` thread, and each is a separate
  decision from this one.
- **The COMBINED-master-state failure mode, and what now catches it.** Two overseer
  branches can merge git-clean and still leave the folder red: a concurrent change
  to shared surface (e.g. the `TMUX_TMPDIR`/`exec` wrap once added to
  `_launch_command` — since REMOVED by `plan/tmux-fleet-visibility/`)
  can invalidate the OTHER branch's assertions, which passed on its own base.
  Proven live 2026-07-18 (the codex-reboot-recovery branch was green on its base,
  red on combined master; fixed by PR #1373). CI's `push: branches: [master]` leg
  now runs `check-overseer` against combined master after every merge, so this is
  caught rather than silent. It is caught AFTER the merge, though — auto-merge
  lands a PR before the master run finishes. So when landing an overseer change
  while another overseer branch is in flight, still re-run the beside-tests against
  the combined state yourself rather than trusting either PR's own green.
- **Codex discovery is seam-injected end-to-end, so the suite is hermetic even
  with a live codex on the host (test-isolation, 2026-07-18).** `codex_sessions` was
  already injectable at the FUNCTION level, but the `Supervisor` only threaded
  `ppid_of` into it — so `adopt_sessions` / `_refresh_codex_sessions` still read the
  real `/proc` `comm==codex` scan and the real `~/.codex/session_index.jsonl`, a host
  coupling in a unit suite (a running codex could in principle perturb a test). The
  `Supervisor` now carries `codex_home` + `codex_pids_of_comm` / `codex_fd_targets_of`
  / `codex_cwd_of` fields (default real, mirroring the Claude `sessions_dir` + `/proc`
  seams) and threads ALL of them into BOTH codex call sites. The beside-tests' `_sup`
  factory defaults `codex_pids_of_comm` to an empty scan + `codex_home` to a
  non-existent dir, so no adopt/refresh test touches real host state (with an empty
  pid scan the fd/cwd readers are never reached). A codex-behavior test injects the
  seams to SIMULATE a session end-to-end
  (`test_refresh_and_adopt_route_codex_through_injected_seams`) — the proof the
  threading holds; sabotage either call site's seams and it goes red.
- **Adding a `.py` here?** Keep it stdlib-only. The ruff `**` exclude covers new
  files automatically, and new beside-tests are picked up by `just check-overseer`
  (which globs the whole folder) with no wiring of their own.
- **The nested `.claude/CLAUDE.md -> ../AGENTS.md` symlink beside this file** is
  the repo's per-directory nested-memory convention (so Claude Code loads this
  guide when working in the folder). No structural or coverage check objects to
  a nested `.claude/` dir inside a skill folder — verified against
  `tests/test_plugin_distribution.py` (which only asserts `.claude-plugin/skills/`
  is absent and the repo-root `.claude/skills` is not a symlink).

## How to exercise it live

The **beside-tests are the primary, complete gate** for the acting mechanics
(inject → declare → restart, archive-GC, reboot recovery, and the RB1
declaration / round timing) — they drive a FAKE tmux deterministically, so they
own that coverage. Run them first (see "Build / toolchain facts"). Since the CLI
no longer has a `--repos` / `--store` escape hatch, there is no scratch-repo
sandbox: live exercise runs against the **real fleet** (maintainer decision
2026-07-13). That is safe because the daemon is **surface-only** — nothing is
restarted unless a real track crosses threshold AND declares `ready` AND is idle.

For a change to the invocation / config surface (this file's usual subject), the
end-to-end check is the discovery + render path, exercised safely read-only:

1. Run a **read-only render** against the real fleet:
   `uv run --no-project python .claude/skills/overseer/supervisor.py list` — it
   calls `tick(act=False)`, so it discovers every declared repo's `plan/*/`,
   joins the mapping, and prints the `Status · Topic · tmux · Ctx% · Repo` table
   **without injecting or restarting anything**. This exercises the whole reshaped
   surface (module invocation, fixed store path, fleet-only watch-set) with zero
   mutation risk.
2. Optionally observe a **brief live daemon** (`.claude/skills/overseer/overseerd
   2> tmp/overseer/daemon.log`, stopped after a render or two) to confirm the loop
   renders and refreshes. Surface-only means it will not act on any real session
   unless that session is genuinely at threshold + certified + idle.

   **Isolation tip for exercising `overseerd` safely off the real fleet — this
   got MUCH simpler, and the old recipe is obsolete.** The watch-set is now an
   absolute `$HOME` path, so isolation is just a scratch `HOME`:

   ```bash
   mkdir -p /tmp/ov/{home,projects/demo/plan/demo-topic}
   printf '{"repos": ["/tmp/ov/projects/demo"]}' > /tmp/ov/home/.livespec-overseer-repos.json
   touch /tmp/ov/projects/demo/plan/demo-topic/handoff.md
   HOME=/tmp/ov/home .venv/bin/python3 .claude/skills/overseer/supervisor.py list
   ```

   That redirects the watch-set AND the mapping store AND the stamp sidecar in
   one move, since all three are `$HOME`-anchored — real sessions untouched.
   Verified 2026-07-20: it renders exactly one row, `unassigned  demo-topic`,
   which also demonstrates the invariant the design turns on — a plan with NO
   assigned session is still discovered, because the watch-set is declared
   rather than derived from the mapping store's existing rows.

   **Gotcha: do NOT wrap this in `mise exec` / `uv run`.** `mise` reads its own
   config out of `$HOME`, so overriding `HOME` makes it fail with
   "Config files in /home/ubuntu/mise.toml are not trusted" before your code
   runs at all. Invoke the venv interpreter directly, as above.

   The SUPERSEDED recipe was to copy this whole folder into a scratch repo tree
   (`<scratch>/<repo>/.claude/skills/overseer/`) with a scratch
   `.livespec-fleet-manifest.jsonc` beside it, because the manifest was resolved
   by walking up from the module file — so the only way to change the watch-set
   was to physically move the code. Do not do that any more; it works by
   accident at best. Two gotchas from that era still apply:
   - **Do NOT point `HOME` at a fresh empty dir to isolate the store.** `uv run`
     keys its cache off `$HOME/.cache/uv`; an empty HOME forces uv to cold-rebuild
     its whole environment and **hangs** (looks exactly like a daemon bug — it is
     not). If you must isolate the store off `~`, symlink the warm cache in first
     (`ln -s ~/.cache "$SCRATCH_HOME/.cache"`), or just run with the real `$HOME`:
     an `act=True` scratch daemon with no live scratch sessions never writes to
     the real store (it only auto-links sessions that actually exist).
   - The render flushes each tick but `uv run` may swallow piped stdout when the
     process is `timeout`-SIGTERM-killed; capture with a decent timeout and read
     the streamed lines, or observe the pane directly. (Direct `python`/venv-python
     runs the same body identically; the beside-tests remain the primary gate.)

The daemon's diagnostics + `overseer[SURFACE]:` alerts go to stderr; redirect
them to a log under `tmp/overseer/` (maintainer-owned scratch root — use a
scoped subdir, never `rm` the root).

**Timing-sensitive behavior (the RB1 lesson) is covered by the beside-tests, not
a hand-driven loop.** The regression that once slipped through a live re-test —
the "void the `ready` declaration when busy" logic racing the declaring turn's own
busy tail (final streaming + stop hooks keep the pane busy 10–60s AFTER the file
is written) — is now pinned by deterministic fake-tmux tests
(`test_fresh_marker_survives_busy_certifying_tail`,
`test_stale_marker_voided_when_busy_past_grace`,
`test_void_resets_inject_state_so_round_can_recertify`). The invariant-7/8/9
behaviors are pinned the same way
(`test_idle_at_danger_with_no_declaration_is_never_restarted`,
`test_winding_down_ack_suppresses_the_rewarn`,
`test_stale_winding_down_ack_resumes_escalation_but_still_never_acts`,
`test_malformed_state_value_is_surfaced_and_never_restarts`,
`test_every_track_alert_names_the_tmux_session_and_pane`). Do NOT try to reproduce
any of it by manufacturing a threshold crossing on a real working session — the
daemon exercises the full inject → declare → restart cycle live only when a real
track naturally reaches it (its steady-state job); the deterministic tests own that
coverage, and hand-spaced ticks would mask the timing anyway.

## Recovering + restoring sessions after a reboot or tmux crash/kill

When the tmux server dies (a crash, a `kill-server`, a host reboot) every tracked
pane's Claude process dies with it. This is the runbook to bring the tracks back
**with their prior conversations intact** — the exact procedure, plus the three
launch commands that are WRONG for it, each learned the hard way (2026-07-18: two
consecutive wrong relaunches before the right one).

### What survives the crash, and what does not

| Survives (on disk) | Dies with the tmux server |
|---|---|
| The JSONL mapping `~/.livespec-overseer.jsonl` — one row per assigned track (topic ↔ tmux name ↔ repo ↔ handoff ↔ resume line). | Every tmux session / window / pane (no `tmux-resurrect` / `tmux-continuum` is installed — a server death loses the whole layout). |
| Each Claude session's **conversation transcript**: `~/.claude/projects/<cwd-slug>/<session-id>.jsonl`, where `<cwd-slug>` is the repo path with every `/` rewritten to `-` (e.g. `/data/projects/livespec` → `-data-projects-livespec`). | Claude Code's pid-keyed live registry `~/.claude/sessions/<pid>.json` (keyed by the now-dead pid). |
| Each Codex session's **rollout** (`~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<id>.jsonl`) AND the **codex index** (`~/.codex/session_index.jsonl`, mapping id → thread_name = topic). This is what lets `recover_missing_sessions` reverse-look-up a dead codex track's id by topic and `codex resume` it AUTOMATICALLY (defect #5) — no manual step for codex. | The running codex process + its held-open rollout fd (the LIVE signal `self._codex` derives from — gone at cold start, which is why recovery uses the surviving INDEX instead). |
| Each plan's `plan/<topic>/handoff.md`. | The daemon process + its in-memory round state. |

The transcript is what makes a TRUE resume possible: the tmux pane is gone, but the
conversation was streamed to disk continuously, so it can be re-attached by session
id. Nothing in tmux persists — the only durable identity is that transcript file.

### The daemon does NOT do this for you

`overseerd` is **surface-only** — it never auto-spawns a session (invariant 3), and
its startup `recover_missing_sessions` is **split by runtime** (defect #5, 2026-07-18):
a **Claude** track is relaunched with the LAUNCH command + a handoff paste, **not**
`--resume`, so it restores a *handoff re-read*, never the *live conversation*; a
**Codex** track IS resumed by `codex resume <id>`, which reattaches the *live rollout*
(the codex conversation restores automatically — the Claude gap this section works
around does not apply to codex). So this **manual, human-driven** procedure is the way
to restore the actual **Claude** conversations (see invariant 7 and the
`recover_missing_sessions` docstring). (SKILL.md's "Cold-start / crash recovery"
section describes the `start`-based path, which is the handoff-re-read one; THIS
section is the Claude conversation-restore one, and they are different outcomes.)

### The three launch commands that are WRONG (each was tried and failed)

1. **`claude -n <topic>`** — a BRAND-NEW session. `-n` only sets the display name;
   there is no resume. This is the overseer's OWN `_launch_command`, correct ONLY
   when *followed by a paste* of the handoff resume line. With nothing pasted you
   get a fresh, context-free session — the tracks lose all their state.
2. **`claude --resume` with NO value** — opens the interactive picker and leaves
   every pane stuck on it. `--resume` resumes directly ONLY when given a session id;
   bare `--resume` is by definition the picker.
3. **`claude --continue`** — resumes the single most-recent conversation in the cwd.
   WRONG whenever a repo holds more than one track (e.g. `livespec` holds ~6): every
   pane would race for the same one conversation. And right after a botched attempt
   the "most recent in cwd" is your own junk session, not the real one.

### The RIGHT command

```
claude --resume <session-id> --dangerously-skip-permissions -n <topic>
```

- **Carry NO tmux env scoping — no `unset TMUX`, no `TMUX_TMPDIR` export.** The
  former L1 env-inversion prefix (`unset TMUX; export TMUX_TMPDIR=…; exec …`)
  was REMOVED by `plan/tmux-fleet-visibility/` (2026-07-19): it blinded every
  scoped agent to the real fleet (`tmux ls` returned a clean, plausible, wrong
  "no server running", producing repeated false session-liveness claims) while
  silently failing open whenever its tmpfs-backed directory vanished. The L2
  `PreToolUse` command guards are the sole mechanical fleet-kill control — they
  are the only layer that can distinguish a listing from a teardown. A restored
  session's bare `tmux ls` MUST tell the truth; do not re-add a scoping prefix
  here or in `supervisor.py` (`test_claude_launch_command_carries_no_tmux_scoping`
  and its codex twin pin the absence). An earlier version of this bullet said the
  prefix was "NOT optional" — that guidance is REVERSED, deliberately.
- `--resume <session-id>` re-attaches THAT exact conversation, no picker.
- `--dangerously-skip-permissions` — required so the resumed session is autonomous
  (the whole fleet runs with it; without it the session stalls on its first
  permission prompt).
- `-n <topic>` — keeps the display name equal to the plan topic, which is what the
  daemon adopts on (`names_by_tmux_session`); belt-and-suspenders, since the resumed
  transcript already carries the topic as its `customTitle`.

### Step-by-step

**0. Re-establish the daemon top pane.** From the bottom (Claude) `/overseer` pane,
re-run `.claude/skills/overseer/overseer-start` (idempotent; splits the daemon pane,
re-attaches to the surviving mapping, adopts sessions).

**1. Read the surviving mapping** — it is the recipe (which topics, which tmux names,
which repos):
```
cat ~/.livespec-overseer.jsonl
```

**2. List the live tmux sessions and note which to LEAVE ALONE.** Never respawn a
session a human is actively using (e.g. a crash-investigation shell). Confirm the
current set first:
```
command tmux list-sessions -F '#{session_name}'
```

**3. Compute topic → correct session-id.** The transcript filename is the id; the
`-n <topic>` name is stored inside as `customTitle` (also `agentName`); `sessionId`
repeats it. THE TRAP: your own fresh/junk relaunches and picker respawns ALSO carry
`customTitle=<topic>`, so "most recent with this title" can select junk. Filter by
SIZE (real pre-crash conversations are hundreds of KB to several MB; a fresh/junk
session is a few KB) and take the most-recent above the threshold. This snippet
prints the candidates so you can eyeball them:
```
python3 - <<'EOF'
import json, os, glob, time
now = time.time()
# {cwd-slug: [topics]} — fill from the mapping read in step 1.
TARGETS = {
    "-data-projects-livespec": ["fabro-ci-image-factoring", "autonomous-mode"],
    "-data-projects-livespec-orchestrator-beads-fabro": ["codex-factory-telemetry"],
    "-data-projects-livespec-dev-tooling": ["fleet-plan-lifecycle-enforcement"],
}
base = os.path.expanduser("~/.claude/projects")
def title_of(path):
    ct = None
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for i, line in enumerate(fh):
            if i > 25:
                break
            try:
                o = json.loads(line)
            except Exception:
                continue
            if isinstance(o, dict) and o.get("customTitle"):
                ct = o["customTitle"]
    return ct
for slug, topics in TARGETS.items():
    d = os.path.join(base, slug)
    recs = [(f, title_of(f), os.path.getsize(f), os.path.getmtime(f))
            for f in glob.glob(d + "/*.jsonl")]
    for t in topics:
        cands = sorted([r for r in recs if r[1] == t and r[2] > 100_000],
                       key=lambda r: r[3], reverse=True)
        print(f"\n### {slug} :: {t}  ({len(cands)} real candidate(s))")
        for f, ct, sz, mt in cands[:4]:
            print(f"   {os.path.basename(f)[:-6]}  {sz/1e6:6.2f}MB  {(now-mt)/60:6.1f}min ago")
EOF
```
The top row per topic is the one to resume. CROSS-CHECK it before trusting it:
`claude --resume` (the picker) shows each conversation's size + age + PR number; the
chosen transcript's size/age must match the picker row for that topic. The correct
target is the one last-written **at the crash moment** — every crash-time session
shares roughly the same mtime, which clusters them apart from older, larger
predecessors carrying the same title.

**4. Canary ONE pane first.** Do not batch all of them at once — a wrong command
wastes every pane. Respawn one and confirm the actual conversation loaded:
```
command tmux respawn-pane -k -c <repo> -t <tmux-name> \
  "claude --resume <session-id> --dangerously-skip-permissions -n <topic>"
sleep 15
command tmux capture-pane -p -t <tmux-name> | tail -30
```
SUCCESS looks like the prior conversation's tail + an empty `❯` box + a statusline
reading `── <topic> ──` and `Ctx: N% left`. FAILURE looks like the picker (`Search…`
/ `show all projects`), a fresh welcome banner, or the wrong topic. A big
conversation can take 10–25s to render — wait and re-capture before judging it
failed (`#{pane_current_command}` == `claude` while the screen is still blank means
it is still loading, not broken).

**5. Batch the rest** once the canary is verified — one
`respawn-pane -k … --resume <id> … -n <topic>` per remaining track, each with its
own computed id.

**6. KICK each restored track — restoring it does NOT make it run.** A `--resume`d
pane comes back with its conversation loaded but its last turn already FINISHED, so
it sits at an idle `❯` doing nothing until something prompts it. This step is the
difference between "the tracks are back" and "the tracks are working"; skipping it
is the single most common way a recovery is reported complete while the whole fleet
sits idle. Paste a kick and submit it (`load-buffer -` + `paste-buffer -p`, then
`Enter` — the same atomic-paste discipline the daemon uses; never type it key-by-key):

```
Your tmux session was killed at <time> by an external fleet-wide tmux kill-server
(not caused by anything you did, and not a maintainer decision). The session has now
been restored with your full conversation intact. Re-read <repo>/plan/<topic>/handoff.md
to re-ground yourself, then continue exactly where you left off.
```

**Say explicitly that the kill was external.** A restored pane renders its dead
sub-agents as `Agent "…" was stopped by user` and its dead background commands as
`Background command "…" was stopped` — a resumed session reads those as the
MAINTAINER having cancelled its work and will abandon it. Name what died in the kick
(live 2026-07-19: `rop-sweep-fleet-policy`'s Fable review and `codex-yolo-sandbox`'s
factory dispatch both had to be corrected this way).

**DO NOT kick a track in any of these four states — read the pane FIRST, one at a
time.** A kick is arbitrary text submitted into whatever is focused, so kicking a
waiting session ANSWERS its question on the maintainer's behalf:

| State | How it looks | What to do instead |
|---|---|---|
| **Structured gate** | an `AskUserQuestion` picker, permission prompt, or trust prompt (`❯ 1.` / `› 1.`) | Leave it. Report the tmux session + pane; the maintainer answers IN THAT PANE. |
| **Prose question to the human** | the turn ENDS asking the maintainer something ("Want me to X, or leave it?") | Leave it. This has no picker and no gate — only reading the tail catches it. |
| **Declared `blocked: <reason>`** | `<repo>/tmp/overseer/<topic>/.overseer-state` reads `blocked:` | Leave it. It is waiting on a human by its own declaration. |
| **Already self-continuing** | it died mid-turn and resumes on its own; pane goes busy with no prompting | Leave it. A kick would queue a redundant turn. |

Both waiting states occurred in ONE recovery (2026-07-19): `autonomous-mode` had
ended its turn asking the maintainer a question, and `tmux-fleet-kill-prevention`
sat on a 3-option `AskUserQuestion` picker. A blind kick-everything sweep would have
silently answered both. Checking the four states costs one `capture-pane` per track.

**7. Verify all — by the REGISTRY, not by the pane.** Read
`~/.claude/sessions/<pid>.json` (`status` is `busy` / `shell` / `waiting` / `idle`)
rather than grepping the pane for a spinner: a streaming Claude renders NO busy
marker in the captured region, and the lingering completed-turn summary
(`✻ Baked for 3h 43m`) false-matches a naive `✻` grep — so pane-scraping reports
working tracks as idle AND idle tracks as working, in both directions at once
(live 2026-07-19). A kicked track must read `busy`; a deliberately-unkicked one
reads `waiting` or `idle`. Each pane's statusline should also name its own topic
and show no unexpected picker; the daemon re-adopts each within a tick.

### Two post-resume states are BOTH correct

- **Small sessions** load straight to an empty `❯` prompt — ready to continue.
- **Large sessions** (high token count) show Claude's own guard first:
  `Resume from summary (recommended) / Resume full session as-is / Don't ask me
  again`. **ALWAYS select 2. Resume full session as-is** — `Down` then `Enter`
  (maintainer-declared 2026-07-19: this is a STANDING rule, not a per-incident
  choice; do not re-ask it). Recovery exists to restore exact state, and Claude's
  own "recommended" summary option silently compacts away the in-flight detail a
  killed-mid-turn track needs. CANARY the keystroke: send `Down`, re-capture and
  CONFIRM the cursor moved to option 2 before sending `Enter` (the first capture
  often lags the redraw), so you never confirm the wrong choice.

  This REPLACED a directly contradictory instruction. An earlier version of this
  bullet said to "leave it for the human; do NOT keystroke a selection", while the
  paragraph below it said you MUST clear the modal to get the track working — a
  reader following the first sentence would restore the fleet into a frozen state
  and report success. If you find yourself re-adding "leave the modal alone", stop:
  that is the contradiction, not a safety rule. (The modal is NOT universal — it is
  the large-session case only. In the 2026-07-19 recovery all five restored tracks
  came back at 43–74% context and none showed it; every one landed idle at `❯` and
  needed step 6's kick instead. Expect the kick path far more often than this one.)

While a picker OR that resume-choice prompt is open, the daemon reads the pane as a
structured gate and classifies it `blocked:human`, so it will not inject or restart
it. That self-heals the moment the human answers.

**A large session sitting on that modal is LOADED-BUT-NOT-RUNNING — that is what
"restored but still stuck" looks like (live 2026-07-19).** Restoring five Claude
tracks with `--resume` re-attached every conversation correctly, yet all five then
sat frozen on the summary-vs-full guard: the operator reads "not restarted." The
conversation IS back (verify by the pane's real tail + the token count matching the
transcript size), but nothing runs until the modal is answered. Clear it as the
bullet above says (`Down` → confirm → `Enter`, always option 2).

**LOADED IS NOT RUNNING — and that is true whether or not a modal appeared.** After
the modal is cleared (or when none appeared at all) the pane either self-continues,
because it died mid-turn, or lands idle at a ready `❯`, because its last turn had
finished. The second case is the common one, and it is what step 6's kick is for:
an idle restored track will sit there indefinitely. "Every conversation re-attached
correctly" is NOT the success condition for this runbook — "every track is `busy` in
the registry, or is deliberately left waiting on the maintainer" is.

### tmux gotchas that bit during this procedure

- **Use `command tmux`, never bare `tmux`.** A zsh `tmux` function shim errors
  `zsh: command not found: _zsh_tmux_plugin_run`; `command tmux` bypasses it (the
  same reason `tmuxio.py` shells out with an argv list rather than a shell string).
- **`respawn-pane -t` wants the BARE session name**, e.g. `-t livespec1` — NOT the
  `=name` exact-match form. `=livespec1` works for `has-session` / `list-panes` but
  `respawn-pane` rejects it with `can't find pane`. Bare exact names are unambiguous
  as long as no other session name is a prefix-extension of it.
- **Fresh session vs. existing pane.** If the tmux session is GONE, recreate it
  first (`command tmux new-session -d -s <name> -c <repo>`), then `respawn-pane -k …`
  — this mirrors the daemon's own `new_session` + `respawn_pane` split, so the shell
  / env behavior matches what works in production. If the pane already exists (e.g. a
  prior wrong-command attempt), `respawn-pane -k …` alone replaces it.

### Known gap worth closing — now CLAUDE-only (codex is closed)

For **codex**, `recover_missing_sessions` now DOES restore the live conversation: it
resumes by `codex resume <id>`, the id recovered from the surviving codex index by plan
topic (defect #5, 2026-07-18). For **claude**, the gap remains — `start` /
`recover_missing_sessions` relaunch fresh + paste a handoff rather than `--resume`. If
native "restore the live CLAUDE conversation after a crash" is wanted, that is where it
would go: a `claude --resume <id>` arm that looks the topic's id up by `customTitle` in
`~/.claude/projects/<cwd-slug>/` (the exact computation step 3 automates) — the direct
analogue of the codex reverse-index lookup just landed. Until then, this manual runbook
is the procedure for Claude tracks.

### Session-restart learnings (live-verified 2026-07-19)

A dedicated log of what actually bit while restarting tracks, so the next operator
does not re-learn it. Append here — do NOT scatter these.

- **`start` / `add` `--repo` MUST be the full ABSOLUTE path, never the bare slug.**
  `start --repo livespec --topic <t>` silently launches the session in `$HOME`: the
  bare `livespec` is a RELATIVE path, so tmux's `-c livespec` fails to that repo and
  falls back to home, the resume-line path (`livespec/plan/<t>/handoff.md`) is wrong,
  and `_do_launch` then fails at the await/submit while claude boots in the wrong cwd
  — reported only as a generic `start FAILED to launch`. Always pass
  `--repo /data/projects/<repo>`. (`repo_slug`/`tmux_id` still produce the right
  session NAME from a bare slug, which is why the failure is silent — only the cwd and
  resume path are wrong.)
- **A `--resume`d large session FREEZES on the summary-vs-full modal** — see "Two
  post-resume states are BOTH correct" above. Loaded ≠ running; answer the modal to
  make it run, canarying the `Down`→confirm→`Enter` keystroke.
- **Renaming a session out-of-band SELF-HEALS in the store — no manual store edit.**
  Renaming `<repo-slug>--<topic>` → the plain `<topic>` (or any name) with
  `command tmux rename-session` is safe: the daemon adopts the live claude by its
  REGISTRY name (the topic), independent of the tmux session name, and `adopt_sessions`
  re-points the mapping row's `tmux` field to the new name within one tick (R2 repoint).
  Verified live: renaming all six live sessions to bare topic names left the store
  auto-repointed and every row still tracked.
- **`overseerd` NEVER runs `recover_missing_sessions` — this runbook is the ONLY
  path back.** Recovery is gated behind `run_daemon`'s `recover` parameter, and the
  `overseerd` executable passes no `--recover` flag (it is surface-only). So a
  restarted daemon will NOT bring dead tracks back, and — the useful corollary —
  it also cannot CLOBBER a manual `--resume` restore that is in progress. The
  "Recovering + restoring" section's talk of "its startup `recover_missing_sessions`"
  describes the function, not something the shipped daemon actually invokes.
- **The codex index can hold a STALE NAMESAKE — never classify a track's runtime by
  topic alone.** `autonomous-mode` appeared in `~/.codex/session_index.jsonl` (so a
  reverse-index lookup calls it a Codex track and would `codex resume` it), while its
  REAL live track was a Claude session whose transcript sat in the crash-moment
  cluster; the index entry was a 6-day-old namesake. Cross-check the index hit's
  `updated_at` against the Claude transcript cluster and prefer the crash-moment
  evidence. Conversely, a topic NAMED for codex is not a codex track:
  `codex-yolo-sandbox` is a Claude session whose SUBJECT is codex.
- **A mapped track may have NEVER LAUNCHED — that needs `start`, not `--resume`.**
  `cockpit-ux-docs-release` was in `~/.livespec-overseer.jsonl` but had no transcript
  with that `customTitle` ANYWHERE on the host (and its repo had been untouched for
  ~9 days): it was registered and never started, so there was nothing to resume.
  Distinguish it from a killed track by the absence of ANY titled transcript, then
  launch it with the CLI (`supervisor.py start --repo <ABSOLUTE path> --topic <t>`),
  which pastes and auto-submits the resume line for you — no manual kick needed.
- **The crash-moment mtime cluster is the reliable id selector.** All six killed
  tracks' transcripts shared the same mtime to within a rounding minute, which
  separated them cleanly from older same-title predecessors. Trust that cluster over
  "most recent with this title"; a topic with 16 title-matching candidates resolved
  unambiguously this way.
- **`overseerd` keeps running the OLD code until you restart it.** The daemon is a
  long-lived process; editing `supervisor.py`/`registry.py` and merging does NOT change
  a running daemon's behavior. After landing an overseer code change, restart the daemon
  (re-run `overseer-start`, or kill the daemon pane and relaunch) to load it. The
  one-shot track CLI (`list`/`add`/`start`) DOES pick up new code immediately (fresh
  process per invocation).
- **The beside-tests are the ONLY gate and neither CI nor Fabro runs them.** Live proof
  (2026-07-19): commit `574192a8` wrapped every spawn with `unset TMUX; export
  TMUX_TMPDIR=…; exec …` but left `test_recover_still_recreates_a_claude_track_as_claude`
  asserting the bare command — it merged red and stayed red until this change repaired
  it. (That spawn wrap has since been REMOVED entirely by
  `plan/tmux-fleet-visibility/`; the lesson about the gate stands.) ALWAYS run
  `uv run pytest .claude/skills/overseer/ -q` before pushing any overseer
  change; a green PR here proves nothing on its own.

## Pointers

- `design.md` (beside the plan at `plan/overseer-rewrite/`) — the hardened
  design, including its "Adversarial review (2026-07-12)" section (the 8 blockers
  and why the mechanics are shaped as they are).
- `SKILL.md` — the runtime bottom-pane contract.
- `marker-protocol.md` — the escalating wrap-up + the ONE-state-file declaration
  contract (`ready` / `blocked: <reason>` / `winding-down`) and the restart
  interlock.
- The repo-root agent-instruction guidance — the root `AGENTS.md` and its
  `.ai/agent-disciplines` topic (the "Overseer / long-running-coordinator
  discipline" and "Factory-dispatch over inline implementation" sections).
