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
   `type()`-dodge, `.buffer.write`-dodge, or add a file_lloc/lloc exemption; **do NOT add a
   dynamic `__getattr__` (module- or class-level) compat/re-export shim** — it re-exposes the
   moved private names while being invisible to BOTH `reportPrivateUsage` and `private_calls`,
   so it passes the mechanical gates while defeating the whole point of the cut. (The factory's
   first `bk0` attempt did exactly this at intermediate commit `720be73`; the in-PR follow-up
   `af4a5c2` had to strip it. Ban it up front.) A moved private helper that a caller still needs
   is PROMOTED to a public name, not tunnelled through `__getattr__`.
   **Do NOT compress names or delete comments/docstrings to hit the LLOC target.** The target is
   met by MOVING a cohesive cluster OUT into its own module, never by golfing what remains —
   renaming descriptive kwargs to terse forms (`action_id`→`aid`, `work_item_id`→`wid`,
   `summary`→`msg`) or stripping docstrings to squeak under 200/250 violates livespec's
   no-compression style value and is a review blocker when it is what got the file under the line.
   (The `bd-ib-51a` drive slice did this — behavior-neutral, private-only, so it shipped, but
   `_drive_valves.py` landed at exactly 200 via compressed names; a future touch should restore
   them.) If a moved cluster is still >200 after a clean cut, cut again — don't golf.
4. **Cycle-breaking idiom (when the extracted module needs a name that STAYS in the source).**
   Extraction sometimes creates a would-be import cycle (source imports the new module at module
   level; the new module needs a function/type that stayed in the source). Break it WITHOUT a
   cross-module private import, in this preference order: (a) **dependency injection** — pass the
   needed callable/type in as a parameter (the L3 engine slice's `outcome_type=DispatchOutcome`
   class-injection; the reflection slice's injected `scan=` callable + a frozen config); (b) a
   `TYPE_CHECKING`-only import when the need is purely a type annotation (the engine janitor module);
   (c) a **method-local (deferred) import** as a last resort (the store slice's
   `BeadsWorkItemStore.read_work_items`). Prefer (a); reserve (c) for when injection would distort
   the public API. Whichever you use, add ONE journal line naming it (the L3 series used all three;
   name yours so the L2 dispatcher.py slices stay consistent).
5. Behavior-preserving refactor; 100% per-file coverage; RGR ritual; measure `file_lloc`
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

## Session-6 state — Layer 1 DONE; L2/L3 slice ledger (measured @ orch origin/master ae87e96, dev-tooling v0.37.3)

**Layer 1 COMPLETE + MERGED (all three genuine cohesion cuts; independent-review-gated):**
`bd-ib-mmp` PROOF → PR #452 (dispatcher.py → `_dispatcher_paths.py`) CLOSED;
`bd-ib-9t1` → PR #455 (`_dispatcher_plan.py` 730 → a FOUR-way split: `_dispatcher_fabro_argv` 179/`_dispatcher_run_status` 172/`_dispatcher_overlay` 199/`_dispatcher_projection` 104 — the 4th, credential/telemetry projection, was a good extra cut beyond the briefed three; `_dispatcher_plan.py` now 200 LLOC and is ~half a public re-export hub, so Layer 2 SHOULD rewire dispatcher.py to import directly from the four extracted modules rather than through `_dispatcher_plan`);
`bd-ib-bk0` → PR #454 (`_dispatcher_reflector_oob.py` 719 → `_reflector_findings_parse`/`_reflector_spans`/`_reflector_lessons` + `_reflector_filing`/`_filing_store`/`_runtime`; the PR title "remove reflector private helper facade" is the build removing its own intermediate facade — final state is a genuine public-API cut). After L1: **11 files remain >250** (dispatcher.py 1713, `_beads_client.py` 462, `_otel_receive.py` 456, `_dispatcher_engine.py` 445, `drive.py` 424, `_dispatcher_reflection.py` 402, `store.py` 389, `needs_attention.py` 385, `_otel_enrich.py` 302, `_dispatcher_cost_sink.py` 259, `_dispatcher_io.py` 253).

**Layer 2 — dispatcher.py cluster surgery (SEQUENTIAL chain; all edit dispatcher.py).** Extract each
cluster's PUBLIC entry point(s) + exclusive privates into a `_`-prefixed public-API module. The
dispatcher.py spine to KEEP: `main`, `_build_parser`, `_prepare`, `_candidates`, `_ready_items`,
`_is_dispatch_candidate`, `_dispatch_one`, `_post_run_dispositions`, `_run_id`, `_janitor_core_ref`.
The named clusters (functions by name — line numbers drift as each slice lands, so match by name):
- **L2-a cost-gate** → NEW `_dispatcher_cost_gate.py`: `_cost_gate_after_verdict`, `_cost_gate`,
  `_emit_cost_report_telemetry`, `_dispatch_id_of`, `_derived_costs`/`_read_derived_costs`,
  `_derived_reports`/`_read_derived_reports`. (Do NOT fold into `_dispatcher_cost_sink.py` — it is
  itself over-ceiling.) FILED `bd-ib-xwx` (ready, the L2 PROOF).
- **L2-b self-update** → EXISTING `_dispatcher_self_update.py` (97): `_self_update_after_verdict`,
  `_candidate_dispatcher_bin`, `_self_update_after_merge`, `_self_update`. (If fold >200 → new module.)
- **L2-c admission** → NEW `_dispatcher_admission.py`: `_Admission`, `_autonomous_armed`,
  `_admit_and_select`, `_admission_held_outcome`.
- **L2-d completion/bounce** → NEW `_dispatcher_completion.py`: `_complete_and_accept`,
  `_bounce_non_convergence_to_backlog`, `_bounce_blocked`, `_host_only_refusal`, `_warn_item_sizing`.
- **L2-e needs-human** → EXISTING `_dispatcher_needs_human.py` (103): `_resolve_or_bounce_needs_human`,
  `_journal_needs_human_decision`, `_route_needs_human_resolved`.
- **L2-f credentials/sibling** → NEW `_dispatcher_credentials.py`: `_github_token_supplier`,
  `_dispatch_required_credentials_text`, `_read_dispatch_target_credential_wrapper`,
  `_credential_wrapper_text`, `_check_credential_env`, `_read_host_codex_auth`,
  `_CodexProjectionRefusal`, `_project_codex_auth`, `_resolve_sibling_clones`,
  `_fetch_fleet_manifest_text`, `_materialize_overlay`, `_read_dispatch_comments`.
- **L2-g ledger-close** → NEW `_dispatcher_ledger_close.py` (name avoids existing `_dispatcher_ledger_checks.py`):
  `_close_item`, `_normalize_native_open_statuses`, `_append_normalization_note`,
  `_ledger_blocked_after_normalization`, `_ledger_blocked`, `_write_findings`, `_load_items`, `_emit_outcomes`.
- **L2-h calibration** → EXISTING `_dispatcher_calibration.py` (108): `_emit_calibration`,
  `_read_journal_records_for`, `_calibration_token_cost`, `_merged_pr_diff_size`, `_parse_pr_diff_size`.
  (If fold >200 → new module.)
- **L2-i post-verdict** → NEW `_dispatcher_post_verdict.py`: `_reflector_oob_after_verdict`,
  `_default_reflector_spawn`, `_spawn_daemon`, `_spawn_daemon_joining`, `_alarm_on_terminal_failure`,
  `_github_token_error_supplier`, `_post_verdict_runner`, `_ReflectorSpawn`.
- **L2-j otel-wiring** → NEW `_dispatcher_otel_wiring.py`: `_build_otel_receiver`, `_ensure_otel_receiver`,
  `_parse_janitor`.
- **L2-k command handlers** → NEW `_dispatcher_run_commands.py`: `_run_dispatch_command`,
  `_run_loop_command`, `_dispatch_preamble`, `_requested_items_preflight_error`, `_resolve_fabro_bin_for`,
  `_fabro_preflight_error`, `_run_ledger_check`, `_run_spec_check`, `_run_janitor_check`, `_emit_check_findings`.
Order a→k, each blocked_by the previous. Only L2-a filed so far; file b→k as the chain advances (or up
front chained) — each with a design-specifying brief per the Slice-brief template above. A final trim
slice may be needed once a–k land.

**Layer 3 — single-file residuals (independent → PARALLEL; none overlaps L2 or each other). ALL FILED `ready`:**
`bd-ib-9a3` `_dispatcher_cost_sink.py` 259 (trivial); `bd-ib-3hk` `_dispatcher_io.py` 253 (trivial);
`bd-ib-xyf` `_otel_enrich.py` 302; `bd-ib-d4v` `needs_attention.py` 385 → `_needs_attention_core_roots`;
`bd-ib-7my` `store.py` 389 → `_store_mutations`; `bd-ib-epx` `_dispatcher_reflection.py` 402 →
`_dispatcher_reflection_spans`; `bd-ib-51a` `drive.py` 424 → `_drive_valves`; `bd-ib-xw5`
`_dispatcher_engine.py` 445 → `_dispatcher_engine_merge`; `bd-ib-g6a` `_beads_client.py` 462 →
`_beads_client_fake`+`_beads_client_argv`; `bd-ib-grr` `_otel_receive.py` 456 → `_otel_http_handler`+`_otel_parse`
(the latter is the orch-C hand-rolled HTTP handler the design record calls out). Full seam detail is in
each slice's `bd show <id>` description.

**Done-definition:** all 11 files ≤250 (pinned-venv file_lloc, `just check` green) → orchestrator
Phase-1 file_lloc burndown COMPLETE. The Phase-2 file_lloc *flip* then waits on the dev-tooling
legacy-tree follow-up (`livespec-iily`) so a non-core repo can flip file_lloc via config.
