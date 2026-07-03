# Phase 1 dispositions — livespec-console-beads-fabro

**Epic:** cleanup-research-and-prompt-cruft (`livespec-ztepy5`) · **Phase:** 1 (disposition validation, read-only) · **Date:** 2026-07-03
**Repo:** `/data/projects/livespec-console-beads-fabro` · **State read at:** `origin/master` = `48ba514` (2026-07-03)

Root-cruft re-check (`git ls-tree -r origin/master -- research/ prompts/`): exactly **3 files** — `research/tui-first-milestone-bootstrap-plan.md`, `prompts/impl-obligations-handoff.md`, `prompts/spec-refinement-critique-handoff.md`. No missed files. (A third prompts file — the fleet-wiring runbook — existed transiently, added `b194e3a` and removed `c54a00f`, both 2026-06-27; already gone, no action.)

Spec-reference sweep: `git grep -E '(research|prompts)/'` over `origin/master` excluding `research/`, `prompts/`, `SPECIFICATION/history/`, `plan/archive/`, lockfiles returns **only** `AGENTS.md:55` and `README.md:64`. **No SPECIFICATION/ file references either path → no SPEC-ABSORB items in this repo.**

## Finalized table

| Item | Final disposition | Evidence |
|---|---|---|
| `research/tui-first-milestone-bootstrap-plan.md` | **ARCHIVE** → `archive/research/` + rewrite `README.md:63–65` | Retired as a live tracker by `2ffb82e` (2026-06-25, "docs: retire bootstrap plan as live tracker"); sole inbound ref `README.md:64` already calls it "retained only as historical rationale and … no longer a live work tracker"; grep confirms zero SPECIFICATION/ or code refs; tracking home is the Beads ledger (10 live items enumerated below). |
| `prompts/impl-obligations-handoff.md` | **ARCHIVE** → `archive/prompts/` — track is ACTIVE, but its D2 plan-thread conversion **already exists**: `plan/impl-dispatch/handoff.md` (parked `cb77ed5`, 2026-07-02). Do **not** create a second thread. | Closed-work evidence: slice A `uljbzh` CLOSED (PR #48, merge `edbb06c`); `gkqyaf` CLOSED (PR #42, merge `6171984`); S7 `idgql3` **CLOSED 2026-07-02** (PR #79, merge `8fc8a71f759b`, app/livespec-pr-bot auto-merge — ledger close reason cites the `in7snc` live validation); SC-nfr spec change LANDED as **v012** (`f3566c4`, 2026-07-01). Still-open ledger remainder (wrapped `bd list`/`show`, 2026-07-03): keystone epic `rrr4i4` (P0, BACKLOG), `qvrwag` S6 (READY), blocked chain `cvqcnx`→`cc3nlr`→`77t6mk`, plus `mvu22t`/`txtzn5`/`topr34`/`pke3y3` (BACKLOG). The plan thread + ledger own all of it; the prompts/ file is stale against both (says idgql3 "now ready" — closed; says SC-nfr "awaiting revise" — landed). |
| `prompts/spec-refinement-critique-handoff.md` | **ARCHIVE** → `archive/prompts/` — track FINISHED | Convergence self-recorded at `9f891d2` (2026-06-26): capture-drift + capture-gaps converged at v009 (cut `9daa48b`, 2026-06-25, on `origin/master`); critique sub-track converged at v008. Its one routed outstanding deliverable (SC-nfr → `nfr-contributor-scenarios`) landed as **v012** (`f3566c4`, 2026-07-01). `SPECIFICATION/proposed_changes/` contains only `README.md` (empty queue). Later cuts v010–v013 were driven by other tracks (v010 `a696125` TUI nav, v011 `ab7b684` attention-model/E-3b, v012 `f3566c4`, v013 `851188d` autonomous mode) — none by this handoff. |

## Corrections vs inventory

1. **AGENTS.md anchor drifted: line 47 → line 55.** The handoff-home bullet ("Handoffs: update the living handoff file; NEVER print one inline… UPDATE the existing handoff prompt under `prompts/` (the single living handoff…)") now spans **AGENTS.md:53–57**, with the `prompts/` reference at **:55** — pushed down by the 2026-07-03 `.ai/` reference additions (`630a291`, `48ba514`). Re-resolve by content, not line number, at Phase 3 time.
2. **"Console has plan/archive/ but no active plan/ threads" is WRONG.** `plan/impl-dispatch/handoff.md` is a live (PARKED, not archived) thread — parked `cb77ed5` 2026-07-02. Its park reason ("BLOCKED on github-app-auth") is itself stale: the blocking core epic `livespec-2ef0` has since closed (livespec master `b16b9f2`) and the canary dispatch it was waiting on already succeeded (`idgql3` PR #79 merged `8fc8a71`, bot-identity chain verified in the close reason).
3. **Both prompts/ VERIFY rows resolve to ARCHIVE** — neither needs a new PLAN-THREAD. Spec-refinement: done. Impl-obligations: active, but the D2 conversion target already exists (`plan/impl-dispatch/`); creating a new thread would duplicate it.
4. **README.md:64 anchor holds exactly** as inventoried; the referencing sentence spans lines 63–65. `research/` last commit is `2ffb82e` (2026-06-25), matching the inventory; both prompts/ files last touched 2026-06-26 (`f722850`, `9f891d2`), matching.
5. Side observation (non-blocking): a new P0 ledger item `livespec-console-beads-fabro-vfd` (2026-07-03, SessionStart ensure-plugins hook / frozen plugin pointers) is open but unrelated to this cleanup — no bearing on dispositions.

## Escalations for Phase 2

- **None strictly required** — both VERIFY items resolved with concrete evidence. Two judgment calls surfaced for checkpoint confirmation:
  - Treat `plan/impl-dispatch/` as the completed D2 conversion of `prompts/impl-obligations-handoff.md` (recommended verdict: **yes — archive the prompts/ file, no new thread**; the ledger + parked thread carry every open obligation).
  - The stale "BLOCKED on github-app-auth" park note in `plan/impl-dispatch/handoff.md` (recommended verdict: **out of this epic's scope** — refresh it at that thread's next resume, not in the Phase 3 cruft PR; noting it here so it isn't lost).

## Reference-update obligations (Phase 3 executor)

1. **Move** `research/tui-first-milestone-bootstrap-plan.md` → `archive/research/tui-first-milestone-bootstrap-plan.md` (creates `archive/` — this repo has none yet).
2. **Move** `prompts/impl-obligations-handoff.md` and `prompts/spec-refinement-critique-handoff.md` → `archive/prompts/` (removes the now-empty `prompts/` dir).
3. **README.md:63–65** — rewrite the sentence so the pointer follows the move: "The original bootstrap plan in `archive/research/tui-first-milestone-bootstrap-plan.md` is retained only as historical rationale…" (keep the "no longer a live work tracker" framing).
4. **AGENTS.md:53–57 (D2 rewrite — resolve by content)** — replace the `prompts/`-as-handoff-home bullet with the successor convention, e.g.: "**Handoffs: update the living plan-thread handoff; NEVER print one inline.** Session handoffs live at `plan/<topic>/handoff.md` (one durable thread per topic; resume via `/livespec-orchestrator-beads-fabro:plan <topic>`); update it in place and print its PATH. Completed handoffs archive to `archive/prompts/` (legacy) or `plan/archive/<topic>/` (threads). Do not print a handoff body in chat or proliferate new handoff files."
5. **Relocate-never-drop fold-in:** add a ledger comment on `livespec-console-beads-fabro-mvu22t` carrying the archived handoff's blast-radius warning (once landed, its `commit-msg` hook gates ALL later commits — test thoroughly first; exempt `docs(...)`/`chore(...)`), which the ledger description does NOT currently carry. (`topr34`'s MIXED-autonomy/host-ops flag is already in its ledger description — no action.)
6. **Gate command:** this is a Rust repo but the full gate is **`just check`** (justfile:95) — it aggregates `check-format`, `check-clippy`, `check-test`, `check-nextest`, `check-coverage`, `check-deps`, `check-arch`, `check-behavior-coverage`, `check-baseline`, `check-plugin-resolution`, `check-doctor-static`. The Phase 3 changeset is docs-only (no `.rs`/`.py` product code) → `chore(...)`/`docs(...)` subject, Red-Green-Replay-exempt, but must land via worktree → PR → merge with `just check` green (note: `check-doctor-static`/`check-behavior-coverage` read `SPECIFICATION/`, which this changeset does not touch).
