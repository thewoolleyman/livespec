# Autonomous-mode MVP — overall plan handoff (livespec core)

**Status:** DRAFT — awaiting the Step-0 multi-model (Fable) validation pass before
any implementation begins. First-drafted 2026-07-10 from a three-repo survey.

**Thread role:** the OVERALL cross-repo plan. Ties together the console operator
surface and the orchestrator decision engine, owns the dependency graph, and
defines the tmux/session delegation model. livespec core authors no product code
here.

## Read first
1. This file, then `design.md` in this directory (the full plan).
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
Step 0 (Fable validation of ALL plans — HARD GATE)
  ├─ Console track (session console-autonomous-mode):  C1 spec-currency ─► C2 command foundation ─► C3 autonomous feature
  └─ Orchestrator track (session orchestrator-autonomous-mode): O1 spec-currency + publish arming contract ─► O2 build engine (bd-ib-82a)
                          O1 arming contract (I1) ─► C3
  Integration (driver session autonomous-mode): I2 end-to-end live exercise on a real tenant = MVP "done"
```
Console C2 and orchestrator O1→O2 run in parallel. Contract-first: O1 publishes the
arming/audit contract before C3 builds on it.

## Delegation model (design.md §8)
- Driver: Claude session `autonomous-mode` in tmux pane `livespec-autonomous-mode` (cwd `/data/projects/livespec`).
- Delegate: session/pane `console-autonomous-mode` (cwd console repo) → C1/C2/C3.
- Delegate: session/pane `orchestrator-autonomous-mode` (cwd orchestrator repo) → O1/O2.

## Ledger items in play (per repo tenant)
- Console: `rt4` (operator surface), `pke3y3` (5 valve commands), `ipi` (attention-stream TUI migration), `mb64bv` (backlog-bounce vocab rename).
- Orchestrator: `bd-ib-82a` (the engine).
- Core deps TRACKED not re-owned: `livespec-nrdk` (factory-safe admission gate), `livespec-0jxs` (operability preconditions); orchestrator `plan/fabro-token-refresh` (long-run publish robustness).

## Key cross-repo risks for Step-0 to resolve (design.md §6)
1. Persistence-model seam: console persists `autonomous_mode.enabled`; orchestrator autonomous mode must NOT persist beyond invocation. Define the arming surface mapping.
2. Division of resolution: console Scenario-10 LLM-stand-in vs orchestrator engine — no double-resolution.
3. Vocab drift: lane names / acceptance+reject enums / `attention_item.*` schema vs current core+orchestrator.

## Next action
Run Step 0: the maintainer's Fable session validates all three plans. On
NO-BLOCKERS, the driver dispatches C1 and O1 in parallel to the two delegate
sessions. Nothing implements before Step 0 passes.

## Pointers
- Ledger read (per tenant): `CACHE=$(find ~/.claude/plugins/cache/livespec-orchestrator-beads-fabro -name list_work_items.py -path "*/scripts/bin/*" | sort | tail -1); /usr/local/bin/with-livespec-env.sh -- env -C <repo> python3 "$CACHE" --json` — but prefer `bd list --json` from inside the repo when the cache path mis-resolves the tenant.
- Repo mutation: worktree → PR → merge → cleanup; `mise exec -- git …`; never `--no-verify`; plan docs are `docs(plan):` commits.
