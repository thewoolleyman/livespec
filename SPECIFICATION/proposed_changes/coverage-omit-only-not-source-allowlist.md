---
topic: coverage-omit-only-not-source-allowlist
author: claude-fable-5
created_at: 2026-07-02T05:00:49Z
---

## Proposal: Coverage measurement uses an omit-only blocklist, not a source allowlist

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/contracts.md

### Summary

Reconcile the spec's coverage-configuration prose with the shipped pyproject.toml, which deliberately uses an `omit`-only blocklist and NO `source` allowlist. §"Code coverage thresholds" currently mandates that `[tool.coverage.run]` MUST set `source` to include the livespec package and the bin/ directory, and §"Python-rule compliance" (contracts.md) describes a `source` list "anchored at livespec/, bin/, dev-tooling/". No such `source` list exists: a relative `source` list resolves against the subprocess working directory for the dev-tooling/checks scripts (run via subprocess.run with cwd=tmp_path) and would silently drop those first-party modules from the report, so `source` was removed in favor of an omit-only blocklist. This proposal restates the invariant (all first-party code — livespec/, bin/, dev-tooling/ — measured at 100% line+branch; vendored/venv/scaffolding excluded) and the reasoned constraint (no `source` allowlist) instead of the stale mechanism, per the architecture-not-mechanism principle.

### Motivation

gap-dg2rdlsf from the Session-3 detect-impl-gaps `--since-version 150` pass over the fleet-followups thread; triaged then as impl->spec drift (the omit-only choice is deliberate and correct, so the spec is stale — not a gap). Verified live 2026-07-02 against origin/master's pyproject.toml `[tool.coverage.run]`, whose inline comment documents the subprocess-cwd rationale for dropping `source`. The prose above line 808 already states the true architectural invariant (100% across livespec/**, bin/**, dev-tooling/**; _vendor/ excluded), so the `source`-allowlist mandate is both stale and redundant with that statement. Keeping the 'no source allowlist' constraint is load-bearing: the 100% gate alone does NOT catch a naive `source` allowlist, because silently dropped files register no uncovered lines.

### Proposed Changes

Two prose edits removing the phantom `source`-list framing. No `##`/`###` headings are added, renamed, or removed (heading-coverage unaffected); the 100%/branch/report gate is unchanged.

--- EDIT 1: non-functional-requirements.md, §"Code coverage thresholds" (the [tool.coverage.run] sentence) ---

The current sentence reads:

> `pyproject.toml`'s `[tool.coverage.run]` MUST set `branch = true` and `source` to include both the `livespec` package and the `bin/` directory. `[tool.coverage.report]` MUST set `fail_under = 100`, `show_missing = true`, `skip_covered = false`. Enforced by `just check-coverage`.

REPLACE it with:

> `pyproject.toml`'s `[tool.coverage.run]` MUST set `branch = true` and MUST NOT use a `source` allowlist: because the `dev-tooling/checks/` scripts run via `subprocess.run` with `cwd` set to a temporary directory, a relative `source` list would resolve against that cwd and silently drop those first-party modules from the report. Coverage therefore measures every imported module and excludes non-first-party code (vendored libraries, the project virtualenv, and test scaffolding) through an `omit`-only blocklist. `[tool.coverage.report]` MUST set `fail_under = 100`, `show_missing = true`, `skip_covered = false`. Enforced by `just check-coverage`.

--- EDIT 2: contracts.md, §"Python-rule compliance" (the tests/prompts coverage-exclusion sentence) ---

The current sentence reads:

> Coverage measurement does NOT include `tests/prompts/` — the source list for `[tool.coverage.run]` is anchored at `livespec/`, `bin/`, `dev-tooling/`, so the unit-tier per-file 100% coverage gate does not extend to test infrastructure.

REPLACE the middle clause `the source list for \`[tool.coverage.run]\` is anchored at \`livespec/\`, \`bin/\`, \`dev-tooling/\`` WITH:

> the first-party trees measured by `[tool.coverage.run]` are `livespec/`, `bin/`, and `dev-tooling/` (selected via an `omit`-only blocklist rather than a `source` allowlist, per `non-functional-requirements.md` §"Code coverage thresholds")

so the full sentence becomes: "Coverage measurement does NOT include `tests/prompts/` — the first-party trees measured by `[tool.coverage.run]` are `livespec/`, `bin/`, and `dev-tooling/` (selected via an `omit`-only blocklist rather than a `source` allowlist, per `non-functional-requirements.md` §"Code coverage thresholds"), so the unit-tier per-file 100% coverage gate does not extend to test infrastructure."
