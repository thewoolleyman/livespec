---
name: refresh-gaps
description: Compare the current SPECIFICATION/ tree against this repository's implementation, tests, tooling, and workflow state, then write the current implementation-gap report to implementation-gaps/current.json. Read-only with respect to SPECIFICATION/. Does NOT create or close beads issues. Invoked by /livespec-implementation:refresh-gaps, "refresh implementation gaps", or as the verification step before any beads issue is closed with resolution:fix.
---

# refresh-gaps

You are running the gap-discovery skill for the repo-local
`livespec-implementation` workflow. Your job is to walk the spec
and the repo, find every place where they diverge, and serialise
the diff into `implementation-gaps/current.json` per the schema at
`implementation-gaps/current.schema.json`.

## Spec contract (verbatim)

From `SPECIFICATION/non-functional-requirements.md` §Spec
§"Repo-local implementation workflow":

> `refresh-gaps` — compares the current `SPECIFICATION` against
> this repository's implementation, tests, tooling, and workflow
> state, then writes the current implementation-gap report to
> `implementation-gaps/current.json`. This skill is read-only with
> respect to `SPECIFICATION/`; it MUST NOT edit specs and MUST
> NOT create or close beads issues.

## Hard rules

- Read-only on `SPECIFICATION/`. NEVER edit any file under there.
- Read-only on beads. NEVER call `bd create`, `bd close`,
  `bd update`, `bd dep`, or any other bd write operation. Read
  operations (`bd show --json`, `bd ready --json`) are fine when
  needed to compare against existing tracked issues.
- The output `implementation-gaps/current.json` MUST validate
  against `implementation-gaps/current.schema.json`. Run
  `just implementation::check-gaps` after writing.

## Manual fallback (current state)

The Python automation at
`dev-tooling/implementation/refresh_gaps.py` is itself a tracked
implementation gap and may not exist at the time you read this.
When it doesn't exist, run the skill manually:

1. Read every file under `SPECIFICATION/` (plus
   `non-functional-requirements.md`).
2. For each architectural rule, contract, or constraint in the
   spec, verify the corresponding implementation, test, or config
   exists in the repo at the location the spec implies.
3. For each divergence, draft a `gaps[]` entry with: a
   monotonically-numbered `id` (`gap-NNNN`), `area`, `severity`,
   `priority`, `title`, `spec_refs` (file + section anchor),
   `expected`, `observed`, `evidence`, `evidence_kind`,
   `destructive_to_fix`, `destructive_reason`, `fix_hint`,
   `depends_on`. Per the schema at
   `implementation-gaps/current.schema.json`.
4. Write the assembled report to
   `implementation-gaps/current.json` with `schema_version`,
   `generated_at` (UTC ISO-8601), `spec_sources` (git blob hashes
   of the spec files read), `inspection` metadata, the `gaps[]`
   array, and aggregate `summary` counts.
5. Run `just implementation::check-gaps` to confirm schema
   conformance.

When verifying a previously-fixed gap as part of an `implement`
close, use the SAME steps — run refresh-gaps, then confirm the
gap-id no longer appears in `current.json.gaps[].id`. If it
still appears, the fix is not complete and the beads issue MUST
NOT be closed with `--resolution fix`.

## Pattern source

Open Brain's `update-specification-drift` skill is the canonical
reference for the gap-discovery workflow. Differences:
- Output filename: `current.json` (livespec) vs.
  `current-specification-drift.json` (Open Brain).
- Issue prefix: `li-` (livespec) vs. `ob-` (Open Brain).
