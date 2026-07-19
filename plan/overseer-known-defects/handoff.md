# Handoff — overseer daemon known defects (deferred from overseer-rewrite)

**Owning session:** livespec core, "overseer-known-defects". **Status:** COMPLETE —
all three defects landed: #4 DONE (`a24e3e13`, PR #1348); #6 DONE (`ae2b96f2`, PR #1363);
#5 DONE (this `overseer-codex-reboot-recovery` PR). See the PROGRESS section below. These
were the overseer daemon's known non-critical
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
- **#6 — DONE, merged (`ae2b96f2`, PR #1363).** `codex_sessions` was already injectable at
  the FUNCTION level, but the `Supervisor` threaded only `ppid_of` into it, so
  `adopt_sessions` / `_refresh_codex_sessions` still read the real `/proc` `comm==codex`
  scan and `~/.codex`. The `Supervisor` now carries `codex_home` + `codex_pids_of_comm` /
  `codex_fd_targets_of` / `codex_cwd_of` fields (default real, mirroring the Claude
  `sessions_dir` + `/proc` seams) threaded into BOTH codex call sites; the beside-tests'
  `_sup` factory defaults `codex_pids_of_comm` to an empty scan + `codex_home` to a
  non-existent dir, so no adopt/refresh test touches real host state. New sabotage-verified
  test (`test_refresh_and_adopt_route_codex_through_injected_seams`) simulates a codex
  session end-to-end through the injected seams; reverting either call site's seams reddens
  it. Done in the #6-then-#5 order the conflict required (both edit `codex_sessions.py` +
  `supervisor.py` + `test_supervisor.py`).
- **#5 — DONE (this `overseer-codex-reboot-recovery` PR), option (c) + (b) fallback as
  decided.** `recover_missing_sessions` is now RUNTIME-DISPATCHED. A dead codex is absent
  from the live `self._codex` map (no rollout fd at cold start), so the runtime is derived
  from the PERSISTENT codex index instead: if the track's TOPIC names a session in
  `session_index.jsonl` (`codex_sessions.latest_session_for_thread_name`, most-recent by
  `updated_at`), the track is CODEX — `_recover_codex_track` resumes the SAME rollout via
  `codex resume <id>` (`_do_codex_launch`) when it still exists on disk
  (`codex_sessions.rollout_exists`) [option c], else skips + surfaces ("codex track X was
  down at boot… it will re-adopt") [option b], NEVER mis-recreating as claude. A topic
  absent from the index is a Claude track and recovers as before. Three sabotage-verified
  beside-tests (dispatch, rollout-gate, latest-picker) + seven codex_sessions tests; the
  shared `_read_index_final` parser backs both `read_thread_names` and the new reverse
  lookup so they cannot drift. **Both required live verifications passed (2026-07-18):**
  (1) `codex resume --dangerously-bypass-approvals-and-sandbox <id>` reattached a
  **26-day-old** session (`console-specification-drafting`) with its `thread_name` intact,
  so the daemon re-adopts it; (2) the latest-by-`updated_at` pick is unambiguous — all four
  non-companion multi-id topics in the real index have DISTINCT timestamps. Also
  live-exercised: the reverse-index + `rollout_exists` functions against the real
  `~/.codex` (correct id, correct present/absent gate), and the shipped `_do_codex_launch`
  driving a real `respawn` + await against real tmux (returned True, pane came up codex).
  **Accepted design note (surfaced for the maintainer):** a topic named in the codex index
  is treated as CODEX at recovery, so a topic that was codex in the past but is now a
  Claude track would be resumed as codex — the decision (no stored runtime hint; option a
  was rejected) accepts this, bounded by (b) and by codex `resume` reattaching a real
  conversation (non-destructive, operator-visible). Two interstitials seen live, both a
  `› N.` gate → `blocked:human` → operator clears (self-healing): codex's directory-trust
  prompt (only for a repo codex has NOT trusted — recovery's `track.repo` is where the
  codex session ran, already trusted) and the working-dir picker (only when pane cwd ≠ the
  session's recorded cwd — recovery sets cwd to `track.repo`, which matches).

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

## Order taken (all landed)

The planned order held: **#4** → **#6** → **#5**.

1. **#4** — DONE (`a24e3e13`, PR #1348): the SF5 `(tmux, name)` keying that closed the
   monitoring outage.
2. **#6** — DONE (`ae2b96f2`, PR #1363): codex discovery seams threaded through the
   Supervisor so the beside-tests are hermetic (done before #5 because they conflict).
3. **#5** — DONE (this `overseer-codex-reboot-recovery` PR): reboot recovery is
   runtime-dispatched — codex tracks resume the same rollout (option c) or skip+surface
   (option b), never mis-recreate as claude; both required live verifications passed.

This track is COMPLETE. No further overseer known-defect items remain here.
`livespec-p9s0` (the ledger cross-repo-wiring staleness) is a separate ledger track (see
the "Not in this plan" section above), not an overseer defect.
