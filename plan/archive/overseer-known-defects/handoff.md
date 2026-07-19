# Archived — overseer daemon known defects (COMPLETE)

**Status:** COMPLETE (2026-07-19). All three deferred overseer-daemon known
defects landed in `thewoolleyman/livespec`. None was correctness-critical (none
could violate THE CARDINAL RULE — the daemon never restarts a session that has
not declared itself `ready`). Archived from `plan/overseer-known-defects/`.

The overseer is LOCAL-ONLY and unsynced (`.claude/skills/overseer/`, outside
every product gate — no CI). Durable maintenance context lives in that folder's
`AGENTS.md`; this record is the thread's close-out.

## What landed

- **#4 — two codex sessions in one tmux session shadowed each other**
  (`a24e3e13`, PR #1348). `codex_by_tmux_session` re-keyed by
  `(tmux_session, name)` so neither shadows the other; consumers resolve each
  track by `(tmux, topic)`. The codex analogue of R2's set-valued `_claude_names`.
- **#6 — beside-tests touched the real `/proc` + `~/.codex`** (`ae2b96f2`,
  PR #1363). Threaded codex-discovery seams (`codex_home` +
  `codex_pids_of_comm` / `codex_fd_targets_of` / `codex_cwd_of`) through the
  `Supervisor` so `adopt_sessions` / `_refresh_codex_sessions` are hermetic; the
  beside-tests' `_sup` factory defaults them to an empty scan + a non-existent
  `~/.codex`. Sabotage-verified.
- **#5 — reboot recovery was Claude-only** (`d090466a`, PR #1370).
  `recover_missing_sessions` is now runtime-dispatched: a dead track whose TOPIC
  names a session in the persistent codex index (`session_index.jsonl`, which
  survives the session's death) is CODEX — resumed via `codex resume <id>`
  (option c) when its rollout still exists on disk, else skip+surfaced (option b),
  NEVER mis-recreated as claude. Implemented option (c)+(b) exactly as the
  maintainer decided (2026-07-18). Three sabotage-verified supervisor tests +
  seven `codex_sessions` tests.
- **combine-fix** (`73b0cf1f`, PR #1373). A concurrent overseer merge wrapped the
  launch commands with `unset TMUX; export TMUX_TMPDIR=…; exec …`; #5's
  claude-recovery test hardcoded the old command string and reddened on combined
  master. Rebuilt its expected from `_launch_command` (drift-proof).

**LESSON (proven live this thread):** `.claude/skills/overseer/` runs NO CI, so
two overseer branches can merge git-clean and still leave the folder red — #5 was
green on its own base and red on combined master. After ANY overseer merge,
re-run `uv run pytest .claude/skills/overseer/ -q` against the COMBINED master
state; do not trust either PR's own green. (Now also stated in the folder's
`AGENTS.md` beside-test bullet.)

## Live verification (#5)

Both handoff-required items passed (2026-07-18): (1) `codex resume <id>`
reattached a **26-day-old** session with its `thread_name` intact, so the daemon
re-adopts it; (2) the latest-by-`updated_at` pick is unambiguous — every real
multi-id topic in the index has distinct timestamps. Also live-exercised: the
reverse-index + `rollout_exists` against the real `~/.codex`, and the shipped
`_do_codex_launch` driving a real respawn + await against real tmux.

## Accepted design note (#5)

A topic named in the codex index is treated as CODEX at recovery, so a topic that
was codex in the past but is now a Claude track would resume as codex. The
decision (no stored runtime hint — option (a) was rejected) accepts this, bounded
by (b) and by codex `resume` reattaching a real, operator-visible conversation.
Two startup interstitials seen live, both a `› N.` gate → `blocked:human` →
operator clears (self-healing): codex's directory-trust prompt (only for a repo
codex has NOT trusted — recovery's `track.repo` is where the codex session ran,
already trusted) and the working-dir picker (only when pane cwd ≠ the session's
recorded cwd — recovery sets cwd to `track.repo`, which matches).

## Not in this track

`livespec-p9s0` (the ledger's cross-repo wiring check reading stale LOCAL clones,
which flaps phantom drift) is a **ledger** issue, not an overseer defect — it
lives with the ledger / cross-repo-consistency work, not this daemon. The durable
fix (read the canonical fetched branch, and/or keep local clones fresh) is the
ledger track's call.
