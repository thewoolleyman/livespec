# Overseer startup

## STEP 0 — STARTUP GATE: ask the maintainer BEFORE doing anything (unskippable)

**Stop. Before you read the rest of this prompt, register a track, dispatch, or
touch any work, you MUST confirm the operating model with the maintainer in ONE
clear `AskUserQuestion` (plain language, recommendation first).** This is the one
allowed blocking question — at startup nothing is live yet, so it freezes
nothing. Added 2026-06-28 because a session ignored these rules: it ran the
overseer window as an inline worker (did the track work itself, context blew up),
never spun work out to separate sessions, and left the top pane frozen on a
previous overseer's hours-old "everything idle" snapshot. Confirm ALL of:

1. **Every track runs in its OWN separate session; the overseer does NO track
   work in its own shell.** Confirm the session → track → prompt map. The
   overseer only dispatches (`command tmux send-keys`), maintains `tmp/overseer/`
   status files, and arms/reads the watcher — it never writes product code, runs
   `just check`, commits, opens a track's worktree/PR, or spawns sub-agents to do
   the track work.
2. **Per track: Fabro factory or session-driven?** State, for each track,
   whether it runs via the **Fabro factory** (Dispatcher → Fabro sandbox;
   SEQUENTIAL — one at a time) or is a **session-driven** code-fix / interactive
   track (worktree → PR → merge; parallel-safe). The maintainer confirms the
   split before any dispatch.
3. **Status pane FRESH + LIVE + 33%.** Clear the previous overseer's stale
   artifacts (`rm -f tmp/overseer/status-table.txt tmp/overseer/stallwatch.log`,
   reset `status.md`), stand up THIS session's two-pane layout, arm a fresh
   watcher, and VERIFY the top pane is live (current, advancing timestamp — not a
   stale snapshot) and is **≈33% height, full width, on top — NOT 50%** (force +
   verify per the skill's "## The two-pane layout"). Show the maintainer the live
   pane before proceeding.
4. **Re-derive current work from the ledger, not this prompt.** The "CURRENT
   WORK" section below MAY BE STALE — confirm what is actually open from the
   ledger + each track's own handoff before dispatching.

Do not proceed past this gate until the maintainer has confirmed 1–4.

---

Run this to drive the livespec overseer. The large epics are CLOSED and the
ready punch-list work-items are now carried by the **Beads/Dolt + Fabro
factory**. Load and follow the local overseer skill at
`.claude/skills/overseer/SKILL.md` (invoke `/overseer`). Detailed evidence +
resume commands live in `tmp/overseer/HANDOFF.md`; this prompt is the runbook.

> **Staleness note (2026-06-28):** the phase content below (factory-bug fixes,
> the tail, "groom M2") is largely SPENT — the factory bugs were fixed, and M2
> (`zs22.8`) moved from grooming into implementation: the dev-tooling first-touch
> reconcile verb shipped in `livespec-dev-tooling` **v0.29.0**; the core
> `just bootstrap` rewire + ledger close of `zs22.8.2` are the remaining pieces.
> Treat the sections below as historical context and re-derive live state from
> the ledger + the per-track handoffs (e.g.
> `prompts/governed-repo-lifecycle-handoff.md`).

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
