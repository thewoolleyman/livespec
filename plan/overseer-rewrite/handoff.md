# Handoff — the overseer auto-restart is NON-NEGOTIABLE (bug fixed)

**Status (2026-07-14): DONE + merged (livespec core, branch
`overseer-force-restart-stall`).** The daemon now FORCE-restarts a tracked session
that stalls idle at the danger line without certifying, and the (re)start command
carries `--dangerously-skip-permissions` so the resumed session is actually
autonomous. **HOLD on archive still stands** — this thread is complete but kept per
the maintainer's standing hold. **Owning session:** livespec core, "overseer-rewrite".

## The bug (maintainer-reported 2026-07-14)

The overseer's three PRIMARY requirements — (1) exit the stalled session, (2) restart
it with `claude --dangerously-skip-permissions`, renamed from the plan topic, and
(3) re-kick it from `plan/<topic>/handoff.md` — were **failing hard** on a live track.

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
`_do_restart(certified=…)`, `WRAPUP_TEMPLATE`), beside-tests (**151 green**),
`AGENTS.md` / `marker-protocol.md` / `SKILL.md`.

**The beside-tests are the ONLY gate on this folder** — it sits outside every product
gate (ruff / pyright / coverage / import-linter all exclude it, and `just check` never
collects it), so a broken change here merges green with nothing having exercised it.
ALWAYS run before pushing:

```bash
uv run pytest .claude/skills/overseer/ -q
```

## Resume command

**Nothing to resume — the fix is complete and merged.** If you pick this thread up
again, the live follow-ups are:

- **A running daemon must be restarted to pick up new code.** `overseerd` is a
  long-lived process in the `livespec-overseer` top pane; it keeps running whatever
  code it started with. After any merge here, restart that pane's daemon.
- **Codex adoption (documented gap).** Codex sessions are not in Claude's session
  registry (`~/.claude/sessions/<pid>.json`), so `adopt_sessions` cannot see them.
  The entry point would be a codex session-store reader feeding the same
  `adopt_sessions` guard.
