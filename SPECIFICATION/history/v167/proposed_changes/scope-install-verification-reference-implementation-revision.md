---
proposal: scope-install-verification-reference-implementation.md
decision: modify
revised_at: 2026-07-19T06:42:36Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accepted with modifications. This pass corrects two defects in history/v166 —
one in the ratified spec text, one in v166's own recorded justification.

1. SPEC TEXT (the blocker). v166 cited `ensure_plugins.py` as the unqualified
   "Reference implementation" of the install-verification invariant. Verified
   directly: that file contains zero references to `projectPath` or
   `installed_plugins`, and `run_from_settings` returns on `returncode` alone.
   It is a reference for the derive-and-install flow only, and it is actively
   nonconforming with the invariant's central prohibition. The citation is now
   scoped, the nonconformance is stated explicitly rather than papered over,
   and the remediation is bound to `livespec-zxf6` in the sibling that owns the
   tool.

2. RECORDED JUSTIFICATION (superseding v166's rationale). v166 justified
   omitting a `## Scenario` for the new invariant on the grounds that livespec's
   test suite "structurally cannot exercise" it. That justification is FALSE and
   is withdrawn. The invariant's detection predicate is a pure comparison of two
   JSON documents — committed `enabledPlugins` against
   `installed_plugins.json` entries' `projectPath` — and is straightforwardly
   unit-testable with fixtures in `tmp_path`; the ~15-line verification snippet
   this change landed in `docs/livespec-installation-prompt.md` is proof by
   construction.

   The correct and narrower reason to omit the scenario is OWNERSHIP, not
   testability: per `non-functional-requirements.md` §"Sibling spec ownership",
   the tooling this invariant binds lives in `livespec-dev-tooling`, so the
   covering test ships with that sibling while core states the invariant. This
   contract already applies exactly that split to the copier-scaffold
   enforcement check. The deviation is now paired with a filed work-item
   (`livespec-zxf6`) that carries both the verification and its test, so the
   omission is bound to owned work rather than left as an unowned gap. Adding a
   scenario now would require a heading-coverage entry pointing at a test that
   does not yet exist — an unowned TODO under the current gate, which is the
   failure class that previously blocked five releases.

Process note for the record: v166 was driven after the review's first blocker
was fixed, but before the review's full findings had been received. The
governed loop absorbed the correction as designed — history is append-only and
v167 supersedes — but the ordering was mine, not the mechanism's.

## Modifications

One exact-string replacement in SPECIFICATION/contracts.md, asserted to match
exactly once: the install-verification paragraph's reference-implementation
citation is scoped to the derive-and-install flow, its nonconformance with the
invariant is stated explicitly, and remediation is bound to the sibling-owned
follow-up `livespec-zxf6` per §"Sibling spec ownership".

## Resulting Changes

- contracts.md
