---
name: critique
description: Critique an existing livespec specification or a pending proposed change, surfacing ambiguities, contradictions, and missing rules as findings the user can act on. Invoked by /livespec:critique, "critique the livespec spec", or "find issues in the spec".
allowed-tools: Bash, Read, Write
---

# critique

File a critique-style proposed-change against an existing spec
tree. Internally delegates to `propose-change` with the
`-critique` reserve-suffix appended to the topic.

## When to invoke

- The user types `/livespec:critique`, says "critique the
  spec", "find issues in the spec", or asks to file a critique.
- The repo has a valid `.livespec.jsonc` and a populated spec
  tree.

## Inputs

- `<topic>` (positional, required; canonical kebab-case — the
  wrapper appends `-critique`).
- `--findings-json <path>` (required) — a JSON payload
  conforming to `proposal_findings.schema.json` (same schema
  propose-change uses).
- `--author <id>` (optional; same precedence as
  propose-change).
- `--spec-target <path>` (optional; same default as
  propose-change).
- `--project-root <path>` (optional; defaults to cwd).

## Steps

1. **Resolve the active template.** Invoke
   `bin/resolve_template.py` via Bash; capture the resolved
   path from stdout.

2. **Read the critique prompt.** Use Read on
   `<resolved-path>/prompts/critique.md`.

3. **Capture critique target.** Ask the user: "What do you
   want critiqued? Describe the spec area or proposed-change
   you want to surface findings against."

4. **Pick or derive a topic.** Ask the user for a canonical
   kebab-case topic. The wrapper will append `-critique`
   automatically (e.g., `auth-redirect` → filename
   `auth-redirect-critique.md`).

5. **Generate findings JSON.** Run the critique prompt against
   the user-provided target. The prompt MUST emit JSON
   conforming to `proposal_findings.schema.json` — same shape
   as propose-change, but the findings should describe
   ambiguities / contradictions / missing rules rather than
   new behavior.

6. **Write payload to temp file.** Use the Write tool.

7. **Invoke the wrapper.** Run
   `bin/critique.py <topic> --findings-json <tempfile>` via
   Bash. The wrapper internally invokes `propose_change.run()`
   with the topic + reserve-suffix; the resulting file lands
   at `<spec-target>/proposed_changes/<topic>-critique.md`.

8. **Retry-on-exit-4.** Same pattern as propose-change.

## Post-wrapper

On exit 0, the wrapper wrote
`<spec-target>/proposed_changes/<topic>-critique.md`.
Post-step doctor-static then runs.

## Failure handling

Same as propose-change (exit 0/1/2/3/4/127 mapping; exit 4 is
retryable, exit 3 is not).

## Phase 3 minimum-viable scope

Out of Phase-3 scope (Phase 7 widens):
- Full reserve-suffix canonicalization algorithm (v016 P3 /
  v017 Q1): truncation-aware insertion, pre-attached-suffix
  detection. Phase 3 appends `-critique` verbatim.
- LLM-driven critique flow with delegation toggle.
