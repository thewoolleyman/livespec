---
name: livespec-implementation-beads:refresh-gaps
description: Compare the current SPECIFICATION/ tree against this repository's implementation, tests, tooling, and workflow state, then write the current implementation-gap report to implementation-gaps/current.json. Read-only with respect to SPECIFICATION/. Does NOT create or close beads issues. Invoked by /livespec-implementation-beads:refresh-gaps, "refresh implementation gaps", or as the verification step before any beads issue is closed with resolution:fix.
---

# refresh-gaps

You are running the gap-discovery skill for the repo-local
`livespec-implementation` workflow. Your job is to walk the spec
and the repo, find every place where they diverge, and serialise
the diff into `implementation-gaps/current.json` per the schema
at `implementation-gaps/current.schema.json`.

## Spec contract (verbatim)

From `SPECIFICATION/non-functional-requirements.md` §Spec
§"Repo-local implementation workflow":

> `refresh-gaps` — compares the current `SPECIFICATION` against
> this repository's implementation, tests, tooling, and workflow
> state, then writes the current implementation-gap report to
> `implementation-gaps/current.json`. This skill is read-only
> with respect to `SPECIFICATION/`; it MUST NOT edit specs and
> MUST NOT create or close beads issues.

## Hard rules

- **Read-only on `SPECIFICATION/`.** NEVER edit any file under
  there. Findings about spec drift become entries in
  `current.json`; they do NOT translate into edits.
- **Read-only on beads.** NEVER call `bd create`, `bd close`,
  `bd update`, `bd dep`, or any other bd write operation. Read
  operations (`bd show --json`, `bd ready --json`,
  `bd list --json`) are fine when needed to compare against
  existing tracked issues.
- **Schema-conforming output.** `implementation-gaps/current.json`
  MUST validate against
  `implementation-gaps/current.schema.json`. The Python
  automation runs `fastjsonschema.compile(schema)(report)`
  before writing; manual runs MUST mirror that — run
  `just implementation::check-gaps` after every write.

## Canonical invocation

```
just implementation::refresh-gaps
```

Equivalent direct invocation:

```
uv run python3 dev-tooling/implementation/refresh_gaps.py
```

The script reads the five `SPECIFICATION/` files, computes each
file's git blob SHA1 fingerprint, evaluates a hardcoded registry
of gap-detection predicates against the current repo state,
assembles a JSON report, validates the result against the
schema, and writes it to `implementation-gaps/current.json`. A
fresh `run_id` UUID is assigned per invocation; the timestamp
in `generated_at` reflects the start of the report build.

Per-gap static fields (id, area, severity, title, expected,
observed, evidence, etc.) live in
`dev-tooling/implementation/gap_blueprints.json`. The Python
registry maps each gap id to its presence-predicate; a new gap
is added by appending a blueprint entry and registering a
predicate in `_PRESENCE_PREDICATES`.

## Verifying a closed gap

When the `implement` skill is about to close a gap-tied issue
with `--resolution fix`, the
`SPECIFICATION/non-functional-requirements.md` §Constraints
close-with-audit-fields rule REQUIRES a fresh refresh-gaps
run that confirms the gap-id no longer appears in
`current.json.gaps[].id`. The implement automation does this
via subprocess; if running by hand, the steps are:

1. Run the canonical invocation above.
2. Capture the `run_id` and `generated_at` from the resulting
   `current.json` (`inspection.run_id` and `generated_at`
   fields).
3. Read `current.json.gaps[]` and confirm the target gap-id is
   absent.
4. If absent: feed `run_id` + `generated_at` into the audit
   notes the close requires.
5. If present: the fix is incomplete; do NOT close the issue.

## Output shape

The report shape is locked by
`implementation-gaps/current.schema.json`. Top-level fields:

| Field | Purpose |
| --- | --- |
| `schema_version` | `1`; bumped only on incompatible shape change. |
| `generated_at` | UTC ISO-8601 timestamp at report-build time. |
| `spec_sources` | Per-spec-file path + git blob SHA1 fingerprint. |
| `inspection` | `scopes_inspected`, `scopes_skipped`, `run_id`, `inspection_method`. |
| `gaps` | Array of per-gap entries (see schema `$defs.Gap`). |
| `summary` | Aggregate `by_area` / `by_severity` / `by_status` counts. |

Per-gap fields are documented in the schema; the most
load-bearing for downstream skills are `id` (drives the
`gap-id:gap-NNNN` beads label) and `depends_on` (drives the
`bd dep add` edges plan creates).

## Pattern source

Open Brain's `update-specification-drift` skill is the
canonical reference for the gap-discovery workflow.
Differences:

- Output filename: `current.json` (livespec) vs.
  `current-specification-drift.json` (Open Brain).
- Issue prefix: `li-` (livespec) vs. `ob-` (Open Brain).

## When NOT to invoke

- During `implement` work for an unrelated gap — refresh-gaps
  rewrites the entire report, so an in-flight unrelated change
  could spuriously appear or disappear from the report
  mid-implement. Run refresh-gaps as the verification step at
  close time, not during the work.
- Before reading the existing report — if the existing
  `current.json` is recent enough for your purpose, prefer
  reading it over re-running.
