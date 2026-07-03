# 02 — Phase 1 disposition validation: **livespec** (core)

**Repo:** `livespec` (/data/projects/livespec, validated against `origin/master`)
**Date:** 2026-07-03 · **Validated by:** Phase 1 read-only disposition-validation agent (epic `livespec-ztepy5`)
**Scope:** every row of `plan/cleanup-research-and-prompt-cruft/research/01-inventory.md` §"livespec (core)", re-verified per the evidence standard (merge SHA, accepted `history/vNNN/`, or closed ledger id — never memory).

**Root-cruft re-check.** `git ls-tree --name-only origin/master` confirms `research/` and `prompts/` remain the only root cruft dirs. The root `docs/` dir is NOT cruft — it holds only the living `docs/installation.md`, actively maintained through the terminology migration (`a049143`) and the v156 credential-wrapper revise (`74d90a5`). Full `ls-tree -r` enumeration of `research/` + `prompts/` matches the inventory exactly; **no new files** since the 2026-07-03 morning survey. Precedent confirmed: `archive/prompts/` is already the established destination for retired prompts (`3188d11`, 2026-06-28, moved `prompts/governed-repo-lifecycle-handoff.md` → `archive/prompts/` with a closure banner).

## Finalized disposition table

| Item | Final disposition | Evidence |
|---|---|---|
| `research/architecture/` | **ARCHIVE** | Bootstrap-era; last commit `20f8799` 2026-05-18; zero inbound refs (full sweep 2026-07-03). |
| `research/beads/beads-gaps-workarounds.md` (+ `CLAUDE.md`) | **STAYS** | Actively maintained — last commit `00fcdeb` 2026-07-02 ("link create status PR"); cross-repo inbound ref openbrain `AGENTS.md:304` re-verified (at openbrain HEAD; its checkout has no `origin/master` refname). Non-spec ref → STAYS per D1. |
| `research/codex-support/` | **ARCHIVE** — verified landed | Docs already carry a SUPERSEDED banner (`bbe4909`, 2026-06-23: "retired in PR #528; v129 spec cut adopted the distributed Codex driver"). Codex support accepted across spec history **v057, v117, v118, v119, v120, v129 (codex-distributed-driver), v131, v149**. Zero inbound refs. Archive preserves the banner's "why distributed was chosen" record. |
| `research/copier-extension-distribution/` | **ARCHIVE** — verified landed | Recommendation (work-item **livespec-2jsj**, Option 3′: stamp canonical slugs into a committed template asset) adopted verbatim: `templates/orchestrator-plugin/canonical-slugs.yml` landed via `9dd8b1f` ("project canonical-slug set into committed copier-template data (livespec-2jsj)"); template scaffold `1034834` (PR #116), renamed impl-plugin→orchestrator-plugin `a304b09`; the Jinja extension is deleted — neither `copier.yml:18` nor `templates/orchestrator-plugin/copier.yml:32` declares `_jinja_extensions` (both carry comments saying so). Zero inbound refs. |
| `research/dark-factory-operability/preconditions.md` (+ `CLAUDE.md`) | **STAYS** | Inbound ref `AGENTS.md:81` re-verified (`.claude/CLAUDE.md` is a symlink to `../AGENTS.md` — one anchor, not two; see Corrections). Relocation record for the retired W6 skill duties. Last commit `7986f20` (livespec-0jxs). |
| `research/dark-factory-operability/work-breakdown.md` | **MAINTAINER** (queued) | Self-declares "OPEN RESEARCH — actively iterating; NOT ratified"; last touched `ba7acba` 2026-06-20; no ledger epic anchors it; the grooming surface it deliberated has since landed (`groom` is a required orchestrator contract skill). See Escalations. |
| `research/factory-conformance/cross-repo-conformance-pattern.md` | **STAYS** | Conformance Pattern accepted **v143** (`conformance-pattern.md` + revision in `history/v143/`; landed `9c7c87c`, livespec-zs22.7.2). Cross-repo inbound ref livespec-dev-tooling `livespec_dev_tooling/worktree_pack/branch-protection.sh:15` re-verified on that repo's origin/master. **NEW inbound ref found:** `templates/orchestrator-plugin/copier-questions.yml:75` (comment) — reinforces STAYS. |
| `research/governed-repo-lifecycle/lifecycle-system-design.md` | **ARCHIVE** — verified landed | **v151** `governed-repo-lifecycle-entry-point` decision **accept** (revised 2026-06-27, `history/v151/proposed_changes/`); ledger epic **livespec-zs22.8 CLOSED** with all milestones zs22.8.1–zs22.8.6 closed (M1–M6 ✓); the track's own handoff was already archived at epic close (`3188d11`). Zero inbound refs (single commit `cc6f747`). |
| `research/mutation-testing/` | **ARCHIVE** | Mutation testing live: `.mutmut-baseline.json` at repo root on origin/master; `check-mutation` ratchet wired into `.github/workflows/release-tag.yml:14–17`; last commit `67c550a` (livespec-mutreal.1). Zero inbound refs. |
| `research/planning-workflow-gap/` (both files) | **STAYS** | Inbound refs re-verified: `AGENTS.md:675` (planning-lane-design.md, diagram rationale) + `README.md:148` (design-rationale link). Last commit `e622abd` (livespec-zs22.3). Non-spec refs → STAYS per D1. |
| `research/spec-ready/` | **ARCHIVE** | Bootstrap-era distilled snapshots; single commit `9f98dbc` 2026-05-18; zero inbound refs. |
| `research/w6-cutover-gate/` | **ARCHIVE** — verified executed | Gate rules written `32ee27f` 2026-06-13 (livespec-iaut); cutover executed `ebd7d89` 2026-06-15 ("retire /livespec-orchestrate at the W6 dark-factory cutover", livespec-a8bb, spec cut **v112**). Zero inbound refs. |
| `research/workflow-processes/` — the two spec-mandated artifacts (`tool-agnostic-workflow.md`, `architecture-summary.html` + companion `architecture-summary.md`, `diagrams/`) | **SPEC-ABSORB** | Mandate re-verified at `SPECIFICATION/non-functional-requirements.md:455–457` (§"research/workflow-processes/ tool-agnostic vs implementation-specific split" — an H3). Obsolescence signal is strong: `tool-agnostic-workflow.md` carries **76** `memo` mentions (memo retired at **v123**, `c09f024`), and **v151**'s accepted `tool-agnostic-workflow-diagram` proposal explicitly re-authored the stale SVG into `spec.md:5` §"Tool-agnostic workflow — spec / implementation lifecycle". Propose-change retires (or inlines the still-true residue of) the mandate section, THEN archive. |
| `research/workflow-processes/archive/` (3 dated snapshot trees) + `conversation-transcript.{md,html}` | **ARCHIVE** | Zero inbound refs; frozen dated snapshots. |
| `research/workflow-processes/multi-repo-split-execution-plan.md` | **ARCHIVE** + citation repoints | Split executed (fleet exists); last commit `1487999` 2026-05-19. Both citations re-verified: livespec `tests/dev-tooling/checks/test_copier_template_smoke.py:7` (docstring) and livespec-orchestrator-beads-fabro `.github/workflows/copier-update-drift.yml:26` ("Phase E of …", on that repo's origin/master). The template source `copier-update-drift.yml.jinja` does NOT carry the citation — orchestrator-side comment only. |
| `research/workflow-processes/livespec-as-contract-and-reference-implementations{,-reframing}.md` | **MAINTAINER** (queued) | `README.md:119` + `:121` re-verified — linked as "Design rationale" for the canonical architecture (normative home is spec.md §"Contract + reference implementations architecture"). Non-spec refs. See Escalations. |
| `research/workflow-processes/mermaid-vs-plantuml-llm-readable-specs.md` | **MAINTAINER** (queued) | Decision codified: **v105** `mermaid-diagram-format-standardization` decision **accept** (revised 2026-06-10); research captured same day (`4d89d74`). Zero inbound refs. See Escalations. |
| `research/CLAUDE.md` (+ per-dir `CLAUDE.md`) | **follow their directory** | `research/CLAUDE.md` STAYS (the dir persists — beads, factory-conformance, planning-workflow-gap, dark-factory preconditions all stay); each per-dir `CLAUDE.md` moves with its directory. |
| `prompts/fleet-terminology-migration-{epic,prompt}.md` | **MAINTAINER** — escalated from ARCHIVE (VERIFY) | Migration ran: core `a049143` ("migrate core terminology to fleet"), spec **v133** `core-fleet-terminology` **accept** (`409c355`), dev-tooling `7dfc218` ("migrate fleet terminology"). BUT residual active-scope domain-meaning `family` occurrences remain in core (see Escalations) and the epic's required committed classification-inventory note could not be located — evidence partially contradicts "landed". |
| `prompts/livespec-overseer-startup.md` | **MAINTAINER** (queued) | Last commit `9ab89bb` 2026-06-28 (actively shaped); zero tracked inbound refs; it is the operational companion of the **retained** local `.claude/skills/overseer/SKILL.md`. See Escalations. |
| `prompts/mermaid-diagram-handoff.md` | **ARCHIVE** — verified landed (corrected evidence) | Track = "lifecycle-diagram", NOT the v105 standardization: **v151** `tool-agnostic-workflow-diagram` decision **modify/accepted** 2026-06-27; section live at `SPECIFICATION/spec.md:5`; the declared impl-followup (`readme-link-lifecycle-diagram`) landed at `README.md:13–14`. Every deliverable named in the handoff is on master. |
| `prompts/.gitkeep` | **delete when dir empties** (D2) | — |

## Corrections vs inventory

1. **`prompts/mermaid-diagram-handoff.md` evidence corrected.** The inventory cited "Mermaid standardization accepted v105" — wrong landing. v105 (2026-06-10) predates the prompt (`59e027f`, 2026-06-27). The prompt's actual track is the tool-agnostic lifecycle diagram, which landed via **v151** (`tool-agnostic-workflow-diagram`, revised 2026-06-27) + `spec.md:5` + the README link `README.md:13–14`. Disposition unchanged (ARCHIVE), evidence replaced.
2. **Missed inbound reference:** `templates/orchestrator-plugin/copier-questions.yml:75` (comment) cites `research/factory-conformance/cross-repo-conformance-pattern.md`. The sweep's `':!templates'` exclusion hid it. No action needed (target STAYS), but it must be on record: if that doc is ever archived, this template comment must be repointed too.
3. **"AGENTS.md + project CLAUDE.md" is ONE anchor, not two.** `.claude/CLAUDE.md` on origin/master is a mode-120000 symlink whose blob content is `../AGENTS.md`. All "AGENTS.md + project CLAUDE.md" double-refs in the inventory (dark-factory preconditions, planning-lane-design) collapse to single AGENTS.md edits.
4. **`prompts/fleet-terminology-migration-{epic,prompt}.md` escalated ARCHIVE → MAINTAINER.** Residual active-scope `family` occurrences contradict a clean "migration landed": `.claude/hooks/livespec_footgun_guard.py:5,42` ("livespec family" — unambiguously domain-fleet per the prompt's own mapping table), `.github/scripts/export-ci-telemetry.sh:29` (`NAMESPACE="livespec-family"`), `SPECIFICATION/non-functional-requirements.md:206` ("self-application family", arguably deliberate generic English — it survived the v133 revise), `dev-tooling/checks/behavior_scenario_link.py:15`, `dev-tooling/reap_stale_worktrees.py:4,11`, `dev-tooling/spec_clauses.py:4`, four template copies (`templates/orchestrator-plugin/.claude/hooks/github_auth_guard.py`, `.github/scripts/export-ci-telemetry.sh`, `ci.yml.jinja`, `copier-update-drift.yml.jinja`), and five test-file occurrences. The epic required each retention to be classified with a committed inventory note; none was found (`a049143` has no body, no PR).
5. **Root `docs/` dir exists but is not cruft** (living `docs/installation.md`); inventory's "research/ + prompts/ only" claim stands for cruft purposes.
6. **openbrain anchor verified at HEAD**, not `origin/master` — that checkout has no `origin/master` refname; `HEAD:AGENTS.md:304` carries the `beads-gaps-workarounds.md` Entry-11 reference as inventoried.
7. All other cited anchors re-verified with **no line drift**: `AGENTS.md:81`, `AGENTS.md:675`, `README.md:119`, `README.md:121`, `README.md:148`, `.ai/agent-disciplines.md:13` + `:19`, `non-functional-requirements.md:176` (§"No shadow ledger") + `:455–457` (mandate), `contracts.md:230`, `tests/dev-tooling/checks/test_copier_template_smoke.py:7`, dev-tooling `branch-protection.sh:15`, orchestrator `copier-update-drift.yml:26`.

## Escalations for Phase 2 (MAINTAINER checkpoint)

| Item | Recommended verdict (one line) |
|---|---|
| `research/dark-factory-operability/work-breakdown.md` | **ARCHIVE** — the decomposition surface it deliberated (capture-time judgement + grooming pass) landed as the orchestrator's required `groom` skill; untouched since `ba7acba` 2026-06-20 with no epic anchor; if the maintainer still considers the deliberation open, convert to `plan/dark-factory-work-breakdown/` instead. |
| `research/workflow-processes/livespec-as-contract-and-reference-implementations{,-reframing}.md` | **STAYS** — they are the README's deliberate "Design rationale" citations (`README.md:119,121`) for the canonical architecture whose normative home is the spec; archiving buys nothing but link churn. |
| `research/workflow-processes/mermaid-vs-plantuml-llm-readable-specs.md` | **ARCHIVE** — decision fully codified at v105 (accepted 2026-06-10) and in spec §"Template manifest"; zero inbound refs. |
| `prompts/livespec-overseer-startup.md` | **RELOCATE** to `.claude/skills/overseer/` beside the retained local overseer SKILL.md (still operational until the console cockpit replaces the overseer), satisfying D2 by emptying `prompts/` without losing an in-use artifact. |
| `prompts/fleet-terminology-migration-{epic,prompt}.md` | **ARCHIVE after filing a residual-cleanup work-item** — file one small ledger item to classify/fix the ~13 active-scope `family` occurrences listed in Corrections #4 (footgun-guard wording is a clear fix; telemetry `NAMESPACE="livespec-family"` may be a deliberate continuity freeze needing an explicit recorded exclusion), then archive both prompts. |

## Reference-update obligations (Phase 3 executor)

**D2 convention-doc edits (livespec):**
1. `.ai/agent-disciplines.md:13` — delete the `prompts/<name>.md` alternative from the standing-handoff definition ("whether a \`prompts/<name>.md\` or a plan thread's…" → plan-thread-only wording).
2. `.ai/agent-disciplines.md:18–20` — remove the fenced `run prompts/<name>.md` resume-command block (line 19), leaving the plan-thread form (`/livespec-orchestrator-beads-fabro:plan <topic>`, line 25) as the only pattern.
3. `SPECIFICATION/non-functional-requirements.md:176` (§"Planning Lane guidance" → "No shadow ledger") — via **propose-change → revise**: replace "a per-repo `prompts/AGENTS.md` (or equivalent) defines the convention locally" with the `plan/<topic>/` successor convention. Spec file — never edited directly.
4. `AGENTS.md:24` — refresh the repo-layout `archive/` row ("Frozen historical artifacts from the bootstrap process — do not edit") to also cover relocated research/prompt artifacts (`archive/research/`, `archive/prompts/` — the latter already exists per `3188d11`). One edit only: `.claude/CLAUDE.md` is a symlink to it.
5. `prompts/.gitkeep` — delete once the last prompt file is relocated/archived (D2).

**SPEC-ABSORB propose-change (workflow-processes mandate):**
6. `SPECIFICATION/non-functional-requirements.md:455–457` — propose-change to retire (or inline any still-true residue of) §"research/workflow-processes/ tool-agnostic vs implementation-specific split", citing: memo paradigm retired v123, the v151 `spec.md:5` diagram re-authoring the stale SVG, and the 76 stale `memo` mentions in the mandated artifact. Heading is an H3, so `tests/heading-coverage.json` (H2 map) is likely unaffected — re-check at payload time. Archive the artifacts only AFTER the revise accepts.

**ARCHIVE-driven citation repoints:**
7. `tests/dev-tooling/checks/test_copier_template_smoke.py:7` — repoint docstring path to `archive/research/workflow-processes/multi-repo-split-execution-plan.md`.
8. Cross-repo (file a work-item in livespec-orchestrator-beads-fabro): `.github/workflows/copier-update-drift.yml:26` — same repoint. Note: livespec's template source `copier-update-drift.yml.jinja` does NOT carry the citation; the edit is orchestrator-side only.
9. `README.md:119–121` — retarget the two design-rationale links ONLY IF Phase 2 overrides the recommended STAYS and archives the contract/reframing pair.
10. Conditional on Phase 2 verdicts: overseer-startup relocation (obligation 5's precondition) and the terminology residual-cleanup work-item (Escalations row 5).

**Verified no-change refs (do NOT touch):**
- `SPECIFICATION/contracts.md:230` — Stop-hook description "under a `plan/` or `prompts/` directory" is generic scanner wording, still correct after D2.
- `SPECIFICATION/non-functional-requirements.md:65` and `.claude-plugin/prose/seed.md:14` + the two schema descriptions — all reference **template-internal** `prompts/seed.md`-style paths, not the root dir.
- `SPECIFICATION/non-functional-requirements.md:174` and `:182` — reference the `research/` TREE as a concept; research/ remains spec-blessed under D1.
- `.github/workflows/ci.yml:81` — cites livespec-dev-tooling's `research/justcheck-performance` (STAYS in that repo per its own table).
- `templates/orchestrator-plugin/copier-questions.yml:75`, livespec-dev-tooling `branch-protection.sh:15`, openbrain `AGENTS.md:304` — their targets STAY.

## Phase 2 verdicts — CONFIRMED by the maintainer (2026-07-03)

Every MAINTAINER row above is now resolved; the verdicts below are
authoritative over the table's queued dispositions.

| Item | CONFIRMED verdict |
|---|---|
| `research/dark-factory-operability/work-breakdown.md` | **ARCHIVE** → `archive/research/dark-factory-operability/work-breakdown.md` (sibling `preconditions.md` + dir `CLAUDE.md` STAY). |
| `research/workflow-processes/livespec-as-contract-and-reference-implementations{,-reframing}.md` | **ARCHIVE + retarget README** (maintainer OVERRODE the STAYS recommendation) → `archive/research/workflow-processes/`; obligation 9 ("README.md:119–121 retarget") is now UNCONDITIONAL. |
| `research/workflow-processes/mermaid-vs-plantuml-llm-readable-specs.md` | **ARCHIVE** → `archive/research/workflow-processes/`. |
| `prompts/livespec-overseer-startup.md` | **RELOCATE** → `.claude/skills/overseer/livespec-overseer-startup.md` (beside the retained local overseer SKILL.md; archives later when the console cockpit retires the overseer). |
| `prompts/fleet-terminology-migration-{epic,prompt}.md` | **ARCHIVE + file residual work-item**: file ONE ledger item (livespec tenant, citing livespec-ztepy5) to classify/fix the ~13 residual active-scope `family` occurrences from Corrections #4, THEN `git mv` both files to `archive/prompts/`. |

Consequences for the obligations list: obligation 9 becomes
unconditional; obligation 10's two preconditions are now decided
(relocation YES; residual work-item YES). With the workflow-processes
pair and mermaid doc archived alongside the SPEC-ABSORB artifacts and
the already-ARCHIVE rows, everything under
`research/workflow-processes/` leaves `research/` — the executor
archives the whole directory (preserving subpaths under
`archive/research/workflow-processes/`) once the mandate-retirement
revise lands. `research/` residents after execution: `CLAUDE.md`,
`beads/`, `dark-factory-operability/{CLAUDE.md,preconditions.md}`,
`factory-conformance/`, `planning-workflow-gap/`.
