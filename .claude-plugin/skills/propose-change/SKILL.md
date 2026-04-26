---
name: propose-change
description: File a proposed change against an existing livespec specification, landing it under <spec-root>/proposed_changes/<topic>.md. Invoked by /livespec:propose-change, "propose a change to the spec", or when the user wants to record a spec amendment that the next /livespec:revise pass will accept or reject.
allowed-tools: Bash, Read, Write
---

# propose-change

File a structured proposed-change file under
`<spec-target>/proposed_changes/<topic>.md` based on a user-
provided intent. The wrapper validates the LLM-emitted findings
JSON and writes the resulting file.

## When to invoke

- The user types `/livespec:propose-change`, says "propose a
  change", "file a propose-change", or asks to author a
  proposed change against an existing seeded spec tree.
- The repo has a valid `.livespec.jsonc` and a populated
  `SPECIFICATION/` (or template-declared spec_root).

## Inputs

- The wrapper accepts `<topic>` (positional, required;
  canonical kebab-case) and `--findings-json <path>` (required) —
  a JSON payload conforming to
  `proposal_findings.schema.json`.
- `--spec-target <path>` (optional; defaults to the main spec
  root via `.livespec.jsonc` upward walk). Per v018 Q1, may
  point at a sub-spec tree under
  `<main-spec-root>/templates/<name>/` to route the proposal
  there.
- `--author <id>` (optional; CLI overrides env override
  payload; falls back to `unknown-llm`).
- `--project-root <path>` (optional; defaults to cwd).

## Steps

1. **Resolve the active template.** Invoke
   `bin/resolve_template.py` (no `--template` flag — uses
   `.livespec.jsonc` upward walk) via Bash. Capture the
   resolved template path from stdout.

2. **Read the propose-change prompt.** Use Read on
   `<resolved-path>/prompts/propose-change.md`.

3. **Capture user intent.** Ask the user: "What change do you
   want to propose? Briefly describe the intent." Capture
   free-text intent.

4. **Pick or derive a topic.** Ask the user: "What canonical
   kebab-case topic should this proposal use? (lowercase,
   hyphens, length ≤ 64; e.g., `auth-redirect-fix`)." Phase 3
   minimum-viable rejects non-canonical topics with exit 4;
   help the user pick a canonical value before invoking the
   wrapper.

5. **Generate findings JSON.** Run the propose-change prompt
   against the user intent. The prompt MUST emit JSON
   conforming to `proposal_findings.schema.json`: a top-level
   `findings[]` array, each entry carrying `name`,
   `target_spec_files`, `summary`, `motivation`, and
   `proposed_changes` fields.

6. **Write payload to temp file.** Use the Write tool to write
   the generated JSON to a temp file.

7. **Invoke the wrapper.** Run
   `bin/propose_change.py <topic> --findings-json <tempfile>`
   via Bash, with optional `--author` / `--spec-target` /
   `--project-root` flags as appropriate.

8. **Retry-on-exit-4.** On exit 4 (schema validation failed,
   OR Phase-3 "topic not canonical" rejection), surface the
   error from stderr, re-invoke the prompt with error context,
   and re-assemble corrected JSON. Retry 1-2 times before
   asking the user.

## Post-wrapper

On exit 0, the wrapper wrote
`<spec-target>/proposed_changes/<topic>.md`. Post-step
doctor-static then runs (see `doctor/SKILL.md`).

## Failure handling

- Exit `0` → proceed to post-wrapper.
- Exit `1` → internal bug; surface stderr and abort.
- Exit `2` → usage error; restate invocation and abort.
- Exit `3` → precondition (e.g., collision: a file with this
  topic already exists). Surface the `PreconditionError`
  message and direct the user to pick a different topic or
  delete the existing file.
- Exit `4` → schema-validation failure or non-canonical topic;
  retryable per step 8.
- Exit `127` → too-old Python or missing tool; surface install
  instruction and abort.

## Phase 3 minimum-viable scope

This bootstrap prose is narrower than PROPOSAL.md
§"Per-sub-command SKILL.md body structure" intends. Out of
Phase-3 scope (Phase 7 widens):
- Topic canonicalization (silent canonicalization vs Phase-3's
  reject-with-exit-4).
- Reserve-suffix canonicalization (`-critique`, `-doctor` etc.).
- Full author-precedence chain (payload-author lookup).
- Collision disambiguation prompts (v014 N6 monotonic suffix).
