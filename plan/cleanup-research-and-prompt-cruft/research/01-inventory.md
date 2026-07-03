# 01 — Fleet root-cruft inventory (research/ + prompts/)

Survey evidence for the `cleanup-research-and-prompt-cruft` thread
(epic anchor `livespec-ztepy5`). Captured 2026-07-03 by reading each
repo's canonical committed state (`git ls-tree origin/master`, or
`HEAD` for openbrain whose default branch is `main`), per-file
last-commit dates (`git log -1 --format=%as -- <path>`), and an
inbound-reference grep over current (non-`history/`, non-`archive/`)
tracked files. Re-run the sweep before executing — repos move.

Survey sweep (repeatable — default-branch-aware: openbrain's default
branch is `main`, so never hardcode `origin/master`; a wrong ref makes
`ls-tree` fail silently and false-reports the repo clean):

```bash
for repo in livespec livespec-driver-claude livespec-driver-codex \
    livespec-orchestrator-beads-fabro livespec-orchestrator-git-jsonl \
    livespec-console-beads-fabro livespec-dev-tooling livespec-runtime \
    openbrain; do
  ref=""
  for cand in origin/master origin/main; do
    if git -C /data/projects/$repo rev-parse -q --verify "$cand" >/dev/null 2>&1; then
      ref="$cand"; break
    fi
  done
  echo "=== $repo ($ref) ==="
  if [ -z "$ref" ]; then echo "(ERROR: no origin/master or origin/main — investigate)"; continue; fi
  git -C /data/projects/$repo ls-tree --name-only "$ref" \
    | grep -E '^(research|prompts)$' || echo "(clean)"
done
```

## Scoping decisions (D1–D3) — PROVISIONAL

Recommended defaults, adopted provisionally on 2026-07-03 because the
maintainer was away from keyboard when asked. **Phase 0 of the handoff
confirms all three with the maintainer before any mutation.** Flipping
a decision re-scopes dispositions per the notes in each table.

- **D1 — research/ fate: PRUNE, keep living references.** Stale or
  completed topics move to `archive/research/<topic>/`; genuinely
  active tracks become `plan/<topic>/` threads; load-bearing
  living-reference docs STAY in `research/` — the spec already blesses
  this ("The broader `research/` tree stays for standalone analysis
  that is not an active planning thread",
  `SPECIFICATION/non-functional-requirements.md` §"Planning Lane
  guidance"). The alternative (eliminate `research/` fleet-wide) would
  additionally require: a livespec spec revise (the
  §"research/workflow-processes/ tool-agnostic vs
  implementation-specific split" section MANDATES that directory), an
  orchestrator dispatcher code+test change
  (`_dispatcher_reflector_oob.py:688` hardcodes
  `research/loop-reflection-gate/lessons.md` as a runtime write path),
  and openbrain spec/lefthook/code reference rewrites.
- **D2 — prompts/ fate: RETIRE the root prompts/ handoff convention
  fleet-wide.** The Planning Lane (`plan/<topic>/handoff.md`) is its
  structural successor. Completed prompt files archive to
  `archive/prompts/`; a still-active handoff converts to a proper plan
  thread; convention docs that still teach `prompts/<name>.md` get
  updated (livespec `.ai/agent-disciplines.md`, console `AGENTS.md`
  row, openbrain `AGENTS.md` rows + `prompts/AGENTS.md`, plus the one
  livespec spec sentence naming `prompts/AGENTS.md` in
  `non-functional-requirements.md` §"Planning Lane guidance" → "No
  shadow ledger" — a spec change, so it goes through
  propose-change/revise, never a raw edit).
- **D3 — openbrain uppercase `PLAN/`: OUT of scope.** It is live
  drift-tracking machinery (current-specification-drift.json +
  schemas) wired into openbrain's justfile, lefthook globs,
  SPECIFICATION constraints, and the update-specification-drift
  skill — not planning cruft. The lowercase-`plan/` name collision is
  noted as a possible follow-up epic, nothing more.

## Disposition classes

- **ARCHIVE** — completed/stale; `git mv` to `archive/research/<topic>/`
  or `archive/prompts/<file>` in the same repo, updating every inbound
  reference in the same PR. Both openbrain (`archive/research/`,
  `archive/prompts/`) and livespec (`archive/prompts/`) already carry
  this convention.
- **PLAN-THREAD** — still-active planning track; becomes
  `plan/<topic>/` in its repo with a proper `handoff.md` (+ research
  file(s)) and an epic anchor filed in THAT repo's own ledger tenant
  via the capture-work-item operation, citing `livespec-ztepy5` in its
  description.
- **STAYS** — load-bearing living reference (spec-linked,
  runtime-written, or cross-repo-referenced); remains in `research/`
  under D1.
- **VERIFY** — recommended disposition depends on a mechanical check a
  Phase 1 agent performs (did the work land? grep git log / spec
  history / ledger).
- **MAINTAINER** — genuine relevance judgement; queued for the Phase 2
  maintainer checkpoint.

Evidence standard for "the work landed": a `git log --grep` hit on the
topic noun/id showing the merge, or an accepted spec history version
carrying the change, or a closed ledger item — named in the disposition
file, not asserted from memory.

## livespec (core) — research/ 14 topics, prompts/ 4 files

| Item | Last commit | Inbound refs (current files) | Disposition |
|---|---|---|---|
| `research/architecture/` | 2026-05-18 | none found | ARCHIVE |
| `research/beads/beads-gaps-workarounds.md` (+ `CLAUDE.md`) | 2026-07-02 | openbrain `AGENTS.md:304` (unqualified cross-repo mention); actively maintained | STAYS |
| `research/codex-support/` | 2026-06-24 | none found; Codex support shipped (spec §Codex dogfooding, `.agents/plugins/`) | ARCHIVE (VERIFY landed) |
| `research/copier-extension-distribution/` | 2026-06-13 | none found; copier template ships at `templates/orchestrator-plugin/` | ARCHIVE (VERIFY landed) |
| `research/dark-factory-operability/` | 2026-06-20 | `preconditions.md` ← `AGENTS.md:81` + project `CLAUDE.md` (retired-skill relocation record) | STAYS (`preconditions.md`); `work-breakdown.md` MAINTAINER (candidate split: archive the breakdown, keep the record) |
| `research/factory-conformance/cross-repo-conformance-pattern.md` | 2026-06-26 | livespec-dev-tooling `livespec_dev_tooling/worktree_pack/branch-protection.sh:15` (cross-repo comment); Conformance Pattern accepted spec v143 | STAYS (cross-repo-referenced) |
| `research/governed-repo-lifecycle/lifecycle-system-design.md` | 2026-06-26 | none found; v151 `governed-repo-lifecycle-entry-point` accepted | ARCHIVE (VERIFY v151 landed) |
| `research/mutation-testing/` | 2026-06-13 | none found; mutation testing live (`release-tag.yml`, `.mutmut-baseline.json`) | ARCHIVE |
| `research/planning-workflow-gap/` | 2026-06-25 | `planning-lane-design.md` ← `AGENTS.md:675` + project `CLAUDE.md` (diagram rationale) + `README.md:148` | STAYS |
| `research/spec-ready/` | 2026-05-18 | none found; bootstrap-era snapshots | ARCHIVE |
| `research/w6-cutover-gate/` | 2026-06-13 | none found; W6 cutover executed 2026-06-15 | ARCHIVE |
| `research/workflow-processes/` — the two spec-mandated artifacts (`tool-agnostic-workflow.md`, `architecture-summary.html` + `architecture-summary.md` and `diagrams/`) | 2026-05-18 | MANDATED by `non-functional-requirements.md` §"research/workflow-processes/ tool-agnostic vs implementation-specific split"; `README.md:119–121` links the contract-reframing pair | STAYS (mandated) |
| `research/workflow-processes/archive/` (3 dated snapshot trees) + `conversation-transcript.*` | 2026-05-18 | none found | ARCHIVE (relocate to `archive/research/workflow-processes/`) |
| `research/workflow-processes/multi-repo-split-execution-plan.md` | 2026-05-19 | docstring cite `tests/dev-tooling/checks/test_copier_template_smoke.py:7`; comment cite orchestrator `copier-update-drift.yml:26`; split executed (fleet exists) | ARCHIVE + update both citing comments to the archived path |
| `research/workflow-processes/livespec-as-contract-and-reference-implementations{,-reframing}.md`, `mermaid-vs-plantuml-llm-readable-specs.md` | 2026-06-10 | first two ← `README.md:119–121` | MAINTAINER (reframing docs read as living rationale; mermaid-vs-plantuml decision landed v105 → ARCHIVE candidate) |
| `research/CLAUDE.md` (+ per-dir `CLAUDE.md` files) | 2026-05-09 | directory readmes | follow their directory |
| `prompts/fleet-terminology-migration-{epic,prompt}.md` | 2026-06-24 | none found | ARCHIVE (VERIFY migration landed) |
| `prompts/livespec-overseer-startup.md` | 2026-06-28 | none found in tracked files | MAINTAINER (generic overseer bootstrap prompt — superseded by plan-thread handoffs, or still in maintainer use?) |
| `prompts/mermaid-diagram-handoff.md` | 2026-06-27 | none found; Mermaid standardization accepted v105, diagrams converted | ARCHIVE (VERIFY) |
| `prompts/.gitkeep` | 2026-06-23 | — | delete when dir empties (D2) |

livespec reference-update obligations (same PR as the moves):
`README.md:119–121,148` (if any linked file moves), `.ai/agent-disciplines.md:13,19`
(D2 — rewrite the `prompts/<name>.md` handoff convention to name
`plan/<topic>/handoff.md`), `tests/dev-tooling/checks/test_copier_template_smoke.py:7`
(docstring path), spec sentence naming `prompts/AGENTS.md`
(`non-functional-requirements.md` §"No shadow ledger") via
propose-change/revise. `SPECIFICATION/contracts.md` §Stop-hook text
("under a `plan/` or `prompts/` directory") needs NO change — the hook
scan is defensive and correct either way. The repo-layout table in the
project `CLAUDE.md`/`AGENTS.md` describing `archive/` as "frozen
historical artifacts from the bootstrap process" is already stale
(archive/prompts/ exists); ride-along fix.

## livespec-orchestrator-beads-fabro — research/ 4 topics

| Item | Last commit | Inbound refs (current files) | Disposition |
|---|---|---|---|
| `research/archive/w7-orchestrator-convergence/` (already self-archived in-place) | 2026-07-02 | `orchestrator-image/README.md:86,121`, `orchestrator-image/Dockerfile:5` (comment), `pyproject.toml:319` (config entry — executing agent must inspect what consumes it) | ARCHIVE (relocate to top-level `archive/research/w7-orchestrator-convergence/` + update all four refs) |
| `research/context-completeness/stage-context-audit.md` | 2026-07-02 | none found; VERY recent | VERIFY (ledger: open context-completeness items? active → PLAN-THREAD, else MAINTAINER) |
| `research/loop-reflection-gate/` | 2026-06-21 | RUNTIME: `_dispatcher_reflector_oob.py:688` writes `lessons.md` here; docstring/comment cites in `_dispatcher_cost_pricing.py`, `_dispatcher_heartbeat_probe.py`, `_dispatcher_reflection.py`, `_otel_{enrich,receive,scrub}.py`; `README.md:157` describes `research/` | STAYS (runtime-load-bearing; D1) |
| `research/CLAUDE.md` | 2026-07-02 | directory readme | STAYS while dir exists |

Note: `.claude-plugin/prose/plan.md:54,179` and
`SPECIFICATION/contracts.md:900` carry the "broader research/ tree
stays" language — under D1 no change; if D1 flips, both need revising
here too.

## livespec-console-beads-fabro — research/ 1 file, prompts/ 2 files

| Item | Last commit | Inbound refs (current files) | Disposition |
|---|---|---|---|
| `research/tui-first-milestone-bootstrap-plan.md` | 2026-06-25 | `README.md:64` ("retained only as" historical) | ARCHIVE + update `README.md:64` |
| `prompts/impl-obligations-handoff.md` | 2026-06-26 | `AGENTS.md:47` documents prompts/ as "the single living handoff" home | VERIFY (console ledger: track done → ARCHIVE; still active → PLAN-THREAD in console) |
| `prompts/spec-refinement-critique-handoff.md` | 2026-06-26 | same | VERIFY (same rule) |

D2 obligation: rewrite `AGENTS.md:47` to name `plan/<topic>/handoff.md`
as the handoff home; console has no `plan/` threads yet beyond
`plan/archive/` — the executing agent creates `plan/` content only if a
handoff converts.

## livespec-dev-tooling — research/ 4 topics

| Item | Last commit | Inbound refs (current files) | Disposition |
|---|---|---|---|
| `research/agent-instruction-inheritance/audit.md` | 2026-06-24 | none found; `.ai/` convention accepted livespec v146 | ARCHIVE (VERIFY) |
| `research/justcheck-performance/` | 2026-06-24 | `.github/workflows/ci.yml:92` comment, `red_leg_scope.py:15` docstring, `test_red_leg_scope.py:11` docstring — rationale for live carve-outs; livespec `.github/workflows/ci.yml:81` comment cites it cross-repo | STAYS (code-referenced rationale; D1) |
| `research/shell-logic-audit/findings.md` | 2026-06-30 | none found; recent | VERIFY (ledger: findings converted to work-items and closed → ARCHIVE; open audit → PLAN-THREAD) |
| `research/CLAUDE.md` | 2026-06-30 | directory readme | STAYS while dir exists |

## openbrain (adopter) — research/ 6 topics, prompts/ 1 file

Default branch is `main` (not master). openbrain already has
`archive/research/` + `archive/prompts/` precedent.

| Item | Last commit | Inbound refs (current files) | Disposition |
|---|---|---|---|
| `research/ob1-fork-patches.md` | 2026-06-21 | live patch REGISTRY: `lefthook.yml:133` glob, `AGENTS.md:214`, `spec.md:1667`, `scenarios.md:1772`, `.ai-instructions/{local-gates,ob1-fork}.md`, `implement-task-capture-surfaces.mjs:218`, `README.md:147` | STAYS (active registry, mechanically load-bearing) |
| `research/android-voice-path-decision.md` | 2026-06-10 | `spec.md:1768`, `AndroidManifest.xml:35`, `VoiceCaptureActivity.kt:14` (decision record) | STAYS (spec/code-linked decision record) |
| `research/gmail-ingest-filter/` | 2026-06-23 | `SPECIFICATION/contracts.md:663` links `candidates/human-conversations-stricter.json` as the deployed-filter definition record; migrations were seeded from it | STAYS (spec-linked; archiving would force an openbrain spec revise for one link — not worth it under D1) |
| `research/embedding-model-voyage-investigation.md` | 2026-06-12 | none found; embedding pipeline landed (v043 chunking) | ARCHIVE (VERIFY) |
| `research/livespec-impl-probing-proposal.md` | 2026-06-23 | none found; superseded — openbrain registered as livespec adopter (github-app-auth D17, 2026-07-03) | ARCHIVE (VERIFY) |
| `research/ob1-inline-autonomous-factory.md` | 2026-06-23 | none found; v086 `ob1-inline-autonomous-deploy` accepted; its handoff already archived (`archive/prompts/ob-coq-…`) | ARCHIVE (VERIFY) |
| `prompts/AGENTS.md` (the only tracked file left in prompts/) | 2026-06-15 | `AGENTS.md:31,345,349`, `README.md:283`; livespec spec names "a per-repo prompts/AGENTS.md (or equivalent)" | D2: fold the convention (epic-status-print directive etc.) into the AGENTS.md plan-thread row, archive the file, remove the dir. `README.md:283` is ALREADY stale (cites prompts/ handoffs `li-ruxxwt`, `li-agfejw` that now live in `archive/prompts/`) — fix regardless |

## Clean repos — verify-only

`livespec-driver-claude`, `livespec-driver-codex`,
`livespec-orchestrator-git-jsonl`, `livespec-runtime` carry no root
`research/` or `prompts/` on origin/master (surveyed 2026-07-03).
Phase 5 re-runs the sweep to confirm nothing appeared meanwhile.

## Observed but OUT of scope (log only)

- openbrain `PLAN/` (D3 — live drift machinery; name collision with
  `plan/` noted as possible follow-up).
- openbrain root: `android-capture-spike/`, `docs/`, four
  `*-audit.jsonl` files, `.idea/`, `.vscode/` — not research/prompts
  cruft; separate call.
- livespec `docs/`, `prior-art/` (documented intentional),
  `archive/` bootstrap trees.
- orchestrator `acceptance/`, `orchestrator-image/` — product surface.
- `research/workflow-processes/` internal `archive/` demonstrates
  archive-inside-research; this cleanup relocates it under the
  top-level `archive/` so "archived" means ONE place per repo.

## Cross-repo coordination hazards

- openbrain `AGENTS.md:304` cites `research/beads/beads-gaps-workarounds.md`
  with no repo qualifier — the path exists only in livespec. Under D1
  the livespec file STAYS, so nothing breaks; the executing openbrain
  agent should still qualify the reference (point it at the livespec
  repo explicitly) as a ride-along fix.
- livespec `.github/workflows/ci.yml:81` comment cites dev-tooling's
  `research/justcheck-performance` — STAYS under D1; no change.
- dev-tooling `livespec_dev_tooling/worktree_pack/branch-protection.sh:15`
  cites livespec's `research/factory-conformance/…` — STAYS under D1;
  no change.
- If the maintainer flips D1 to "eliminate", every STAYS row above
  converts to a coordinated multi-repo move with spec revises and the
  orchestrator dispatcher code change — re-plan before executing.
