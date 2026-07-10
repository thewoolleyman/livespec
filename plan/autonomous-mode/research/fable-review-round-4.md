# Fable fresh-review round 4 — autonomous-mode MVP plans

**Reviewer:** a FRESH Fable-model session (no prior involvement in authoring
or revising these plans; spawned by the driver session with
`research/fable-review-brief.md` and ran it end-to-end). **Date:** 2026-07-10.

Scope: all three plans at `origin/master` as revised by rounds 1-3 —
`livespec/plan/autonomous-mode/{handoff,design}.md`,
`livespec-console-beads-fabro/plan/autonomous-mode/{handoff,design}.md`,
`livespec-orchestrator-beads-fabro/plan/autonomous-mode/{handoff,design}.md`.
Every load-bearing claim re-verified against the live spec trees (`git show
origin/master:<path>`), the crate/script sources, the three Beads tenants
(`bd show … --json` via the credential wrapper, from inside each repo), and
master CI (`gh run list --workflow CI` — green on all three repos at review
time). Prior-round records were read only AFTER forming an independent view;
every round-1/2/3 correction verifies as still present in the current plan
texts — nothing was lost.

## Round 4 fresh review: FIXES LANDED

Two real defects found — both in the overall plan, both
consistency/currency, fixed and merged this session. Both sibling plans
passed clean (the console plan's second consecutive clean round; the
orchestrator plan's first). Because fixes landed, this round does NOT clear
the gate; round 5 runs next with another fresh session.

### Per-plan
- **livespec (overall):** solid; two consistency/currency fixes landed
  (design §7 graph missing an edge its own prose + the handoff spine
  already assert; stale "revised rounds 1-2" annotation in the handoff
  Read-first section).
- **console operator surface (`livespec-console-beads-fabro`):** solid;
  NO fixes needed — spec v016 / zero pending proposals, five `work_item.*`
  commands map 1:1 onto action-ids shipping in `commands/drive.py`,
  `AcceptancePolicy` = `AiThenHuman` only, `CommandType` =
  `FactoryDrainRequested` only with zero `autonomous` hits, shipped
  `attention_item` schema fields match, `rt4` still cites v013,
  `mb64bv`/`bounced_to_regroom` caution holds. Second consecutive clean
  round.
- **orchestrator engine (`livespec-orchestrator-beads-fabro`):** solid;
  NO fixes needed — spec v032 / zero pending proposals, no
  `dispatcher.autonomous_mode` key in code (only the cost-label constant),
  `loop` carries `--mode {shadow,autonomous}` while `drive` does not (the
  O1 surface seam), contracts.md:781 `manual` = spec-change-marker collapse
  hazard + Scenario-36 `human-only` carve-out verbatim, `bd-ib-82a`
  feature/backlog/deps=0 still citing v025, bugs `bd-ib-18r`/`bd-ib-6vu`
  open.

### Fixed this round (finding → fix → merged PR)
Both in `thewoolleyman/livespec`, landed together in PR #1022 (merged,
rebase, master `25fab21`):
<https://github.com/thewoolleyman/livespec/pull/1022>

1. **Missing edge in the design §7 dependency graph.** The core handoff
   spine already draws `O1 arming contract (I1) ─► C3 (and C1's
   persistence-seam portion)` and §7's own C1 gate prose says "the
   persistence-seam portion additionally gates on I1", but the §7 graph
   drew only `─► C3` (the "missing edge / graphs must agree" class the
   brief flags). → Annotated the graph edge to match, so the drawn graph
   agrees with its own prose and the handoff spine.
2. **Stale round-count annotation.** The handoff Read-first section cited
   the sibling plans as "revised rounds 1-2, 2026-07-10", but round 3
   (orchestrator PR #410) revised
   `livespec-orchestrator-beads-fabro`'s design §5. → Reworded
   round-agnostically per round 2's fix #6 precedent so it won't re-stale
   each round.

### Non-blocking observations
1. **Unverifiable-read-only causal claim in the core handoff (no fix —
   state is correct).** The `livespec-bvuy4w` Ledger bullet asserts "bd
   refuses an epic→task `blocks` edge by design" as the reason
   `livespec-0jxs` carries a `related` edge. That bd behavior is not in
   `.ai/beads-gaps-workarounds.md` and cannot be verified read-only
   (proving it needs a ledger write, which the loop forbids). The edge
   STATE is verified correct — `livespec-bvuy4w` (epic) → `livespec-nrdk`
   (epic) `blocks`, → `livespec-0jxs` (task) `related` — and the plan's
   dependency-tracking is sound regardless, so no plan change.
   *Driver addendum (first-hand evidence, resolving this observation):
   the driver session that filed `livespec-bvuy4w` on 2026-07-10 observed
   the refusal directly — `bd dep add livespec-bvuy4w livespec-0jxs --type
   blocks` failed with the verbatim error `Error: epics can only block
   other epics, not tasks` — and then landed the `related` edge. The "by
   design" claim is live-observed bd v1.0.5 behavior, not an inference.*
2. **Carried from round 3, still no plan change needed:** orchestrator
   `plan/codex-factory-telemetry/` corroborates the "NO telemetry
   shipping" operability claim (via `livespec-0jxs`); the
   fabro-token-refresh thread's OWN handoff still lists the moot PR #136
   cleanup question (out of this loop's scope); console
   `plan/impl-dispatch/` remains unarchived (separate housekeeping, not a
   dependency).
3. **Repo states at handoff:** core (`livespec`) clean on master at
   `25fab21` (the merged fix); console (`livespec-console-beads-fabro`)
   untouched — on master, clean, behind origin by 2 (pre-existing; the
   reviewer only fetched/read, no PR there); orchestrator
   (`livespec-orchestrator-beads-fabro`) left exactly as found — behind
   origin by 1 with the pre-existing maintainer-owned dirty
   `orchestrator-image/real-work-dispatch.sh` and untracked
   `plan/fabro-token-refresh/design-notes.md` (fetch-only, per the brief).

### Currency findings
Everything re-verified TRUE today except the two fixed items (both core,
above). Confirmed current: console spec v016 / orchestrator spec v032, both
zero pending proposals; master CI green ×3 (core `1ae2c83`, console
`42c189d`, orchestrator `02dced1`, matching origin tips); core epic anchor
`livespec-bvuy4w` (epic, backlog, `livespec-nrdk` blocks / `livespec-0jxs`
related) filed after round 3 via core PR #1020; all console (`rt4`+v013,
`pke3y3` epic, `ipi` task, `mb64bv` chore/active, gate `iblkzp` closed) and
orchestrator (`bd-ib-82a`+v025 deps=0, `bd-ib-18r`/`bd-ib-6vu` bugs) ledger
statuses exact; drive-grammar's five valve action-ids present in
`commands/drive.py` + live contracts; core spec.md:387 drift-acceptance
normative quote, orchestrator spec.md §"Full autonomous mode" collapse
clause, and "orchestrate run" surviving only in `history/vNNN/` all
verbatim.

## Loop consequence

FIXES LANDED → round 5 runs next, with ANOTHER fresh Fable session (the
round-4 session cannot clear the gate on its own fixes). Convergence
signal: round 1 = 9 observations + 4 corrections; round 2 = 6 fixes;
round 3 = 2 fixes; round 4 = 2 small consistency/currency fixes with BOTH
sibling plans passing clean. The handoff's Loop state and Next actions are
updated in the same PR as this record.
