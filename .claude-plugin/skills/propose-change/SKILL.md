---
name: propose-change
description: File a proposed change against an existing livespec specification, landing it under <spec-root>/proposed_changes/<topic>.md. Invoked by /livespec:propose-change, "propose a change to the spec", or when the user wants to record a spec amendment that the next /livespec:revise pass will accept or reject.
allowed-tools: Bash, Read, Write
---

# propose-change

File a structured proposed-change file under
`<spec-target>/proposed_changes/<canonical-topic>.md` based on a
user-provided intent. The wrapper canonicalizes the inbound topic
hint, validates the LLM-emitted findings JSON internally, and
writes one `## Proposal: <name>` section per finding into the
resulting file. Pre-step doctor static runs before the wrapper;
post-step doctor static runs after the wrapper exits, followed by
the LLM-driven post-step phase.

## When to invoke

- The user types `/livespec:propose-change`, says "propose a
  change", "file a propose-change", "amend the spec", or
  otherwise asks to record a spec amendment against an existing
  seeded spec tree.
- The repo has a valid `.livespec.jsonc` and a populated spec
  tree (the wrapper's pre-step doctor static enforces this and
  exits 3 if not).
- If the user asks to *process* pending proposed changes rather
  than file a new one, route to `/livespec:revise` instead —
  propose-change only authors a proposed-change file; it does
  not accept or reject anything. If the user asks to *surface
  ambiguities or contradictions* in the spec rather than propose
  new behavior, route to `/livespec:critique` instead — critique
  delegates back into propose-change with a `-critique` reserve-
  suffix and a different template prompt.

## Inputs

The wrapper `bin/propose_change.py` accepts the following flags
in v1:

- `<topic>` (positional, required). User-facing topic hint. The
  wrapper treats the inbound value as a hint, not yet the
  canonical artifact identifier, and canonicalizes it per: lowercase →
  replace every run of non-`[a-z0-9]` characters with a single
  hyphen → strip leading and trailing hyphens → truncate to
  64 characters. If the result is empty, the wrapper exits 2
  with `UsageError`. The canonicalized form is used uniformly
  for the output filename, the proposed-change front-matter
  `topic` field, and the collision-disambiguation namespace.
- `--findings-json <path>` (required). Absolute or
  project-root-relative path to a JSON payload conforming to
  `proposal_findings.schema.json` (under
  `.claude-plugin/scripts/livespec/schemas/`). The wrapper
  validates the payload internally; the SKILL.md prose does NOT
  invoke a separate validator. Each finding produces one
  `## Proposal: <name>` section in the output file. Field
  mapping is one-to-one:
  `name` → `## Proposal: <name>` heading; `target_spec_files`
  (array of strings) → `### Target specification files` (one
  path per line); `summary` → `### Summary`; `motivation` →
  `### Motivation`; `proposed_changes` (prose or fenced unified
  diff) → `### Proposed Changes`. The payload MAY include a
  top-level `author` field for the LLM's self-declaration; the
  wrapper resolves it per the four-step precedence below.
- `--author <id>` (optional). Uniform `--author` flag with
  identical four-step precedence across all three LLM-driven
  wrappers (propose-change, critique, revise) per:
  1. CLI `--author <id>` if set and non-empty.
  2. Env var `LIVESPEC_AUTHOR_LLM` if set and non-empty.
  3. Payload file-level `author` field if present and
     non-empty.
  4. Literal `"unknown-llm"` fallback.
  The resolved author populates the front-matter `author`
  field on the resulting proposed-change file. When fallback
  (4) is reached, the SKILL.md prose MUST surface a warning to
  the user ("Running with unknown LLM identifier; set
  `LIVESPEC_AUTHOR_LLM` or pass `--author <id>` for an
  audit-trail-clean attribution."). Human authors and LLMs
  SHOULD NOT use the `livespec-` prefix; this is a convention,
  not a mechanical reservation, and no schema or wrapper
  rejects user-supplied `livespec-` values.
- `--reserve-suffix <text>` (optional). Caller-supplied suffix
  preserved intact at the end of the canonicalized topic, even
  when the inbound hint already ends in that suffix
  (pre-attached case) or when truncation would otherwise clip
  it. Per, the resulting canonical topic is at most 64
  characters AND preserves the suffix at the end. User-facing
  use is rare; the primary consumer is `critique`'s internal
  delegation, which passes `--reserve-suffix=-critique` so the
  resulting filename lands as
  `<canonical-author>-critique.md` regardless of author-stem
  length. The same empty-after-canonicalization `UsageError`
  (exit 2) applies to the final composed result.
- `--spec-target <path>` (optional). Defaults to the main
  spec root (resolved via `.livespec.jsonc` upward walk).
  Per (v018 Q1),
  may point at a sub-spec tree under
  `<main-spec-root>/templates/<name>/` to route the proposal
  there. The wrapper validates the target structure before
  writing; if validation fails, exits 3 with
  `PreconditionError` naming the target path and the missing
  structural requirement.
- `--project-root <path>` (optional; defaults to `Path.cwd()`).
  Anchors `<spec-root>/` resolution and the upward walk for
  `.livespec.jsonc`. Uniform across every wrapper per.
- `--skip-pre-check` (optional). Skips the pre-step doctor
  static phase before the wrapper writes. Mutually exclusive
  with `--run-pre-check`.
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

When the user supplies either flag in the same invocation, the
SKILL.md prose forwards the choice to the post-step LLM-driven
phase and never to `bin/propose_change.py`. Both-flags-in-the-
same-pair is a usage error; surface and abort the LLM-driven
phase. See `doctor/SKILL.md` for the full LLM-driven-phase
contract.

`--help` / `-h` is honored at the wrapper level via the
`HelpRequested` supervisor path; help text goes to stdout and
exit code is `0` (NOT an error).

## Steps

1. **Resolve the active template.** Invoke
   `bin/resolve_template.py` (no `--template` flag — uses the
   standard `.livespec.jsonc` upward walk) via the Bash tool.
   Capture the resolved template directory path from stdout.

2. **Read the propose-change prompt.** Use the Read tool on
   `<resolved-path>/prompts/propose-change.md`. Use its
   contents as the template prompt for finding generation.
   This is the two-step template-prompt dispatch from
   (Bash for resolution, then Read for the prompt file) and
   works uniformly for built-in and custom templates.

3. **Capture user intent.** Ask the user: "What change do you
   want to propose? Describe the intent — what should the spec
   say differently, and why." Capture free-text intent. The
   propose-change prompt consumes this alongside the current
   spec content.

4. **Capture topic hint.** Ask the user: "What short topic
   should this proposal use? (a few words; the wrapper will
   canonicalize to lowercase-kebab-case and truncate to 64
   characters)." Capture free-text. Do NOT pre-canonicalize on
   the SKILL.md side — single-canonicalization invariant
  
   requires every `topic` derivation to route through the
   wrapper's shared canonicalization. Pass the hint verbatim as
   the `<topic>` positional argument.

5. **Generate findings JSON.** Run the propose-change prompt
   against the user-described intent. The prompt MUST emit
   JSON conforming to `proposal_findings.schema.json`:
   top-level `findings[]` array, each entry carrying `name`,
   `target_spec_files`, `summary`, `motivation`, and
   `proposed_changes`. The prompt MAY include a top-level
   `author` field for the LLM's self-declaration; the wrapper
   resolves it per the four-step precedence. Each finding
   becomes one `## Proposal` section. A proposal MUST be
   explicit (no open questions, no "we should decide X
   later"); resolve sub-decisions before filing or surface
   them via `/livespec:critique` instead.

6. **Write payload to temp file.** Use the Write tool to write
   the generated JSON to a temp file. Pass the tempfile path
   as `--findings-json` to the wrapper.

7. **Resolve effective flags.** Determine whether the user
   passed `--skip-pre-check` / `--run-pre-check` and the two
   LLM-layer flag pairs. Compose the wrapper argv with the
   pre-step pair when set; reserve the LLM-layer pairs for
   the post-step LLM-driven phase. If the user passed neither
   pre-step flag and `.livespec.jsonc`'s
   `pre_step_skip_static_checks` is `true`, the pre-step will
   be silently skipped — record this for the narration step
   below.

8. **Invoke the wrapper.** Run
   `bin/propose_change.py <topic> --findings-json <tempfile> [flags]`
   via the Bash tool with explicit argv (forwarding
   `--author`, `--reserve-suffix`, `--spec-target`,
   `--project-root`, `--skip-pre-check` / `--run-pre-check`
   as applicable). Capture exit code. The wrapper canonicalizes
   the topic, validates the payload internally, runs pre-step
   doctor static (unless skipped), writes the file, and runs
   post-step doctor static. The resulting file is
   `<spec-target>/proposed_changes/<canonical-topic>.md`
   (or `<canonical-topic>-N.md` on collision; see Post-wrapper).

9. **Narrate skipped pre-step (when silent).** If the
   effective resolution was `skip = true` AND the user did
   NOT explicitly pass `--skip-pre-check` (i.e., the skip came
   from `pre_step_skip_static_checks: true` in config),
   surface a warning to the user: "Pre-step doctor static was
   skipped because `pre_step_skip_static_checks` is set to
   `true` in `.livespec.jsonc`. Run with `--run-pre-check` to
   force the pre-step." When the user passed `--skip-pre-check`
   explicitly, no narration is required (the skip is
   intentional and acknowledged). When the user passed
   `--run-pre-check`, the pre-step ran; no narration needed.

10. **Retry-on-exit-4.** On wrapper exit code `4` (schema
    validation failed; the LLM-emitted JSON did not conform
    to `proposal_findings.schema.json`), treat the return code
    as a retryable malformed-payload signal. Inspect the
    structured error context on stderr, re-invoke the
    propose-change template prompt with that context, and
    re-assemble corrected JSON. The exact retry count is
    intentionally unspecified in v1; orchestration owns the
    retry policy. Exit `3` is NOT retryable (precondition /
    doctor-static failure — surface findings and abort).

11. **Narrate fallback-author warning.** If the resolved
    author was the literal `"unknown-llm"` (i.e., none of
    `--author` / `LIVESPEC_AUTHOR_LLM` / payload `author`
    were set), surface the warning from the Inputs section to
    the user. The wrapper does not gate on this; the warning
    is purely audit-trail hygiene.

## Post-wrapper

On exit 0, the wrapper has:

- Canonicalized the inbound `<topic>` hint per
  SPECIFICATION/spec.md §"Proposed-change and revision file
  formats" (with reserve-suffix preservation when
  `--reserve-suffix` was supplied).
- Validated the `--findings-json` payload against
  `proposal_findings.schema.json`.
- Resolved the author via the four-step precedence.
- Run pre-step doctor static (unless skipped).
- Written
  `<spec-target>/proposed_changes/<canonical-topic>.md`
  containing one `## Proposal: <name>` section per finding,
  with file-level YAML front-matter (`topic`, `author`,
  `created_at`). On collision (a file with the same canonical topic
  already exists), the wrapper auto-disambiguates with a
  hyphen-separated monotonic integer suffix starting at `2`
  (`<canonical-topic>-2.md`, `<canonical-topic>-3.md`, ...)
  per v014 N6; no user prompt. The front-matter `topic` field
  carries ONLY the canonical topic WITHOUT the `-N` suffix;
  the `-N` suffix is filename-level disambiguation only.
- Run post-step doctor static.

The LLM-driven post-step phase then runs per
`doctor/SKILL.md`, honoring the two LLM-layer flag pairs from
Inputs. Propose-change does NOT run revise; the user reviews
the resulting proposed-change file and runs `/livespec:revise`
separately to process it.

**Seed-recovery exit-3 narration (v017 Q4).** When invoked
during the seed post-step-failure recovery flow (heuristic: no
`vNNN` revision beyond `v001` exists AND the user passed
`--skip-pre-check`), and the wrapper exits `3` from the
post-step doctor static, the SKILL.md prose MUST narrate the
exit-3 path distinctly: "this exit 3 is expected during seed
recovery; the proposed-change file IS on disk; commit the
partial state and run `/livespec:revise --skip-pre-check` to
cut `v002` with the corrections." Otherwise, the generic
exit-3 narration in `## Failure handling` applies and the user
is expected to recognize the recovery path from seed's earlier
narration.

## Failure handling

Wrapper exit-code-to-narration mapping:

- Exit `0` → success. The proposed-change file exists at the
  path described in `## Post-wrapper`. Proceed to the
  post-step LLM-driven phase per `doctor/SKILL.md`. This also
  covers intentional `--help` output (user asked for help, not
  an error).
- Exit `1` → internal bug; surface the error from stderr
  (including any traceback) and abort. Do NOT retry.
- Exit `2` → usage error (e.g., empty topic after
  canonicalization; both `--skip-pre-check` and
  `--run-pre-check` supplied; missing `--findings-json`;
  unknown flag). Restate the expected invocation shape per
  `## Inputs` above and abort.
- Exit `3` → precondition / doctor-static failure (pre-step
  fail, `--spec-target` validation fail, or post-step fail).
  Surface the findings from stderr structlog line(s) and
  direct the user to the corrective action each finding
  describes. NOT retryable via prompt re-run; the LLM cannot
  fix a precondition by re-emitting the JSON. See the
  seed-recovery narration above for the special-case
  expected-exit-3 path during seed recovery.
- Exit `4` → schema-validation failure on the LLM-emitted
  JSON payload; **retryable** per Step 10. Inspect the error
  context, re-invoke the propose-change prompt, and re-assemble
  corrected JSON.
- Exit `127` → too-old Python or missing tool; surface the
  install instruction from stderr and abort.
