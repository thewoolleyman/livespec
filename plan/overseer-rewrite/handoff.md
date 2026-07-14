# Handoff — the overseer auto-restart is NON-NEGOTIABLE (fixed, and now proven live)

**Status (2026-07-14): DONE + merged + LIVE-EXERCISED.** The daemon now FORCE-restarts
a tracked session that stalls idle at the danger line without certifying, and the
(re)start command carries `--dangerously-skip-permissions` so the resumed session is
actually autonomous. The fix has since been **exercised end-to-end on a real stalled
track** (evidence below), which closes the "done means rolled out and exercised live"
leg. **HOLD on archive still stands** — this thread is complete but kept per the
maintainer's standing hold. **Owning session:** livespec core, "overseer-rewrite".

## Live-exercise evidence (2026-07-14) — the fix worked on a real track

The very stall that motivated the fix was then resolved BY the fix, unattended.
`tmp/overseer/daemon.log` recorded the full sequence against the real
`overseer-rewrite` track:

```
overseer[SURFACE]: …::overseer-rewrite won't wrap up (ctx 13% left, no ready marker); force-restart in 90s
… (countdown ticks: 78s, 65s, 53s, 41s, 28s, 16s, 4s)
overseer[SURFACE]: …::overseer-rewrite stalled idle at ctx 13% with no ready marker for 98s — force-restarting (auto-restart is non-negotiable)
overseer: restarted /data/projects/livespec::overseer-rewrite (pane %6)
```

All three primary requirements fired: the wedged session was **exited**, **restarted**
as `claude --dangerously-skip-permissions -n overseer-rewrite`, and **re-kicked** with
`read …/plan/overseer-rewrite/handoff.md and follow it`. The fresh session that came up
in pane `%6` (tmux `livespec4`) confirmed its own identity and wrote this section — i.e.
the restarted session IS the evidence. Before the fix, this identical stall wedged the
track forever.

## The bug (maintainer-reported 2026-07-14)

Session `livespec4` (topic `overseer-rewrite`) sat **idle at 13% context**, correctly
rendered as `danger` by the daemon, and was **never restarted**. Two independent root
causes:

1. **The restart was conditional on the tracked session's cooperation.** The daemon
   restarted only on a valid `.overseer-ready` marker; at the danger line with no
   marker it merely SURFACED the stall ("never force-kill a session mid-work" — the
   original design's explicit guard). That session had **refused to write either
   marker**: its real pending work had drifted away from
   `plan/overseer-rewrite/handoff.md` (it had stashed its live handoff in a `/tmp`
   scratchpad), so it reasoned that certifying would resume the next session from a
   stale document — and it stopped, un-certified, explaining itself in prose. The
   track wedged **forever**. A session holding semantic judgment could therefore veto
   the one mechanic the overseer exists to perform.
2. **The launch command never passed `--dangerously-skip-permissions`.**
   `_launch_command` returned `claude -n <topic>`, so even a *successful* restart
   would have come up requiring permission prompts — i.e. not autonomous, silently
   defeating the point.

## The fix

- **`_danger_or_force_restart` + `_STALL_RESTART_GRACE` (90s).** The marker is now a
  **fast path, not a veto**. A warned track that stays continuously **idle + settled**
  at/below `DANGER_CTX_REMAINING` (20% left) without certifying is **force-restarted**
  after the grace, running the *identical* respawn + resume mechanics as the certified
  path. `_InjectState.danger_idle_since` timestamps when the stall began, and
  `evaluate` resets it on any non-stall status, so only a genuine *continuous* stall
  accrues toward the grace. Guarded on `warned` (an injection stamp exists ⇒ the
  wrap-up actually landed), so a pane too broken to receive the wrap-up is surfaced
  rather than respawned into.
- **`_launch_command` → `claude --dangerously-skip-permissions -n <topic>`.**
- **`WRAPUP_TEMPLATE` rewritten** to tell the session plainly that it WILL be
  restarted regardless, that `plan/<topic>/handoff.md` is the ONLY artifact the fresh
  session inherits (so drift is fixed by REWRITING the handoff, never by withholding
  the marker), and that it must write exactly ONE of the two markers — "neither" is
  not a valid outcome.
- **Encoded as REQUIREMENTS**, per the maintainer: `.claude/skills/overseer/AGENTS.md`
  **invariant 7** (the three restart requirements + "a missing certification must not
  wedge a track"), `marker-protocol.md` §"The restart is NON-NEGOTIABLE", `SKILL.md`,
  this thread's `design.md`, and a new `.ai/agent-disciplines.md` §"Tracked-session
  discipline — the overseer wrap-up contract" (the other half of the contract: what a
  supervised session owes).

## Why this is NOT the "never force-kill mid-work" regression

**"Mid-work" means BUSY.** The force-restart is reachable ONLY from the idle branch of
`evaluate` — the pane is already proven not-busy, `_pane_settled` across two captures,
identity-gated Claude, NOT at a structured gate, and NOT `.overseer-blocked`. A busy
pane stays `working` and is never touched; a human-gated pane is never restarted (a
human gate is the one thing that still suppresses the restart). And `respawn-pane -k`
kills a **process**, not work: every file, worktree, commit, and branch on disk
survives it. The only thing a session can actually lose by being force-restarted is
resume state it chose to keep OUTSIDE its handoff — which the wrap-up now explicitly
forbids.

## Where the code lives

`.claude/skills/overseer/` — `supervisor.py` (`_danger_or_force_restart`,
`_STALL_RESTART_GRACE`, `_InjectState.danger_idle_since`, `_launch_command`,
`_do_restart(certified=…)`, `WRAPUP_TEMPLATE`), beside-tests (**164 green**),
`AGENTS.md` / `marker-protocol.md` / `SKILL.md`.

**The beside-tests are the ONLY gate on this folder** — it sits outside every product
gate (ruff / pyright / coverage / import-linter all exclude it, and `just check` never
collects it), so a broken change here merges green with nothing having exercised it.
ALWAYS run before pushing:

```bash
uv run pytest .claude/skills/overseer/ -q
```

## Resume command

**Nothing to resume — the fix is complete, merged, and now live-exercised.** A later
commit (`50648c7`) additionally taught the daemon that a live background shell reads
BUSY rather than idle (so a session with a `run_in_background` command is never
force-restarted out from under its own work) and made `overseer-start` self-heal the
split. If you pick this thread up again, the live follow-ups are:

- **Codex adoption (documented gap — the one genuinely open item).** Codex sessions are
  not in Claude's session registry (`~/.claude/sessions/<pid>.json`), so
  `adopt_sessions` cannot see them. The entry point would be a codex session-store
  reader feeding the same `adopt_sessions` guard. Note the *busy* signal already covers
  Codex (`claude_sessions.has_active_subshell` is a process-tree check, runtime-
  agnostic); it is only ADOPTION that is Claude-only.
- **A running daemon must be restarted to pick up new code** (standing operational rule,
  not an open task). `overseerd` is a long-lived process in the `livespec-overseer` top
  pane; it keeps running whatever code it started with. After any merge here, restart
  that pane's daemon. As of 2026-07-14 the running daemon already carries current code —
  it is the one that executed the force-restart above.
