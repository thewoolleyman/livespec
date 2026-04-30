# Bootstrap status

**Current phase:** 5
**Current sub-step:** Phase 5 §"Retroactive TDD redo of Phase 3 + Phase 4 work — second attempt (v033 D5b)" — batch 3 complete (cycles 118-130 + cleanup); critique/revise/prune-history Phase-3 minimum-viable; doctor static minimum subset still ahead
**Last completed exit criterion:** phase 4
**Next action:** Batch 3 landed at HEAD `b7cee9a`. **100 tests passing** (was 70; +30 new). Coverage **100.00%** (1641 stmts + 142 branches; zero missing). The strict `just check` aggregate (`check-imports-architecture, check-tests, check-coverage`) gated every commit; per-file 100% held throughout.

**Cycles 118-130 + cleanup (`c903b1c`):**

- Cycles 118-122 (`07a*..*..3da*`): **critique** full Phase-3 minimum-viable — parser, parse_argv → fs.read_text → jsonc.loads → schema validation (proposal_findings.schema.json) → delegation to `propose_change.main` with topic = `<author>-critique`.
- Cycles 123-129: **revise** full Phase-3 minimum-viable — parser → read_text → jsonc.loads → schema validation (revise_input.schema.json) → per-decision processing (write paired `<stem>-revision.md` under `history/vNNN/proposed_changes/`; move proposed-change file byte-identically into history; for accept/modify decisions, materialize `resulting_files[]` into the working spec).
- Cycle 130 (`b7cee9a`): **prune-history** Phase-3 minimum scope (parser + parse_argv → exit 0/2). Phase 7 widens to actual prune mechanic.
- Cycle 122 cleanup at `c903b1c`: deleted accidentally-staged `SPECIFICATION/proposed_changes/unknown-llm-critique.md` test-pollution artifact + added `monkeypatch.chdir(tmp_path)` to the leaky test. Lesson saved as feedback memory: tests exercising cwd-fallback branches MUST isolate cwd via `monkeypatch.chdir(tmp_path)`.

**New modules pulled into existence:**

- `livespec/schemas/dataclasses/revise_input.py` (RevisionInput dataclass)
- `livespec/validate/revise_input.py` (factory-shape validator)
- `livespec/io/fs.py` widened with `list_dir(path)` + `move(source, target)` facades
- Paired tests for all of the above

**Phase-3 work still ahead:**

1. **Doctor static minimum subset** (~16-24 cycles) — 8 checks per Plan Phase 3 line 1596-1602:
   - `livespec_jsonc_valid`, `template_exists`, `template_files_present`, `proposed_changes_and_history_dirs`, `version_directories_complete`, `version_contiguity`, `revision_to_proposed_change_pairing`, `proposed_change_topic_format`.
   - Each needs: source module under `livespec/doctor/static/<name>.py` (exports SLUG + run(ctx)), paired test under `tests/livespec/doctor/static/test_<name>.py`, registry entry in `livespec/doctor/static/__init__.py`.
   - Foundation: `DoctorContext` dataclass, `Finding` dataclass (paired with finding.schema.json), orchestrator widening in `livespec/doctor/run_static.py`, applicability-table.
2. **Post-step doctor wiring in `seed.main`** per PROPOSAL §"`seed`" (1-2 cycles).
3. **Phase-3 exit-criterion round-trip integration test** — outermost behavioral seam pinning `seed → propose-change → critique → revise → prune-history` round-trip behavior (1-2 cycles).

**Then Phase-4-parity** (re-author 25 deleted dev-tooling/checks/*.py scripts + re-add each target to `just check` aggregate — estimated 25-50 cycles depending on Phase-4 narrowness).

Open issues: zero unresolved.
**Last updated:** 2026-04-30T05:00:00Z
**Last commit:** b7cee9a
