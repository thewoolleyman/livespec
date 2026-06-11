# propose-change

Harness-neutral driving prose for the `propose-change` operation, per
`SPECIFICATION/spec.md` §"Contract + reference implementations
architecture": this artifact is the core-owned LLM-facing half of the
operation; the propose-change CLI named in `.livespec.jsonc` (core
reference implementation: `bin/propose_change.py`) is the contract
half. Drivers bind this prose to their runtime; nothing in this file
names any specific agent runtime's tools or command namespace.

File a structured proposed-change file under
`<spec-target>/proposed_changes/<canonical-topic>.md` based on a
user-provided intent. The CLI canonicalizes the inbound topic
hint, validates the LLM-emitted findings JSON internally, and
writes one `## Proposal: <name>` section per finding into the
resulting file. Pre-step doctor static runs before the CLI;
post-step doctor static runs after the CLI exits, followed by
the LLM-driven post-step phase.

## When to run

- The user invokes the propose-change operation, says "propose a
  change", "file a propose-change", "amend the spec", or
  otherwise asks to record a spec amendment against an existing
  seeded spec tree.
- The repo has a valid `.livespec.jsonc` and a populated spec
  tree (the CLI's pre-step doctor static enforces this and
  exits 3 if not).
- If the user asks to *process* pending proposed changes rather
  than file a new one, route to the revise operation instead —
  propose-change only authors a proposed-change file; it does
  not accept or reject anything. If the user asks to *surface
  ambiguities or contradictions* in the spec rather than propose
  new behavior, route to the critique operation instead —
  critique delegates back into propose-change with a `-critique`
  reserve-suffix and a different template prompt.

## Inputs

The propose-change CLI accepts the following flags in v1:

- `<topic>` (positional, required). User-facing topic hint. The
  CLI treats the inbound value as a hint, not yet the
  canonical artifact identifier, and canonicalizes it per: lowercase →
  replace every run of non-`[a-z0-9]` characters with a single
  hyphen → strip leading and trailing hyphens → truncate to
  64 characters. If the result is empty, the CLI exits 2
  with `UsageError`. The canonicalized form is used uniformly
  for the output filename, the proposed-change front-matter
  `topic` field, and the collision-disambiguation namespace.
- `--findings-json <path>` (required). Absolute or
  project-root-relative path to a JSON payload conforming to
  `proposal_findings.schema.json` (shipped in core's
  `livespec/schemas/` package). The CLI validates the payload
  internally; this prose does NOT invoke a separate validator.
  Each finding produces one `## Proposal: <name>` section in the
  output file. Field mapping is one-to-one:
  `name` → `## Proposal: <name>` heading; `target_spec_files`
  (array of strings) → `### Target specification files` (one
  path per line); `summary` → `### Summary`; `motivation` →
  `### Motivation`; `proposed_changes` (prose or fenced unified
  diff) → `### Proposed Changes`. The payload MAY include a
  top-level `author` field for the LLM's self-declaration; the
  CLI resolves it per the four-step precedence below.
- `--author <id>` (optional). Uniform `--author` flag with
  identical four-step precedence across all three LLM-driven
  operations (propose-change, critique, revise) per:
  1. CLI `--author <id>` if set and non-empty.
  2. Env var `LIVESPEC_AUTHOR_LLM` if set and non-empty.
  3. Payload file-level `author` field if present and
     non-empty.
  4. Literal `"unknown-llm"` fallback.
  The resolved author populates the front-matter `author`
  field on the resulting proposed-change file. When fallback
  (4) is reached, this prose MUST surface a warning to the
  user ("Running with unknown LLM identifier; set
  `LIVESPEC_AUTHOR_LLM` or pass `--author <id>` for an
  audit-trail-clean attribution."). Human authors and LLMs
  SHOULD NOT use the `livespec-` prefix; this is a convention,
  not a mechanical reservation, and no schema or CLI
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
  there. The CLI validates the target structure before
  writing; if validation fails, exits 3 with
  `PreconditionError` naming the target path and the missing
  structural requirement.
- `--project-root <path>` (optional; defaults to `Path.cwd()`).
  Anchors `<spec-root>/` resolution and the upward walk for
  `.livespec.jsonc`. Uniform across every spec-side CLI.
- `--skip-pre-check` (optional). Skips the pre-step doctor
  static phase before the CLI writes. Mutually exclusive
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
LLM-driven phase but are NEVER passed to the propose-change CLI
(per):

- `--skip-doctor-llm-objective-checks` /
  `--run-doctor-llm-objective-checks` (mutually exclusive).
- `--skip-doctor-llm-subjective-checks` /
  `--run-doctor-llm-subjective-checks` (mutually exclusive).

When the user supplies either flag in the same invocation, this
prose forwards the choice to the post-step LLM-driven phase and
never to the propose-change CLI. Both-flags-in-the-same-pair is
a usage error; surface and abort the LLM-driven phase. See the
doctor prose (`prose/doctor.md`) for the full LLM-driven-phase
contract.

`--help` / `-h` is honored at the CLI level via the
`HelpRequested` supervisor path; help text goes to stdout and
exit code is `0` (NOT an error).

## Steps

1. **Resolve the active template.** Run the template-resolution
   CLI (core reference `bin/resolve_template.py`) with
   `--template <name>`, where `<name>` is the value of
   `.livespec.jsonc`'s `template` field (or the per-tree
   `template_name` when `--spec-target` names a sub-spec
   tree). The flag is required per SPECIFICATION/contracts.md
   §"Wrapper CLI surface". Capture the resolved template
   directory path from stdout.

2. **Read the propose-change prompt.** Read
   `<resolved-path>/prompts/propose-change.md`. Use its
   contents as the template prompt for finding generation.
   This is the two-step template-prompt dispatch (run the
   resolution CLI, then read the prompt file) and works
   uniformly for built-in and custom templates.

2.5. **Survey in-flight spec work (in-flight-survey
   narration).** Per SPECIFICATION/spec.md
   §"`propose-change` skill-prose responsibilities", BEFORE
   the change-authoring dialogue begins (i.e., before
   Step 3), surface every piece of concurrent in-flight
   spec design work:

   (a) **Remote propose-change branches.** Refresh remote
   refs (`git fetch <remote>`), then enumerate every remote
   branch matching the project's propose-change branch
   prefix (default `spec/*`), e.g.
   `git ls-remote --heads <remote> 'spec/*'` or
   `git branch -r --list '<remote>/spec/*'` after the
   fetch.

   (b) **Open spec-touching pull requests.** Query the
   project's code-hosting service (e.g. `gh pr list
   --state open --json number,title,headRefName,files`)
   for every open pull request whose diff touches the
   spec tree — any changed file under `<spec-root>/`.

   For each surfaced item (branch or PR), narrate one
   informational line carrying: the canonical topic slug
   when derivable (the branch-name remainder after the
   prefix, or a canonicalized form of the PR title;
   omit when not derivable) plus a brief characterization
   of which spec sections the item touches (from the
   branch's diff against the default branch or the PR's
   changed-file list — e.g. "touches `spec.md`
   §'Sub-command lifecycle' and `contracts.md`"). When
   the survey finds nothing, narrate a single line saying
   no in-flight spec work was detected, so the user knows
   the survey ran.

   **Degraded-survey tolerance.** Network failures —
   `git fetch` or the pull-request query exiting non-zero,
   missing auth, the hosting CLI being absent, no network —
   MUST be surfaced as a degraded-survey warning naming
   what failed (e.g. "in-flight survey degraded: `git
   fetch` failed; remote branches and open PRs were not
   surveyed — concurrent spec work may exist that this
   session cannot see") and MUST NOT block propose-change;
   continue to Step 2.6 with whatever portion of the
   survey succeeded.

   This cross-branch + open-PR visibility is symmetric to
   the in-tree stale-pending-proposal narration in the
   revise prose (which surfaces local-FS pending state);
   together the two narrations close the loop between
   revise-time and propose-change-time visibility of
   in-flight design work. The narration MUST NOT gate the
   CLI (the propose-change CLI runs regardless), MUST NOT
   add any pre-step or post-step doctor check, and MUST
   NOT block downstream CLI invocations — its sole purpose
   is in-flight-design-drift prevention.

2.6. **Capture alignment intent.** For each in-flight item
   surfaced in Step 2.5, elicit the user's intended
   relationship between the new proposal and that item —
   exactly one of:

   - **align** — the new proposal conforms to the
     in-flight design;
   - **modify-to-accommodate** — the new proposal
     partially supersedes the in-flight design; capture
     an explicit rationale for what is superseded and
     why;
   - **explicitly supersede** — the new proposal replaces
     the in-flight design; the in-flight branch SHOULD be
     closed/abandoned upstream (note this to the user —
     closing it is upstream housekeeping, not this
     operation's job).

   The captured alignment intent feeds the propose-change
   template prompt as steering context for the authoring
   dialogue (Step 5); it is NOT serialized into the
   resulting proposed-change findings JSON. When Step 2.5
   surfaced zero items (or the survey was fully degraded),
   skip this step.

3. **Capture user intent.** Ask the user: "What change do you
   want to propose? Describe the intent — what should the spec
   say differently, and why." Capture free-text intent. The
   propose-change prompt consumes this alongside the current
   spec content.

4. **Capture topic hint.** Ask the user: "What short topic
   should this proposal use? (a few words; the CLI will
   canonicalize to lowercase-kebab-case and truncate to 64
   characters)." Capture free-text. Do NOT pre-canonicalize on
   the prose side — the single-canonicalization invariant
   requires every `topic` derivation to route through the
   CLI's shared canonicalization. Pass the hint verbatim as
   the `<topic>` positional argument.

5. **Generate findings JSON.** Run the propose-change prompt
   against the user-described intent, including any
   alignment intent captured in Step 2.6 as steering
   context (so the authored proposal aligns with,
   accommodates, or supersedes the surfaced in-flight
   designs as the user directed). The prompt MUST emit
   JSON conforming to `proposal_findings.schema.json`:
   top-level `findings[]` array, each entry carrying `name`,
   `target_spec_files`, `summary`, `motivation`, and
   `proposed_changes`. The prompt MAY include a top-level
   `author` field for the LLM's self-declaration; the CLI
   resolves it per the four-step precedence. Each finding
   becomes one `## Proposal` section. A proposal MUST be
   explicit (no open questions, no "we should decide X
   later"); resolve sub-decisions before filing or surface
   them via the critique operation instead.

6. **Write payload to temp file.** Write the generated JSON to
   a temp file. Pass the tempfile path as `--findings-json` to
   the CLI.

7. **Resolve effective flags.** Determine whether the user
   passed `--skip-pre-check` / `--run-pre-check` and the two
   LLM-layer flag pairs. Compose the CLI argv with the
   pre-step pair when set; reserve the LLM-layer pairs for
   the post-step LLM-driven phase. If the user passed neither
   pre-step flag and `.livespec.jsonc`'s
   `pre_step_skip_static_checks` is `true`, the pre-step will
   be silently skipped — record this for the narration step
   below.

8. **Invoke the propose-change CLI.** Run the propose-change
   CLI named in config with
   `<topic> --findings-json <tempfile> [flags]` and explicit
   argv (forwarding `--author`, `--reserve-suffix`,
   `--spec-target`, `--project-root`, `--skip-pre-check` /
   `--run-pre-check` as applicable). Capture the exit code.
   The CLI canonicalizes the topic, validates the payload
   internally, runs pre-step doctor static (unless skipped),
   writes the file, and runs post-step doctor static. The
   resulting file is
   `<spec-target>/proposed_changes/<canonical-topic>.md`
   (or `<canonical-topic>-N.md` on collision; see Post-CLI).

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

10. **Retry-on-exit-4.** On CLI exit code `4` (schema
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
    the user. The CLI does not gate on this; the warning
    is purely audit-trail hygiene.

## Post-CLI

On exit 0, the CLI has:

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
  already exists), the CLI auto-disambiguates with a
  hyphen-separated monotonic integer suffix starting at `2`
  (`<canonical-topic>-2.md`, `<canonical-topic>-3.md`, ...)
  per v014 N6; no user prompt. The front-matter `topic` field
  carries ONLY the canonical topic WITHOUT the `-N` suffix;
  the `-N` suffix is filename-level disambiguation only.
- Run post-step doctor static.

The LLM-driven post-step phase then runs per the doctor prose
(`prose/doctor.md`), honoring the two LLM-layer flag pairs from
Inputs. Propose-change does NOT run revise; the user reviews
the resulting proposed-change file and runs the revise
operation separately to process it.

**Seed-recovery exit-3 narration (v017 Q4).** When invoked
during the seed post-step-failure recovery flow (heuristic: no
`vNNN` revision beyond `v001` exists AND the user passed
`--skip-pre-check`), and the CLI exits `3` from the
post-step doctor static, this prose MUST narrate the
exit-3 path distinctly: "this exit 3 is expected during seed
recovery; the proposed-change file IS on disk; commit the
partial state and run the revise operation with
`--skip-pre-check` to cut `v002` with the corrections."
Otherwise, the generic exit-3 narration in `## Failure
handling` applies and the user is expected to recognize the
recovery path from seed's earlier narration.

## Failure handling

CLI exit-code-to-narration mapping:

- Exit `0` → success. The proposed-change file exists at the
  path described in `## Post-CLI`. Proceed to the
  post-step LLM-driven phase per the doctor prose
  (`prose/doctor.md`). This also covers intentional `--help`
  output (user asked for help, not an error).
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
