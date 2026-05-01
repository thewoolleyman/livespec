# Bootstrap status

**Current phase:** 5
**Current sub-step:** Phase 5 §"Retroactive TDD redo of Phase 3 + Phase 4 work — second attempt (v033 D5b)" — **Phase-3-parity REACHED** at HEAD `42e4caa`; ready to begin Phase-4-parity (re-author 25 deleted dev-tooling/checks/*.py scripts + re-add each target to `just check` aggregate)
**Last completed exit criterion:** phase 4
**Next action:** Batch 5 (cycles 144-146) closed Phase-3-parity in three cycles. **123 tests passing** (was 115; +8 new). Coverage **100.00%** per-file line+branch on every measured file. All commits passed lefthook gates on first attempt.

**Cycles 144-146:**

| Cycle | Subject | sha |
|-|-|-|
| 144 | `livespec/io/proc.py` `run_subprocess` facade | `fb9925b` |
| 145 | seed wires post-step doctor via subprocess + skill-owned README | `9a600c9` |
| 146 | Phase-3 exit-criterion round-trip integration test | `42e4caa` |

**Architecture call resolved (Option A):** seed's post-step doctor invokes `bin/doctor_static.py` via subprocess through the new `livespec/io/proc.py` facade, honoring the layered-architecture import-linter contract `livespec.commands | livespec.doctor` (independent siblings). Bin path resolves via `Path(__file__).resolve().parents[2] / "bin" / "doctor_static.py"` (no hardcoded paths). Non-zero child exits stay on the IOSuccess track; OSError lifts to PreconditionError.

**Phase-3-parity criteria all met:**

- ✓ seed (parser + 5-stage railway + 7 file-shaping stages + skill-owned README + post-step doctor)
- ✓ propose-change (Phase-3 minimum-viable)
- ✓ critique (delegates to propose-change with `<author>-critique` topic)
- ✓ revise (per-decision processing; history snapshot)
- ✓ prune-history (Phase-3 minimum scope; Phase 7 widens)
- ✓ doctor static minimum subset (8 checks registered + orchestrator + applicability table)
- ✓ Phase-3 exit-criterion round-trip integration test green
- ✓ `just check` aggregate green throughout

**Phase-7 deferrals (not in scope until later phases):**

- `version_directories_complete` check should filter `history/` children to directory + `vNNN` shape so seed can also emit `<spec-root>/history/README.md`.
- Each per-check module's `.lash` recovery should produce typed missing-precondition fail Findings rather than ugly "check process error: fs.list_dir: ..." surface strings.
- v020 Q3 sub-spec routing smoke (multi-tree round-trip with `--spec-target`).
- Fail arms for the 6 doctor-static-checks where only the pass arm landed in batch 4.

**Phase-4-parity (next batch's scope):** re-author the 25 deleted dev-tooling/checks/*.py scripts + re-add each target to the `just check` aggregate as it lands. Phase-4 is the bulk of the v033 redo's remaining work — the briefing's halt #6 sets parity at "every dev-tooling/checks/*.py per the canonical list authored with paired test, every Phase-4-active target in the aggregate". Estimated ~25-50 cycles depending on per-check narrowness; sub-agent will likely halt at ~30-cycle context budget partway through, requiring 1-2 Phase-4 batches to finish.

The 25 checks to re-author (all under TDD with paired tests; each cycle re-adds its `check-<slug>` target to the `just check` aggregate):

```
all_declared, assert_never_exhaustiveness, check_tools, claude_md_coverage,
file_lloc, global_writes, heading_coverage, keyword_only_args, main_guard,
match_keyword_only, newtype_domain_primitives, no_direct_tool_invocation,
no_except_outside_io, no_inheritance, no_raise_outside_io, no_todo_registry,
no_write_direct, pbt_coverage_pure_modules, private_calls,
public_api_result_typed, rop_pipeline_shape, schema_dataclass_pairing,
supervisor_discipline, vendor_manifest, wrapper_shape
```

Open issues: zero unresolved.
**Last updated:** 2026-05-01T01:00:00Z
**Last commit:** 42e4caa
