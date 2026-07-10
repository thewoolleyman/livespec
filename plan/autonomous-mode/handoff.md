# Autonomous-mode MVP — overall plan handoff (livespec core)

**Status:** Step 0 PASSED — the independent Fable-model validation pass ran
2026-07-10 over all three plans and returned **NO-BLOCKERS** on each (full
verdict: `research/step0-fable-verdict.md` in this directory). Implementation
may begin: dispatch console C1 and orchestrator O1 in parallel, with the
verdict's observations pinned into each brief (see "Next actions" below).
First-drafted 2026-07-10 from a three-repo survey.

**Thread role:** the OVERALL cross-repo plan. Ties together the console operator
surface and the orchestrator decision engine, owns the dependency graph, and
defines the tmux/session delegation model. livespec core authors no product code
here.

## Read first
1. This file, then `design.md` in this directory (the full plan), then
   `research/step0-fable-verdict.md` (the Step-0 verdict — its numbered
   observations are dispatch-brief inputs, not optional reading).
2. The two sibling repo plans it coordinates:
   - `livespec-console-beads-fabro/plan/autonomous-mode/design.md`
   - `livespec-orchestrator-beads-fabro/plan/autonomous-mode/design.md`

## Goal (one line)
A human flips per-repo **full autonomous mode** from the
`livespec-console-beads-fabro` **TUI** (GUI out of scope) and the Beads/Dolt +
Fabro factory drives ready work to `done` unattended — LLM-resolving the human
gates, auditing every decision, surfacing only the truly-unresolvable back to the
operator.

## The spine (see design.md §7 for the full step catalogue)
```
Step 0 (Fable validation of ALL plans — HARD GATE)  ✅ PASSED 2026-07-10, NO-BLOCKERS
  ├─ Console track (session console-autonomous-mode):  C1 spec-currency ─► C2 command foundation ─► C3 autonomous feature
  └─ Orchestrator track (session orchestrator-autonomous-mode): O1 spec-currency + publish arming contract ─► O2 build engine (bd-ib-82a)
                          O1 arming contract (I1) ─► C3
  Integration (driver session autonomous-mode): I2 end-to-end live exercise on a real tenant = MVP "done"
```
Console C2 and orchestrator O1→O2 run in parallel. Contract-first: O1 publishes the
arming/audit contract before C3 builds on it.

## Next actions (exact steps for a new session)

1. **Dispatch O1 and C1 in parallel** to the two delegate sessions per the
   delegation model below. Both briefs MUST forbid `--no-verify`, require
   worktree → PR → merge, and instruct halt-and-report on hook failure.
2. **The O1 brief MUST carry, verbatim from the verdict** (observations 1, 2,
   and 5):
   - The O1 propose-change is REQUIRED, not "likely": orchestrator spec v032's
     collapse auto-approves stored-`manual` items while its own grooming clause
     names `manual` admission the realization of the human-gated **spec-change**
     marker; and the blanket acceptance→`ai-only` collapse conflicts with
     Scenario 36's `human-only` carve-out. The propose-change must name the
     design-human-gated set (drift acceptance, spec-change slices,
     regroom/backlog-bounce), define how the engine distinguishes design-gated
     `manual` from routine `manual`, and reconcile the `human-only` tension.
     Attribute the touchpoints precisely: only drift-acceptance is normative core
     law; spec-change gating and regroom are core NON-normative guidance being
     promoted into the orchestrator spec by maintainer declaration.
   - The arming contract must pin: the disposition of the orchestrator's own
     persistent `dispatcher.autonomous_mode` permission key versus the console's
     namespaced intent block (avoid two persistent booleans in the same
     `.livespec.jsonc` — recommended: the console's enable/disable commands set
     the orchestrator's key; the console block is dropped or derived); WHO the
     loop launcher is (recommended: the console's factory-drain path extended to
     pass the mode); and which surface carries `--mode autonomous` (spec says
     `drive`, a one-action executor; the shipped mode-bearing entry point is the
     dispatcher `loop` subcommand).
   - Refresh `bd-ib-82a`'s stale spec pointer (cites v025; spec is v032).
3. **The C1 brief MUST carry, verbatim from the verdict** (observations 3, 4,
   and 5):
   - Expect a ratified console revision, not "no change needed": Scenario 10's
     first Gherkin case (the console records an auto-decision command) is
     unsatisfiable for orchestrator-owned gates under the recommended
     engine-owns-all-gate-resolution reading; re-scope it (and the §"Full
     Autonomous Mode" blanket resolve-MUST) to the delegation model.
   - Add two confirmed drift instances to the vocab diff: the console contract's
     "`orchestrate run`" citation (the orchestrator surface is now `drive`) and
     its "lane vocabulary is owned by livespec core" attribution (it is owned by
     `livespec-orchestrator-beads-fabro`). The lane names, `blocked:dependency`
     overlay routing, and acceptance/reject enums verified drift-free.
   - Sequence C1's persistence-seam portion AFTER O1's arming contract freezes
     (I1), or resolve it as an explicit joint decision at a driver boundary —
     do not ratify a console-side persistence resolution before I1.
   - Refresh `rt4`'s stale version pointer (cites v013; spec is v016); when
     regrooming `pke3y3`, SPLIT out the four still-contract commands C2/C3 do
     not cover (`factory.dispatch_item_requested`, `factory.pause_requested`,
     `factory.resume_requested`, `spec.doctor_requested`) rather than narrowing
     them away.
4. **Gates unchanged:** C2 after C1; C3 after C1 + C2 + I1; O2 after O1; I2
   after C3 + O2 AND the design.md §9 operability conditions (verified cost
   ceiling + a real failure-surfacing path — note orchestrator bug `bd-ib-18r`:
   an in-loop park today orphans without ledger write-back, so I2's
   truly-unresolvable plant must be ledger-level or `bd-ib-18r` triaged first).
5. Every spec change in either repo routes propose-change → independent Fable
   review → revise, co-editing `tests/heading-coverage.json` for any H2 change.

## Delegation model (design.md §8)
- Driver: Claude session `autonomous-mode` in tmux pane `livespec-autonomous-mode` (cwd `/data/projects/livespec`).
- Delegate: session/pane `console-autonomous-mode` (cwd console repo) → C1/C2/C3.
- Delegate: session/pane `orchestrator-autonomous-mode` (cwd orchestrator repo) → O1/O2.

## Ledger items in play (per repo tenant)
- Console: `rt4` (operator surface; epic-shaped feature, stale v013 pointer), `pke3y3` (epic, "7 unimplemented commands" — regroom + split per Next actions), `ipi` (attention-stream TUI migration), `mb64bv` (backlog-bounce vocab rename — verify the rename target against the orchestrator's actual journal field `bounced_to_regroom` before landing).
- Orchestrator: `bd-ib-82a` (the engine; stale v025 pointer).
- Core deps TRACKED not re-owned: `livespec-nrdk` (factory-safe admission gate), `livespec-0jxs` (operability preconditions); orchestrator `plan/fabro-token-refresh` (long-run publish robustness); orchestrator bugs `bd-ib-18r` / `bd-ib-6vu` (unattended-run robustness — sequence around).

## Key cross-repo risks (design.md §6) — Step-0 disposition
1. Persistence-model seam: RESOLVABLE as planned; O1 must additionally pin the
   orchestrator's own config key, the launcher identity, and the
   `drive`-vs-`loop` mode placement (verdict obs. 2).
2. Division of resolution: RESOLVABLE via the engine-owns-all-gate-resolution
   reading; expect a console Scenario-10 re-scope in C1 (verdict obs. 3).
3. Vocab drift: lanes/enums verified clean; two extra drift instances found for
   C1 (`orchestrate run` → `drive`; lane-ownership attribution) (verdict obs. 4).

## Next action
Execute "Next actions" above: the driver dispatches C1 and O1 in parallel to the
two delegate sessions. Step 0 is complete; nothing else gates the dispatch.

## Pointers
- Ledger read (per tenant): `bd list --json` (or `bd show <id> --json`) run from
  inside the repo, via the credential wrapper
  `/usr/local/bin/with-livespec-env.sh -- bd …`; prefer it over the shared
  `list_work_items.py` cache path, which can mis-resolve the tenant.
- Repo mutation: worktree → PR → merge → cleanup; `mise exec -- git …`; never `--no-verify`; plan docs are `docs(plan):` commits.
