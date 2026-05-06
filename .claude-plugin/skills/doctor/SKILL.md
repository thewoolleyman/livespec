---
name: doctor
description: Run the doctor checks against a livespec spec tree — the static phase (structural failures) plus the LLM-driven objective and subjective phases — surfacing findings as JSON or as a per-finding user dialogue. Invoked by /livespec:doctor, "run livespec doctor", or "check the spec for invariants", and as the post-step LLM-driven phase from every wrapper-having sub-command.
allowed-tools: Bash, Read
---

# doctor

`doctor` runs in two layers lines
2546-2606:

- **Static phase** is implemented in Python at
  `.claude-plugin/scripts/livespec/doctor/run_static.py` and
  invoked via `bin/doctor_static.py`. The orchestrator
  enumerates every spec tree (main spec + each sub-spec under
  `templates/<name>/`), runs the registered checks per the
  per-tree applicability table, and emits
  `{"findings": [...]}` JSON to stdout. Each finding carries
  `check_id`, `status` (`pass`/`fail`/`skipped`), `message`,
  optional `path`, optional `line`, and `spec_root` (the
  per-tree origin marker).
- **LLM-driven phase** is skill behavior — there is no Python
  entry point because Python doesn't invoke the LLM. The
  LLM-driven phase has two categories (objective + subjective)
  and is template-extensible via the active template's
  `template.json` declarations
  (`doctor_llm_objective_checks_prompt`,
  `doctor_llm_subjective_checks_prompt`).

There is no `bin/doctor.py` wrapper; the user invokes `/livespec:doctor` (or
expresses intent in dialogue) and the LLM follows this skill's
prose end-to-end.

## When to invoke

- **Direct user request.** The user types `/livespec:doctor`,
  says "run doctor", "check the spec", or asks to verify spec
  invariants. The LLM follows this skill from the top:
  Steps 1-4 (static phase) → Steps 5-9 (LLM-driven phase) →
  Step 10 (per-finding dialogue).
- **Post-step from another wrapper-having sub-command.** The
  `seed`, `propose-change`, `critique`, and `revise` wrappers
  internally run the static phase as their post-step (the
  Python wrapper invokes `run_static.run` in-process; the
  static findings are emitted by the calling wrapper, not by
  `bin/doctor_static.py`). When the wrapper exits `0`, the
  calling skill's prose delegates to **this** SKILL.md for the
  LLM-driven phase only (Steps 5-10; Steps 1-4 are skipped).
  When the wrapper exits non-zero (1 or 3), the LLM-driven
  phase MUST NOT run; the calling skill surfaces the failure
  to the user and aborts.

## Inputs

`bin/doctor_static.py` accepts:

- `--project-root <path>` (optional; defaults to cwd).

The wrapper has no JSON input; it reads `.livespec.jsonc` from
disk via the upward walk and discovers sub-spec trees by
listing `<main-spec-root>/templates/<name>/`.

Two LLM-layer flag pairs apply during the LLM-driven phase but
are NEVER passed to the Python wrapper (per PROPOSAL.md
§"Skill-prose-side: LLM-driven post-step"):

- `--skip-doctor-llm-objective-checks` /
  `--run-doctor-llm-objective-checks` (mutually exclusive).
- `--skip-doctor-llm-subjective-checks` /
  `--run-doctor-llm-subjective-checks` (mutually exclusive).

Both-flags-in-the-same-pair is a usage error; surface and
abort the LLM-driven phase. The flags interpret per the
precedence chain in §"Skip control" below.

`--help` / `-h` is honored at the wrapper level via the
`HelpRequested` supervisor path; help text goes to stdout and
exit code is `0` (NOT an error).

## Steps

### Static phase

1. **Invoke the wrapper.** Run
   `bin/doctor_static.py [--project-root <path>]` via Bash.
   Capture stdout (the findings JSON) and exit code.

2. **Parse findings.** Use Read or Bash (`cat`) to inspect the
   stdout JSON: a `{"findings": [...]}` object where each
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

If the static phase emitted any `fail` findings (wrapper
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

   For each finding, capture: `check_id` (a stable
   identifier matching the check's name), `spec_root`
   (which tree surfaced it), `path` (file containing the
   issue when applicable), `message` (1-2 sentence
   description), and `proposed_change_hint` (the suggested
   propose-change body, ready to thread into Step 10).

7. **Template-extension objective checks.** Read the
   active template's `template.json`:

   - Resolve the template path via
     `bin/resolve_template.py --template <name>`, where
     `<name>` is the value of `.livespec.jsonc`'s
     `template` field (or the per-tree `template_name`
     when iterating sub-specs).
   - Read `<resolved-template>/template.json` via the Read
     tool.
   - If `doctor_llm_objective_checks_prompt` is non-null,
     resolve `<resolved-template>/<that-path>` and Read
     the prompt file. Execute the template-defined checks
     in this same LLM turn, surfacing each finding under
     the same shape as Step 6. The template owns the
     check criteria entirely; any template-internal
     reference files are read by the prompt itself, not
     by this skill.
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

11. For every finding accumulated across Steps 6, 7, 9,
    10 — in `spec_root`-grouped order matching how the
    static-phase findings were surfaced — prompt the user
    with:

    - The finding's `check_id`, `spec_root`, optional
      `path`, and `message`.
    - The `proposed_change_hint` rendered as the body the
      `critique` skill would receive.
    - Three options: **accept** (invoke `/livespec:critique`
      with the hint), **defer** (record the finding in this
      session's narration but do nothing), **dismiss** (the
      user judges the finding does not apply).

    Accept invokes `/livespec:critique` against the
    appropriate `--spec-target` (the tree whose `spec_root`
    surfaced the finding) and threads the
    `proposed_change_hint` as the user-described change.

    No cross-invocation persistence of dismissals in v1
   . A
    finding the user dismissed in one run MAY surface again
    in the next run; the user dismisses again or chooses a
    different disposition.

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
3006-3013): the skill MUST surface a warning via LLM narration
whenever an LLM-driven phase is SILENTLY skipped (the skip
came from the config key with no CLI flag passed). When a
`--skip-*` CLI flag is passed explicitly, the skip is
self-evident to the user and no narration fires. When a
`--run-*` CLI flag overrides a config default of `true`, no
narration fires either — the explicit flag makes the override
self-evident.

Direct `livespec doctor` invocations honor the same flags as
post-step invocations from `seed` / `propose-change` /
`critique` / `revise`; the skill prose mirrors the same
precedence chain in either case.

## Post-wrapper

When the wrapper-having sub-commands (`seed`, `propose-change`,
`critique`, `revise`) call `doctor` as a post-step, the static
phase has ALREADY run inside the wrapper (the parent skill's
wrapper invocation includes static-doctor in its lifecycle).
The calling skill's prose passes control here for the
LLM-driven phase only — Steps 1-4 are skipped, the LLM
proceeds directly from Step 5 (or Step 8 when the objective
phase is skipped). The calling skill's narration of the static
findings already surfaced in the user's reading buffer; this
skill MUST NOT re-emit them.

## Failure handling

Wrapper exit-code-to-narration mapping (Steps 1-4 only — the
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

When this skill is run as post-step delegation from another
skill (Steps 5-11), the calling skill has already classified
the wrapper's exit code; the LLM-driven phase only runs when
the parent wrapper exited `0`. Failures during the LLM-driven
phase itself (e.g., `bin/resolve_template.py` failing during
Step 7's template resolution) are surfaced as narrative
warnings — they do NOT short-circuit later subjective-phase
checks because the two phases are independent surfaces.
