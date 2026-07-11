# Orchestrator file_lloc decomposition — design record

Design record for regrooming **`bd-ib-ll0`** (236f-D orchestrator file_lloc) after the
mechanical factory slice failed HONESTLY (the anti-evasion brief worked: the agent
refused to shim-split and surfaced a real design blocker). Authored 2026-07-10 after a
maintainer decision.

## The decision (ceiling stays 200/250)

The `file_lloc` soft/hard limits (soft 200 via `no_lloc_soft_warnings`, hard 250 via
`file_lloc`) STAY. The fleet LLOC distribution proves they are well-calibrated, not too
tight:

| band | orchestrator (86) | core (129, cleaned) | runtime (32, cleaned) |
|---|---:|---:|---:|
| 0–150 | 64 | 103 | 29 |
| 150–200 | 8 | 25 | 3 |
| 200–250 | 1 | 1 | 0 |
| 250–300 | 2 | 0 | 0 |
| 300–400 | 3 | 0 | 0 |
| 400–500 | 5 | 0 | 0 |
| 500+ | 3 | 0 | 0 |

Core (128/129 ≤200, 80% under 150) and runtime (32/32 ≤200) fit comfortably — livespec's
functional style (small typed functions, ROP, no compression) naturally produces small
files. The orchestrator's fat tail (13 over 250, **8 over 400, 3 over 500**) is NOT the
limit biting good code; it is the dispatcher god-modules that accreted many concerns.
Raising the ceiling to 500 would HIDE 5 of the 8 oversized files (the "carve-out that
relaxes the invariant" the discipline forbids) — so we decompose instead.

## Root cause of the mechanical failure — and the fix

A mechanical/generated split moves **individual private (`_`-prefixed) helpers** into
sibling modules and imports them back. That trips BOTH guards:
- **pyright strict `reportPrivateUsage`** — using a `_`-name from another module.
- **livespec's `private_calls` check** — "from another module, calling
  `other_module._helper()` is banned."

**The fix — cut along PUBLIC-ENTRY-POINT boundaries.** Extract each *public* entry point
together with the private helpers **only it uses** into one new module. Only the public
entry point crosses the boundary; its private helpers stay private *within the new
module*. No promotion, no cross-module private import → both guards pass. This is exactly
the pattern the existing `_dispatcher_*` siblings already follow (`_dispatcher_plan.py`
exports `build_plan`/`render_goal`/`fabro_run_argv` as public; `dispatcher.py` imports
them publicly today). Coupling is already low: functions are keyword-only with explicit
inputs and no shared mutable module state, so the only cross-module surface is public
entry points + shared dataclasses in `types.py`.

## Slice-brief template (the fix for the honest failure)

Every decomposition slice MUST specify the DESIGN, not just "make file_lloc pass":
1. Name the SOURCE file and the TARGET new module (`_dispatcher_<concern>.py` /
   `_reflector_<concern>.py`).
2. Name the PUBLIC entry point(s) to move.
3. Instruct: move each public entry point together with the private helpers ONLY it uses;
   keep those helpers private *inside the new module*; the source file imports the public
   entry point(s) back. Do NOT import a `_`-prefixed name across modules; do NOT
   `type()`-dodge, `.buffer.write`-dodge, or add a file_lloc/lloc exemption.
4. Behavior-preserving refactor; 100% per-file coverage; RGR ritual; measure `file_lloc`
   (and `no_lloc_soft`) newly_covered → confirm the source file dropped below 250 (aim
   ≤200) and no new offender was introduced.

## The layered cut (by risk; low-risk pure clusters first)

**Layer 1 — low-risk pure-cluster extractions (factory-dispatchable with the brief above):**
- `_dispatcher_plan.py` 730 → `_dispatcher_fabro_argv.py` (the `fabro_*_argv` / `pr_*_argv` /
  `janitor_*_argv` builders, ~15 pure fns) + `_dispatcher_run_status.py` (`parse_run_id`,
  `parse_run_status`, `parse_pr_view`, `_status_check_rollup_items`, `_merge_sha_of`, …) +
  `_dispatcher_overlay.py` (`render_goal`, `render_run_config_overlay`, `_*_env_lines`,
  `_sibling_clone_steps_block`). Three extractions land plan ≤200.
- `_dispatcher_reflector_oob.py` 719 → `_reflector_findings_parse.py` (`parse_findings` +
  its `_coerce/_extract/_parse_one/_*_field` privates) + `_reflector_spans.py` (`_emit_spans`,
  `_build_span`, `_hex_id`, `_request_line`, `_emit_summary`) + `_reflector_lessons.py`
  (the `LessonProposal`/`LessonsProposer`/`RecordingLessonsProposer`/`GitPrLessonsProposer`
  classes).
- `dispatcher.py` 1634 → `_dispatcher_paths.py` (the ~11 `_*_path` / `_workflow_toml` /
  `_store_config` one-liners) — trivial leaf extraction, first proof slice.

**Layer 2 — dispatcher.py cluster extractions (medium risk; the factory's core):**
- cost-gate cluster (806–1095) → fold into the existing `_dispatcher_cost*` family.
- self-update cluster (1095–1345) → fold into the EXISTING `_dispatcher_self_update.py`
  (already a sibling — this is unfinished extraction).
- credentials cluster (2248–2388) → `_dispatcher_credentials.py`.
- admission cluster (1739–1861) → `_dispatcher_admission.py`.
- completion/bounce cluster (1861–2067) → `_dispatcher_completion.py`.
- ledger-close cluster (2388–2481) → `_dispatcher_ledger.py`.
Leaves `dispatcher.py` at its actual spine (`main`, `_run_loop_command`, `_prepare`,
`_candidates`, `_dispatch_one`, `_ready_items`) ~300 LLOC.

**Layer 3 — the medium residual files (one extraction each, per-file slices):**
`_beads_client.py` 462, `_dispatcher_engine.py` 445, `_otel_receive.py` 439 (also carries
the orch-C hand-rolled HTTP handler — extract it), `drive.py` 424, `_dispatcher_reflection.py`
402, `store.py` 389, `needs_attention.py` 385, `_otel_enrich.py` 302, `_dispatcher_cost_sink.py`
259, `_dispatcher_io.py` 253.

## Sequencing

Prove the approach on ONE Layer-1 slice (a well-briefed extraction succeeds where the
mechanical one failed), then fan out Layer 1, then Layer 2 (the dispatcher.py surgery —
higher review bar; it is the code that runs the factory), then Layer 3. Each slice is a
behavior-preserving refactor under the janitor gate + an independent Fable review. The
ceiling does NOT change; `no_lloc_soft` legacy warnings resolve as each file drops ≤200.
