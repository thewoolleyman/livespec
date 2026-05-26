---
name: next
description: Rank the next spec-side action (revise, propose-change, critique, prune-history, or none) over the current `<spec-target>/proposed_changes/` and `<spec-target>/history/` state, emitting structured JSON. Invoked by /livespec:next, "what should I work on next on the spec side", or as a Layer 3 loop-driver primitive.
allowed-tools: Bash
---

# next

Thin-transport skill per `SPECIFICATION/contracts.md`
§"Thin-transport skill doctrine". Invokes
`bin/next.py` and presents its stdout JSON verbatim;
all ranking, urgency, and threshold logic lives in the
Python wrapper. The skill body MUST NOT accrete logic.

The wrapper is a pure function of spec-side file state —
no LLM in the ranking path; no impl-side store reads
(cross-side composition is the project-local Layer 3
loop driver's job per `SPECIFICATION/spec.md`
§"Three-layer orchestration architecture"). The skill is
exempt from the pre-step / post-step doctor static
lifecycle and has no LLM-driven post-step phase per
`SPECIFICATION/spec.md` §"Sub-command lifecycle".

## When to invoke

- The user types `/livespec:next`, says "what should I
  work on next on the spec side", "what's the next spec
  move", or otherwise asks for the most ripe spec-side
  action against the current queue + history state.
- The project-local Layer 3 loop driver
  (`.claude/skills/loop/SKILL.md`) calls this skill as
  one of two `next` primitives it composes (the other
  being the active impl-plugin's `next`).

## Inputs

The wrapper `bin/next.py` accepts only:

- `--spec-target <path>` (optional). Defaults to
  `<project-root>/SPECIFICATION/`. Selects the spec tree
  (main spec or a sub-spec under
  `<main-spec-root>/templates/<name>/`) to rank against.
- `--project-root <path>` (optional; defaults to
  `Path.cwd()`).

No JSON payload input, no pre-step / post-step flags
(the skill is lifecycle-exempt). `--help` / `-h` is
honored at the wrapper level via the `HelpRequested`
supervisor path; help text goes to stdout and exit code
is `0` (NOT an error).

## Steps

1. **Surface the Layer 3 discoverability nudge.** On
   direct user invocation (the user typed
   `/livespec:next` or asked for the next spec-side
   move in plain language), before invoking the
   wrapper, surface a one-time nudge per
   `SPECIFICATION/contracts.md` §"`/livespec:next`
   spec-side thin-transport skill" → §"Layer 3
   discoverability nudge". The nudge MUST:

   - Inform the user that
     `.claude/skills/loop/SKILL.md` (the project-local
     Layer 3 loop driver per `spec.md`
     §"Three-layer orchestration architecture" →
     "Layer 3 — Project-local composition") is the
     cohesive cross-side composition surface that
     combines `/livespec:next` with the active
     impl-plugin's `next`.
   - Ask the user to confirm they want to run
     `/livespec:next` directly rather than via the
     project's Layer 3 driver.

   SKIP the nudge when `/livespec:next` is invoked by
   another skill (e.g., the Layer 3 driver itself, the
   `doctor` cross-boundary surface) rather than by a
   direct user request. The detection mechanism is
   per-harness; this skill simply gates the nudge on
   whether the entry path is a direct user invocation.

   When `.claude/skills/loop/SKILL.md` is absent in the
   current project (the file is OPTIONAL per `spec.md`
   §"Layer 3 — Project-local composition"), the nudge
   MAY soften to a documentation pointer (e.g.,
   "consider authoring a Layer 3 loop driver per
   `spec.md` §...") rather than being suppressed. The
   discoverability discipline applies whenever direct
   user invocation is the entry path, regardless of
   whether the driver exists.

   The nudge is informational only — it points the
   user at the Layer 3 surface but never selects the
   cross-side weighting itself, preserving the
   §"Cross-side composition exclusion" invariant. The
   wrapper at `bin/next.py` MUST NOT accrete any
   confirmation dialogue or opt-in flag; the nudge is
   SKILL.md-prose discipline only.

2. **Invoke the wrapper.** Run
   `bin/next.py [--spec-target <path>] [--project-root <path>]`
   via the Bash tool. Capture stdout (the JSON payload)
   and exit code.

3. **Present the JSON verbatim.** On exit `0`, surface
   the captured stdout to the user without
   re-interpretation, re-summarization, or judgment. The
   payload conforms to `next_output.schema.json` with
   fields `action`, `reason`, and `urgency`; downstream
   consumers (the Layer 3 loop driver, automated
   tooling, or the user reading the recommendation) own
   the dispatch. The skill body does NOT recommend a
   follow-up sub-command beyond what the `action` field
   already names.

This skill MUST NOT dispatch any template prompt, run
any post-step phase, or mutate spec-side state.

## Failure handling

Wrapper exit-code-to-narration mapping per
`SPECIFICATION/contracts.md` §"Lifecycle exit-code
table":

- Exit `0` → success. Surface the stdout JSON verbatim
  per Step 3.
- Exit `1` → internal bug; surface stderr (including
  any structured-error JSON line and traceback) and
  abort. Do NOT retry.
- Exit `2` → usage error (e.g., unknown flag). Restate
  the expected invocation shape per `## Inputs` above
  and abort.
- Exit `3` → `PreconditionError` (e.g.,
  `--spec-target` does not exist or is not a directory,
  malformed proposed-change front-matter). Surface the
  stderr findings and direct the user to the corrective
  action. NOT retryable.
- Exit `127` → too-old Python or missing tool; surface
  the install instruction from stderr and abort.

Exit `4` is N/A for this sub-command (no LLM-provided
JSON payload to schema-validate).
