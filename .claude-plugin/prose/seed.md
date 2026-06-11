# seed

Harness-neutral driving prose for the `seed` operation, per
`SPECIFICATION/spec.md` §"Contract + reference implementations
architecture": this artifact is the core-owned LLM-facing half of the
operation; the seed CLI named in `.livespec.jsonc` (core reference
implementation: `bin/seed.py`) is the contract half. Drivers bind this
prose to their runtime; nothing in this file names any specific agent
runtime's tools or command namespace.

Bootstrap a fresh livespec specification tree from a single
user-provided intent. Drive a three-question pre-seed dialogue
(template choice, sub-spec emission, intent), invoke the chosen
template's `prompts/seed.md` to generate spec content, then hand a
fully-assembled JSON payload to the seed CLI, which writes
`.livespec.jsonc`, the main spec tree, every requested sub-spec tree,
and the auto-captured seed proposed-change / revision pair atomically.
Seed is **exempt from pre-step** doctor static (the green-field repo
has no spec for pre-step to inspect); post-step doctor static runs
after the CLI exits, followed by the LLM-driven post-step phase.

## When to run

- The user invokes the seed operation, says "seed a livespec spec",
  "set up a livespec", "start a new spec", or otherwise asks to
  create a brand-new spec in a project that does not yet have one.
- The project's `.livespec.jsonc` is absent (or present but the
  spec tree it points at is empty). Seed is the only operation
  designed to run before `.livespec.jsonc` exists; every other
  operation's pre-step doctor static will exit 3 on a missing
  config.
- If the user asks to *file a change* against an existing spec
  rather than start a new one, route to the propose-change
  operation instead. If the user asks to *surface ambiguities*,
  route to the critique operation. Seed only authors the initial
  spec; it refuses with exit 3 (idempotency) when any
  template-declared target file already exists.

## Inputs

The seed CLI accepts the following flags in v1:

- `--seed-json <path>` (required). Absolute or
  project-root-relative path to a JSON payload conforming to
  `seed_input.schema.json` (shipped in core's `livespec/schemas/`
  package). The CLI validates the payload internally; this prose
  does NOT invoke a separate validator. The schema's top-level
  shape is:
  ```json
  {
    "template": "<chosen-template-name-or-path>",
    "intent": "<verbatim user intent>",
    "files": [
      {"path": "<template-declared spec file path>", "content": "..."}
    ],
    "sub_specs": [
      {
        "template_name": "<sub-spec-template-name>",
        "files": [
          {"path": "SPECIFICATION/templates/<name>/spec.md", "content": "..."}
        ]
      }
    ]
  }
  ```
  The required top-level `template` field carries the user-
  chosen template value from the pre-seed dialogue (one of
  `livespec`, `minimal`, or a custom template path); the
  CLI consumes it to bootstrap `.livespec.jsonc` per bullet "`.livespec.jsonc` is wrapper-
  owned" (v016 P2). The `sub_specs[]` list MAY be empty (the
  default end-user case) or carry one entry per template the
  user selected for sub-spec governance (v018 Q1; v020 Q2).
- `--project-root <path>` (optional; defaults to `Path.cwd()`).
  Anchors `.livespec.jsonc` placement and template-relative
  path resolution. Uniform across every spec-side CLI.

Seed has **no `--skip-pre-check` / `--run-pre-check` flag pair**
because seed has no pre-step (:
"`seed` is exempt from pre-step doctor static"). Seed also has
**no `--author` flag**: the auto-captured seed proposed-change
and its revision pair are written with the literal author
identifiers `livespec-seed` (LLM-side) and the user's git
identity (human-side) auto-generated-
file details. Author resolution applies only to the three
LLM-driven user-authored operations (`propose-change`, `critique`,
`revise`).

Two LLM-layer flag pairs apply during the post-step LLM-driven
phase but are NEVER passed to the seed CLI (per):

- `--skip-doctor-llm-objective-checks` /
  `--run-doctor-llm-objective-checks` (mutually exclusive).
- `--skip-doctor-llm-subjective-checks` /
  `--run-doctor-llm-subjective-checks` (mutually exclusive).

When the user supplies either flag in the same invocation, this
prose forwards the choice to the post-step LLM-driven phase and
never to the seed CLI. Both-flags-in-the-same-pair is a usage
error; surface and abort the LLM-driven phase. See the doctor
prose (`prose/doctor.md`) for the full LLM-driven-phase contract.

`--help` / `-h` is honored at the CLI level via the
`HelpRequested` supervisor path; help text goes to stdout and
exit code is `0` (NOT an error).

## Steps

1. **Pre-seed dialogue (three questions; v014 N1 + v020 Q2).**
   When `.livespec.jsonc` is absent at the project root (the
   normal pre-seed state), ask the user the following three
   questions in order BEFORE invoking any CLI or template
   prompt:

   1. **Template choice.** "Which template should this spec
      use? Options: `livespec` (recommended default — multi-
      file `SPECIFICATION/` layout with `spec.md`,
      `contracts.md`, `constraints.md`, `scenarios.md`),
      `minimal` (single-file `SPECIFICATION.md` at repo root),
      or a path to a custom template directory containing
      `template.json`."
   2. **Sub-spec emission (v020 Q2; meta-project case).**
      "Does this project ship its own livespec templates that
      should be governed by sub-spec trees under
      `SPECIFICATION/templates/<name>/`? (default: no)" On
      "yes," follow up with: "Which template directory names
      under the project's bundled specification-templates
      directory should each receive a sub-spec tree?" Capture
      one or more template names (e.g., `livespec`,
      `minimal`). On "no" (the typical end-user case), the
      seed prompt will emit `sub_specs: []`.
   3. **Seed intent.** "What is the intent of this project?
      Free-text description of what you want the
      specification to cover; this becomes the `<intent>` that
      drives the seed prompt and is preserved verbatim in the
      auto-captured seed proposed-change's
      `Motivation` / `Proposed Changes` sections."

   If `.livespec.jsonc` IS already present (re-running seed in
   a project where it was previously committed but the spec
   tree is empty / partial — uncommon but legal), MAY skip the
   template-choice question and re-use the on-disk `template`
   value; still ask the sub-spec-emission and intent questions.
   The CLI's `template` ↔ on-disk consistency check exits
   3 on mismatch (v016 P2; v017 Q6).

2. **Resolve the chosen template (pre-seed dispatch; v017 Q2).**
   Run the template-resolution CLI (core reference
   `bin/resolve_template.py`) with `--project-root .
   --template <chosen>`. `--template` is a required flag for
   every operation (per SPECIFICATION/contracts.md §"Wrapper
   CLI surface"); it resolves built-in names (`livespec`,
   `livespec-with-diagrams`, `minimal`) to the bundle's
   `specification-templates/<name>/` path or treats any other
   value as a path relative to `--project-root`. Capture the
   resolved absolute template directory path from stdout.
   Seed's deviation from the other operations is the SOURCE
   of the name: seed passes the user's chosen value directly
   because `.livespec.jsonc` does not exist yet; every other
   operation passes the `template` value read from
   `.livespec.jsonc`.

3. **Read the seed prompt.** Read
   `<resolved-path>/prompts/seed.md`. Use its contents as the
   template prompt for spec-content generation. This is the
   two-step template-prompt dispatch (run the resolution CLI,
   then read the prompt file) and works uniformly for
   built-in and custom templates.

4. **Generate seed payload JSON.** Run the seed template
   prompt against the user's intent (from question 3), the
   sub-spec selections (from question 2), and the active
   template's `specification-template/` starter content. The
   prompt MUST emit JSON conforming to
   `seed_input.schema.json`:
   - Top-level `template` (required, the chosen value from
     question 1).
   - Top-level `intent` (required, the verbatim user intent
     from question 3).
   - Top-level `files[]` (required) — the main-spec files,
     one entry per template-declared spec-file path.
   - Top-level `sub_specs[]` (required, possibly empty) — one
     entry per template named in question 2's follow-up. On
     "no" to sub-spec emission, emit `sub_specs: []`. Each
     entry carries `template_name` (matching the bundled
     specification-templates `<name>/` directory name) and a
     `files[]` array with content at
     `SPECIFICATION/templates/<template_name>/<spec-file>`
     paths.

5. **Write payload to temp file.** Write the assembled JSON to
   a temp file (e.g., `/tmp/livespec-seed-<uuid>.json`). Pass
   the tempfile path as `--seed-json` to the seed CLI. This
   prose MUST NOT write `.livespec.jsonc` directly — CLI-owned
   file-shaping is the single source of truth for that file.

6. **Invoke the seed CLI.** Run the seed CLI named in config
   with `--seed-json <tempfile> [--project-root <path>]` and
   explicit argv. Capture the exit code. The CLI validates the
   payload internally, then performs its deterministic
   file-shaping work in this order BEFORE post-step doctor
   static runs (per): write `.livespec.jsonc` from the
   payload's `template` value, write each main-spec `files[]`
   entry, write every `sub_specs[]` entry's `files[]` entries
   to their `SPECIFICATION/templates/<template_name>/` paths,
   create `<spec-root>/history/v001/` (and one per sub-spec
   tree), and auto-capture the seed itself as
   `<spec-root>/history/v001/proposed_changes/seed.md` paired
   with `seed-revision.md` (front-matter `author:
   livespec-seed`, `decision: accept`).

7. **Multi-tree atomic dispatch (v018 Q1).** When the payload
   carries a non-empty `sub_specs[]`, the CLI materializes
   the main spec tree AND every sub-spec tree atomically in a
   single invocation. Partial-write refusal applies: if any
   tree fails to write for any reason (permission errors,
   pre-existing files at target paths, validation failure on
   any sub-spec's content), the CLI rolls the entire seed
   back and exits non-zero with a `PreconditionError`
   describing the failing tree; no partial trees are left on
   disk. Narration MUST surface the failing tree's path and
   the structural cause from the CLI's stderr structlog
   line(s).

8. **Retry-on-exit-4.** On CLI exit code `4` (schema
   validation failed; the LLM-emitted JSON did not conform to
   `seed_input.schema.json`), treat the return code as a
   retryable malformed-payload signal. Inspect the structured
   error context on stderr, re-invoke the seed template
   prompt with that context, re-assemble corrected JSON, and
   re-invoke the CLI. The exact retry count is intentionally
   unspecified in v1; orchestration owns the retry policy.
   Exit `3` is NOT retryable (precondition / doctor-static
   failure — see Failure handling for the recovery flow).

## Post-CLI

On exit 0, the CLI has:

- Validated the `--seed-json` payload against
  `seed_input.schema.json`.
- Written `.livespec.jsonc` at the project root with the full
  commented schema skeleton, populated from the payload's
  top-level `template` value (v016 P2).
- Written every main-spec `files[]` entry to its template-
  declared path (e.g., `SPECIFICATION/spec.md` under the
  built-in `livespec` template; `SPECIFICATION.md` under the
  built-in `minimal` template).
- Written every `sub_specs[]` tree's files to
  `SPECIFICATION/templates/<template_name>/` atomically
  alongside the main tree (v018 Q1).
- Created `<spec-root>/history/v001/` for the main spec
  (initial versioned spec files, `proposed_changes/` subdir,
  per-version `README.md` only when the active template's
  versioned surface declares one) and the equivalent
  `SPECIFICATION/templates/<template_name>/history/v001/`
  layout for every sub-spec tree (v018 Q1; v020 Q1 uniform
  README — every sub-spec tree captures both a sub-spec-root
  `README.md` AND a per-version `README.md` snapshot).
- Auto-captured the seed itself as
  `<spec-root>/history/v001/proposed_changes/seed.md` (front-
  matter `topic: seed`, `author: livespec-seed`,
  `created_at: <UTC ISO-8601>`; one `## Proposal: seed`
  section quoting every seed-written file under
  `### Target specification files` and the verbatim
  `<intent>` under `### Motivation` and `### Proposed
  Changes`) paired with
  `<spec-root>/history/v001/proposed_changes/seed-revision.md`
  (front-matter `proposal: seed.md`, `decision: accept`,
  `revised_at` matching `created_at`, `author_llm:
  livespec-seed`, `author_human` from `git config user.name`
  / `user.email` or `"unknown"` fallback). The auto-captured
  seed proposal lands ONLY in the main spec's
  `proposed_changes/`; sub-spec trees do not each get their
  own auto-captured seed proposal — the single main-spec seed
  artifact documents the whole multi-tree creation.
- Run post-step doctor static across every tree.

The LLM-driven post-step phase then runs per the doctor prose
(`prose/doctor.md`), honoring the two LLM-layer flag pairs from
Inputs.

## Failure handling

CLI exit-code-to-narration mapping:

- Exit `0` → success. The full multi-tree spec, history, and
  auto-captured seed artifacts exist at the paths described in
  `## Post-CLI`. Proceed to the post-step LLM-driven phase per
  the doctor prose (`prose/doctor.md`). This also covers
  intentional `--help` output (user asked for help, not an
  error).
- Exit `1` → internal bug; surface the error from stderr
  (including any traceback) and abort. Do NOT retry.
- Exit `2` → usage error (e.g., missing `--seed-json`,
  unknown flag). Restate the expected invocation shape per
  `## Inputs` above and abort.
- Exit `3` → precondition / post-step doctor-static failure.
  Two distinct sub-cases exist:
  1. **Idempotency / pre-existing files / `.livespec.jsonc`
     mismatch** (the CLI refused before touching disk).
     Surface the offending paths from stderr and direct the
     user to either remove the offending files or run the
     propose-change / critique operation against the existing
     spec instead of re-seeding. Re-running seed is NOT a
     recovery path — there is no `--force-reseed` flag.
  2. **Post-step doctor-static fail Findings** (the CLI
     completed its file-shaping work BEFORE post-step ran;
     the spec, history, and auto-captured seed artifacts ARE
     on disk but doctor-static rejected the result). This
     prose MUST surface the recovery path concretely
     (v014 N7; v017 Q4):

     > On exit 3 after seed's operation logic completed
     > (post-step fail): the specification and history files
     > are on disk but doctor-static rejected them. To
     > correct WITHOUT re-seeding (seed's idempotency blocks
     > re-seed):
     >
     > 1. Review the fail Findings surfaced in stderr /
     >    narration.
     > 2. Run the propose-change operation with
     >    `--skip-pre-check`, the fix topic, and the fix
     >    description to file a fix proposal.
     >    `--skip-pre-check` bypasses the pre-step.
     >    **Expect propose-change to ALSO exit 3** (its own
     >    post-step doctor-static trips the same findings),
     >    but the proposed-change file IS on disk per
     >; this is the expected sequential-
     >    lifecycle behavior, not a separate failure.
     > 3. `git commit` the partial state (the seed-written
     >    files plus the new proposed-change file). This step
     >    is load-bearing — without it, the next invocation's
     >    `doctor-out-of-band-edits` check will trip its pre-
     >    backfill guard. livespec does NOT write to git
     >    itself; the commit is a user
     >    action.
     > 4. Run the revise operation with `--skip-pre-check` to
     >    process the proposed-change and cut `v002` with the
     >    corrections. Revise's post-step runs against the
     >    now-fixed state and passes. (`v001` is the seed;
     >    `v002` is the first revision that makes the spec
     >    pass its own doctor-static.)

  Exit 3 is NOT retryable via prompt re-run; the LLM cannot
  fix a precondition or a doctor-static finding by re-emitting
  the JSON.
- Exit `4` → schema-validation failure on the LLM-emitted JSON
  payload; **retryable** per Step 8. Inspect the error
  context, re-invoke the seed prompt, and re-assemble
  corrected JSON.
- Exit `127` → too-old Python or missing tool; surface the
  install instruction from stderr and abort.
