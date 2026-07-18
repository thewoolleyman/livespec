# Handoff — overseer daemon known defects (deferred from overseer-rewrite)

**Owning session:** livespec core, "overseer-known-defects". **Status:** IN PROGRESS —
#4 DONE (merged `a24e3e13`, PR #1348); #5 DECIDED (option c + b-fallback); #6 UNBLOCKED.
See the PROGRESS section below. These are the overseer daemon's known non-critical
defects, deferred while the
**restart-correctness** priority was in flight. That priority is now DONE — R1
(self-healing resume-submit) + R2 (Claude name-gate + stale-mapping re-point) + the
idle-nudge 1-hour floor are merged (`cf52b669`, PR #1318) and the daemon is respawned onto
that code. This track picks up the leftovers.

None of these is correctness-critical (none can violate THE CARDINAL RULE — the daemon
never restarts a session that has not declared itself `ready`). They are a monitoring
outage (#4), a runtime-recovery gap that needs a design call (#5), and test-isolation
hygiene (#6). Work them in the order below; each is independent.

## PROGRESS (2026-07-18)

- **#4 — DONE, merged.** `codex_by_tmux_session` is now keyed by `(tmux_session, name)`
  so two codex sessions sharing one tmux session no longer shadow each other; both
  consumers (`_is_codex_track`, `_do_codex_restart`) resolve each track to ITS OWN
  session by `(tmux, topic)`. Merged as `a24e3e13` (PR #1348). Two new beside-tests,
  BOTH sabotage-verified (the map builder + the supervisor consumers). This is the codex
  analogue of R2's set-valued `_claude_names` (SF5).
- **Combined-state reconciliation — merged (PR #1350).** #4 auto-merged (rebase) cleanly
  at the git level ON TOP of the concurrently-merged `overseer-tmux-runtime-column`
  feature (`467e9cb3`), but that feature's new test built `sup._codex = {session: ...}`
  (the OLD single-string key) and #4's `_is_codex_track` reads the map by `(session,
  topic)` — so on combined master the runtime test read `runtime=None` and went red
  (1 failed / 279 passed). Fixed by the same mechanical `(session, topic)` key update.
  **LESSON (load-bearing for this folder):** because `.claude/skills/overseer/` runs NO
  CI, two overseer branches can merge git-clean and still leave the folder red. After ANY
  concurrent overseer merge, re-run `uv run pytest .claude/skills/overseer/ -q` against
  the COMBINED master state — do not trust either PR's own green.
- **#5 — DECIDED (maintainer, 2026-07-18): option (c) + (b) fallback.** Give reboot
  recovery Codex parity: resume a dead codex track via `codex resume <id>` rather than
  recreating it as claude. The session-id is recovered by REVERSING the persistent codex
  index (`session_index.jsonl`, which survives the session's death — `read_thread_names`)
  to find the session(s) for the mapped topic, picking the most-recent by `updated_at`.
  Resume ONLY if that rollout still exists on disk; otherwise FALL BACK to (b) — skip and
  surface in NEEDS YOU ("codex track X was down at boot; relaunch it, it'll re-adopt"),
  never mis-recreating as claude. Rationale: Claude recovery launches a FRESH session +
  handoff (continuity via the handoff file); codex `resume` reattaches the OLD rollout,
  which is parity-or-better continuity. Two things to VERIFY LIVE before claiming done
  (the (b) fallback bounds the risk if either disappoints): (1) `codex resume <old-id>`
  reliably reattaches a long-dead session; (2) the latest-by-`updated_at` pick is
  unambiguous in real index data. NOT yet implemented — implement on post-#4 master.
- **#6 — now UNBLOCKED.** It was held only because the `overseer-tmux-runtime-column`
  work had uncommitted edits in `supervisor.py` + `test_supervisor.py`; that feature is
  now merged (`467e9cb3`), so the contention is gone. #6 still edits `codex_sessions.py`
  + `supervisor.py` + `test_supervisor.py`, which #5 ALSO touches, so **#5 and #6 conflict
  with each other — sequence them** (original suggested order: #6 then #5).

## Where the code + the discipline live

All code is folder-local to `.claude/skills/overseer/` (stdlib-only, host-only, OUTSIDE
every product gate — ruff / pyright / coverage / import-linter all exclude it, and
`just check` never collects it). Read `.claude/skills/overseer/AGENTS.md` first — it is the
maintenance guide with the load-bearing invariants.

**The beside-tests are the SOLE gate on this folder.** `just check`, the pre-push hook, and
CI do NOT exercise it, so a broken change here merges green with nothing having run it.
ALWAYS, before any push:

```bash
uv run pytest .claude/skills/overseer/ -q
```

And **sabotage-verify every new guard** — break the thing it guards and watch its test go
red, then restore. This folder has a history of silently-vacuous guards that only sabotage
revealed. Follow the repo mutation protocol (worktree → PR → merge → cleanup); overseer
`.py` is exempt from the Red-Green-Replay ritual (it is not an `_IMPL_PREFIXES` path), so
use a `fix(overseer):` subject with test + impl in one commit, and never `--no-verify`.

Relevant modules: `supervisor.py` (the daemon), `codex_sessions.py` (codex discovery),
`claude_sessions.py` (Claude registry discovery — its R2/SF5 `names_by_tmux_session`
set-valued map is the pattern to mirror for #4). Beside-tests: `test_supervisor.py`,
`test_codex_sessions.py`, `test_claude_sessions.py`.

## Defect #4 — two codex sessions in one tmux session shadow each other

**Symptom (monitoring outage, not destructive).** `codex_sessions.codex_by_tmux_session`
keeps ONE `CodexSession` per tmux session (first/last-by-pid wins), so when two codex
sessions run in the SAME tmux session, the second shadows the first — that track silently
loses its ctx reading and its monitoring (no wrap-up, no restart, invisible in the table).

**Root cause.** `codex_by_tmux_session` returns `{tmux_session: CodexSession}` — a single
value per tmux session. `_is_codex_track` and `_do_codex_restart` look the track's session
up by tmux session (`self._codex.get(session)`), so if two codex tracks share a tmux
session, one of them resolves to the wrong `CodexSession` (or None).

**Fix direction.** This is the codex analogue of R2's SF5 fix for Claude
(`_claude_names` became a SET so a helper Claude in the same tmux session can't shadow the
track). Disambiguate codex sessions by NAME (= plan topic) within a tmux session: either
key the map by `(tmux_session, name)`, or make it multi-valued (`{tmux_session:
[CodexSession, ...]}`) and have `_is_codex_track` / `_do_codex_restart` pick the
`CodexSession` whose `name == topic`. The join already carries `name`; the fix is purely in
how the map is keyed/consumed. Keep it fail-soft (no match → not codex, as today).

**Acceptance (beside-tests).** A test with TWO codex sessions (different `name`s) resolving
to the SAME tmux session: assert each track resolves to ITS OWN `CodexSession` (correct ctx
+ session-id), neither shadows the other, and a `ready` restart of one targets the right
session id. Sabotage-verify (revert to single-valued → the second track's test goes red).

## Defect #5 — `recover_missing_sessions` is Claude-only (needs a design call)

**Symptom.** Startup recovery (`recover_missing_sessions`, run once at daemon boot)
re-launches the CLAUDE command for any mapped session that is gone. A codex track that died
while the daemon was DOWN is therefore recreated as a CLAUDE session — its rollout orphaned.
Non-destructive (only ABSENT sessions are recreated; a live codex is never touched), but
wrong-runtime.

**Root cause.** Recovery cannot know a dead track's runtime under the runtime-derived-live
design: a dead codex has no live rollout fd at recovery, so there is no live signal that
says "this topic was codex." While the daemon is UP, the per-tick restart path DOES dispatch
by runtime (it reads the live codex map) — the gap is ONLY the cold-start recovery path.

**Fix direction — this one needs a maintainer decision before coding, so START by drafting
the options and surfacing them (notify-never-block), do not just pick one:**
- **(a) Persist a runtime hint.** Store the last-known runtime (or codex session-id /
  `thread_name`) on the mapping row, so recovery can dispatch codex correctly. Cost: a new
  stored field + keeping it fresh (adoption writes it). This reintroduces a small piece of
  stored-not-derived state — weigh against the "identity derives; nothing is stored"
  principle (AGENTS.md invariant on the codex mapping).
- **(b) Skip + surface.** Recovery skips a track it cannot prove is Claude and SURFACES it
  ("codex track <topic> was down at boot; restart it manually / it will re-adopt when
  relaunched") rather than mis-recreating it as claude. Cheaper, no stored state, but
  recovery no longer auto-restarts codex tracks.
- **(c) Codex-session-store lookup by `thread_name`** (the `recover_missing_sessions`
  docstring names this): a persistent codex index (`session_index.jsonl`) already maps
  session-id → `thread_name`; if a dead track's topic can be resolved to a prior session-id
  there, `codex resume <id>` could recreate it as codex. Verify the index survives the
  session's death and the id is still resumable.

Recommend **(b)** as the smallest correct fix (no stored state, never mis-recreates), with
**(a)/(c)** as follow-ups if auto-restart-on-reboot for codex is wanted. Surface the choice
to the maintainer first.

**Acceptance.** A beside-test: a mapped codex track absent at startup → recovery does NOT
launch the claude command for it (per the chosen option: skips + surfaces, or recreates via
`codex resume`). Keep the existing Claude-recovery test green.

## Defect #6 — beside-tests touch the REAL `/proc` and `~/.codex`

**Symptom.** Some beside-tests call `adopt_sessions()` / `_refresh_claude_status()` (which
calls `_refresh_codex_sessions()`) with the Supervisor's DEFAULT seams, so they read the
REAL `/proc` and `~/.codex` rollout dir. Deterministic today (a tmp-dir cwd cannot match a
fleet repo, so nothing is adopted), but it is a real host coupling in a unit suite — a
running codex on the host could in principle perturb a test, and the suite is not hermetic.

**Root cause.** `codex_sessions` reads `/proc` (the pid scan) and the real `~/.codex`
rollout dir directly, and the Supervisor's `_refresh_codex_sessions` calls it without an
injected fake for those. `claude_sessions` is already fully injectable (its `/proc` readers
+ `sessions_dir` are seams the tests fake); `codex_sessions` needs the same treatment.

**Fix direction.** Add injection seams to `codex_sessions` (the `/proc` pid scanner + the
codex rollout dir / `session_index.jsonl` path), mirroring `claude_sessions`
(`default_sessions_dir` + injected `proc_*` readers). Thread them through the Supervisor
(`codex_scan` / `codex_home` fields, defaulting to real, injected by tests) so EVERY test
path drives fakes and touches no real host state. Then the existing tests that call
adopt/refresh can inject empty codex state explicitly.

**Acceptance.** A test-isolation assertion: exercising the adopt/refresh paths with injected
codex seams reads NO real `/proc` or `~/.codex` (e.g. inject a scanner that raises if
called with real paths, or assert the injected fake is the only reader hit). The suite stays
green with a running codex on the host.

## Not in this plan — `livespec-p9s0` (ledger, separate repo/track)

The old overseer-rewrite handoff listed a defect #7: the ledger's cross-repo wiring check
reads siblings' LOCAL clones (not `origin`, no fetch), so a stale local clone flaps phantom
drift. That is a **ledger** issue (`livespec-p9s0`, P1), NOT an overseer defect — it belongs
to the ledger/cross-repo-consistency work, not this daemon. Track it there; it is noted here
only so it is not lost. The durable fix (read the canonical fetched branch, and/or keep
local clones fresh, and the orphaned-repo angle) is the ledger track's call.

## Suggested order

1. **#4** first — smallest, self-contained, and the SF5 pattern (`names_by_tmux_session`) is
   right there to mirror; closes a real monitoring outage.
2. **#6** next — test hygiene, unblocks confident work on codex paths (a hermetic suite).
3. **#5** last — needs the maintainer design call (surface options (a)/(b)/(c) first); the
   smallest correct fix (b) is non-destructive and can land independently.
