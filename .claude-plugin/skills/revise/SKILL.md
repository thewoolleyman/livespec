---
name: revise
description: Walk the user through accepting or rejecting each pending proposed change in <spec-root>/proposed_changes/, then snapshot the result as a new <spec-root>/history/vNNN/ revision. Invoked by /livespec:revise, "revise the livespec", or "process pending proposed changes".
allowed-tools: Bash, Read, Write
---

# revise

Drive per-proposal accept/modify/reject decisions for the
pending proposed-changes under `<spec-target>/proposed_changes/`,
then cut a new `<spec-target>/history/vNNN/` snapshot via the
wrapper.

## When to invoke

- The user types `/livespec:revise`, says "revise the spec",
  "process pending proposed changes", or asks to advance the
  spec to a new version.
- `<spec-target>/proposed_changes/` is non-empty (otherwise
  the wrapper exits 3).

## Inputs

- The wrapper accepts `--revise-json <path>` (required) — a
  JSON payload conforming to `revise_input.schema.json`.
- `--author <id>` (optional; CLI overrides env override
  payload; falls back to `unknown-llm`).
- `--spec-target <path>` (optional; defaults to the main spec
  root via `.livespec.jsonc`).
- `--project-root <path>` (optional; defaults to cwd).

## Steps

1. **Resolve the active template.** Invoke
   `bin/resolve_template.py` via Bash; capture the resolved
   path from stdout.

2. **Read the revise prompt.** Use Read on
   `<resolved-path>/prompts/revise.md`.

3. **Enumerate proposed-changes.** Use Read or Bash (`ls`) to
   list `<spec-target>/proposed_changes/*.md`. Skip
   `README.md` and any file ending in `-revision.md` (those
   are revision pairings from prior cycles, not in-flight
   proposals).

4. **Optional steering intent.** Ask the user (optional):
   "Any steering intent for this revise pass? (e.g., 'reject
   anything touching the auth section') — leave blank to let
   the LLM decide each proposal independently."

5. **Per-proposal decisions.** For each proposed-change file
   (in `created_at` front-matter order with lexicographic
   filename fallback):
   - Run the revise prompt with the proposed-change content +
     current spec content + optional steering intent.
   - The LLM proposes an `accept`, `modify`, or `reject`
     decision with rationale, plus (for accept/modify)
     `resulting_files` containing the updated spec content.
   - Present each per-proposal decision to the user; capture
     confirm / override.
   - The user MAY toggle "delegate remaining proposals to the
     LLM" — once set, auto-accept the LLM's decisions for all
     remaining proposals across all remaining files.

6. **Assemble revise-json payload.** Compose the JSON
   conforming to `revise_input.schema.json`:
   - `author` (optional; LLM self-declaration).
   - `decisions[]` — one entry per proposed-change file, each
     with `proposal_topic`, `decision`, `rationale`, optional
     `modifications` (for `modify`), and optional
     `resulting_files[]` (for `accept`/`modify`).

7. **Write payload to temp file.** Use the Write tool.

8. **Invoke the wrapper.** Run
   `bin/revise.py --revise-json <tempfile>` via Bash, with
   optional `--author` / `--spec-target` / `--project-root`
   flags as appropriate.

9. **Retry-on-exit-4.** On exit 4 (schema validation), surface
   the error from stderr, re-assemble the payload (or
   re-prompt the LLM with error context), and re-invoke.
   Retry 1-2 times before asking the user.

## Post-wrapper

On exit 0, the wrapper has:
- Cut a new `<spec-target>/history/vNNN/` (incrementing past
  the highest existing vNNN).
- Moved each processed proposed-change file into
  `<spec-target>/history/vNNN/proposed_changes/<topic>.md`
  (byte-identical) and written the paired
  `<topic>-revision.md`.
- Applied any `accept`/`modify` `resulting_files[]` updates
  to the working spec files in place.
- Snapshotted the post-update spec files into
  `<spec-target>/history/vNNN/<filename>` for each `.md`
  spec file at the spec root.

`<spec-target>/proposed_changes/` is now empty (of in-flight
proposals; the skill-owned `README.md` persists). Post-step
doctor-static then runs (see `doctor/SKILL.md`).

## Failure handling

- Exit `0` → proceed to post-wrapper.
- Exit `1` → internal bug; surface stderr and abort.
- Exit `2` → usage error; restate invocation and abort.
- Exit `3` → precondition (e.g., proposed_changes/ is empty;
  history/ has gaps; required spec files missing). Surface
  the `PreconditionError` and direct the user.
- Exit `4` → schema-validation; retryable per step 9.
- Exit `127` → too-old Python or missing tool; surface
  install instruction and abort.

## Phase 3 minimum-viable scope

Out of Phase-3 scope (Phase 7 widens):
- LLM-driven per-proposal decision flow with delegation
  toggle (full PROPOSAL §"revise" interactive flow).
- Richer rejection-flow audit-trail content.
- Per-version README for templates whose versioned surface
  defines one.
- v014 N6 collision-suffix filename handling.
