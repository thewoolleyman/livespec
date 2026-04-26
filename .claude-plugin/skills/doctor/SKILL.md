---
name: doctor
description: Run the static-phase doctor checks against a livespec spec tree, surfacing structural failures (missing files, version-contiguity gaps, out-of-band edits, malformed front matter, etc.) as JSON findings. Invoked by /livespec:doctor, "run livespec doctor", or "check the spec for invariants".
allowed-tools: Bash, Read
---

# doctor

Phase 3 minimum-viable: covers ONLY the static-phase invocation.
The static phase enumerates `(spec_root, template_name)` pairs
(main spec + each sub-spec under `templates/<name>/`) and runs
the registered checks per the orchestrator-owned applicability
table, emitting `{"findings": [...]}` JSON to stdout.

The LLM-driven post-step phases (objective + subjective checks)
are deferred — Phase 7 adds the LLM orchestration per the
`skill-md-prose-authoring` deferred-items entry.

## When to invoke

- The user types `/livespec:doctor`, says "run doctor", "check
  the spec", or asks to verify spec invariants.
- The skill is also invoked automatically as the post-step of
  `seed`, `propose-change`, `critique`, and `revise` (with
  exit 3 surfacing fail Findings to the user).

## Inputs

- `--project-root <path>` (optional; defaults to cwd).

The wrapper has no JSON input; it reads `.livespec.jsonc` from
disk via the upward walk and discovers sub-spec trees by
listing `<main-spec-root>/templates/<name>/`.

## Steps

1. **Invoke the wrapper.** Run
   `bin/doctor_static.py [--project-root <path>]` via Bash.
   Capture stdout (the findings JSON) and exit code.

2. **Parse findings.** Use Read or Bash (`cat`) to inspect the
   stdout JSON: a `{"findings": [...]}` object where each
   finding carries `check_id`, `status` (`pass`/`fail`/
   `skipped`), `message`, optional `path`, optional `line`,
   and `spec_root` (the per-tree origin marker per v018 Q1).

3. **Surface findings.** Group findings by `spec_root` and
   present them to the user:
   - "main" tree findings first.
   - Each sub-spec tree's findings under its own heading.
   - Highlight any `fail` status entries; describe the
     corrective action implied by the message.

4. **Bootstrap-lenience handling (v014 N3).** When
   `livespec_jsonc_valid` returns `skipped` (because
   `.livespec.jsonc` is absent), narrate it as "the project
   has no `.livespec.jsonc` — defaults apply" rather than
   surfacing as a problem.

## Post-wrapper

No post-step LLM-driven phase in Phase 3 minimum-viable.
Phase 7 widens with two post-step phases (objective + subjective
checks), each gated by `--skip-doctor-llm-objective-checks` /
`--skip-doctor-llm-subjective-checks` flags and the
corresponding `.livespec.jsonc` config keys.

## Failure handling

- Exit `0` → all findings are `pass` or `skipped` (no `fail`).
  Surface the findings and proceed.
- Exit `1` → internal bug; surface stderr (including
  traceback) and abort.
- Exit `2` → usage error; restate invocation and abort.
- Exit `3` → at least one fail Finding. Surface ALL findings
  grouped by `spec_root`; emphasize the failures; describe
  corrective actions.
- Exit `127` → too-old Python or missing tool; surface install
  instruction and abort.

## Phase 3 minimum-viable scope

Out of Phase-3 scope (Phase 7 widens):
- LLM-driven objective-checks phase (skill-baked checks +
  template-extension checks via `template.json`'s
  `doctor_llm_objective_checks_prompt` field).
- LLM-driven subjective-checks phase (NLSpec conformance, prose
  quality, spec↔implementation drift).
- The four checks not yet registered: `out_of_band_edits`,
  `bcp14_keyword_wellformedness`, `gherkin_blank_line_format`,
  `anchor_reference_resolution`.
- `--skip-pre-check` / `--run-pre-check` flag pair (this is
  doctor; it IS the static phase).
- LLM-finding-to-critique conversion prompt (the user-prompt
  flow that converts an LLM-driven finding into a
  `critique`-filed proposed-change).
