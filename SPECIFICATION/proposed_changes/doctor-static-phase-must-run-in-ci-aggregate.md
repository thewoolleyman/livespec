---
topic: doctor-static-phase-must-run-in-ci-aggregate
author: claude-opus-4-7
created_at: 2026-05-27T13:57:01Z
---

## Proposal: doctor-static-phase-must-run-in-just-check-aggregate

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Mandate that doctor's deterministic static phase MUST run as part of the `just check` enforcement aggregate (and therefore in CI and pre-push) against the main spec tree AND every sub-spec under `SPECIFICATION/templates/<name>/`. The LLM-driven objective and subjective phases are explicitly OUT of scope for CI — they remain interactive-only because they require LLM judgment and cannot reliably gate on machine-readable status.

### Motivation

Pre-existing doctor-static `fail` findings have sat undetected on master because doctor was never invoked by CI or `just check`. Examples surfaced 2026-05-27 by manual investigation: `constraints.md:298` mixed-case `Shall` self-violation, `constraints.md:243` self-violating Markdown-link example, `history/v081/.../revision.md` byte-identical to v080 (silent resulting_files[] write loss), `.github/workflows/copier-update-drift.yml` missing (livespec self-coverage gap). Each was authored cleanly per the wrapper-lifecycle pre-step/post-step at the time of its commit, but stale invariant additions and orphan write losses go undetected because doctor's static phase is only ever run by the wrapper-lifecycle of a /livespec:* skill being invoked against the affected spec tree. Closing this gap requires running doctor's static phase mechanically — same cadence as ruff, pyright, pytest, and the dev-tooling AST checks. The LLM-driven phases (objective + subjective) MUST remain interactive-only: they require LLM judgment, run with non-deterministic output, and are unsuitable for machine-gated CI.

### Proposed Changes

Add a new subsection under §"Enforcement suite — Invocation surfaces" (or equivalent, whichever section enumerates the `just check` aggregate's targets): the `just check` aggregate MUST include a `check-doctor-static` target that runs doctor's deterministic static phase against the main `SPECIFICATION/` tree AND every `SPECIFICATION/templates/<name>/` sub-spec, exiting non-zero on any `fail`-status finding from any tree. The target MUST NOT invoke doctor's LLM-driven objective phase or LLM-driven subjective phase — those phases are interactive-only because they require LLM judgment and cannot reliably gate on machine-readable status. The `check-doctor-static` target MUST be invocation-agnostic per the existing §"Enforcement suite — invocation-agnostic" rule: it runs identically from lefthook pre-push, CI, and ad-hoc developer invocation. The target MUST be enforced by the existing `check-all-declared` invariant against the canonical aggregate list so the contract is mechanically pinned. The pre-step / post-step doctor invocations carried by individual /livespec:* wrappers MUST remain in place per the existing sub-command lifecycle contract; the new CI-running gate is a coverage backstop, not a replacement.
