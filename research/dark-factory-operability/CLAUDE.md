# research/dark-factory-operability/

Design artifacts for the operability preconditions that must hold
before the W6 dark-factory cutover — the point where the Beads+Fabro
Dispatcher runs unattended and `/livespec-orchestrate` (livespec
`a8bb`) retires.

## What lives here

- `preconditions.md` — the livespec-0jxs design pass: the
  minimal-operability trio (failure notification, spend ceiling,
  telemetry shipping) as an explicit cutover precondition, the
  pre-gate vs post-gate sequencing correction, and the a8bb
  duty-relocation table (relocate-never-drop applied to
  responsibilities).

## Conventions

Documents here are DRAFT until the user ratifies them; ratified
decisions flow into ledger work-items (filed by the orchestrator from
the doc's proposed one-liners) and, where durable, into the spec via
`/livespec:propose-change` → `/livespec:revise`. Per `research/CLAUDE.md`,
nothing here is spec content or load-bearing on its own.
