---
topic: scope-copier-template-workflow-coverage-to-consumers
author: claude-opus-4-8
created_at: 2026-06-08T00:37:51Z
---

## Proposal: Scope copier-template-workflow-coverage to copier consumers only

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Amend §"copier-template-workflow-coverage" so the invariant applies ONLY to project roots that are copier-template consumers, detected by the presence of a `.copier-answers.yml` file at the project root. A project root lacking `.copier-answers.yml` is out of scope: the check returns a non-failing (skip/pass) finding WITHOUT inspecting `.github/workflows/`. The required-file list is unchanged.

### Motivation

The check currently runs unconditionally against every project root, so it fires `fail` against repos that legitimately carry a different workflow set (livespec itself, livespec-dev-tooling, livespec-runtime, dolt-server) and were never generated from the copier impl-plugin template. Only `livespec-impl-*` repos carry `.copier-answers.yml`. Gating on that file makes the invariant correct for non-consumer repos while preserving full enforcement against actual copier consumers.

### Proposed Changes

Add a precondition clause to the `### copier-template-workflow-coverage` section in `SPECIFICATION/contracts.md`.

The invariant MUST apply ONLY to project roots that are copier-template consumers, detected by the presence of a `.copier-answers.yml` file at the project root. A project root that does NOT carry `.copier-answers.yml` is out of scope for this invariant: the check MUST return a single non-failing `skipped` finding WITHOUT inspecting `.github/workflows/`. This scoping makes the invariant correct for livespec itself, `livespec-dev-tooling`, `livespec-runtime`, and any other livespec-governed repo that was not generated from the impl-plugin copier template and therefore legitimately carries a different workflow set; those repos catalogue their own workflows via their own specs. Repos that DO carry `.copier-answers.yml` (the `livespec-impl-*` consumers generated from `templates/impl-plugin/`) remain fully in scope and the `fail`-on-missing-required-file behavior described above applies to them unchanged.

The required-file list (the seven impl-plugin workflow files enumerated in §"Shared content sync — copier template") is NOT changed by this scoping.

Proposed clause (to insert immediately after the existing first paragraph of the section, before the `copier update --dry-run` complement paragraph):

> The invariant applies ONLY to project roots that are copier-template consumers, detected by the presence of a `.copier-answers.yml` file at the project root. A project root that does NOT carry `.copier-answers.yml` is out of scope: the check MUST emit a single non-failing `skipped` finding and MUST NOT inspect `.github/workflows/`. Only `livespec-impl-*` consumers generated from the impl-plugin copier template carry `.copier-answers.yml`; `livespec` itself, `livespec-dev-tooling`, `livespec-runtime`, and other non-consumer repos legitimately carry a different workflow set and are exempt. Consumer repos that DO carry `.copier-answers.yml` remain fully in scope and the `fail`-on-missing-required-file behavior above applies to them unchanged.
