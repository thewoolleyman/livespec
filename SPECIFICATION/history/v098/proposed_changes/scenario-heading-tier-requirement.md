---
topic: scenario-heading-tier-requirement
author: livespec-orchestrate
created_at: 2026-05-30T22:01:33Z
---

## Proposal: Scenario headings require integration-tier-or-above test coverage

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Strengthen the existing heading-coverage invariant in `constraints.md`
§"Heading taxonomy" with a sub-rule specific to `scenarios.md`: each scenario
heading's mapped test MUST live at the **middle (integration) or top (e2e / CLI)
tier** of the test pyramid, not the unit tier. The rule is structural — a per-repo
`[tool.livespec_dev_tooling.scenario_tiers]` allowlist of node-id path prefixes —
so each repo declares its own integration-test convention without amending the
shared check. The shared `heading_coverage` check is extended to enforce it.

### Motivation

`constraints.md` §"Heading taxonomy" mandates that every `##` heading in a
template-declared NLSpec file have a `tests/heading-coverage.json` entry mapping
to a pytest node id, mechanically enforced by `heading_coverage`. The rule is
uniform across spec files — a unit test satisfies the gate for a `## Scenario: …`
heading just as it does for a `## Specification model` heading.

But scenarios are categorically different: `scenarios.md` describes
user-observable behavior. A scenario covered only by a unit test is not really
covered — the unit test verifies internal shape, not the user-observable round
trip the scenario describes. Today's gate accepts that substitution silently.
This sub-rule closes the gap for the one spec file where it matters, leaving
`contracts.md` / `constraints.md` / `spec.md` headings free to be exercised by
unit-tier tests (they are not user-observable-by-definition).

### Proposed Changes

Add a sub-rule to `constraints.md` §"Heading taxonomy" (as a `### ` / sub-rule
within the existing `## ` section — NOT a new H2, so NO `tests/heading-coverage.json`
co-edit is required: the shared `heading_coverage` check's H2 extractor tracks
`## ` headings only). The sub-rule MUST read along these lines:

---

**Scenario headings require integration-tier-or-above coverage.** For a
`tests/heading-coverage.json` entry whose `spec_file` is `scenarios.md`, the
mapped `test` node id MUST resolve to a test at the **integration tier or above**
(middle or top of the pyramid), never a unit-tier test. Operationally, one of the
following MUST hold: (a) the node-id path component begins with one of the
integration-tier prefixes enumerated in the per-repo
`[tool.livespec_dev_tooling.scenario_tiers]` allowlist (e.g. `tests.e2e.…`,
`tests.integration.…`, `tests.consumer.…`, `tests.prompts.…`); OR (b) the
resolved test function carries an explicit `pytest.mark.integration` (or stronger)
marker. A `TODO` entry remains allowed during transition but MUST carry a `reason`
that explicitly acknowledges the tier requirement. This sub-rule applies ONLY to
`scenarios.md`; headings in other template-declared spec files MAY be exercised by
unit-tier tests.

---

The `livespec_dev_tooling.checks.heading_coverage` check MUST be extended to
enforce this sub-rule with a new diagnostic class (e.g. `scenario heading mapped
to unit-tier test`). The per-repo allowlist is read from the consumer's
`pyproject.toml` `[tool.livespec_dev_tooling.scenario_tiers]` table; absent a
table, the check MAY fall back to a documented default prefix set. A
dev-tooling release is cut at the matching version so downstream repos can
bump-pin to pick up the strengthened check.

**Out of scope for this propose-change** (tracked as later phases of epic
li-scetier): re-tier-ing any existing `scenarios.md` entries that currently point
at unit-tier tests (per-repo cleanup); and propagating the invariant text into the
library repos' own `SPECIFICATION/` trees (each must independently restate it per
§"Forbidden: references OUTSIDE the same SPECIFICATION/ tree"). livespec's own
`scenarios.md` entries are audited as already mostly-compliant; any residual
unit-tier mappings are re-pointed at e2e equivalents or moved to `TODO` with a
tier-rationale `reason` as part of landing this rule.
