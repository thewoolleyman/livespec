---
topic: behavior-clause-scenario-link-contract
author: guardrail-1a
created_at: 2026-06-19T19:22:33Z
---

## Proposal: Behavior-clause-to-scenario link contract

### Target specification files

- SPECIFICATION/constraints.md
- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/spec.md
- SPECIFICATION/scenarios.md

### Summary

Codify the clause-to-scenario link mechanism (Guardrail #1a) already shipped as the shared dev-tooling/spec_clauses.py extractor and the dev-tooling/checks/behavior_scenario_link.py advisory check: extend the tests/heading-coverage.json registry with an optional clauses[] array linking a behavior clause's gap-id to the scenarios.md H2 section that exercises it; make the behavior_scenario_link check always-wired and always-running with a self-documenting warn|fail severity lever; extend the §Self-application co-edit discipline so a behavior clause and its clauses[] link stay in lockstep; and add the acceptance scenario for the check.

### Motivation

A grooming-realization spec-writing failure (descriptive prose that the mechanical gap-detector could not see) showed that load-bearing behavior needs a mechanical clause-to-scenario binding, not author vigilance. The shared gap-id primitive and the advisory check are already on master; this proposal makes their contract durable in the spec, advisory-first (warn) while the link backlog is backfilled, and makes the §Self-application co-edit discipline cover the clause-to-scenario map the same way it already covers the heading-to-test map.

### Proposed Changes

This proposal codifies behavior already shipped on master (the shared `dev-tooling/spec_clauses.py` extractor + gap-id primitive, and the `dev-tooling/checks/behavior_scenario_link.py` advisory check). Per the §"Authoring discipline — three splits" rule in `prose/propose-change.md`, every load-bearing behavior below is stated as a BCP14 `MUST`/`SHOULD` clause AND backed by the new scenarios.md scenario; the prose is augmentation only.

--- 1. `constraints.md` §"Heading taxonomy" — extend the registry contract with the optional `clauses[]` array ---

Add, after the existing paragraph that defines the `(spec_root, spec_file, heading)` → `test` registry entry shape, a new paragraph:

> A registry entry MAY additionally carry an OPTIONAL `clauses` array binding individual behavior clauses under its heading to the scenarios that exercise them. Each `clauses[]` element is an object `{"gap_id": "<gap-id>", "scenario": "<scenarios.md H2 section name>"}`. The `gap_id` MUST be the stable identifier the shared `dev-tooling/spec_clauses.py` extractor derives for the clause (the first 8 lowercase-base32 characters of `sha256(spec_file \x1f heading_path \x1f rule_text)`). The `scenario` value MUST name a live `scenarios.md` H2 section heading, written with or without the leading `## `; a `scenario` that does not resolve to a live `scenarios.md` H2 section does NOT count as a link. The `clauses` array is OPTIONAL and backward-compatible: an entry without it is unchanged, and the `heading_coverage` check ignores the key. The `clauses[]` link is consumed by the `behavior_scenario_link` check (see `non-functional-requirements.md`).

--- 2. `non-functional-requirements.md` — the `behavior_scenario_link` check and its severity lever ---

Add a new `## Behavior-clause-to-scenario link check` section (enforcement-suite behavior; contributor-only concern per the §Boundary litmus):

> The `behavior_scenario_link` enforcement-suite check extracts every `MUST` / `MUST NOT` / `SHOULD` / `SHOULD NOT` behavior clause from the live core spec's behavior-bearing files via the shared `dev-tooling/spec_clauses.py` extractor, derives each clause's gap-id, and surfaces every clause whose gap-id has no `clauses[]` link to a live `scenarios.md` H2 section in `tests/heading-coverage.json`.
>
> The check MUST be always-wired into the `just check` aggregate and always-running; it MUST NOT be silently skipped. Its severity is governed by a self-documenting per-check lever, the `LIVESPEC_BEHAVIOR_SCENARIO_LINK` environment variable, whose only recognized values are `warn` and `fail`. In `warn` mode (the DEFAULT) the check MUST surface each unlinked behavior clause as a warning and exit 0 — advisory while the clause-to-scenario backlog is backfilled. In `fail` mode the check MUST surface each unlinked behavior clause as an error and exit non-zero. An unset or unrecognized lever value MUST default to `warn`. The lever is the SEVERITY switch, NOT a wiring carve-out: the check always extracts every clause and always runs regardless of the lever (per the carve-out-is-a-severity-lever-not-an-invariant-relax discipline).

--- 3. `spec.md` §"Self-application" — extend the co-edit discipline to clause links ---

Add, after the existing paragraph requiring `tests/heading-coverage.json` heading co-edits, a new paragraph:

> The same co-edit discipline extends to behavior-clause links: every revise pass that adds, changes, or removes a load-bearing behavior clause (a `MUST` / `SHOULD` line) in a behavior-bearing spec file MUST also maintain that clause's `clauses[]` link in `tests/heading-coverage.json` via the same `resulting_files[]` mechanism — adding the link for a new clause, dropping it for a removed clause, and re-deriving the gap-id when the clause text or its heading path changes — so the clause-to-scenario map stays in lockstep with the spec.

--- 4. `scenarios.md` — acceptance scenario for the check ---

Add a new Gherkin scenario H2 section:

> ## Behavior clause lacking a scenario link is surfaced
>
> ```gherkin
> Given a behavior-bearing core spec file carries a MUST/SHOULD clause
>   And that clause's gap-id has no clauses[] link to a live scenarios.md H2 section in tests/heading-coverage.json
> When the behavior_scenario_link check runs
> Then in warn mode it emits a behavior-scenario-link-unlinked warning for the clause and exits 0
>   And in fail mode (LIVESPEC_BEHAVIOR_SCENARIO_LINK=fail) it emits the error and exits non-zero
> ```

This scenario is the acceptance for the `behavior_scenario_link` check; at revise time it maps to `tests.dev-tooling.checks.test_behavior_scenario_link` (an integration-tier subprocess test of the check) in `tests/heading-coverage.json`.

--- Self-application compliance ---

The new behavior clauses introduced by parts 1-3 are themselves load-bearing behavior, so at revise time their `clauses[]` links to the new scenario (part 4) MUST be backfilled in `tests/heading-coverage.json`, demonstrating the rule on its own introduction.
