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
- `work-breakdown.md` — **OPEN, actively iterating.** The human-led
  front-end decomposition step: how a maintainer breaks/splits work
  into manageable, factory-feedable chunks BEFORE autonomous dispatch
  (at capture or in a grooming pass). Captures the durable 2026-06-16
  deep research (verified patterns + the unsolved sizing gap + refuted
  claims), a **2026-06-19 round-2 pass** resolving the named-but-absent
  shops (Stripe minions / Cursor / Factory.ai / Fabro / Dan Shapiro / —
  Remy unresolved; agent-drafts/human-approves is the field's only ritual,
  and still no quantitative sizing cut-point), the **2026-06-19 reframe**
  (cross-repo is a category error;
  the functional/non-functional split is the spine; grooming is
  Orchestrator-internal — non-functional core guidance + reference-
  orchestrator-spec realization, never a core skill), and three pieces:
  **the slice cut-line** (two-mode "done": scenario-verified OR
  gate-verified; plus a slice-size floor), **the grooming ritual** (intake
  checklist + optional regroom pass; agent-drafts/human-approves), and
  **slice-size calibration** (invent + instrument ceiling AND floor). The
  user flagged this as the largest open unknown in the ecosystem —
  expect multi-session iteration.

## Conventions

Documents here are DRAFT until the user ratifies them; ratified
decisions flow into ledger work-items (filed by the orchestrator from
the doc's proposed one-liners) and, where durable, into the spec via
`/livespec:propose-change` → `/livespec:revise`. Per `research/CLAUDE.md`,
nothing here is spec content or load-bearing on its own.
