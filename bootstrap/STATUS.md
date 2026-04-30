# Bootstrap status

**Current phase:** 5
**Current sub-step:** Phase 5 §"Retroactive TDD redo of Phase 3 + Phase 4 work — second attempt (v033 D5b)" — batch 4 complete (cycles 131-143); doctor static minimum subset DONE; Phase-3-parity is one small batch away
**Last completed exit criterion:** phase 4
**Next action:** Batch 4 landed at HEAD `9442266`. **115 tests passing** (was 100; +15 new). Coverage **100.00%** (2069 stmts + 160 branches; per-file 100% on every measured file). The strict `just check` aggregate held on every commit.

**Phase-3 doctor static minimum subset COMPLETE** (per briefing halt condition #5):

- All 8 checks in `STATIC_CHECKS` registry
- `run_static.main` orchestrator dispatches them, collects Findings, emits canonical JSON, derives exit code (0/2/3)
- `APPLICABILITY_BY_TREE_KIND` table populated explicitly
- Integration test passes against fully-seeded fixture spec tree

**Cycles 131-143 (13 cycles):**

| Cycle | Subject | sha |
|-|-|-|
| 131 | `livespec_jsonc_valid` pass arm + `Finding` + `DoctorContext` | `674e78e` |
| 132 | `livespec_jsonc_valid` fail arm for missing config | `a2626ff` |
| 133 | `livespec_jsonc_valid` fail arm for malformed JSONC | `9d67ee6` |
| 134 | `template_exists` pass arm + registry entry | `7ef8d63` |
| 135 | `template_exists` fail arm for unknown name | `8ca75fb` |
| 136 | `template_files_present` pass arm + registry | `0ed0793` |
| 137 | `proposed_changes_and_history_dirs` pass arm | `4c70e7b` |
| 138 | `version_directories_complete` pass arm | `bd8999e` |
| 139 | `version_contiguity` pass arm + registry | `f80193e` |
| 140 | `revision_to_proposed_change_pairing` pass arm | `663c67b` |
| 141 | `proposed_change_topic_format` pass arm + 8/8 registered | `2b47c04` |
| 142 | `run_static` dispatches all 8 checks + emits JSON | `a2de360` |
| 143 | explicit `APPLICABILITY_BY_TREE_KIND` table | `9442266` |

**New modules pulled into existence:**

- `livespec/context.py` — `DoctorContext(project_root, spec_root)` dataclass (frozen=True, kw_only=True, slots=True; minimal shape; widened by consumer pressure in future cycles).
- `livespec/schemas/dataclasses/finding.py` — `Finding` dataclass paired with `finding.schema.json` (six fields: check_id, status, message, path, line, spec_root).
- 8 check modules under `livespec/doctor/static/<name>.py` + paired tests.
- `livespec/doctor/static/__init__.py` widened: `STATIC_CHECKS` tuple + `APPLICABILITY_BY_TREE_KIND` dict.
- `livespec/doctor/run_static.py` widened: stub → working orchestrator (`build_parser`, `_resolve_project_root`, `_orchestrate`, `_run_one_check`, `_emit_findings_json`, `_derive_exit_code`, supervisor pattern-match).

**Decisions captured by the sub-agent (informational; no halt-and-revise needed):**

- **`Finding` shape conformed to `finding.schema.json` literally** (six fields). All checks return `IOResult[Finding, LivespecError]` per the static/CLAUDE.md contract.
- **`DoctorContext` kept minimal** (project_root + spec_root). Future cycles widen via consumer pressure when sub-spec enumeration / template_resolved_path / parsed-config caching demand it.
- **`.lash` recovery pattern** folds expected-domain `LivespecError` into fail-status `Finding` so the orchestrator's stdout JSON contract stays uniform across pass/fail outcomes.
- **6 of 8 checks landed "pass arm only"** — fail arms (e.g., gap-detection in version_contiguity, orphan-detection in revision_to_proposed_change_pairing, slug-regex in proposed_change_topic_format) deferred per "minimum subset" framing. Phase 7 hardening adds them.
- **Cycle 142 applied `monkeypatch.chdir(tmp_path)`** per the cycle-122 cwd-fallback isolation memory rule — `argv=[]` now exercises the `Path.cwd()` fallback in the orchestrator supervisor.

**Phase-3 work remaining (small):**

1. Post-step doctor wiring in `seed.main` per PROPOSAL §"`seed`" (1-2 cycles)
2. Phase-3 exit-criterion round-trip integration test pinning `seed → propose-change → critique → revise → prune-history` round-trip behavior (1-2 cycles)
3. Optional Phase-7 pre-fetch: fail arms for the 6 pass-arm-only checks + path-resolution branch for `template_exists` — deferrable but a future batch could opportunistically add them.

After 1-2 above land, **Phase-3-parity is reached**. Then **Phase-4-parity** begins: re-author 25 deleted dev-tooling/checks/*.py scripts + re-add each target to `just check` aggregate (estimated 25-50 cycles).

Open issues: zero unresolved.
**Last updated:** 2026-04-30T05:30:00Z
**Last commit:** 9442266
