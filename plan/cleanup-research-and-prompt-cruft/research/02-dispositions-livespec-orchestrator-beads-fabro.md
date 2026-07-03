# Phase 1 disposition validation — livespec-orchestrator-beads-fabro

- **Epic:** cleanup-research-and-prompt-cruft (anchor `livespec-ztepy5`, livespec tenant)
- **Repo:** `livespec-orchestrator-beads-fabro` (validated against `origin/master`)
- **Date:** 2026-07-03 · **Phase:** 1 (read-only disposition validation)

Root-cruft check: `research/` present at root; **no root `prompts/` directory exists** (D2 verified — nothing to retire here). The `.fabro` `@prompts/*.md` mentions are workflow-internal paths under `.claude-plugin/.fabro/workflows/implement-work-item/prompts/` (`workflow.fabro:81,101,118,140,158` + comments at `:225,259,289`) — confirmed NOT root `prompts/`, excluded.

Full `research/` enumeration (16 files) matches the inventory's four topics; no files missed: `CLAUDE.md`; `archive/w7-orchestrator-convergence/` (10 files, incl. nested `dind-spike/Dockerfile`); `context-completeness/stage-context-audit.md`; `loop-reflection-gate/` (4 files, incl. runtime-written `lessons.md`).

SPECIFICATION check: `SPECIFICATION/contracts.md:900` says only "The broader `research/` tree stays for standalone analysis that is not an active planning thread" — conceptual, names no specific doc. Same for `.claude-plugin/prose/plan.md:54` and `:179`. **No SPECIFICATION/ file references a specific research doc → zero SPEC-ABSORB items in this repo.** (Archiving subtrees keeps `research/` extant, so the conceptual references stay true.)

## Finalized dispositions

| Item | Final disposition | Evidence |
|---|---|---|
| `research/archive/w7-orchestrator-convergence/` (10 files) | **ARCHIVE** → `archive/research/w7-orchestrator-convergence/` (top-level `archive/` does not exist yet — executor creates it). See Escalation 1 (convention conflict). | Self-archived whole at merge `de5adfb` (2026-07-02, "chore(plan): archive completed plan threads + W7 convergence research"); all 5 inbound refs are doc/comment citations, none runtime (list below) |
| `research/context-completeness/stage-context-audit.md` | **ARCHIVE** → `archive/research/context-completeness/` (inventory's VERIFY resolved — see Escalation 2) | Epic `bd-ib-fqh` "Factory context-completeness…" CLOSED with all children closed (`bd-ib-fqh.1/.2/.3`); delivering merges `1485fb1` ("fix: map beads acceptance and notes") and `2fd4efd` ("fix: render spec id in dispatch goal"), both 2026-07-02, both co-committing this audit doc; the doc's own "Follow-Up Targets" states "No further per-stage/per-field gaps remain from this audit"; zero inbound refs; no open ledger item mentions context/stage/goal |
| `research/loop-reflection-gate/` (4 files) | **STAYS** (runtime-load-bearing; code-referenced only — D1 STAY rule) | RUNTIME: `_dispatcher_reflector_oob.py:688` default `lessons_path = Path("research/loop-reflection-gate/lessons.md")`; design-of-record docstring cites at `_dispatcher_cost_pricing.py:11`, `_dispatcher_heartbeat_probe.py:10`, `_dispatcher_reflection.py:3`, `_otel_enrich.py:4`, `_otel_receive.py:5`, `_otel_scrub.py:6`; `README.md:157`; `research/CLAUDE.md` marks it "LOAD-BEARING — do not move or archive without a coordinated code change"; epic `livespec-impl-beads-29f` (Reflection gate realization) still non-closed in the ledger |
| `research/CLAUDE.md` | **STAYS** (dir persists for loop-reflection-gate) — but requires a co-edit when w7 relocates (obligation 7) | Directory readme; its `archive/` paragraph documents the in-repo `research/archive/` convention that the relocation retires |

## Corrections vs inventory

1. **Fifth inbound w7 ref missed:** `orchestrator-image/README.md:13` cites `../research/archive/w7-orchestrator-convergence/dind-spike.md`. The inventory said "all four refs"; it is five.
2. **`orchestrator-image/Dockerfile:5` is ALREADY stale:** it reads `research/w7-orchestrator-convergence/dind-spike.md` — missing the `archive/` segment (pre-dates the `de5adfb` self-archival). The Phase 3 edit fixes pre-existing drift, not just the relocation.
3. **`pyproject.toml:319` consumer identified:** the entry is the last element of `[tool.livespec_dev_tooling].destructive_cli_allowlist` (block opens ~:315), read by the `no_direct_destructive_cli` check shipped from sibling `livespec-dev-tooling` (uv git source, tag `v0.31.1`), invoked via justfile target `check-no-direct-destructive-cli` (justfile:817-818). The check's `_SCANNED_TREES = (dev-tooling, .claude-plugin, .claude/plugins)` — `research/` (and `archive/`) are OUTSIDE scan reach, so the entry is documentary (per the in-file comment: "these entries document the exemption and keep it intact if a script is ever relocated"). The correct edit is a non-behavioral path rewrite, not a delete. Current block:
   ```toml
   destructive_cli_allowlist = [
       ".claude-plugin/.fabro/workflows/implement-work-item/prompts/",
       "orchestrator-image/acceptance-live-golden-master.sh",
       "orchestrator-image/reap-e2e-repos.sh",
       "research/archive/w7-orchestrator-convergence/e2e-repo-reaper.md",
   ]
   ```
4. **context-completeness VERIFY resolved to ARCHIVE** — not PLAN-THREAD (no open items) and not MAINTAINER (signal is conclusive: closed epic + merged SHAs + doc self-declares complete).
5. **Convention conflict discovered:** `research/CLAUDE.md` documents `research/archive/<topic>/` as this repo's deliberate archive home ("moved here WHOLE… the research analogue of `plan/archive/<topic>/`… remain citable at their archived paths"). The fleet `archive/research/` relocation contradicts this ratified repo-local convention → Escalation 1.
6. **New sweep refs, examined and excluded as non-load-bearing:** `_orchestrator_spec_reader.py:13` + `tests/livespec_orchestrator_beads_fabro/commands/test_orchestrator.py:167` (`research/foo.md` / `research/notes.md` are spec-TREE category-derivation examples, spec-target-relative, not root `research/`); `plan/archive/*/handoff.md` + `plan/archive/*/research/*.md` (thread-relative `plan/<topic>/research/` paths); `research/CLAUDE.md:22` (intra-tree self-reference).
7. **New CROSS-REPO ref:** `.github/workflows/copier-update-drift.yml:26` comment cites "Phase E of `research/workflow-processes/multi-repo-split-execution-plan.md`" — that doc exists in **livespec CORE** (`origin/master:research/workflow-processes/multi-repo-split-execution-plan.md`), not this repo. Contingent obligation 9.

## Escalations for Phase 2

1. **w7 relocation vs repo-local convention** — `research/CLAUDE.md` ratifies `research/archive/` and promises archived paths stay citable; recommended verdict: **relocate anyway** for fleet-wide `archive/research/` uniformity, rewriting the `research/CLAUDE.md` `archive/` paragraph in the same commit (the promise is repo-internal documentation, updatable atomically with all 5 refs).
2. **context-completeness final call** — inventory's VERIFY branch offered only PLAN-THREAD/MAINTAINER, but evidence (closed epic `bd-ib-fqh`, merges `1485fb1`/`2fd4efd`, doc self-declares no remaining gaps, zero inbound refs) supports **ARCHIVE**; recommended verdict: confirm ARCHIVE at the checkpoint.
3. **Cross-repo contingent ref** (`copier-update-drift.yml:26` → livespec core's `research/workflow-processes/multi-repo-split-execution-plan.md`) — recommended verdict: add to the livespec-core Phase 3 executor's fan-out list; bump this comment path only if core relocates that doc, no action otherwise.

## Reference-update obligations (Phase 3 executor)

Relocation moves (top-level `archive/` must be created; archived files themselves are frozen — move, never edit content):

1. `git mv research/archive/w7-orchestrator-convergence archive/research/w7-orchestrator-convergence`
2. `git mv research/context-completeness archive/research/context-completeness` (zero inbound refs — no edits)

Exact edits (all paths repo-root-relative, line numbers per `origin/master` at validation time):

3. `orchestrator-image/README.md:13` — `../research/archive/w7-orchestrator-convergence/dind-spike.md` → `../archive/research/w7-orchestrator-convergence/dind-spike.md`
4. `orchestrator-image/README.md:86` — `research/archive/w7-orchestrator-convergence/tier2-dispatch-proof.md` → `archive/research/w7-orchestrator-convergence/tier2-dispatch-proof.md`
5. `orchestrator-image/README.md:121` — `research/archive/w7-orchestrator-convergence/e2e-repo-reaper.md` → `archive/research/w7-orchestrator-convergence/e2e-repo-reaper.md`
6. `orchestrator-image/Dockerfile:5` — STALE `research/w7-orchestrator-convergence/dind-spike.md` → `archive/research/w7-orchestrator-convergence/dind-spike.md` (fixes pre-existing missing-`archive/` drift in the same edit)
7. `pyproject.toml:319` — in `[tool.livespec_dev_tooling].destructive_cli_allowlist`, rewrite `"research/archive/w7-orchestrator-convergence/e2e-repo-reaper.md",` → `"archive/research/w7-orchestrator-convergence/e2e-repo-reaper.md",`. KEEP the entry (documentary exemption per the comment block above it); non-behavioral — the path is outside the check's `_SCANNED_TREES` (`dev-tooling/`, `.claude-plugin/`, `.claude/plugins/`) both before and after.
8. `research/CLAUDE.md` — rewrite the "What lives here" `archive/` bullet (the paragraph beginning "- `archive/` — completed research topics…Currently: `w7-orchestrator-convergence/`"): retire the `research/archive/<topic>/` convention in favor of top-level `archive/research/<topic>/` (or delete the bullet once `research/archive/` is empty), keeping the LOAD-BEARING loop-reflection-gate paragraph untouched.
9. CONTINGENT (cross-repo): `.github/workflows/copier-update-drift.yml:26` — update the `research/workflow-processes/multi-repo-split-execution-plan.md` citation only if livespec core's Phase 3 relocates that doc; new path per core's disposition.

Explicit no-edits: `justfile:816-818` (names the allowlist key, no research path); all `research/loop-reflection-gate/` code refs (STAYS); `_orchestrator_spec_reader.py:13` + `test_orchestrator.py:167` (spec-tree examples); `plan/archive/*` (thread-relative); `.fabro` workflow `@prompts/*` (workflow-internal); archived w7 file contents incl. `e2e-repo-reaper.md:71,78` internal allowlist mentions (frozen).

## Phase 2 verdicts — CONFIRMED by the maintainer (2026-07-03)

| Escalation | CONFIRMED verdict |
|---|---|
| 1 — w7 relocation vs repo-local `research/archive/` convention | **Relocate** to top-level `archive/research/w7-orchestrator-convergence/`, rewriting the `research/CLAUDE.md` convention paragraph atomically with all five reference edits (obligations 1, 3–8 stand as written). |
| 2 — context-completeness final call | **ARCHIVE confirmed** → `archive/research/context-completeness/` (obligation 2 stands). |
| 3 — cross-repo `copier-update-drift.yml:26` citation | Handled: livespec IS relocating `multi-repo-split-execution-plan.md`, so obligation 9 fires — repoint the comment to livespec's `archive/research/workflow-processes/multi-repo-split-execution-plan.md` in this repo's Phase 3 PR. |
