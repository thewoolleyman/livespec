# Stage-2 live-TUI validation — findings (session cont.21, 2026-07-17)

Driving the fresh console binary
(`/data/projects/livespec-console-beads-fabro/target/release/livespec-console-beads-fabro`,
built from console master `14ec65d`) against the **orchestrator tenant**
(`/data/projects/livespec-orchestrator-beads-fabro`, release 0.43.0) in the
`console-autonomous-mode:2` (`orch`) tmux window, launched with
`with-livespec-env.sh -- <binary> serve` from the orchestrator cwd.

## VALIDATED LIVE (through the TUI, on the real orchestrator ledger)

1. **New binary + new surface present** — `Settings` view now in the left-nav;
   key handler exposes `s` (move), `g`/`f`/`k` (the 3 per-item cap overrides),
   `p`/`c`/`r`/`m`/`n` (approve/accept/reject/set-admission/set-acceptance),
   `space` (select), `:` (drain), `?` (help).
2. **All ten new drive action-ids** present in released orchestrator 0.43.0
   scripts (approve, accept, reject, set-admission, set-acceptance,
   set-merge-on-review-cap, set-review-fix-cap, set-acceptance-rework-cap,
   move, resolve-blocked) — the plumbing the TUI keys shell into resolves.
3. **Individual selection** — Lanes view → drill into a lane (Enter) → per-item
   list → item selected (`bd-ib-98c.10`).
4. **All three per-item cap overrides** — SET + CLEAR (clear-to-inherit), each
   landed live in the ledger (verified via `bd show`), each restored:
   - `f` review-fix-cap (int) → label `review-fix-cap:5`
   - `g` merge-on-review-cap (**bool** path) → label `merge-on-review-cap:true`
     (modal cycles clear/off/on; `on`→`true`)
   - `k` acceptance-rework-cap (int) → label `acceptance-rework-cap:9`
   Both value-type modal paths (int + bool) exercised. Item ends `origin:freeform`.
5. **Broad move `s` (ready→backlog)** — landed live (`bd-ib-98c.10` status went
   `ready`→`backlog`, verified via `list_work_items.py`). Restored to `ready`
   via the backing drive CLI afterward.

### Fix in flight
A scoped sub-agent (`console-live-update-fix`) is implementing the Bug A + Bug B
fix in `livespec-console-beads-fabro` on worktree branch `fix-cockpit-live-update`,
bound to Scenarios 2/3/11 (spec-conformance, no spec change). It will open a DRAFT
PR and stop for driver review before merge.

## USABILITY HOLES (per operating-directive #3 — route to maintainer)

- **H1 — Lanes board stale on launch.** `serve` (what `just tui` runs) shows a
  stale work-item board: on a fresh relaunch the Attention view went LIVE
  (attention 20, canonical) but the Lanes view still showed a days-old snapshot
  (done 182 vs canonical 212; phantom pending-approval `bd-ib-jz62h3`, ready
  `bd-ib-e0t`, acceptance `bd-ib-86k` — all actually CLOSED). Running the
  console's own `backfill` (5 adapters, 518 events) refreshed the board to
  canonical (done 212, ready `bd-ib-98c.10`, acceptance `bd-ib-dqt`,
  pending-approval 0). So `serve` refreshes only the needs-attention source, not
  the work-item/lane source; the documented `just tui` launch path shows stale
  lanes until a manual `backfill`. **cont.20's own driver mistook the stale
  numbers ("backlog 24 / ready 1 / acceptance 1 bd-ib-86k") for live state** —
  the staleness has gone unnoticed across sessions.

- **H2 — No post-action refresh.** After a move/valve lands in the ledger, the
  TUI does NOT re-probe: the lane view kept showing `bd-ib-98c.10` in "Lane:
  ready" after it moved to `backlog`. The operator drives blind (actions land
  but the cockpit doesn't show the effect), and a follow-up action computes
  wrong options from the stale lane (the second move would offer the ready
  lane's targets, not backlog's — so you cannot cleanly move an item back
  through the TUI). Silent success: neither H1 nor a valve write surfaced a
  Status-bar confirmation message.

**Impact:** the operator can DRIVE actions (they land correctly), but the
cockpit does not reflect live state or action effects without a manual
`backfill` + relaunch. This directly undercuts the Stage-2 acceptance goal of
"drive work-items end-to-end through the TUI and watch them park in acceptance."

## NOT YET EXERCISED (need target items that don't exist / are risky)

- `g` (merge-on-review-cap, bool) and `k` (acceptance-rework-cap, int) — same
  override modal as `f`, different action-id; high confidence, not yet run.
- `p` approve — needs a pending-approval item; canonical count is **0**, and
  `move` refuses pending-approval as a target, so one must be FILED.
- `r` reject — needs a rejectable item.
- resolve-blocked — needs a safely-blocked item; the 8 blocked are REAL
  needs-human items, so touching them disturbs real state → file a throwaway.
- `c` accept — `bd-ib-dqt` sits in acceptance; reserved for the maintainer's
  final accept per the plan.

## ROOT CAUSE (event-sourcing frame) — the cockpit is NOT live at runtime

The maintainer's frame is correct: this is an event-sourced app; every projection
(lanes, attention, detail) should reduce over the latest appended events and
update automatically. It does not. The cockpit reduces its projections over a
**frozen event snapshot taken once at startup**. Two code-level causes, both
breaking the "append event → projection updates" contract:

- **Bug A — first-run-only source ingestion.**
  `run_store_backed_tui_session` (`crates/console-cli/src/lib.rs:395-401`) gates
  `backfill_source_adapters(...)` behind `if existing_events.is_empty()`. The
  needs-attention source is ingested **unconditionally** (line 401), but the
  source adapters that emit the `work_item.*` lane events are ingested **only
  when the event log is empty** (first-ever run). Every normal `serve` reduces
  the Lanes projection over stale `work_item.*` events → **H1**. (The standalone
  `backfill` command has NO such gate — `backfill_source_report`/
  `backfill_source_adapters`, lines 458-513 — which is why a manual `backfill`
  refreshed the board.)

- **Bug B — the render loop never re-reads the log.**
  `run_terminal_loop` (`crates/console-tui/src/lib.rs:140-174`) rebuilds the
  model each frame from the immutable `events: &[ConsoleEvent]` slice captured
  once (`console-cli/src/lib.rs:405`, passed at line 409). Its 250 ms
  `event::poll` is a **keyboard** poll; on timeout it just redraws the same
  snapshot. The effect sink appends the operator's action-outcome events to the
  store (`console-cli/src/lib.rs:292`, `handle_runtime_effect` →
  `persist_tui_runtime_effects`) and shells `drive.py` inline, but the loop
  never calls `store.list_console_events()` again — so those appended events, and
  any newly-ingested source events, are never folded into the projection until
  the process restarts → **H2**.

**Event-sourcing-correct fix:** the loop must, on its poll cadence AND after each
applied effect, (a) re-ingest the source adapters (append fresh source events,
unconditionally — kill Bug A's `is_empty` gate), (b) re-list `store.list_console_events()`,
and (c) rebuild the model — so every projection continuously reduces over the
newest events, including the operator's own appended outcomes. This requires
threading the store + source ports + needs-attention into `run_terminal_loop`
(today it only gets the immutable `events` slice + the effect sink), which is a
non-trivial core-render-loop change (Rust; Fabro sandbox has no Rust → do it via
a scoped sub-agent, the cont.6 Stage-1 pattern, not the factory).

This also explains why the staleness went unnoticed across sessions: since the
TUI never live-updates, whatever snapshot was in the store from the last explicit
`backfill`/first-run shows forever, and reads as "live."

## ALSO VALIDATED (read-only, no fix needed)

- **Settings view (W4) renders** the effective dispatcher policy read live at
  startup: Auto-approve ready `off` (dangerous), Merge-on-review-cap `off`
  (dangerous), Acceptance mode `ai-then-human` (dangerous), Review-fix-cap `3`,
  Acceptance-rework-cap `2`, WIP cap `5` — the safe-default disarmed state
  (no `dispatcher.*` block set). NOT edited (global settings toggle real factory
  autonomy — not a casual-validation target; the per-item caps `g`/`f`/`k` are the
  safe per-item analogue and were exercised).

## META-FINDING — why a spec→impl conformance gap shipped past ALL gates (follow-up)

The console has `console-spec-check` (scenario↔test heading-coverage) and
`console-completeness-check` (W6). Neither caught that the running TUI doesn't
live-update, because **the interactive loop (`run_terminal_loop` /
`run_interactive_tui_with_effect_sink`) is `#[cfg(all(not(test), not(coverage)))]`
— excluded from tests + coverage.** So the most operator-critical code is untested,
and Scenarios 2/3/11 are "covered" only by tests exercising
`run_store_backed_tui_session` PER-CALL (which re-ingests on each call, modulo Bug A),
never the loop's per-iteration behavior. Structural blind spot: conformance gaps in
the render/interaction loop pass every gate. cont.20 flag #2 named the OPPOSITE
direction (impl ahead of spec); this is spec ahead of impl — same "gates don't catch
drift both ways" theme. **Follow-up (file on the console tenant): require the
live-update logic to live in a covered, injectable seam, and bind Scenarios 2/11 to
tests that actually exercise the refresh — so the cfg-excluded loop shrinks to a thin
untestable shell.** The `fix-cockpit-live-update` PR does this for the fix itself;
the systemic guard is the follow-up.

## POST-FIX VALIDATION RUNBOOK (execute once `fix-cockpit-live-update` merges)

Priority order — the live-update proof is the acceptance-critical part; the valve
surface is secondary (all ten action-ids already CLI-confirmed to resolve, and the
write path already proven live via caps + move).

**Setup.** Relaunch the orch-tenant TUI with the merged binary:
`cd /data/projects/livespec-orchestrator-beads-fabro && /usr/local/bin/with-livespec-env.sh -- /data/projects/livespec-console-beads-fabro/target/release/livespec-console-beads-fabro serve`
(rebuild first: `just build-release` in the console checkout, or `just tui` from the
orchestrator cwd once the console binary is rebuilt — note `just tui` targets the
console tenant; to target the orchestrator tenant run the binary from the
orchestrator cwd as above).

1. **Bug A proof (live lanes on launch, NO manual backfill).** On first launch,
   Lanes must show canonical (done 212+, ready `bd-ib-98c.10`, acceptance
   `bd-ib-dqt`) WITHOUT running `backfill`. If it still shows a stale board, the
   fix is incomplete.
2. **Bug B proof (action reflected live, NO restart) — THE key evidence.** Select
   `bd-ib-98c.10` (ready), `s` move → `backlog`, confirm. The lane view MUST show
   it move ready→backlog within a few seconds, no restart. Then `s` move → `ready`
   to restore (now possible through the TUI, since the picker sees the true lane).
3. **Approve `p` end-to-end (core admission valve).** File a throwaway
   pending-approval item, approve it via the TUI, watch it move to `ready` live:
   ```
   cd /data/projects/livespec-orchestrator-beads-fabro
   with-livespec-env.sh -- bd create "throwaway Stage-2: approve-valve dogfood" -t task -p 3
   #   (note the new id; if create needs a role: git config beads.role maintainer)
   with-livespec-env.sh -- bd update <id> -s pending-approval --label origin:freeform
   ```
   In the TUI: select it in pending-approval → `p` → confirm → it must move to
   `ready` live. Then close it: `with-livespec-env.sh -- bd close <id> --reason "throwaway Stage-2 cleanup"`.
4. **Reject `r`** (optional): file a throwaway in `ready`/`acceptance`, `r` (regroom)
   → confirm → verify rejected; clean up.
5. **resolve-blocked** (optional): file a throwaway `-s blocked --label blocked-reason:needs-human`,
   select it (Attention shows "Resolve human-needed block…"), resolve → ready/backlog;
   clean up. Do NOT touch the 8 REAL needs-human blocked items.
6. **Leave `bd-ib-dqt` in `acceptance`** for the maintainer's final `c` accept via
   the TUI — that is the Stage-2 acceptance handoff, done only after all the above
   self-validates.
7. **Then** cut the console release (mark PR **#246** ready → merge) to publish the
   standalone binary deliverable.

All throwaway items must be closed after use. `bd-ib-98c.10` and `bd-ib-dqt` are
pre-existing throwaways — leave them (they're the ready/acceptance drive subjects).

## LIVE-EXERCISE OF THE MERGED FIX (PR #255, master 347906a) — Bug A/B PASS, but interactive regression FOUND

Rebuilt the console binary from merged master and relaunched the orch-tenant TUI.

- **Bug A PROOF — PASS.** On FIRST launch, NO manual `backfill`, the Lanes board
  showed fully live/current state (done **213**, ready `bd-ib-98c.10` + a NEW real
  item `bd-ib-esxztq`, acceptance `bd-ib-dqt`, blocked 9). The ledger had even
  evolved since the pre-fix read (new items from active fleet work) and the TUI
  picked them all up at launch. Source re-ingestion now happens every launch. ✓
- **Bug B (passive) — PASS.** Selection is preserved across live refreshes (cursor
  stayed put through a refresh cycle). ✓

- **⚠ REGRESSION FOUND (this is why "done = exercised live" matters):**
  - **Interactive `s` MOVE via the TUI does NOT land post-fix.** The move modal
    opens (Target correct), Enter (eventually) closes it, but the item's ledger
    status is UNCHANGED across ~4 attempts. Move via TUI WORKED pre-fix (on 14ec65d,
    earlier this session). Cap overrides `f`/`g`/`k` STILL work post-fix
    (`review-fix-cap:9` landed) — so it's move-specific (or move's confirm is being
    lost under the new loop). No move command events appear in the console store.
  - **UI is laggy / keystrokes unreliable.** The fix polls sources SYNCHRONOUSLY
    (every 3s + after each mutating effect), shelling `list_work_items.py`/`bd`,
    which blocks the event loop 1-3s per poll. During that window keystrokes are
    delayed or DROPPED — a modal `s` took ~5s to appear; single Enters were lost;
    it took a burst of Enters to close the modal. The synchronous poll the agent
    landed as an "acceptable first" is NOT acceptable: during a poll the UI thread
    never calls `event::read`, so keystrokes queue and process 1-3s LATE and
    out-of-order vs what the operator sees. The fix: poll sources on a BACKGROUND
    THREAD (append to the store; UI thread re-lists every frame, never blocks).
    (Subprocess PTY-stdin theft was RULED OUT — agent verified Rust `.output()`
    nulls child stdin; `Stdio::null()` kept only as belt-and-suspenders.)
  - This shipped past `just check` (100% coverage, all green) because the
    interactive LOOP is `#[cfg]`-excluded from tests — the META-FINDING above,
    now concretely demonstrated. The fix-forward MUST add a loop-level integration
    test that drives an effect→command→drive round-trip for MOVE.

- **CORRECTION to the move diagnosis (agent code-inspection, confirmed):** move's
  command dispatch is CORRECT and unit-tested — move did NOT regress in logic. Two
  real causes combined to make my move test fail:
  1. **Dropped keystrokes (the #255 responsiveness regression):** the synchronous
     in-loop poll blocks the event loop / a child eats PTY stdin → the move confirm
     keystroke is lost. Real, fixed by the async fix-forward.
  2. **A PRE-EXISTING latent bug (predates #255):** the move command's idempotency
     key is `<id>:work_item.move_requested` — it OMITS the target. I'd moved
     `bd-ib-98c.10` ready→backlog EARLIER this session (pre-fix), persisting that
     command in the store; every later move of the SAME item deduped against it →
     silent no-op. (Cap-overrides worked because their keys carry the payload.) So
     "move an item twice via the TUI" is impossible today. Being fixed IN the
     fix-forward: key must include target + a per-action distinguisher so genuine
     re-moves land while exact re-emits still dedupe.
  Net: the async fix-forward carries subprocess-stdin isolation + background-thread
  poll + the move idempotency-key fix + a loop-level move test + folds in #256's
  every-tick reflection. #256 to be closed as moot when it lands.

**Master state:** #255 is MERGED (347906a) — passive live-update FIXED, interactive
move REGRESSED + laggy. Console is a dogfooding tool (not production); fix-forward
is in flight (revert is the fallback if it stalls). Flagged to maintainer.

## Environment left as-found

`bd-ib-98c.10` back in `ready`; no throwaway items created yet; orch-tenant
console TUI still running in `console-autonomous-mode:2`.
