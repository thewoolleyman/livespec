---
name: revise
description: Walk the user through accepting or rejecting each pending proposed change in <spec-root>/proposed_changes/, then snapshot the result as a new <spec-root>/history/vNNN/ revision. Invoked by /livespec:revise, "revise the livespec", or "process pending proposed changes".
allowed-tools: Bash, Read, Write
---

# revise

Drive per-proposal `accept` / `modify` / `reject` decisions for
every in-flight proposed-change file under
`<spec-target>/proposed_changes/`, then cut a new
`<spec-target>/history/vNNN/` snapshot via the wrapper. Each
decision is presented to the user for confirmation before the
JSON payload is assembled and the wrapper is invoked. Pre-step
doctor static runs before revise; post-step doctor static runs
after the wrapper exits, followed by the LLM-driven post-step
phase.

## When to invoke

- The user types `/livespec:revise`, says "revise the spec",
  "revise the livespec", "process pending proposed changes",
  or asks to advance the spec to a new version.
- The repo has a valid `.livespec.jsonc`, a populated spec
  tree, AND `<spec-target>/proposed_changes/` is non-empty
  (the wrapper's pre-step doctor static enforces the first
  two; the empty-proposed-changes case is a v011 K9 fail-fast
  precondition that exits 3 with `PreconditionError` directing
  the user to run `/livespec:propose-change` first).
- If the user asks to *file* a new amendment rather than
  process pending ones, route to `/livespec:propose-change`
  instead. If the user asks to *surface* ambiguities or
  contradictions, route to `/livespec:critique` instead.
  Revise only processes existing proposed-change files; it
  never authors new ones.

## Inputs

The wrapper `bin/revise.py` accepts the following flags in v1:

- `--revise-json <path>` (required). Absolute or
  project-root-relative path to a JSON payload conforming to
  `revise_input.schema.json` (under
  `.claude-plugin/scripts/livespec/schemas/`). The wrapper
  validates the payload internally; the SKILL.md prose does
  NOT invoke a separate validator. The schema's top-level
  shape is `{"author": "<optional>", "decisions": [...]}`,
  with one entry in `decisions[]` per proposed-change file
  processed in this revise pass. Each decision carries
  `proposal_topic`, `decision` (`accept` | `modify` |
  `reject`), `rationale`, optional `modifications` (required
  semantically when `decision == "modify"`), and optional
  `resulting_files[]` of `{path, content}` pairs (used when
  `decision` is `accept` or `modify`; empty / omitted when
  `decision == "reject"`). The payload MAY include a
  top-level `author` field for the LLM's self-declaration;
  the wrapper resolves it per the four-step precedence below.
- `--author <id>` (optional). Uniform `--author` flag with
  identical four-step precedence across all three LLM-driven
  wrappers (propose-change, critique, revise) per:
  1. CLI `--author <id>` if set and non-empty.
  2. Env var `LIVESPEC_AUTHOR_LLM` if set and non-empty.
  3. Payload file-level `author` field if present and
     non-empty.
  4. Literal `"unknown-llm"` fallback.
  The resolved author populates the `author_llm` field on
  every revision-file front-matter written by this revise
  pass. A second front-matter field, `author_human`, is
  populated independently by the wrapper via
  `livespec.io.git.get_git_user()` from `git config user.name`
  and `user.email` (literal `"unknown"` fallback when git
  is available but the config values are unset). The
  `--author` flag does NOT touch `author_human`. When
  fallback (4) is reached for `author_llm`, the SKILL.md
  prose MUST surface a warning to the user ("Running with
  unknown LLM identifier; set `LIVESPEC_AUTHOR_LLM` or pass
  `--author <id>` for an audit-trail-clean attribution.").
- `--spec-target <path>` (optional). Defaults to the main
  spec root (resolved via `.livespec.jsonc` upward walk).
  Per (v018
  Q1), may point at a sub-spec tree under
  `<main-spec-root>/templates/<name>/` to route the revise
  there. The wrapper validates the target structure
  (`proposed_changes/`, `history/`, plus at least one
  template-declared spec file) before processing; if
  validation fails, exits 3 with `PreconditionError`
  naming the target path and the missing structural
  requirement.
- `--project-root <path>` (optional; defaults to
  `Path.cwd()`). Anchors `<spec-root>/` resolution and the
  upward walk for `.livespec.jsonc`. Uniform across every
  wrapper.
- `--skip-pre-check` (optional). Skips the pre-step doctor
  static phase before revise runs. Mutually exclusive with
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
LLM-driven phase and never to `bin/revise.py`. Both-flags-
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

2. **Read the revise prompt.** Use the Read tool on
   `<resolved-path>/prompts/revise.md`. Use its contents
   as the template prompt for per-proposal decision
   generation. This is the two-step template-prompt
   dispatch from (Bash for resolution, then Read for the
   prompt file) and works uniformly for built-in and
   custom templates.

3. **Enumerate pending proposed-change files.** Use the
   Read tool (or Bash `ls`) to list
   `<spec-target>/proposed_changes/*.md`. Skip the
   skill-owned `README.md` and any file ending in
   `-revision.md` (those are revision pairings from prior
   cycles, not in-flight proposals; the wrapper's pre-step
   doctor static separately verifies pairing invariants).
   Sort the remaining files in **creation-time order** by
   YAML front-matter `created_at` (oldest first), with
   lexicographic filename as fallback on tie. Within each
   file, `## Proposal` sections are processed in document
   order (top to bottom). If the resulting list is empty,
   STOP — the wrapper's pre-step will exit 3 with the
   v011 K9 empty-proposed-changes precondition; surface
   that finding to the user and direct them to run
   `/livespec:propose-change` first.

   **Narrate stale-pending-proposal count + oldest.**
   Before the per-proposal accept/modify/reject loop
   begins, surface a single informational line of the
   form: "N pending proposal(s); oldest is
   `<canonical-topic>` from <created_at>." (Use the
   YAML front-matter `topic` field for the canonical
   topic and `created_at` for the timestamp.) Per
   SPECIFICATION/spec.md (v052) §"Sub-command lifecycle"
   revise-lifecycle paragraph, this narration MUST NOT
   gate the wrapper, MUST NOT add any pre-step or
   post-step doctor check, and MUST NOT block
   downstream wrapper invocations. The sole purpose is
   pending-proposal-accumulation visibility so the user
   MAY choose to address older proposals during the
   current pass.

4. **Capture optional steering intent.** Ask the user
   (optional, single free-text prompt): "Any steering
   intent for this revise pass? (e.g., 'reject anything
   touching the auth section') — leave blank to let the
   LLM decide each proposal independently." Capture
   free-text. Per, the steering
   intent MUST only steer per-proposal decisions for the
   current revise invocation; it MUST NOT contain new
   spec content. If the user-supplied content reads as
   *new intent* rather than decision-steering (best-effort
   LLM judgment), surface a warning and direct the user
   to run `/livespec:propose-change` first; on ambiguity,
   proceed with a visible warning. The steering intent
   feeds the revise template prompt during step 5; it is
   NOT included in the JSON payload.

5. **Per-proposal decision dialogue.** For each
   proposed-change file in the order from step 3:
   - Run the revise template prompt with the
     proposed-change content + current spec content +
     optional steering intent. The prompt emits an
     `accept`, `modify`, or `reject` decision per
     `## Proposal` section, with rationale and (for
     `accept` / `modify`) the updated `resulting_files[]`.
   - **Prompt the user for confirmation.** Present each
     per-proposal decision (decision verb, rationale,
     resulting-files list when applicable) and capture
     confirm / override. This is the only sub-command
     in the suite that runs a per-proposal confirmation
     dialogue ( Step 4 — "Prompt the user for
     confirmation (only for `revise`'s per-proposal
     dialogue)").
   - On `modify`, the LLM drafts the modification and
     iterates with the user in dialogue until the user
     confirms; the converged content lands in the
     decision's `modifications` field and updated
     `resulting_files[]`.
   - The user MAY at any per-proposal turn toggle
     "delegate remaining proposals to the LLM." Once
     set, this toggle applies to **all remaining
     proposals across all remaining files**
     (whole-revise scope) and the skill auto-accepts
     the LLM's decisions for every remaining proposal
     without further confirmation. The `--spec-target`
     value is presented clearly during the dialogue
     when it routes to a sub-spec tree (so the user
     sees which tree a `modify`/`accept` will mutate).

6. **Assemble revise-json payload.** Compose the JSON
   conforming to `revise_input.schema.json`:
   - Optional top-level `author` (LLM self-declaration).
   - `decisions[]` — one entry per processed
     proposed-change file, each with `proposal_topic`,
     `decision`, `rationale`, optional `modifications`
     (required semantically when `decision == "modify"`),
     and optional `resulting_files[]` of
     `{path, content}` pairs (for `accept` / `modify`).
   The steering intent from step 4 is consumed by the
   prompt but never serialized into the payload.

7. **Write payload to temp file.** Use the Write tool to
   write the assembled JSON to a temp file. Pass the
   tempfile path as `--revise-json` to the wrapper.

8. **Resolve effective flags.** Determine whether the user
   passed `--skip-pre-check` / `--run-pre-check` and the
   two LLM-layer flag pairs. Compose the wrapper argv with
   the pre-step pair when set; reserve the LLM-layer pairs
   for the post-step LLM-driven phase. If the user passed
   neither pre-step flag and `.livespec.jsonc`'s
   `pre_step_skip_static_checks` is `true`, the pre-step
   will be silently skipped — record this for the
   narration step below.

9. **Invoke the wrapper.** Run
   `bin/revise.py --revise-json <tempfile> [flags]` via
   the Bash tool with explicit argv (forwarding
   `--author`, `--spec-target`, `--project-root`,
   `--skip-pre-check` / `--run-pre-check` as applicable).
   Capture exit code. The wrapper validates the payload
   internally, runs pre-step doctor static (unless
   skipped), performs the deterministic file-shaping work
   (cut new `vNNN`, snapshot working spec files,
   move + pair proposed-changes into history, apply
   `resulting_files` updates), and runs post-step doctor
   static.

10. **Narrate skipped pre-step (when silent).** If the
    effective resolution was `skip = true` AND the user
    did NOT explicitly pass `--skip-pre-check` (i.e., the
    skip came from `pre_step_skip_static_checks: true` in
    config), surface a warning to the user: "Pre-step
    doctor static was skipped because
    `pre_step_skip_static_checks` is set to `true` in
    `.livespec.jsonc`. Run with `--run-pre-check` to
    force the pre-step." When the user passed
    `--skip-pre-check` explicitly, no narration is
    required (the skip is intentional and acknowledged).
    When the user passed `--run-pre-check`, the pre-step
    ran; no narration needed.

11. **Retry-on-exit-4.** On wrapper exit code `4` (schema
    validation failed; the LLM-emitted JSON did not
    conform to `revise_input.schema.json`), treat the
    return code as a retryable malformed-payload signal.
    Inspect the structured error context on stderr,
    re-invoke the revise template prompt with that
    context, re-assemble corrected JSON, and re-invoke
    the wrapper. The exact retry count is intentionally
    unspecified in v1; orchestration owns the retry
    policy. Exit `3` is NOT retryable (precondition /
    doctor-static failure — surface findings and abort).

12. **Narrate fallback-author warning.** If the resolved
    `author_llm` was the literal `"unknown-llm"` (i.e.,
    none of `--author` / `LIVESPEC_AUTHOR_LLM` / payload
    `author` were set), surface the warning from the
    Inputs section to the user. The wrapper does not
    gate on this; the warning is purely audit-trail
    hygiene. `author_human` is independent of this
    warning and is populated by the wrapper from git
    config (or its `"unknown"` fallback) regardless of
    whether `author_llm` resolved cleanly.

## Post-wrapper

On exit 0, the wrapper has:

- Validated the `--revise-json` payload against
  `revise_input.schema.json`.
- Resolved `author_llm` via the four-step precedence and
  `author_human` via `livespec.io.git.get_git_user()`.
- Run pre-step doctor static (unless skipped).
- **Cut a new `vN` per** (every
  successful revise cuts one new version, incrementing
  past the highest existing `vNNN`; v038 D1 Statement B).
  When at least one decision is `accept` or `modify`, the
  working-spec files named in those decisions'
  `resulting_files[]` are updated in place before the
  snapshot. When every decision is `reject`, the new
  version's spec files are byte-identical copies of the
  prior version's spec files (preserving the audit trail).
- **Snapshotted working spec files into
  `<spec-target>/history/vN/`** byte-identically. The
  in-tree shape under `history/vN/` mirrors the active
  template's versioned-surface declaration; a per-version
  `README.md` is written only when the active template's
  versioned surface defines one.
- **Moved each processed proposed-change file
  byte-identically** from
  `<spec-target>/proposed_changes/<stem>.md` into
  `<spec-target>/history/vN/proposed_changes/<stem>.md`,
  preserving the existing filename stem (which under
  v014 N6 collision disambiguation may include a `-N`
  suffix — e.g., `foo.md`, `foo-2.md`).
- **Paired each processed proposal with a revision file**
  at
  `<spec-target>/history/vN/proposed_changes/<stem>-revision.md`
  using the same `<stem>` value as the proposed-change
  filename. The revision file conforms to
  SPECIFICATION/spec.md §"Proposed-change and revision file
  formats": YAML front-matter (`proposal`,
  `decision`, `revised_at` UTC ISO-8601 seconds,
  `author_human`, `author_llm`) validated against
  `revision_front_matter.schema.json`, followed by
  `## Decision and Rationale` (always),
  `## Modifications` (required when `decision == "modify"`),
  `## Resulting Changes` (required when `decision` is
  `accept` or `modify`), and `## Rejection Notes`
  (required when `decision == "reject"`).
- **Filename stem vs. front-matter `topic` distinction
  (v017 Q7).** The filename stem carries any `-N`
  collision suffix; the proposed-change file's
  front-matter `topic` does NOT. Revision-pairing (by
  doctor's `revision-to-proposed-change-pairing` check)
  walks filename stems — for every `<stem>-revision.md`,
  the check verifies `<stem>.md` exists in the same
  directory.
- Run post-step doctor static.

After successful completion,
`<spec-target>/proposed_changes/` MUST be empty (of
in-flight proposals; the skill-owned
`proposed_changes/README.md` persists).

The LLM-driven post-step phase then runs per
`doctor/SKILL.md`, honoring the two LLM-layer flag pairs
from Inputs.

## Failure handling

Wrapper exit-code-to-narration mapping:

- Exit `0` → success. The new `vN` exists at the path
  described in `## Post-wrapper`. Proceed to the
  post-step LLM-driven phase per `doctor/SKILL.md`. This
  also covers intentional `--help` output (user asked
  for help, not an error).
- Exit `1` → internal bug; surface the error from stderr
  (including any traceback) and abort. Do NOT retry.
- Exit `2` → usage error (e.g., both `--skip-pre-check`
  and `--run-pre-check` supplied; missing
  `--revise-json`; unknown flag). Restate the expected
  invocation shape per `## Inputs` above and abort.
- Exit `3` → precondition / doctor-static failure
  (pre-step fail, empty
  `<spec-target>/proposed_changes/` per v011 K9,
  history-contiguity gaps, `--spec-target` validation
  fail, or post-step fail). Surface the findings from
  stderr structlog line(s) and direct the user to the
  corrective action each finding describes. NOT
  retryable via prompt re-run; the LLM cannot fix a
  precondition by re-emitting the JSON.
- Exit `4` → schema-validation failure on the
  LLM-emitted JSON payload; **retryable** per Step 11.
  Inspect the error context, re-invoke the revise
  prompt, and re-assemble corrected JSON.
- Exit `127` → too-old Python or missing tool; surface
  the install instruction from stderr and abort.
