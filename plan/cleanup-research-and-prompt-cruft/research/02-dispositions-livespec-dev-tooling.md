# Phase 1 dispositions — livespec-dev-tooling

- **Repo:** `livespec-dev-tooling` (`/data/projects/livespec-dev-tooling`, read at `origin/master`)
- **Date:** 2026-07-03
- **Phase:** 1 (disposition validation, read-only) — epic anchor `livespec-ztepy5` (livespec tenant)
- **Root-cruft check:** `research/` present at root; `prompts/` ABSENT (D2 is a no-op for this repo — verified via `git ls-tree --name-only origin/master`). Repo already carries top-level `archive/` (README.md + memos.jsonl + work-items.jsonl) and `plan/` (`plan/work-item-state-machine/`).
- **Full `research/` enumeration on origin/master** (5 files): `research/CLAUDE.md`, `research/agent-instruction-inheritance/audit.md`, `research/justcheck-performance/baseline-and-research.md`, `research/justcheck-performance/ci-build-speed-telemetry-7us10.md`, `research/shell-logic-audit/findings.md`.
- **SPEC-ABSORB scan:** zero references to `research/` paths in any current `SPECIFICATION/` file (grep over `origin/master` excluding `research/` and `SPECIFICATION/history` — no SPECIFICATION hits). No SPEC-ABSORB items in this repo.

## Finalized table

| Item | Final disposition | Evidence |
|---|---|---|
| `research/agent-instruction-inheritance/audit.md` | **ARCHIVE** → `archive/research/agent-instruction-inheritance/` | Convention landed: livespec core `SPECIFICATION/history/v146/proposed_changes/agent-instruction-ai-convention-revision.md` carries `decision: accept`, `revised_at: 2026-06-26T03:26:34Z` (epic livespec-hso8). Dev-tooling share merged: `90f2cd5` (2026-06-22, "feat: assert agent-instruction surface in the fleet contract (livespec-3yebgl)") + `0353f79` (2026-06-26, "feat(checks): assert AGENTS.md .ai/<topic>.md references resolve"). Zero inbound refs on origin/master (only the `research/CLAUDE.md` directory listing). Audit filed as `fdbfee3` (2026-06-22). |
| `research/justcheck-performance/` (BOTH files: `baseline-and-research.md` + `ci-build-speed-telemetry-7us10.md`) | **STAYS** (D1: code/CI-referenced rationale, no SPECIFICATION refs) | Anchors re-verified on origin/master: `.github/workflows/ci.yml:92` ("See livespec-dev-tooling-7us.10 (research/justcheck-performance)."), `livespec_dev_tooling/red_leg_scope.py:15` (docstring), `tests/livespec_dev_tooling/test_red_leg_scope.py:11` (docstring, cites `baseline-and-research.md §(2)`). Cross-repo: livespec core `.github/workflows/ci.yml:81-82` cites "livespec-dev-tooling research/justcheck-performance (work-item livespec-dev-tooling-7us.10)". Parent epic `livespec-dev-tooling-7us` still open in ledger. |
| `research/shell-logic-audit/findings.md` | **PLAN-THREAD** → `plan/shell-logic-hardening/` in THIS repo, anchored on the EXISTING epic `livespec-dev-tooling-9j8` (no new anchor needed) | Open audit per the inventory's VERIFY rule: epic `livespec-dev-tooling-9j8` is `BACKLOG` (created 2026-06-30, updated 2026-07-01) and ALL 8 children (`9j8.1`–`9j8.8`) are `BACKLOG` — none closed (`bd show`, 2026-07-03). `git log --grep=9j8` finds only `b9f5ee8` (2026-06-30, the audit-consolidation doc commit itself) — zero remediation landings. The doc is the epic's authoritative context: the epic description AND every child description cite `research/shell-logic-audit/findings.md` verbatim. |
| `research/CLAUDE.md` | **STAYS** (directory readme; directory survives via the justcheck-performance STAYS) | Enumerates the topic subdirs and the research-vs-SPECIFICATION-vs-archive boundary; requires edits when siblings move (see obligations below). |

## Corrections vs inventory

1. **Missed file:** `research/justcheck-performance/ci-build-speed-telemetry-7us10.md` was not itemized (inventory listed the directory generically). Same STAYS disposition — `ci.yml:92` cites the directory + work-item `livespec-dev-tooling-7us.10`, and the filename itself carries the item id.
2. **Missed inbound ref (cross-repo, affects the LIVESPEC CORE inventory row):** `livespec_dev_tooling/worktree_pack/branch-protection.sh:15` references `research/factory-conformance/cross-repo-conformance-pattern.md` — a path that exists ONLY in livespec CORE's `research/` tree, not in this repo. This is a code-comment inbound ref that core's `research/factory-conformance/` disposition must account for (D1 → STAYS for core, or a reference-update obligation here if core relocates it).
3. **shell-logic-audit VERIFY resolved to PLAN-THREAD**, not ARCHIVE: findings were all converted to work-items, but the epic + all 8 children remain open (BACKLOG) with zero remediation merges.
4. **D2 verified:** no root `prompts/` directory on origin/master — nothing to retire in this repo.
5. **Non-load-bearing grep hits** (for completeness; no disposition impact): `plan/work-item-state-machine/handoff.md:87` and `plan/work-item-state-machine/research/00-l2-thin-migration.md:7` reference livespec core's `plan/<topic>/research/` (plan-thread-internal, out of epic scope); `tests/livespec_dev_tooling/checks/test_no_direct_destructive_cli.py:181,186,202,207` and `tests/livespec_dev_tooling/test_config.py:331,335` use `"dev-tooling/research/"` as synthetic fixture strings in test data, not real paths.

## Escalations for Phase 2

- **Core-row addendum (cross-repo ref):** add `livespec-dev-tooling/livespec_dev_tooling/worktree_pack/branch-protection.sh:15` as an inbound code ref on livespec core's `research/factory-conformance/` row — recommended verdict: STAYS in core per D1 (code-comment-referenced only); if core relocates it anyway, the Phase 3 executor must rewrite this dev-tooling comment in the same pass.
- No MAINTAINER-class items in this repo — all four items resolved with concrete evidence.

## Reference-update obligations (Phase 3 executor)

For the **ARCHIVE** of `research/agent-instruction-inheritance/audit.md`:

- `research/CLAUDE.md` — remove the `agent-instruction-inheritance/` bullet from "What lives here" (the bullet also cites work-item `livespec-4g2pg3`).

For the **PLAN-THREAD** move of `research/shell-logic-audit/findings.md` → `plan/shell-logic-hardening/`:

- `research/CLAUDE.md` — remove the `shell-logic-audit/` bullet from "What lives here".
- Ledger description edits (`bd update`, this repo's tenant) — every record cites the literal path `research/shell-logic-audit/findings.md` and must be repointed to the new `plan/shell-logic-hardening/` path:
  - `livespec-dev-tooling-9j8` (epic — description says "Consolidated findings ... live at livespec-dev-tooling/research/shell-logic-audit/findings.md")
  - `livespec-dev-tooling-9j8.1` through `livespec-dev-tooling-9j8.8` (all 8 children — each carries "Audit doc: research/shell-logic-audit/findings.md")
- Cross-tenant prose refs to sweep for the same literal path (the findings doc names them as prose cross-references): `livespec-gnjb` + `livespec-9sxx` (livespec core tenant), `livespec-driver-claude-hxn` (driver-claude tenant), `bd-ib-k5p` (orchestrator-beads-fabro tenant), `ob-vc7y` (openbrain tenant) — verify each description at execution time and repoint any that embed the path.

Contingent (only if livespec core relocates `research/factory-conformance/`):

- `livespec_dev_tooling/worktree_pack/branch-protection.sh:15` — rewrite the comment's `research/factory-conformance/cross-repo-conformance-pattern.md` pointer. Note this file is shipped fleet-wide via the worktree pack, so the edit lands here (single source) and propagates on the next stamp.

No obligations for the two STAYS items (`research/justcheck-performance/`, `research/CLAUDE.md`) — anchors `ci.yml:92`, `red_leg_scope.py:15`, `test_red_leg_scope.py:11`, and core `ci.yml:81-82` all hold unchanged as of 2026-07-03.
