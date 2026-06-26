# doctor

Harness-neutral driving prose for the `doctor` operation, per
`SPECIFICATION/spec.md` §"Contract + reference implementations
architecture": this artifact is the core-owned LLM-facing half of the
operation; the doctor CLI named in `.livespec.jsonc` (core reference
implementation: `bin/doctor_static.py`) is the contract half. Drivers
bind this prose to their runtime; nothing in this file names any
specific agent runtime's tools or command namespace.

`doctor` runs in two layers lines
2546-2606:

- **Static phase** is implemented in Python at core's
  `livespec/doctor/run_static.py` and invoked via the doctor CLI
  (core reference `bin/doctor_static.py`). The orchestrating loop
  enumerates every spec tree (main spec + each sub-spec under
  `templates/<name>/`), runs the registered checks per the
  per-tree applicability table, and emits
  `{"findings": [...]}` JSON to stdout. Each finding carries
  `check_id`, `status` (`pass`/`fail`/`skipped`), `message`,
  optional `path`, optional `line`, and `spec_root` (the
  per-tree origin marker).
- **LLM-driven phase** is prose-driven behavior — there is no
  Python entry point because Python doesn't invoke the LLM. The
  LLM-driven phase has two categories (objective + subjective)
  and is template-extensible via the active template's
  `template.json` declarations
  (`doctor_llm_objective_checks_prompt`,
  `doctor_llm_subjective_checks_prompt`).

There is no separate `bin/doctor.py` wrapper; the user invokes the
doctor operation (or expresses intent in dialogue) and the LLM
follows this prose end-to-end.

## When to run

- **Direct user request.** The user invokes the doctor operation,
  says "run doctor", "check the spec", or asks to verify spec
  invariants. The LLM follows this prose from the top:
  Steps 1-4 (static phase) → Steps 5-9 (LLM-driven phase) →
  Step 10 (per-finding dialogue).
- **Post-step from another CLI-backed operation.** The
  `seed`, `propose-change`, `critique`, and `revise` CLIs
  internally run the static phase as their post-step (the
  CLI invokes `run_static.run` in-process; the
  static findings are emitted by the calling CLI, not by
  the standalone doctor CLI). When the CLI exits `0`, the
  calling operation's prose delegates to **this** prose for the
  LLM-driven phase only (Steps 5-10; Steps 1-4 are skipped).
  When the CLI exits non-zero (1 or 3), the LLM-driven
  phase MUST NOT run; the calling operation surfaces the failure
  to the user and aborts.

## Inputs

The doctor CLI accepts:

- `--project-root <path>` (optional; defaults to cwd).

The CLI has no JSON input; it reads `.livespec.jsonc` from
disk via the upward walk and discovers sub-spec trees by
listing `<main-spec-root>/templates/<name>/`.

Two LLM-layer flag pairs apply during the LLM-driven phase but
are NEVER passed to the doctor CLI (per
SPECIFICATION/spec.md §"Sub-command lifecycle"):

- `--skip-doctor-llm-objective-checks` /
  `--run-doctor-llm-objective-checks` (mutually exclusive).
- `--skip-doctor-llm-subjective-checks` /
  `--run-doctor-llm-subjective-checks` (mutually exclusive).

Both-flags-in-the-same-pair is a usage error; surface and
abort the LLM-driven phase. The flags interpret per the
precedence chain in §"Skip control" below.

`--help` / `-h` is honored at the CLI level via the
`HelpRequested` supervisor path; help text goes to stdout and
exit code is `0` (NOT an error).

## Steps

### Static phase

1. **Invoke the doctor CLI.** Run the doctor CLI named in
   config with `[--project-root <path>]`. Capture stdout (the
   findings JSON) and the exit code.

2. **Parse findings.** Inspect the stdout JSON: a
   `{"findings": [...]}` object where each
   finding carries `check_id`, `status`, `message`, optional
   `path`, optional `line`, and `spec_root`.

3. **Surface findings.** Group findings by `spec_root` and
   present them to the user:

   - "main" tree findings first.
   - Each sub-spec tree's findings under its own heading
     (e.g., "livespec sub-spec", "minimal sub-spec").
   - Highlight any `fail` status entries; describe the
     corrective action implied by the message.

4. **Bootstrap-lenience handling (v014 N3).** When
   `livespec_jsonc_valid` returns `skipped` (because
   `.livespec.jsonc` is absent), narrate it as "the project
   has no `.livespec.jsonc` — defaults apply" rather than
   surfacing as a problem. Same treatment applies to
   `template_exists` when `template.json` is absent.

If the static phase emitted any `fail` findings (the CLI
exited `3`), STOP HERE — the LLM-driven phase MUST NOT run
when the static phase failed. Surface the failures and
proceed to §"Failure handling".

### LLM-driven objective phase

5. **Skip control.** Resolve the objective-checks skip
   decision per the precedence chain at §"Skip control".
   When the resolved skip is `true`, narrate per the rule
   there and SKIP to Step 8 (subjective phase). Otherwise
   proceed.

6. **Skill-baked objective checks.** Run the following
   checks against every spec tree, surfacing each finding
   as it arises (per):

   - Internal contradiction detection (section A says X,
     section B says not-X).
   - Undefined term detection (a requirement references a
     term not defined anywhere in the spec).
   - Dangling / unresolvable references that escaped the
     `anchor-reference-resolution` static check (e.g.,
     case-variant spellings, alias forms).
   - **Open spec-PR status** (skill-baked, GitHub-hosted
     projects only). Surfaces findings for open `spec/*`
     PRs whose state warrants attention per
     `doctor-llm-objective-checks.md` §"Open spec-PR
     status".
   - **Since-version delta review** (skill-baked, only when
     a prior `vNNN` exists). Reasons ONLY about the regions
     of each spec tree that CHANGED since the immediately-
     prior history snapshot, surfacing new behavior with no
     clause/scenario, clauses in the wrong functional /
     non-functional bucket, and (in multi-repo projects)
     realization mechanism that belongs in the
     orchestrator's own spec, per
     `doctor-llm-objective-checks.md` §"Since-version delta
     review". This check consumes the `<prior-vN>` diff
     threaded in sub-step 6a below.

   For each finding, capture: `check_id` (a stable
   identifier matching the check's name), `spec_root`
   (which tree surfaced it), `path` (file containing the
   issue when applicable), `message` (1-2 sentence
   description), and `proposed_change_hint` (the suggested
   propose-change body, ready to thread into Step 10).

   6a. **Thread the since-version diff.** For each spec
   tree, resolve `<prior-vN>` the SAME way the revise prose
   does (`prose/revise.md` Step 13(d), "Compute
   `<prior-vN>`"): read the `vNNN` directory names under
   `<spec-root>/history/`, identify the most-recently-cut
   `v<N>`, and take `<prior-vN>` as the version immediately
   preceding it — the highest `vNNN` BEFORE `v<N>`. When
   only `v001` exists (no prior snapshot), the since-version
   delta dimension is a no-op for that tree; narrate the
   no-op as a structured `info`-level line and thread no
   diff. Otherwise compute the live-vs-prior diff: each
   `<spec-root>/history/<prior-vN>/` snapshot is a full copy
   of the template-declared spec files, so the diff is a
   per-file comparison of each live spec file against its
   `<prior-vN>` counterpart (the LLM-driven phase is
   permitted to read files and run tooling per the
   LLM-phase contract; the static phase remains
   network-free). Make the resolved `<prior-vN>` and the
   computed diff available to the since-version delta check
   above and to the template-extension prompt invoked in
   Step 7 — it reasons over the changed regions only.

7. **Template-extension objective checks.** Read the
   active template's `template.json`:

   - Resolve the template path by running the
     template-resolution CLI (core reference
     `bin/resolve_template.py`) with `--template <name>`,
     where `<name>` is the value of `.livespec.jsonc`'s
     `template` field (or the per-tree `template_name`
     when iterating sub-specs).
   - Read `<resolved-template>/template.json`.
   - If `doctor_llm_objective_checks_prompt` is non-null,
     resolve `<resolved-template>/<that-path>` and read
     the prompt file. Execute the template-defined checks
     in this same LLM turn, surfacing each finding under
     the same shape as Step 6. The template owns the
     check criteria entirely; any template-internal
     reference files are read by the prompt itself, not
     by this prose.
   - When `doctor_llm_objective_checks_prompt` is null or
     absent, no template-extension objective checks run.

### LLM-driven subjective phase

8. **Skip control.** Resolve the subjective-checks skip
   decision per the precedence chain at §"Skip control".
   When the resolved skip is `true`, narrate per the rule
   there and SKIP to Step 10. Otherwise proceed.

9. **Skill-baked subjective checks.** Run the following
   against every spec tree (per):

   - Spec↔implementation drift (compare the spec's stated
     contracts and constraints to the surrounding repo's
     source code; surface meaningful divergences).
   - Prose quality and structural suggestions
     (paragraphs that should be split, headings that
     should be merged or renamed, sentences whose BCP14
     keyword is missing or weak).

   Surface each finding with the same shape as Step 6.

10. **Template-extension subjective checks.** Same
    mechanism as Step 7, using the
    `doctor_llm_subjective_checks_prompt` field. For the
    built-in `livespec` template this prompt contains
    NLSpec-conformance evaluation (economy, conceptual
    fidelity, spec readability) and template-compliance
    semantic judgments — the prompt Reads
    `<resolved-template>/livespec-nlspec-spec.md`
    template-internally for the canonical NLSpec
    discipline.

### Per-finding user dialogue

Per `contracts.md` §"Doctor per-finding disposition
dialogue", this dialogue MUST run for EVERY non-`pass`
finding surfaced in a single invocation, whichever phase
produced it: a static-phase `fail` or `warn`, or any of the
four LLM-driven phase categories (Steps 6, 7, 9, 10).
Findings with status `pass` and `skipped` are NOT
dispositioned — they remain narrated in Step 3 only. The
dialogue MUST run BEFORE the Driver binding aborts on a
static-phase `fail` (the wrapper's Exit 3): "abort" narrows
to "do not run further LLM-driven check generation", not
"stop interacting with the user" — disposition of
already-surfaced findings is not check generation, so the
no-LLM-after-`fail` safety contract is preserved. The
dialogue MUST also run for static-phase `warn` findings
(whose status does NOT lift the wrapper to Exit 3).

11. For every non-`pass` finding accumulated across the
    static phase and Steps 6, 7, 9, 10 — in `spec_root`-grouped
    order matching how the static-phase findings were
    surfaced — present the user with:

    - The finding's `check_id`, `spec_root`, optional
      `path`, and `message`.
    - The `proposed_change_hint` rendered as the body the
      `critique` operation would receive.
    - A disposition menu of AT MINIMUM these five options,
      in this canonical order:

      1. **fix-now** — apply the corrective action implied
         by the finding's `message`. OPTIONAL per finding:
         offer it ONLY when that action is mechanically
         describable from `message` (text edits, `mkdir`,
         single-shell-command cleanups); when it is not,
         this option MUST NOT be offered for that finding
         (the menu surfaces the remaining four).
      2. **capture-as-work-item** — route the finding to the
         active orchestrator's work-item machinery via the
         interactive front-end the orchestrator ships (the
         interactive consent dialogue is orchestrator-owned,
         not part of core's contract). The handed-off finding embeds
         the `check_id`, `spec_root`, optional `path`, and
         `message` so the trail back to the originating
         doctor finding is preserved. This option MUST ALWAYS
         be offered for every non-`pass` finding.
      3. **propose-change** — invoke the `critique` operation
         against the appropriate `--spec-target` (the tree
         whose `spec_root` surfaced the finding) and thread
         the `proposed_change_hint` as the user-described
         change. This option MUST ALWAYS be offered.
      4. **defer** — record the finding in this session's
         narration; take no durable action. It MAY surface
         again on the next invocation.
      5. **dismiss** — the user judges the finding does not
         apply; take no durable action. No cross-invocation
         persistence of dismissals in v1: a dismissed finding
         MAY surface again on the next invocation, where the
         user dismisses again or chooses a different
         disposition.

## Skip control

Each LLM-layer flag pair resolves to a `skip` boolean per the
precedence chain:

1. **CLI flag.** If `--skip-<phase>-checks` is on the
   invocation: `skip = true`. If `--run-<phase>-checks` is on:
   `skip = false` (overrides config).
2. **Config key.** Otherwise read
   `post_step_skip_doctor_llm_objective_checks` (or its
   subjective sibling) from `.livespec.jsonc`. Default is
   `false`.
3. **Both flags present.** Argparse-style usage error: surface
   and abort the LLM-driven phase. Do NOT proceed.

**Narration rule** ( lines
3006-3013): this prose MUST surface a warning via LLM narration
whenever an LLM-driven phase is SILENTLY skipped (the skip
came from the config key with no CLI flag passed). When a
`--skip-*` CLI flag is passed explicitly, the skip is
self-evident to the user and no narration fires. When a
`--run-*` CLI flag overrides a config default of `true`, no
narration fires either — the explicit flag makes the override
self-evident.

Direct doctor invocations honor the same flags as
post-step invocations from `seed` / `propose-change` /
`critique` / `revise`; this prose mirrors the same
precedence chain in either case.

## Post-CLI

When the CLI-backed operations (`seed`, `propose-change`,
`critique`, `revise`) call `doctor` as a post-step, the static
phase has ALREADY run inside the CLI (the parent operation's
CLI invocation includes static-doctor in its lifecycle).
The calling operation's prose passes control here for the
LLM-driven phase only — Steps 1-4 are skipped, the LLM
proceeds directly from Step 5 (or Step 8 when the objective
phase is skipped). The calling operation's narration of the
static findings already surfaced in the user's reading buffer;
this prose MUST NOT re-emit them.

## Failure handling

CLI exit-code-to-narration mapping (Steps 1-4 only — the
LLM-driven phase has no exit codes):

- Exit `0` → all static findings are `pass` or `skipped` (no
  `fail`). Surface the findings and proceed to Step 5.
- Exit `1` → internal bug; surface stderr (including the
  structured-error JSON line and any traceback) and abort.
  LLM-driven phase MUST NOT run.
- Exit `2` → usage error; restate the invocation and abort.
- Exit `3` → at least one fail Finding. Surface ALL findings
  grouped by `spec_root`; emphasize the failures; describe the
  corrective actions implied by each message; abort.
  LLM-driven phase MUST NOT run.
- Exit `127` → too-old Python or missing tool; surface the
  install instruction and abort.

When this prose is run as post-step delegation from another
operation (Steps 5-11), the calling operation has already
classified the CLI's exit code; the LLM-driven phase only runs
when the parent CLI exited `0`. Failures during the LLM-driven
phase itself (e.g., the template-resolution CLI failing during
Step 7's template resolution) are surfaced as narrative
warnings — they do NOT short-circuit later subjective-phase
checks because the two phases are independent surfaces.
