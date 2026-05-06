---
name: critique
description: Critique an existing livespec specification or a pending proposed change, surfacing ambiguities, contradictions, and missing rules as findings the user can act on. Invoked by /livespec:critique, "critique the livespec spec", or "find issues in the spec".
allowed-tools: Bash, Read, Write
---

# critique

File a critique-style proposed-change against an existing
spec tree. Internally delegates to `propose-change` with the
reserve-suffix `"-critique"`, so the resulting file lands at
`<spec-target>/proposed_changes/<canonical-author>-critique.md`
(or `<canonical-author>-critique-<n>.md` on collision). Pre-step
doctor static runs before critique; post-step doctor static
runs after the wrapper exits, followed by the LLM-driven
post-step phase.

## When to invoke

- The user types `/livespec:critique`, says "critique the
  livespec spec", "find issues in the spec", "surface
  ambiguities", or otherwise asks to file a critique against
  the current spec or a pending proposed-change.
- The repo has a valid `.livespec.jsonc` and a populated spec
  tree (the wrapper's pre-step doctor static enforces this and
  exits 3 if not).
- If the user asks to *process* findings rather than surface
  them, route to `/livespec:revise` instead — critique only
  emits findings as a proposed-change file; it does not
  accept or reject them.

## Inputs

The wrapper `bin/critique.py` accepts the following flags in
v1:

- `--findings-json <path>` (required). Absolute or
  project-root-relative path to a JSON payload conforming to
  `proposal_findings.schema.json`
  (under `.claude-plugin/scripts/livespec/schemas/`). The wrapper
  validates the payload internally; the SKILL.md prose does
  NOT invoke a separate validator. The schema shape is
  identical to propose-change's input — same `findings[]`
  array with `name`, `target_spec_files`, `summary`,
  `motivation`, and `proposed_changes` per finding. The
  semantic difference is content: critique findings describe
  ambiguities, contradictions, or missing rules in the
  current spec, not new behavior.
- `--author <id>` (optional). Uniform `--author` flag with
  identical four-step precedence across all three LLM-driven
  wrappers (propose-change, critique, revise) per:
  1. CLI `--author <id>` if set and non-empty.
  2. Env var `LIVESPEC_AUTHOR_LLM` if set and non-empty.
  3. Payload file-level `author` field if present and
     non-empty.
  4. Literal `"unknown-llm"` fallback.
  The resolved author is used both as the front-matter
  `author` field and as the un-slugged topic-hint passed to
  propose-change's internal canonicalization (paired with
  `reserve-suffix="-critique"`). When fallback (4) is reached,
  the SKILL.md prose MUST surface a warning to the user
  ("Running with unknown LLM identifier; set
  `LIVESPEC_AUTHOR_LLM` or pass `--author <id>` for an
  audit-trail-clean attribution.").
- `--spec-target <path>` (optional). Defaults to the main
  spec root (resolved via `.livespec.jsonc` upward walk).
  Per (v018 Q1),
  may point at a sub-spec tree under
  `<main-spec-root>/templates/<name>/` to route the critique
  there. The wrapper validates the target structure before
  delegating; if validation fails, exits 3 with
  `PreconditionError`. Critique forwards `--spec-target`
  verbatim to its internal propose-change delegation.
- `--project-root <path>` (optional; defaults to `Path.cwd()`).
  Anchors `<spec-root>/` resolution and the upward walk for
  `.livespec.jsonc`. Uniform across every wrapper per.
- `--skip-pre-check` (optional). Skips the pre-step doctor
  static phase before critique runs. Mutually exclusive with
  `--run-pre-check`.
- `--run-pre-check` (optional). Forces the pre-step doctor
  static phase to run even if `pre_step_skip_static_checks`
  is `true` in `.livespec.jsonc`. Mutually exclusive with
  `--skip-pre-check`.

Effective skip resolution for the pre-step (per
SPECIFICATION/spec.md §"Sub-command lifecycle"):

1. `--skip-pre-check` on the CLI → skip = true.
2. `--run-pre-check` on the CLI → skip = false (overrides
   config).
3. Neither flag → use config key
   `pre_step_skip_static_checks` (default `false`).
4. Both flags set → argparse usage error (exit 2).

Two LLM-layer flag pairs ALSO apply during the post-step
LLM-driven phase but are NEVER passed to the Python wrapper
(per):

- `--skip-doctor-llm-objective-checks` /
  `--run-doctor-llm-objective-checks` (mutually exclusive).
- `--skip-doctor-llm-subjective-checks` /
  `--run-doctor-llm-subjective-checks` (mutually exclusive).

When the user supplies either flag in the same invocation,
the SKILL.md prose forwards the choice to the post-step
LLM-driven phase and never to `bin/critique.py`. Both-flags-
in-the-same-pair is a usage error; surface and abort the
LLM-driven phase. See `doctor/SKILL.md` for the full
LLM-driven-phase contract.

`--help` / `-h` is honored at the wrapper level via the
`HelpRequested` supervisor path; help text goes to stdout
and exit code is `0` (NOT an error).

## Steps

1. **Resolve the active template.** Invoke
   `bin/resolve_template.py` (no `--template` flag — uses
   the standard `.livespec.jsonc` upward walk) via the Bash
   tool. Capture the resolved template directory path from
   stdout.

2. **Read the critique prompt.** Use the Read tool on
   `<resolved-path>/prompts/critique.md`. Use its contents
   as the template prompt for finding generation. This is
   the two-step template-prompt dispatch (Bash for resolution,
   then Read for the prompt file) and works uniformly for
   built-in and custom templates.

3. **Capture critique target.** Ask the user: "What do you
   want critiqued? Describe the spec area, contract, or
   pending proposed-change you want to surface findings
   against." Capture free-text intent. The critique prompt
   consumes this alongside the current spec content.

4. **Generate findings JSON.** Run the critique prompt
   against the user-described target. The prompt MUST emit
   JSON conforming to `proposal_findings.schema.json`:
   top-level `findings[]` array, each entry carrying
   `name`, `target_spec_files`, `summary`, `motivation`,
   and `proposed_changes`. Findings should describe
   ambiguities / contradictions / missing rules; the
   `proposed_changes` field still describes the corrective
   action (typically prose, occasionally a unified-diff
   sketch). The prompt MAY include a top-level `author`
   field for the LLM's self-declaration; the wrapper
   resolves it per the four-step precedence.

5. **Write payload to temp file.** Use the Write tool to
   write the generated JSON to a temp file. Pass the
   tempfile path as `--findings-json` to the wrapper.

6. **Resolve effective flags.** Determine whether the user
   passed `--skip-pre-check` / `--run-pre-check` and the two
   LLM-layer flag pairs. Compose the wrapper argv with the
   pre-step pair when set; reserve the LLM-layer pairs for
   the post-step LLM-driven phase. If the user passed
   neither pre-step flag and `.livespec.jsonc`'s
   `pre_step_skip_static_checks` is `true`, the pre-step
   will be silently skipped — record this for the
   narration step below.

7. **Invoke the wrapper.** Run
   `bin/critique.py --findings-json <tempfile> [flags]`
   via the Bash tool with explicit argv (forwarding
   `--author`, `--spec-target`, `--project-root`,
   `--skip-pre-check` / `--run-pre-check` as applicable).
   Capture exit code. The wrapper internally delegates to
   `propose_change.run()` with the un-slugged resolved-author
   stem as the topic hint AND `--reserve-suffix=-critique`,
   so propose-change's v016 P3 / v017 Q1 reserve-suffix
   canonicalization composes the two and preserves the
   `-critique` suffix at the 64-char filename cap. The
   resulting file is
   `<spec-target>/proposed_changes/<canonical-author>-critique.md`
   (or `<canonical-author>-critique-<n>.md` on collision).

8. **Narrate skipped pre-step (when silent).** If the
   effective resolution was `skip = true` AND the user did
   NOT explicitly pass `--skip-pre-check` (i.e., the skip
   came from `pre_step_skip_static_checks: true` in config),
   surface a warning to the user: "Pre-step doctor static
   was skipped because `pre_step_skip_static_checks` is set
   to `true` in `.livespec.jsonc`. Run with
   `--run-pre-check` to force the pre-step." When the user
   passed `--skip-pre-check` explicitly, no narration is
   required (the skip is intentional and acknowledged).
   When the user passed `--run-pre-check`, the pre-step
   ran; no narration needed.

9. **Retry-on-exit-4.** On wrapper exit code `4` (schema
   validation failed; the LLM-emitted JSON did not conform
   to `proposal_findings.schema.json`), treat the return code
   as a retryable malformed-payload signal. Inspect the
   structured error context on stderr, re-invoke the
   critique template prompt with that context, and
   re-assemble corrected JSON. The exact retry count is
   intentionally unspecified in v1; orchestration owns the
   retry policy. Exit `3` is NOT retryable (precondition /
   doctor-static failure — surface findings and abort).

10. **Narrate fallback-author warning.** If the resolved
    author was the literal `"unknown-llm"` (i.e., none of
    `--author` / `LIVESPEC_AUTHOR_LLM` / payload `author`
    were set), surface the warning from the Inputs section
    to the user. The wrapper does not gate on this; the
    warning is purely audit-trail hygiene.

## Post-wrapper

On exit 0, the wrapper has:

- Validated the `--findings-json` payload against
  `proposal_findings.schema.json`.
- Resolved the author via the four-step precedence.
- Delegated to `propose_change.run()` with topic hint
  `<resolved-author>` and `reserve-suffix="-critique"`. The
  internal delegation skips the inner pre/post doctor cycle
  since critique's outer wrapper ROP chain already covers
  the whole operation.
- Written
  `<spec-target>/proposed_changes/<canonical-author>-critique.md`
  (or `<canonical-author>-critique-<n>.md` if a file with
  the same canonicalized topic already exists; collision
  disambiguation uses the v014 N6 monotonic-counter-from-`2`
  convention with no user prompt).

The post-step doctor static runs over every spec tree per
the standard wrapper-side lifecycle. Then the LLM-driven
post-step phase runs per `doctor/SKILL.md`, honoring the
two LLM-layer flag pairs from Inputs. Critique does NOT
run revise; the user reviews the resulting proposed-change
file and runs `/livespec:revise` separately to process it.

## Failure handling

Wrapper exit-code-to-narration mapping:

- Exit `0` → success. The proposed-change file exists at
  the path described in `## Post-wrapper`. Proceed to the
  post-step LLM-driven phase per `doctor/SKILL.md`. This
  also covers intentional `--help` output (user asked for
  help, not an error).
- Exit `1` → internal bug; surface the error from stderr
  (including any traceback) and abort. Do NOT retry.
- Exit `2` → usage error (e.g., both `--skip-pre-check`
  and `--run-pre-check` supplied; missing `--findings-json`;
  unknown flag). Restate the expected invocation shape per
  `## Inputs` above and abort.
- Exit `3` → precondition / doctor-static failure (pre-step
  fail, `--spec-target` validation fail, or post-step fail).
  Surface the findings from stderr structlog line(s) and
  direct the user to the corrective action each finding
  describes. NOT retryable via prompt re-run; the LLM
  cannot fix a precondition by re-emitting the JSON.
- Exit `4` → schema-validation failure on the LLM-emitted
  JSON payload; **retryable** per Step 9. Inspect the error
  context, re-invoke the critique prompt, and re-assemble
  corrected JSON.
- Exit `127` → too-old Python or missing tool; surface the
  install instruction from stderr and abort.
