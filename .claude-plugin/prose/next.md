# next

Harness-neutral driving prose for the `next` operation, per
`SPECIFICATION/spec.md` §"Contract + reference implementations
architecture": this artifact is the core-owned LLM-facing half of the
operation; the next CLI named in `.livespec.jsonc` (core reference
implementation: `bin/next.py`) is the contract half. Drivers bind
this prose to their runtime; nothing in this file names any specific
agent runtime's tools or command namespace.

Thin-transport pass-through per `SPECIFICATION/contracts.md`
§"`/livespec:next` spec-side thin-transport skill". Invokes
the next CLI and presents its stdout JSON verbatim;
all ranking, urgency, and threshold logic lives in the
Python implementation. This prose MUST NOT accrete logic.

The CLI is a pure function of spec-side file state —
no LLM in the ranking path; no impl-side store reads
(spec-side ranking is a spec-tier concern and impl-side
ranking is orchestrator-private, per
`SPECIFICATION/contracts.md` §"`/livespec:next` spec-side
thin-transport skill"; core performs no cross-side ranking
composition). The operation is exempt from the pre-step /
post-step doctor static lifecycle and has no LLM-driven
post-step phase per `SPECIFICATION/spec.md` §"Sub-command
lifecycle".

## When to run

- The user invokes the next operation, says "what should I
  work on next on the spec side", "what's the next spec
  move", or otherwise asks for the most ripe spec-side
  action against the current queue + history state.
- A composing loop driver (e.g. livespec's repo-local
  cross-repo orchestration driver — non-contract working
  tooling per `SPECIFICATION/spec.md` §"Contract + reference
  implementations architecture" → "No required cross-repo
  loop driver") calls this operation as one of the `next`
  primitives it composes (the other being the active
  orchestrator's own ranking surface).

## Inputs

The next CLI accepts only:

- `--spec-target <path>` (optional). Defaults to
  `<project-root>/SPECIFICATION/`. Selects the spec tree
  (main spec or a sub-spec under
  `<main-spec-root>/templates/<name>/`) to rank against.
- `--project-root <path>` (optional; defaults to
  `Path.cwd()`).
- `--limit <count>` (optional; positive integer, default
  `5`). Maximum number of candidates returned in the
  `candidates` array.
- `--offset <count>` (optional; non-negative integer,
  default `0`). Number of ranked candidates to skip from
  the front of the ranked list before returning.

No JSON payload input, no pre-step / post-step flags
(the operation is lifecycle-exempt). `--help` / `-h` is
honored at the CLI level via the `HelpRequested`
supervisor path; help text goes to stdout and exit code
is `0` (NOT an error).

## Steps

1. **Surface the loop-driver discoverability nudge.** On
   direct user invocation (the user invoked the next
   operation directly or asked for the next spec-side
   move in plain language), before invoking the
   CLI, surface a one-time nudge. The nudge MUST:

   - Inform the user that a cross-repo loop driver
     (when the project carries one — e.g. livespec's
     repo-local orchestration driver, which is
     non-contract working tooling) is the cohesive
     cross-side composition surface that combines
     spec-side `next` with the active orchestrator's
     own ranking surface.
   - Ask the user to confirm they want to run the
     spec-side next operation directly rather than via
     such a loop driver.

   SKIP the nudge when the next operation is invoked by
   another operation or composing driver (e.g. a loop
   driver itself, or the doctor surface) rather than by
   a direct user request. The detection mechanism is
   per-Driver; this prose simply gates the nudge on
   whether the entry path is a direct user invocation.

   The nudge is informational only — it points the
   user at the composition surface but never selects the
   cross-side weighting itself (core performs no
   cross-side ranking composition). The next CLI
   MUST NOT accrete any confirmation dialogue or opt-in
   flag; the nudge is prose-level discipline only.

2. **Invoke the next CLI.** Run the next CLI named in
   config with `[--spec-target <path>] [--project-root <path>]
   [--limit <count>] [--offset <count>]` and explicit argv.
   Capture stdout (the JSON payload) and the exit code.

3. **Present the JSON verbatim.** On exit `0`, surface
   the captured stdout to the user without
   re-interpretation, re-summarization, or judgment. The
   payload conforms to `next_output.schema.json` with two
   top-level keys: `candidates` (the ranked candidate
   array — each entry carrying `action`, `reason`,
   `urgency`, and optionally `target`; an empty array IS
   the no-work signal) and `pagination` (`offset`,
   `limit`, `total`, `has_more`); downstream consumers (a
   composing loop driver, automated tooling, or the user
   reading the recommendation) own the dispatch. This
   prose does NOT recommend a follow-up operation beyond
   what each candidate's `action` field already names.

This operation MUST NOT dispatch any template prompt, run
any post-step phase, or mutate spec-side state.

## Failure handling

CLI exit-code-to-narration mapping per
`SPECIFICATION/contracts.md` §"Lifecycle exit-code
table":

- Exit `0` → success. Surface the stdout JSON verbatim
  per Step 3.
- Exit `1` → internal bug; surface stderr (including
  any structured-error JSON line and traceback) and
  abort. Do NOT retry.
- Exit `2` → usage error (e.g., unknown flag,
  non-positive `--limit`, negative `--offset`). Restate
  the expected invocation shape per `## Inputs` above
  and abort.
- Exit `3` → `PreconditionError` (e.g.,
  `--spec-target` does not exist or is not a directory,
  malformed proposed-change front-matter). Surface the
  stderr findings and direct the user to the corrective
  action. NOT retryable.
- Exit `127` → too-old Python or missing tool; surface
  the install instruction from stderr and abort.

Exit `4` is N/A for this operation (no LLM-provided
JSON payload to schema-validate).
