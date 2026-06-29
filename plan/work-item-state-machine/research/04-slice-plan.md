# Slice plan — the work-item lifecycle epic, decomposed for execution

This is the execution structure for the work-item-state-machine epic: the
cut into dependency-layered tracks, which repo/tenant each lands in, how
each track is driven, and the spec-vs-ledger routing. It is grounded in a
four-repo fleet survey (livespec CORE spec, livespec-runtime, both
orchestrators) captured in session 6; the design of record is
`02-design.md` and the locked decisions are `03-decision-log.md`
(authoritative on any conflict).

**Maintainer owns the cut.** Grooming each epic into *ready* slices is the
`groom` operation; this plan names the slices and their order, not the
final dispatchable cut.

## The reframe (the load-bearing finding)

This redesign is **overwhelmingly a `livespec-runtime` + orchestrator
change; livespec CORE's own spec is barely touched.** CORE's
`SPECIFICATION/` *explicitly delegates* the entire surface — the work-item
lifecycle/states, the Dispatcher/WIP/admission/janitor, acceptance
pre-vs-post-merge, the `WorkItem` schema and its fields, `lane_of` /
`is_item_ready` / work-item ranking — to the orchestrator's own
specification, marked NON-normative ("core neither names nor verifies any
of it"). CORE's contract sees only: the three named orchestrator CLIs, the
`capture-work-item` seam, the Planning-Lane two-seam frame, `livespec-runtime`
policy, and CI telemetry.

Consequence: **the contract for this redesign lives in the
`livespec-runtime` + orchestrator `SPECIFICATION`s, not in CORE's spec.**
The epic stays *anchored* in core (decision 20 — core is the fleet anchor),
but core is the anchor, not the work site. (This tightens decision 41's
loose "core owns the contract" wording: the schema/lifecycle contract is
owned by the runtime + orchestrator spec trees.)

Verified clean (session 6): nothing lifecycle/schema-shaped is mis-routed
into CORE's spec today. One drift to fix as an L0 ride-along:
`livespec-runtime/SPECIFICATION/contracts.md:131` claims the record schema
is "codified upstream in `livespec/SPECIFICATION/contracts.md`," but CORE
hosts no such schema — the real home is the runtime's own
`### livespec_runtime.work_items.types`.

## Tenants and tracks (9 beads tenants)

Every fleet beads tenant plus the OpenBrain adopter must migrate in
lockstep — the shared validator means a required-`rank` change makes any
un-migrated tenant unreadable (the standing "required-key schema change is
a cross-repo epic" rule). **Each repo gets its own `/plan` track** so its
spec/code/migration lands in — and is captured in the history of — the
correct repo, with its own epic in its own tenant, prose-linked to the core
anchor `livespec-35s3zo` (the console precedent, decision 41 — a prose
reference, never a typed cross-tenant `depends_on`, which would dangle).

| Tenant / session | Track kind | Layer |
|---|---|---|
| `livespec` (core) | anchor + coordinator (this thread); core tenant swept | — |
| `livespec-runtime` | full spec+code | **L0 foundation** |
| `livespec-orchestrator-beads-fabro` | full spec+code | **L1a** |
| `livespec-orchestrator-git-jsonl` | full spec+code | **L1b** |
| `livespec-console-beads-fabro` | existing thread `work-item-lifecycle-redesign` | console (consume) |
| `openbrain` | adopter: pin bump + config + tenant migration | L2 |
| `livespec-dev-tooling` | thin: tenant migration only | L2 |
| `livespec-driver-claude` | thin: tenant migration only | L2 |
| `livespec-driver-codex` | thin: tenant migration only | L2 |

The drivers + dev-tooling need **no code/spec change** (decision 42:
`Driver → orchestrator = zero deps`; their spec carries no work-item
schema) — only the **data migration of their tenant** (custom-status
registration + `rank` backfill). They get a thin track each so the
migration is formalized and captured in each repo's history (maintainer
call, session 6).

## Dependency layers

One hard cross-repo edge forces the layering: the shared `WorkItem` schema
+ `lifecycle.py` + `rank` live in `livespec-runtime`, which both
orchestrators **vendor**. So L0 must land and **cut a runtime release**
before any L1 track can re-vendor and consume it. Spec propose-changes for
L1 can begin in parallel with L0 (independent docs); the L1 **code** gates
on the L0 release; L2 gates on the L1 releases (the `rebalance-ranks`
command ships in L1a).

```
L0  livespec-runtime           ── cut release ──┐
                                                 ├─► L1a beads-fabro  ─┐
                                                 ├─► L1b git-jsonl    ─┤── cut releases ──► L2 migration (all 9 tenants)
                                                 │                     └─► console (consume lane)
exit gate (on livespec-35s3zo): delete .claude/skills/overseer/ once dogfooded
```

## Per-track slices (the cut)

Each track's first action is to create its own `/plan` thread (slug
`work-item-state-machine`, except the console's existing
`work-item-lifecycle-redesign`) + anchor its repo epic, then run the
livespec dogfooding order **propose-change → revise (ratify) → file/groom/
implement** for its slice. Each `## `-heading-touching propose-change
co-edits THAT repo's own `tests/heading-coverage.json`.

### L0 — livespec-runtime (critical path)

- **Spec (propose-change → `livespec-runtime/SPECIFICATION/contracts.md`):**
  `### …work_items.types` — `status` → the 7-state enum; `+ rank: str`
  (required, non-null); `− priority: int`; `+ admission_policy`,
  `+ acceptance_policy`, `+ blocked_reason` (`| None`, optional-on-read);
  the `active ⟹ assignee` invariant. New `### …work_items.lifecycle`
  (`lane_of` + `Lane`/`LaneName`/`BlockedReason`; `is_item_ready` =
  `lane_of(...).name=="ready"`; `ready_sort_key` keyed on `rank`; injected
  status-lookups — no `runtime → beads` back-edge). New `### …work_items.rank`
  (the `rank.py` wrapper API + the ported module + the bottom-sentinel
  constant). Fix the `:131` upstream-schema drift.
- **Code (runtime tenant):** port `_fractional_indexing.py` (CC0 verbatim)
  + `rank.py` + `NOTICES`; `types.py` edits; net-new `lifecycle.py`
  (relocate `is_item_ready`/`ready_sort_key` from beads-fabro `_cross_repo.py`
  with DI); the shared bottom-sentinel constant; paired tests.
- **Gate:** cut a `livespec-runtime` release — the artifact L1 vendors.

### L1a — livespec-orchestrator-beads-fabro

- **Spec (→ its `contracts.md`):** Dispatcher per-repo WIP cap
  (`.livespec.jsonc`, default 5) + admission valve (`admission_policy`
  field replaces the `host-only`/`human-gated` *text markers*) +
  post-merge acceptance (`complete` = merge-on-green → `acceptance` state;
  `accept` = post-ship confirm; `reject` = revert/fix-forward).
  `## Work-item beads-issue mapping` → 5 custom statuses + `blocked` /
  `done→closed` reuse (closes the open "needs-regroom: label vs status"
  question at `:699`); 2-step `append_work_item`. `#### list-work-items` →
  emit flat `lane`/`lane_reason`.
- **Code (beads-fabro tenant; gates on L0 release):** re-vendor
  `livespec_runtime`; shrink `_cross_repo.py` (lifecycle logic moves to the
  runtime; inject status-lookups; keep `load_manifest`/`parse_entry`);
  custom-status registration (bootstrap) + 2-step create→update +
  `done↔closed` in `store.py`/`_beads_client.py`; Dispatcher WIP + valves +
  post-merge acceptance; `lane`/`lane_reason` emission; `next` rank order;
  **new `rebalance-ranks` command** (+ a legacy-seed entry path for L2's
  backfill); doctor checks (non-sentinel-`rank`, rank-key-length warning,
  `active⟹assignee`, `blocked⟹reason`).

### L1b — livespec-orchestrator-git-jsonl

- **Spec (→ its `contracts.md`):** `## Work-items JSONL record schema`
  16→17 keys (`+ rank`, `− priority`); status-enum prose → the 7 states.
- **Code (git-jsonl tenant; gates on L0 release):** re-vendor
  `livespec_runtime`; `store.py` required-keys + `rank` + the
  bottom-sentinel adapter for rank-less legacy lines; `commands/next.py`
  `_sort_key` `priority → rank`; tests + the golden-master + e2e-cli
  fixtures.

### console — livespec-console-beads-fabro (existing thread)

Delegated (decision 41); driven by its own
`plan/work-item-lifecycle-redesign/` thread (epic
`livespec-console-beads-fabro-vqh36l`). Consume `lane`/`lane_reason`;
retire the `bd ready` re-derivation. Gates on L1a's lane emission.

### L2 — migration (all 9 tenants; gates on L1 releases)

`openbrain` (adopter): pin bump to the new runtime/orchestrator releases +
`.livespec.jsonc` updates (WIP cap) + custom-status registration +
`rank` backfill of its tenant. `livespec-dev-tooling`,
`livespec-driver-claude`, `livespec-driver-codex` (thin): custom-status
registration + `rank` backfill of each tenant, applied *through the
orchestrator's tooling* (`rebalance-ranks` legacy-seeded + `bd config set
status.custom`) — the repo files don't change beyond capturing the
migration in history. The core `livespec` tenant is swept too.

### exit gate

On `livespec-35s3zo`: delete `.claude/skills/overseer/` once the new system
is dogfooded (decision 18) — the epic is not done until this lands.

## Execution model — per-repo `/plan` tracks, coordinated from core

- **This (core) session is the coordinator + anchor.** It runs a
  *lightweight, manual* overseer — **informed by** `.claude/skills/overseer/`
  but NOT invoking it and NOT standing up its three-pane dashboard
  (maintainer call, session 6: the dashboard is the heavy, throwaway part
  this epic deletes). What it adopts: the **status table**
  (`Epic · Track · Status · %Complete`) printed *in this pane* before any
  gate/status; the **anti-stall discipline** (never freeze the coordinator
  on one track; keep other tracks self-sustaining before surfacing a gate;
  decide-and-inform for reversible calls); `command tmux send-keys` kickoff;
  and the cross-repo run-prompt discipline (a cold-startable brief landed in
  each repo, status derived from its ledger, no shadow queue).
- **Each track runs in its own tmux session** (all required sessions exist:
  `livespec-runtime`, `livespec-orchestrator-beads-fabro`,
  `livespec-orchestrator-git-jsonl`, `livespec-console-beads-fabro`,
  `openbrain`, `livespec-dev-tooling`, `livespec-driver-claude`,
  `livespec-driver-codex`). Each is driven into its own
  `/livespec-orchestrator-beads-fabro:plan work-item-state-machine` thread
  (interactive-create) seeded by a per-repo kickoff brief this coordinator
  authors and lands in that repo. The brief carries: the reframe, that
  repo's slice (above), the pinned contract deltas, the dogfooding order,
  the worktree→PR discipline, and the prose-link-to-`livespec-35s3zo`
  instruction.
- **Rollout: foundation-first.** Start the `livespec-runtime` (L0) track
  first — critical path, and it validates the per-repo-session +
  lightweight-overseer mechanics on one track. Once L0 is moving, the L1a/
  L1b spec work can start in parallel; their code + the console + L2 gate on
  the respective releases.

## Spec-vs-ledger routing (summary)

- **becomes-contract → `/livespec:propose-change`** against THAT repo's
  `SPECIFICATION` (runtime, beads-fabro, git-jsonl as above; **not** CORE,
  per the reframe). Ratified by that repo's `/livespec:revise`. Co-edits the
  repo's own `heading-coverage.json`.
- **becomes-work → `/livespec-orchestrator-beads-fabro:capture-work-item`**
  as children of that repo's epic (own tenant). The real cross-repo
  work-blocking edge (L1 code → L0 release) is the place for a typed
  cross-repo `depends_on`; epic→anchor links stay prose.
- **CORE guidance prose** → left as-is for now (non-normative; editing only
  adds heading-coverage churn) — revisit only if a clause actively
  contradicts the new model.

## Open impl-detail seams (resolved by the owning track, not here)

- **Custom-status registration home** — shared bootstrap vs. per-repo (L1a
  owns; decides whether L2's thin tenants get a file change or a pure
  sweep).
- **WIP-cap config key shape** in `.livespec.jsonc` (L1a owns).
- **`needs-regroom` / `host-only` / `human-gated`** become first-class
  fields/labels vs. stay markers, now that `admission_policy` is a field
  (L1a owns).
- **Whether today's advisory in-graph `review` node** stays pre-merge or
  folds into the post-merge acceptance pass (L1a owns; decision 34).
