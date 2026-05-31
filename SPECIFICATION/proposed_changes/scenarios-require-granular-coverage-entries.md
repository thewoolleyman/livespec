---
topic: scenarios-require-granular-coverage-entries
author: claude-opus-4-8-1m
created_at: 2026-05-31T20:49:42Z
---

## Proposal: Scenarios require granular per-scenario coverage entries

### Target specification files

- constraints.md

### Summary

Amend constraints.md §"Heading taxonomy" so that every `##` heading in scenarios.md — including those carrying the `Scenario:` prefix — requires its own registry entry in tests/heading-coverage.json. Scenarios are tracked granularly (one entry per scenario), with a many-to-one mapping to test node ids permitted.

### Motivation

The current rule SKIPS `Scenario:`-prefixed `##` headings from the heading-coverage registry, relying solely on the per-spec-file rule test that validates scenario format. That leaves individual scenarios without their own coverage entries, so the existing "Scenario headings require integration-tier-or-above coverage" sub-rule has nothing to bite on. Tracking scenarios granularly — one registry entry per scenario, mapping (many-to-one) to integration-tier test node ids — restores per-scenario coverage accounting while acknowledging that one integration-tier test commonly exercises several related scenarios.

### Proposed Changes

Within §"Heading taxonomy" of `constraints.md`, replace the existing `Scenario:`-skip sentence.

OLD (remove this exact sentence):

> The check SKIPS `##` headings whose text begins with the literal `Scenario:` prefix: scenario blocks are exercised by the per-spec-file rule test for the scenario-carrying spec file; per-scenario registry entries are not required.

NEW (replace with this exact text):

> Within `scenarios.md`, every `##` heading — including those beginning with the `Scenario:` prefix — MUST have its own registry entry; scenarios are tracked **granularly**, one entry per scenario. Multiple scenario entries MAY map to the **same** test node id — a many-to-one mapping is expected, since one integration-tier test commonly exercises several related scenarios. The per-spec-file rule test that validates scenario *format* does NOT substitute for these per-scenario coverage entries. (`Scenario:`-prefixed headings outside `scenarios.md`, if any, remain out of registry scope.)

The existing **"Scenario headings require integration-tier-or-above coverage."** sub-rule paragraph is left intact — it already requires the integration-tier mapping; it now simply has entries to bite on. No `##` heading is added, changed, or removed by this amendment (it edits only body text inside the existing `## Heading taxonomy` H2), so no `tests/heading-coverage.json` co-edit is required.
