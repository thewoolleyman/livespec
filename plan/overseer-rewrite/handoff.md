# Handoff — overseer rewrite (final validation + code-review hardening)

**Status (2026-07-13):** BUILT + MERGED + LIVE-EXERCISED + CODE-REVIEWED +
HARDENED. The deterministic overseer daemon shipped, was validated end-to-end
against a real Claude TUI, then two independent adversarial CODE reviews found 8
real blocker-classes — all fixed in **livespec PR #1138**
(`fix-overseer-review-blockers`) and re-validated live. This file is the
self-sufficient record. **Owning session:** livespec core, "overseer-rewrite".

## Bottom line

The overseer is a deterministic tmux-supervising daemon (top pane,
`supervisor.py`) + a thin interactive `/overseer` skill (bottom pane), local-only
at `.claude/skills/overseer/` in **livespec**. It watches each tracked session's
context %, injects a wrap-up at threshold, and — once the session certifies "done"
via an out-of-band `.overseer-ready` marker — atomically restarts it with a fresh
context, renamed to the plan topic. It is a **PERMANENT human-supervised alternate
to autonomous mode** (the Beads/Dolt + Fabro Dispatcher), not a stopgap. Full
design: `design.md` beside this file.

## What is DONE (all on `master` unless a PR is noted)

1. **Built + merged + first live-exercise** — PRs #1106/#1108/#1109, dev-tooling
   #344/#345, #1118/#1119/#1121/#1124/#1125/#1128. Modules: `registry.py`,
   `signals.py`, `tmuxio.py`, `supervisor.py`, `SKILL.md`, `AGENTS.md`,
   `marker-protocol.md`, `.claude/CLAUDE.md` symlink.

2. **REMAINING TASK 1 (full one-shot live test) — PASS.** Drove the whole
   unattended cycle against a real Claude TUI in an isolated scratch session
   (never any of the ~19 real sessions): inject → session self-certified (wrote
   `.overseer-ready` = sha256(handoff), hash matched, NO stand-in) → restart +
   rename (PID changed, marker deleted) → resumed `RESUMED` on fresh context;
   plus archive-GC and reboot-recovery. Signal functions validated against the
   REAL pane. **Gap found later:** this test stopped at the first restart and
   never ran a SECOND cycle on a daemon-RENAMED session, nor drove the shipped
   `--`/colon naming — both of which the re-review caught (B2, B1).

3. **REMAINING TASK 2 (two adversarial CODE reviews) — DONE, found 8 blockers.**
   A Fable-model agent (8) + a Codex agent (5, a corroborating subset) reviewed
   the SHIPPED code. NOT a NO-BLOCKERS pass. All 8 verified (B1/B2 empirically
   against tmux 3.5a + a live TUI; the rest by source reading) and FIXED in
   **PR #1138**:
   - **B1** `<slug>:<topic>` tmux name never round-trips (tmux sanitizes `:`→`_`)
     + `has-session` prefix-matches → `--` separator + exact `list_sessions`
     membership.
   - **B2** `claude -n <topic>` titled input-box border defeated `is_idle_input`
     → every daemon-launched/restarted session became permanently unmanageable
     (ran to autocompact) → title-tolerant border match.
   - **B3** no pane-identity check on the act path → wrap-up pasted into a shell,
     executing + forging a marker → gate every act on `pane_is_claude` +
     `path_in_repo` (`not-claude` status).
   - **B4** injection stamp outlived the round + a human resuming a certified pane
     got respawn-killed → clear stamp on restart + void the ready marker on
     post-cert activity (durable).
   - **B5** failed respawn/paste ignored + marker deleted anyway → propagate
     return values; keep the marker on a failed restart.
   - **B6** store non-atomic/unlocked/GC'd every tick (incl. `list`), global paste
     buffer, two-daemon races → atomic writes, flock'd RMW, read-only `list`,
     per-op paste buffer, singleton daemon lock, active-wins + repo-root-present
     GC semantics.
   - **B7** one unreadable `plan/` crashed the whole loop → OSError guards + broad
     per-tick except.
   - **B8** `start` respawn-killed a live session → refuse without `--force`.

4. **Fix validation.** 101 beside-tests green (+18 new B1–B8 regression tests);
   `just check` green (all 63 targets); **fuller live re-test** drove the `--`
   naming round-trip (B1), **TWO full inject→certify→restart cycles on a
   daemon-renamed session** (B2 — the missed case), a shell pane reading
   `not-claude` with no forged marker (B3), the stamp cleared on restart (B4),
   acting archive-GC, read-only `list`, and reboot-recovery. All scratch state
   removed; real sessions untouched.

5. **Reframe (maintainer instruction 2026-07-13).** Removed all
   "temporary / retained-until-console" framing from `SKILL.md`, `AGENTS.md`, and
   `design.md`; the overseer is now documented as a PERMANENT human-supervised
   alternate to autonomous mode, still local-only and usable only from this repo.

## Re-review of the fixes (2 rounds) — 7 findings, all resolved bar 1 tradeoff

Per the ratification discipline, PR #1138's fixes got a second independent
READ-ONLY re-review (Fable + Codex). Both flagged real issues in the FIXES — the
re-review earned its keep:

**Fable re-review (4):**
- **RB1 (critical):** the B4 "void ready marker when busy" raced the certifying
  turn's OWN busy tail (final streaming + stop hooks keep the pane busy 10-60s
  while the marker is already valid), so a continuous loop voided legit
  certifications and the restart never fired. FIXED with a **120s grace** — a
  marker is voided on busy only once older than the grace (too old to be the
  tail). My first live re-test MASKED this by using hand-spaced `--once` ticks;
  re-validated with a CONTINUOUS 5s loop (below).
- **RB2 (high):** after a void, the round could not re-certify (stamp cleared but
  in-memory count stuck at 1). FIXED — `_void_ready_marker` pops the inject state.
- **RB3 (incomplete):** `-t <session>` was still prefix-prone if the session died
  mid-tick (could `respawn-pane -k` a live sibling like `livespec--overseer-rewrite`).
  The `=`-prefix suggestion does NOT work for pane ops (verified). FIXED with
  **pane-id targeting** (exact, stable across respawn, fails-soft — verified live).
- **RB4 (low):** `start` failed OPEN on an unreadable command. FIXED — fails closed.

**Codex re-review (3):**
- **#1 (real):** the identity gate ran once at tick top, then the 0.6s settle
  opened a TOCTOU window (claude could exit to a shell). FIXED — re-check
  `pane_is_claude`+`path_in_repo` IMMEDIATELY before acting.
- **#3 (real):** `new_session()` failure was ignored before `_do_launch`→respawn,
  which could target a prefix-matched sibling. FIXED — require exact
  `session_exists` after `new_session` in recover + start.
- **#2 (deliberate tradeoff, KEPT):** `_do_restart` voids the marker even on a
  failed resume-submit. Keeping it would re-`respawn-pane -k` and kill the fresh
  session in a loop; voiding + surfacing is the safe choice. Documented in the
  `_do_restart` docstring; noted for the maintainer.

**Fix re-validation:** 106 beside-tests green (+ RB/Codex regression tests);
CONTINUOUS 5s-loop live test ran **THREE full inject→certify→restart cycles**
unattended with **zero spurious marker voids** (RB1 proof) and stable pane-id
`%39` across restarts (RB3 proof); all scratch state removed; real sessions
untouched.

## Current status (2026-07-13) — ALL FIXED + LANDED; HOLD before archive

- **All 15 review findings are fixed and on `master`** (release **0.9.4**): the 8
  blockers via **PR #1138** (auto-merged green by `app/livespec-pr-bot`), the 7
  fix-re-review findings via **PR #1142**. Codex #2 intentionally kept (documented
  tradeoff). Both PRs auto-merged on CI-green — note CI does NOT exercise this
  folder, so "green" only ever meant the product/plugin was unbroken, never that
  the overseer works; the review was an out-of-band human/agent pass.
- **Beside-tests are the ONLY gate on this folder** (not `just check`/CI). **PR
  #1144** added an AGENTS.md rule: ALWAYS run `uv run pytest
  .claude/skills/overseer/ -q` before pushing any change here, and exercise
  timing behavior with a CONTINUOUS loop (the RB1 lesson).
- **Final master-artifact validation done** (against the merged code on the
  primary checkout): a deterministic restart tick restarted the session
  (`respawn` by pane `%41`, PID changed, marker consumed, resume line pasted →
  `RESUMED`); the blocked-marker path was also exercised live (a session with an
  emptied fixture correctly wrote `.overseer-blocked` and the daemon suppressed
  restart). All scratch state removed; the 20 real sessions untouched.
- **HOLD — do NOT archive or close this plan thread.** Maintainer instruction
  (2026-07-13): the overseer stays as-is until the maintainer has done their OWN
  exploratory testing and gives the go-ahead. Only THEN archive to
  `plan/archive/overseer-rewrite/`.

## Read-first chain (before acting)

1. `design.md` — full design + "Adversarial review (2026-07-12)" (design
   blockers) + "Live-exercise corrections (2026-07-13)".
2. `.claude/skills/overseer/signals.py`, `supervisor.py`, `tmuxio.py`,
   `registry.py` — the shipped code (post-PR #1138).
3. `.claude/skills/overseer/AGENTS.md` — maintenance invariants + the B1–B8 fix
   rationale embedded in the docstrings.
4. `.claude/skills/overseer/marker-protocol.md` — the wrap-up + marker contract.

## Verified environment facts

- `command tmux` = tmux 3.5a (bypass the zsh alias). `claude` at
  `/home/ubuntu/.local/bin/claude`. Statusline emits `Ctx: N% left` LAST (after
  cwd) — a narrow pane / very long path truncates it → daemon reads unknown and
  degrades safely (fail-closed); a fresh 0-turn session has no `Ctx:` until its
  first turn.
- Beside-tests: `uv run pytest .claude/skills/overseer/ -q` (NOT in the product
  `tests/` suite). The folder is OUTSIDE the product gates (ruff extend-exclude,
  pyright.include omit, coverage testpaths, import-linter root). `just check`
  passes but does NOT run the beside-tests.
- **SAFETY:** all live testing uses ISOLATED scratch sessions with unique names
  (e.g. `ov--e2e2`, `ovtest-*`) in a scratch repo under the scratchpad — NEVER a
  real session. Managed repos must be Claude-*trusted* before a restart (the
  first-run trust prompt otherwise intervenes).

## Definition of DONE

Everything the code/review side requires is DONE: both original remaining tasks
passed; all 15 review findings (8 blockers + 7 fix-re-review) are fixed, landed on
`master` (0.9.4), and validated live; the AGENTS.md test-before-push rule is added
(PR #1144). The ONLY thing left is the maintainer's own exploratory testing.

**Archive is BLOCKED on the maintainer.** Do NOT move this thread to
`plan/archive/overseer-rewrite/` until the maintainer confirms they have
exploratory-tested the overseer themselves and gives the go-ahead. Until then the
thread stays active as the resume point.

## Resume command

`read plan/overseer-rewrite/handoff.md and follow it`
