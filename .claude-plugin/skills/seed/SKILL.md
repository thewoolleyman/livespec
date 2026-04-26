---
name: seed
description: Author the initial natural-language specification for a new project, populating the chosen template's spec_root layout. Invoked by /livespec:seed, "seed a livespec spec", "set up a livespec", or when starting a brand-new spec in an empty SPECIFICATION/ tree.
allowed-tools: Bash, Read, Write
---

# seed

Bootstrap a fresh livespec specification tree by capturing user
intent, invoking the active template's `prompts/seed.md` to
generate initial content, and shaping the on-disk tree via
`bin/seed.py`.

## When to invoke

- The user types `/livespec:seed`, says "seed a livespec spec",
  "set up a livespec", or otherwise asks to start a brand-new
  spec in an empty `SPECIFICATION/` tree.
- The project's `SPECIFICATION/` (or its template-declared
  spec_root) is absent or empty.

## Inputs

- The wrapper accepts `--seed-json <path>` (required) — a JSON
  payload conforming to `seed_input.schema.json`. The skill
  composes this payload from the template's `prompts/seed.md`
  output and writes it to a temp file before invoking the
  wrapper.
- `--project-root <path>` (optional; defaults to cwd).

## Steps

1. **Pre-seed dialogue (3 questions per v021 Q2).** Ask the user
   in this order:

   1. **Template selection.** "Which template? Options: `livespec`
      (default — multi-file `SPECIFICATION/` layout), `minimal`
      (single-file `SPECIFICATION.md`), or a path to a custom
      template directory."
   2. **Sub-spec emission.** "Does this project ship its own
      livespec templates that should be governed by sub-spec
      trees under `SPECIFICATION/templates/<name>/`? (default:
      no)"
   3. **Template-name follow-up** (only when the user answered
      "yes" to question 2). "Which template directory names
      under `.claude-plugin/specification-templates/` (or
      equivalent) should each receive a sub-spec tree? (e.g.,
      `livespec`, `minimal`)"

   Then ask one more open question:

   - **Seed intent.** "What is the intent of this project?
      (free-text; this becomes the motivation for the
      auto-captured seed proposal.)"

2. **Resolve the template path.** Invoke `bin/resolve_template.py`
   via Bash with `--template <chosen-name-or-path>` (the
   pre-seed flow per v017 Q2; bypasses `.livespec.jsonc` lookup
   since it does not exist yet). Capture the resolved absolute
   path from stdout.

3. **Read the seed prompt.** Use the Read tool to read
   `<resolved-path>/prompts/seed.md` and use its contents as the
   template prompt.

4. **Generate the seed payload.** Run the seed prompt against
   the captured user intent. The prompt MUST emit JSON
   conforming to `seed_input.schema.json`:
   - Top-level fields: `template`, `intent`, `files[]`,
     `sub_specs[]`.
   - On "no" to sub-spec emission, emit `sub_specs: []`.
   - On "yes", emit one `sub_specs[]` entry per template named
     in the dialogue.

5. **Write payload to temp file.** Write the generated JSON to a
   temp file (e.g., `/tmp/livespec-seed-<uuid>.json`) using the
   Write tool.

6. **Invoke the wrapper.** Run
   `bin/seed.py --seed-json <tempfile>` via Bash. Capture the
   exit code; structured findings (if any) are on stderr.

7. **Retry-on-exit-4.** If the wrapper exits 4 (schema
   validation failure), surface the validation error from
   stderr to the user, re-invoke the seed prompt with the
   structured error context, re-assemble corrected JSON, and
   re-invoke the wrapper. Retry count is unspecified in v1;
   prefer 1-2 retries before aborting and asking the user.

## Post-wrapper

On exit 0, the seed wrapper has written:
- `.livespec.jsonc` at project root (with the chosen template).
- All main-spec files at their template-declared paths.
- Sub-spec trees under `SPECIFICATION/templates/<name>/` (when
  `sub_specs[]` was non-empty).
- `<spec-root>/history/v001/` for the main spec and each sub-spec.
- Auto-captured `seed.md` proposed-change + `seed-revision.md`
  under the main spec's `history/v001/proposed_changes/`.

Post-step doctor-static then runs (see `doctor/SKILL.md`) to
verify the bootstrapped tree.

## Failure handling

- Exit `0` → proceed to post-wrapper.
- Exit `1` → internal bug; surface the structlog stderr lines
  (including traceback) and abort.
- Exit `2` → usage error; restate the expected invocation
  shape and abort.
- Exit `3` → precondition failure (e.g., `.livespec.jsonc`
  already exists with a mismatching template; idempotency
  refusal because target files exist). Surface the
  `PreconditionError` message from stderr and direct the user
  to the corrective action. NOT retryable via prompt re-run.
- Exit `4` → schema-validation failure; **retryable** per
  step 7 above.
- Exit `127` → too-old Python or missing tool; surface the
  install instruction and abort.

## Phase 3 minimum-viable scope

This bootstrap prose is intentionally narrower than the full
per-sub-command body structure documented in PROPOSAL.md
§"Per-sub-command SKILL.md body structure". Phase 7 brings
this file to final per the `skill-md-prose-authoring`
deferred-items entry, regenerated from the `livespec`
template's sub-spec via the dogfooded propose-change/revise
loop.
