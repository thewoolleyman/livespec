---
topic: fix-constraints-livespec-runtime-vendored-entries
author: claude-opus-4-7
created_at: 2026-05-27T02:10:00Z
---

## Proposal: Correct livespec_runtime license attribution in constraints.md

### Target specification files

- constraints.md

### Summary

`SPECIFICATION/constraints.md` §"Locked vendored libs" declares the
`livespec_runtime` vendored entry as `BSD-3-Clause`, but upstream
`livespec-runtime` (`thewoolleyman/livespec-runtime`) declares MIT in
its `pyproject.toml` `[project].license` field, and the vendored
`LICENSE` shipped at `.claude-plugin/scripts/_vendor/livespec_runtime/LICENSE`
records MIT attribution. `NOTICES.md`'s `livespec_runtime` entry also
declares MIT. The constraints.md attribution is the only artifact in
the repo declaring BSD-3-Clause for this lib, and it is wrong.

### Motivation

The spec MUST accurately reflect upstream's license declaration so
contributors auditing the vendored tree against `## Lib admission
policy` are not misled. The lib admission policy enumerates the
permitted license set (MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0,
PSF-2.0); MIT is on that list, so the correction does not change the
admission outcome — it only repairs the recorded attribution.

### Proposed Changes

In `SPECIFICATION/constraints.md` under §"Locked vendored libs", the
bullet at line ~70 currently reads:

> **`livespec_runtime`** (thewoolleyman/livespec-runtime, BSD-3-Clause) — …

Replace the parenthetical license token with `MIT`:

> **`livespec_runtime`** (thewoolleyman/livespec-runtime, MIT) — …

No other text on the bullet changes. No `tests/heading-coverage.json`
change is needed (the H2 set of `constraints.md` is untouched).

## Proposal: Add livespec_runtime to the re-vendoring lib enumeration

### Target specification files

- constraints.md

### Summary

`SPECIFICATION/constraints.md` §"Vendoring procedure" enumerates the
re-vendoring target list as `(returns, fastjsonschema, structlog,
typing_extensions)` — 4 libs. Since PR #284 landed `livespec_runtime`
as the 5th upstream-sourced vendored lib (per `.vendor.jsonc` and
`.claude-plugin/scripts/_vendor/livespec_runtime/`), the enumeration
is out of date and silently excludes `livespec_runtime` from the
"only blessed mutation path" rule it is meant to declare.

### Motivation

The "blessed mutation path" rule is load-bearing: it tells
contributors that any change to a vendored upstream-sourced lib's
source tree MUST go through `just vendor-update <lib>` and not via
hand-edits. If `livespec_runtime` is not named in the enumeration,
the rule does not formally apply to it, even though
`just vendor-update livespec_runtime` is the recipe that
`reusable-bump-pin-from-dispatch.yml` invokes and which the
`li-tvi7lm` PR exercised end-to-end. The enumeration MUST list
every upstream-sourced vendored lib, not just the libs present at
the rule's authoring time.

### Proposed Changes

In `SPECIFICATION/constraints.md` under §"Vendoring procedure", the
bullet at line ~78 currently reads:

> **Re-vendoring** of upstream-sourced libs (`returns`,
> `fastjsonschema`, `structlog`, `typing_extensions`) MUST go through
> `just vendor-update <lib>` — the only blessed mutation path. …

Add `livespec_runtime` to the parenthetical list so it reads:

> **Re-vendoring** of upstream-sourced libs (`returns`,
> `fastjsonschema`, `structlog`, `typing_extensions`,
> `livespec_runtime`) MUST go through `just vendor-update <lib>` —
> the only blessed mutation path. …

No other text on the bullet changes. No `tests/heading-coverage.json`
change is needed (the H2 set of `constraints.md` is untouched).
