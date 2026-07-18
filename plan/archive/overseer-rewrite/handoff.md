# Handoff — overseer-rewrite

This plan thread is complete and archived.

The overseer-rewrite work rebuilt the two-pane overseer around one
**cardinal rule** — the daemon NEVER restarts a session that has not
declared itself `ready` — replacing the earlier timer-based
force-restart, which was removed as a severe bug (a live
`Bash(run_in_background)` build reads exactly like an idle session, so
a timer could `respawn-pane -k` real work). On top of that rule it
delivered the single tri-state `.overseer-state` indicator, the
escalating wrap-up lever, the notify-never-block console relay, full
Codex-track citizenship, and restart-correctness self-healing.

## Final State

- **Restart-correctness (R1 + R2 + idle-nudge 1-hour floor):** merged in
  livespec repository PR #1318 (`cf52b669`); 269 beside-tests green; each
  new guard sabotage-verified; Fable adversarial review NO BLOCKERS (five
  should-fix items addressed). R1 makes a failed resume-submit self-healing
  (the marker is not discarded; the SUBMIT is retried, never a re-respawn).
  R2 gives the Claude identity gate `topic in names` parity with the Codex
  gate and re-points a stale tmux mapping instead of freezing it. The
  idle-nudge now fires only after ≥1 hour continuously idle. The
  `livespec-overseer` daemon was respawned onto the merged code and
  re-adopted the fleet.
- **Codex full-citizen (monitor-only retired):** merged in livespec
  repository PR #1308 (`31fb34cb` + `c1aed0a4`) — a Codex track receives the
  escalating wrap-up AND is auto-restarted on its own `ready` via
  `codex resume --dangerously-bypass-approvals-and-sandbox <session-id>`,
  never the claude command (the one destructive bug, pinned by a
  sabotage-verified guard). Two independent Fable reviews: no blockers.
- **Codex session discovery:** merged in livespec repository PR #1296 —
  `codex_sessions.py` joins a codex process to its plan topic via the open
  rollout file → `session_index.jsonl` → `thread_name`, and reads ctx from
  each runtime's OWN statusline (never a re-derived occupancy formula).
- **Row taxonomy settled (`unassigned` / `session-gone` / `live-outside-tmux`;
  `not-claude` deleted; a dead mapping is KEPT as the memory of "ever seen"):**
  merged in livespec repository PRs #1293, #1295, #1299.
- **Detection accuracy + surfaces:** idle-with-context-left keep-going nudge
  (PR #1282), live-outside-tmux + note elision (PR #1286), labeled NEEDS YOU
  coordinates with a copy-pasteable jump command (PR #1258).
- **Gate:** this folder (`.claude/skills/overseer/`) sits OUTSIDE every product
  gate — ruff, pyright, coverage, and import-linter all exclude it and
  `just check` never collects it. The beside-tests are the ONLY gate:
  `uv run pytest .claude/skills/overseer/ -q`. Run them before any push, and
  sabotage-verify any new safety guard (one guard here was silently vacuous
  until sabotage revealed it).

## Read-First Chain

- `design.md` — the full two-pane / cardinal-rule design, the tri-state
  `.overseer-state` file, and the mapping-store schema.
- `restart-correctness-defects.md` — the R1/R2 defect analysis with the live
  timeline that motivated the self-healing resume-submit.
- `research/codex-ctx-and-restart-evidence.md` — the Codex ctx-source decision
  and the `codex resume` restart live-evidence.

## Deferred defects relocated (NOT closed by this thread)

- The daemon's non-critical defects #4–#6 were relocated to a dedicated,
  startable plan: `plan/overseer-known-defects/handoff.md` — two-codex-in-one-
  tmux shadowing (#4), the Claude-only reboot-recovery gap that needs a design
  call (#5), and the beside-tests touching real `/proc` and `~/.codex` (#6).
  Start that track to work them.
- `livespec-p9s0` (livespec repository ledger, P1) — the cross-repo pin
  "staleness" root cause (the wiring check reads siblings' LOCAL clones) belongs
  to the ledger / cross-repo-consistency track, not this daemon.

No next action remains for this thread.
