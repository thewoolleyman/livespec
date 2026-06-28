# Overseer startup — factory-reliability phase: harden the factory, finish the tail, groom M2

Run this to drive the livespec overseer. The large epics are CLOSED and the
ready punch-list work-items are now carried by the **Beads/Dolt + Fabro
factory**. This phase: make the factory reliable enough to run those items
unattended, finish a small deferred tail, and walk the maintainer through the M2
groom. Load and follow the local overseer skill at
`.claude/skills/overseer/SKILL.md` (invoke `/overseer`). Detailed evidence +
resume commands live in `tmp/overseer/HANDOFF.md`; this prompt is the runbook.

## Prime law (do not violate)

**Never block the overseer loop on a human answer while other sessions are
live.** Decide-and-inform over ask-and-wait; make every other track
self-sustaining before surfacing any unavoidable gate.

## Operating model (LOCKED — corrected 2026-06-28; hold to it)

- The overseer **ORCHESTRATES** (plan, dispatch, watch, synthesize). It does
  **NOT** run factory dispatches or author fixes in its own shell. **livespec
  SESSIONS host the work** (a session runs the factory dispatch / does the code
  fix); the overseer watches panes + ledger + PRs.
- The blessed carrier for ready ledger work-items is the **Fabro factory**
  (`orchestrator-image/real-work-dispatch.sh` → Dispatcher → Fabro docker
  sandbox → review gate → janitor → auto-merge → ledger-close), **NOT**
  hand-briefed direct execution.
- **Factory dispatches are SEQUENTIAL**: real-work-dispatch.sh uses
  `--network host` (to reach host Dolt at `127.0.0.1:3307`), so a 2nd concurrent
  orchestrator container collides on fixed inner ports/namespace and dies at
  provisioning. Code-fix sessions (worktree→PR→merge) are NOT factory dispatches
  and CAN run in parallel.

## Maintainer interaction style (learned 2026-06-27 — hold to it)

- **One clear, CLICKABLE choice at a time** (`AskUserQuestion`), plain language,
  no jargon. Lead with a recommended option. Define every domain term inside the
  question.
- **Never** dump a prose wall of decisions; walk the maintainer through items one
  by one. Say the plain-language bottom line first, then detail.

## What's DONE (do NOT redo)

- The `zs22` epic family is CLOSED (prior sessions).
- Factory items landed end-to-end via the factory: **dt-23n** (PR #207),
  **n70w** (PR #677) — merged + janitor-green + ledger-closed.
- Factory fixes merged to **orchestrator** master: **#188** (project ONLY
  `~/.codex/auth.json` into the container — credential-only) and **#189**
  (regen beads `metadata.json` in a non-git scratch dir — livespec-tenant fix).

## CURRENT WORK

### A — Factory-bug fixes (IN FLIGHT; maintainer chose "fix the factory bugs first")

Two reliability bugs surfaced dispatching real work; fixes dispatched into
sessions (code fixes on the **livespec-orchestrator-beads-fabro** repo;
worktree→PR→merge; parallel-safe):

1. **PR-stage path-mapping** — `livespec3`, brief
   `tmp/overseer/briefs/fix-factory-prstage-path.md`. The Fabro sandbox mounts
   the repo at `/workspace/<repo>` but the PR stage looked for
   `/workspace/dispatch-target` → "no committed work" → no PR. INTERMITTENT
   (n70w succeeded on the same repo).
2. **Coverage-gate gap** — `livespec4`, brief
   `tmp/overseer/briefs/fix-factory-coverage-gate.md`. The in-sandbox janitor
   passed but the PR's CI `check-coverage` failed → the factory ships
   unmergeable PRs. Make the pre-PR gate enforce the same coverage CI does.

MONITOR: watch `livespec3`/`livespec4` panes + the orchestrator's open PRs. They
report `DONE <pr>` or `BLOCKED <diagnosis>`. **Review any BLOCKED diagnosis
before they implement** (the briefs tell them to surface, not guess).

### B — Deferred tail (after the factory bugs are fixed + merged)

3. **retry `livespec-vtxt`** (OPEN) — intermittent PR-stage failure; re-dispatch
   through the fixed factory (sequential, default container, host in a session).
4. **`livespec-dev-tooling-04g`** (OPEN) — **PR #209** (branch
   `feat/livespec-dev-tooling-04g`) carries the impl but fails `check-coverage`;
   P3 + oversized (`sizing-warn`). Re-dispatch through the fixed coverage-gate OR
   regroom/split. Do NOT abandon PR #209.
5. **`livespec-2exa`** (OPEN) — VERIFY-only + close (no code → no PR;
   overseer-handled): confirm fan-out green for the 4 aggregate-enforced
   consumers + check-plugin-structure driver-only, then close.
6. **`livespec-2rab`** (OPEN) — cross-repo caller-workflow pin bump (many repos →
   not a single sandbox; overseer-handled or decompose into per-repo items).

### C — M2 groom (MAINTAINER-GATED, interactive)

**`livespec-zs22.8`** governed-repo-lifecycle. M2 = "Generalize `just bootstrap`
→ the lifecycle verb" (first code milestone; verb lives in dev-tooling beside
`wire_fleet_member`, reuse-first). Walk the maintainer through the cut **one
clean `AskUserQuestion` at a time**; the maintainer OWNS the cut, files ONLY on
approval. See `prompts/governed-repo-lifecycle-handoff.md` +
`research/governed-repo-lifecycle/`.

## Factory bug inventory (the reliability picture)

1. codex-cred not projected — FIXED (#188). 2. beads-regen in-clone dolt-over-git
fail — FIXED (#189). 3. PR-stage path mismatch — FIXING (livespec3). 4. pre-PR
gate ≠ CI coverage — FIXING (livespec4). 5. can't run concurrently
(`--network host`) — NOTED, not filed (consider a work-item: redesign the factory
network/port model for parallel dispatch).

## How to run it

- **Set up the two-pane layout first** (overseer skill "## The two-pane layout").
- Enumerate sessions (`command tmux ls`). **Session `/clear` is FLAKY when a
  session is busy/has queued msgs**: Escape (drain) → confirm idle (no spinner) →
  `/clear` → verify the welcome banner BEFORE dispatching. `livespec1` got stuck
  this way (stale TODOs that never cleared); `livespec2`/`3`/`4`/`5` cleared fine.
- **Dispatch a factory run** (sequential, default container) — host it in a
  session via its brief:
  `cd /data/projects/livespec-orchestrator-beads-fabro && source /data/projects/1password-env-wrapper/with-livespec-env.sh bash orchestrator-image/real-work-dispatch.sh --run --target-repo <repo> --item <id> --mode shadow`
  (~30–50 min; ledger-closes the item on success; add `--preflight` to validate
  env first).
- **Surface to the maintainer ONLY:** the M2 cut approvals, a genuine
  architectural/contract decision, a factory-fix `BLOCKED` diagnosis, or an
  unauthorized destructive op. Everything else is decide-and-inform.
- **House rules:** repo mutations go `worktree → PR → rebase-merge`; never commit
  on a primary; never `--no-verify`; beads via
  `source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C <repo> <args>`;
  scratch under `tmp/overseer/`.

## Explicitly OUT of scope (do NOT pull in unless the maintainer asks)

The broader pre-existing fleet backlog (~12 items): `gcp2`, `4dzbcv`, `yc8e`,
`4moata`, `mutreal*`, `9msu`, `qtjd`, `i6rc`, `kvzt`, `h3e7`, `1t17`, `aava`,
`0jxs`, etc. Note they exist; leave them for a future session.

## Cold-start / crash recovery

Durable state is the **ledger** + this prompt + **`tmp/overseer/HANDOFF.md`**
(detailed evidence, open PRs, resume commands). After a crash: confirm the ledger
is reachable
(`source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec list`),
all three primaries (`livespec`, `livespec-dev-tooling`,
`livespec-orchestrator-beads-fabro`) clean on master, reap merged worktrees, then
re-run this prompt — current state re-derives from the ledger + open PRs +
`HANDOFF.md`.
