---
name: wism-l1a-rollout-state
description: "L1a work-item-state-machine rollout (epic bd-ib-vvrxcb) is COMPLETE — all 7 slices merged + released as v0.3.0; epic closed"
metadata: 
  node_type: memory
  type: project
  originSessionId: 53bfcf04-05f7-4e09-8662-51172f6c8298
---

L1a track of the fleet work-item-lifecycle rollout (the deterministic
work-item state machine) in `livespec-orchestrator-beads-fabro`. Thread:
`plan/work-item-state-machine/`. Epic: **`bd-ib-vvrxcb`** (this repo's
beads tenant), prose-linked to fleet anchor `livespec-35s3zo`. Design is
LOCKED (decisions 1-46 at `/data/projects/livespec/plan/work-item-state-machine/research/`).

**Done (as of 2026-06-29):**
- Thread + epic anchored (PR #201).
- Spec RATIFIED → history **v020** (PR #202): beads 7-state custom-status
  mapping + 2-step append + rank/policy field homes (priority dropped);
  new `## Dispatcher admission, WIP cap, and post-merge acceptance` H2;
  list-work-items lane emission; next rank ordering; scenarios 22-28.
- GROOMED into 7 ready children of `bd-ib-vvrxcb`:
  S1 `bd-ib-ojlmr6` (revendor-runtime-v050) · S2 `bd-ib-7mounw`
  (beads-custom-status-encoding) · S3 `bd-ib-dnw2ei` · S4 `bd-ib-3wjakl`
  · S5 `bd-ib-6gwl23` · S6 `bd-ib-6zndit` · S7 `bd-ib-jysmuu` (cut release).

**S1 + S2 DONE (merged 2026-06-29, PR #203, merge `dfbb21e`).** Adopted
the auto bump-pin PR #203 (re-vendor v0.5.0) as the base and landed the
coordinated S1+S2 on top: `_cross_repo.py` shrink (relocated
`is_item_ready`/`ready_sort_key`/`lane_of` to `livespec_runtime.work_items.lifecycle`)
+ the beads store adapter (`done`↔`closed` status map, 2-step append,
`register_custom_statuses`, `rank` in `metadata.rank` + `BOTTOM_SENTINEL`
fallback, admission/acceptance/blocked-reason labels, `priority` dropped)
+ the full `priority→rank` & 7-state sweep across the package, the 18
breaking test files, and **`dev-tooling/checks/`** (closed_item_integrity
+ work_item_merge_evidence — a status site outside the package dir, easy
to miss). 100% coverage, green-per-commit via red-green-replay. Duplicate
PR #200 closed. Ledger children S1 `bd-ib-ojlmr6` + S2 `bd-ib-7mounw`
CLOSED (done/completed, `AuditRecord.merge_sha=dfbb21e`).

Gotchas learned: the 244-test TypeError was only the *runtime* breakage —
re-vendor ALSO fails pyright (strict `reportUnnecessaryComparison`) on
every `status="open"`/`== "closed"` (must migrate `"closed"→"done"`,
`"open"→"ready"` in product too). Red-green-replay against a re-vendor
base that fails pyright: keep the working tree structurally green, stub
ONE behavior so the staged Red test fails on-disk, stage only that one
test file, then Green-amend everything (used a `_beads_status_for`→`"open"`
stub). The host-only `check-codex-skill-picker` gate fails locally on a
Codex "trust hooks" prompt — skipped in pre-commit/pre-push/CI.

**S4 + S6 + S5 DONE (merged 2026-06-29).** `master` at `0dd6ced`.
- S4 `bd-ib-3wjakl` (PR #206, merge `da3c46c`): list-work-items emits
  computed `lane`/`lane_reason` via `lifecycle.lane_of`; `--filter=blocked`
  is lane semantics. (Scenario-27 `next` rank order was ALREADY satisfied
  by the S1/S2 sweep.)
- S6 `bd-ib-6zndit` (PR #207, merge `8bb59d5`): new
  `dev-tooling/checks/work_item_state_invariants.py` +
  `check-work-item-state-invariants` — fail-soft non-sentinel-rank +
  rank-key-length WARNINGS, hard `active⟹assignee` / `blocked⟹blocked_reason`
  ERRORS.
- S5 `bd-ib-6gwl23` (PR #208, merge `5d49d2b`): new
  `commands/rebalance_ranks.py` (`rebalanced` order-preserving re-key +
  `legacy_seed` L2-backfill primitive) + `store.update_work_item_rank`
  (in-place re-key). On-demand only.
All three ledger children CLOSED (done/completed, merge-evidence audit).
Handoff refreshed (PR #209, merge `0dd6ced`).

S6/S5 red-green gotcha: new-module Red needs the impl present (mirror-pairing
`rglob`s the filesystem), so use a lint/type-clean STUB on disk + stage only
the test; revert co-edited tracked files (justfile/CLAUDE.md/store.py) to
master at Red, restore at Green-amend. A `@dataclass(kw_only=True)` loaded via
`importlib.spec_from_file_location` needs `sys.modules[spec.name]=module` BEFORE
`exec_module` (Py3.10 KW_ONLY resolution).

**S3 DONE (merged 2026-06-29, PR #210, merge `da61be6`).** `bd-ib-dnw2ei`,
the largest slice — the Dispatcher's two valves: new pure
`commands/_dispatcher_valves.py` (`resolve_wip_cap` reads
`dispatcher.wip_cap` default 5; `plan_admissions`; `acceptance_decision`;
`reject_routing`; effective-policy/assignee resolvers). Admission valve
admits highest-`rank` `admission_policy=auto`+resolvable `ready` items up to
the WIP cap (sets `assignee`, `ready→active`); manual/unresolvable items are
HELD+surfaced (this REPLACES the deleted `human-gated` text marker —
Scenario 10 re-expressed). Post-merge acceptance replaces the old
`ready→done` close: green `complete`→`acceptance`, AI pass, then `accept`
per `acceptance_policy` (`ai-only`→`done`, else park). Non-convergence now
bounces to `backlog` (Scenario 11 re-expressed, not the needs-regroom
label). Store: `update_work_item_status` (in-place status+assignee);
`_beads_client.update_issue` gained an `assignee` param. Scenarios 22-25
integration tests + bound in heading-coverage. Ledger child closed.

**S7 DONE → L1a COMPLETE (2026-06-29).** Release **v0.3.0** cut by
release-please (PR #168, merge `9cf1de2`) — the L1a exit gate L2 + the
console consume. S7 `bd-ib-jysmuu` closed; **epic `bd-ib-vvrxcb` CLOSED**
(done/completed, all 7 children done, no audit — epics are merge-evidence
exempt). Handoff marked COMPLETE (PR #211, merge `8e06503`). `master` at
`8e06503`. Nothing remains on this track.

S3 red-green gotchas: (1) admission moves `ready→active` BEFORE the run, so
every existing dispatch test needed `admission_policy="auto"` (+
`acceptance_policy="ai-only"` to preserve `→done`) in its `_item` factory,
and prior `status=="ready"`-after-failure assertions became `"active"`.
(2) PLR0913 caps a def at 6 args — adding `assignee` to `update_issue`/
`_build_update_argv` needed `# noqa: PLR0913`. (3) pyright
`reportImplicitStringConcatenation` flags MIXED f+plain multi-line strings
but allows all-f (ruff F541 treats an implicitly-concatenated group as one,
so an all-f group with ≥1 placeholder is fine). (4) `doctor-static`
forbids the `§"heading"` spec-citation form in code — cite the spec FILE.

**L2 TENANT MIGRATION DONE (2026-06-29, this tenant).** Migrated this
repo's own `livespec-orch-beads-fabro` tenant onto the new schema using the
shipped primitives (no pin — this repo is the producer), 2 mechanical steps
under `with-livespec-env.sh`: (1) `store.register_custom_statuses` →
`bd config set status.custom "backlog,pending-approval,ready:active,active:wip,acceptance:wip"`;
(2) `rebalance_ranks.legacy_seed` rank backfill on the 9 live (non-closed)
heads in legacy `priority→captured_at→id` order (a0..a8), written via
`update_work_item_rank` (metadata was None on all — nothing clobbered;
`blocks` edges untouched). Pre-state: 99 issues (90 closed / 9 open), all
live rank-less, priority∈{2,3}. Verified: 9/9 live heads now ranked; S6
`work_item_state_invariants` doctor exits 0 against the LIVE tenant.
Recorded in `plan/work-item-state-machine/l2-tenant-migration.md` (PR #212,
merge `57dc275`). **Scope boundary:** mechanical SCHEMA migration only —
legacy beads status VALUES are NOT reclassified: `closed` rows read as `done`
via the adapter (correct); the 9 `open` rows are left `open` (read path passes
`open` through unmapped; mapping open→backlog/pending-approval/ready is
per-item judgment, a separate follow-up, not a bulk transform). To migrate
ANOTHER fleet tenant, repeat the same 2 primitives from that repo.

Migration gotcha: `legacy_seed` needs the native `priority` column, which the
materialized WorkItem DROPS — read RAW records via
`make_beads_client(cfg).list_issues()` to build `LegacySeedRow`, then map the
returned `(id, rank)` onto materialized items + `update_work_item_rank`. Run
the doctor against live by invoking
`dev-tooling/checks/work_item_state_invariants.py` directly under the wrapper
WITHOUT `LIVESPEC_BEADS_FAKE` (the justfile target forces the fake).

Discipline: worktree → PR → rebase-merge; `mise exec -- git`; never
`--no-verify`; red-green-replay for product `.py`; 100% per-file
coverage; close each child via the store seam under `with-livespec-env.sh`
with merge-evidence in the `AuditRecord`. Run beads via
`with-livespec-env.sh`.
