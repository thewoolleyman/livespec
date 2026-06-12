---
topic: copier-vcs-ref-master-pin
author: claude-fable-5
created_at: 2026-06-12T17:54:46Z
---

## Proposal: copier-vcs-ref-master-pin

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Pin every blessed `copier copy` / `copier update` invocation prescribed by the spec to `--vcs-ref=master`, and align the generation command in contracts.md §"Shared content sync — copier template" with the implemented consumer flow (repo-root source path routed via `_subdirectory`). A bare `copier update` resolves the template repo's latest git tag (currently `v1.0.0`, which predates the entire `.github/workflows/` template set), silently re-syncing consumers to stale scaffolding; PR #420 fixed the mechanical surfaces (template headers, the copier-update-drift workflow, copier.yml contract comments, and the doctor corrective-action text), and this proposal realigns the contract prose that still prescribes the bare form.

### Motivation

Work-item livespec-3hnd (found 2026-06-12 via livespec-n9f0): SPECIFICATION/contracts.md §"Shared content sync — copier template" and §"Doctor cross-boundary invariants", plus non-functional-requirements.md §"Shared content provenance", still prescribe bare `copier update` / `copier update --dry-run`. The regression hazard was fixed mechanically in PR #420 for the template and check text, but spec files were out of scope for that mechanical PR and need their own propose-change → revise pass. Leaving the bare form in the contract would direct future consumers and check authors back into the latest-tag regression the mechanical fix just closed. The same hazard applies to the generation prescription: the only release tag (`v1.0.0`) predates the workflow set, so generating a sibling at `--vcs-ref=<core-release-tag>` would yield a repo that immediately fails the `copier-template-workflow-coverage` invariant; the implemented blessed invocation (per `templates/impl-plugin/copier.yml`) is `copier copy gh:thewoolleyman/livespec <target> --vcs-ref=master`, with subdirectory routing handled by the repo-root `copier.yml`'s `_subdirectory` key rather than a URL path suffix.

### Proposed Changes

All edits are intra-section prose; no `## ` headings are added, changed, or removed.

In `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" (the `copier-template-workflow-coverage` invariant):

1. The corrective-action sentence MUST read "MUST direct the user to run `copier update --vcs-ref=master` to re-sync from the template" (was bare `copier update`), matching the shipped check's corrective-action text.
2. The complementarity sentence MUST read "The invariant complements `copier update --dry-run --vcs-ref=master` (…)" (was bare `copier update --dry-run`).

In `SPECIFICATION/contracts.md` §"Shared content sync — copier template":

3. The opening paragraph MUST prescribe re-sync via `copier update --vcs-ref=master` and the CI drift check as `copier update --dry-run --vcs-ref=master` (both were bare).
4. A new paragraph MUST follow the opening paragraph stating the rationale: every blessed `copier copy` / `copier update` invocation (including `--dry-run` drift checks) MUST pin `--vcs-ref=master`, because a bare invocation resolves the template repo's latest git tag — which can long predate template HEAD (the `v1.0.0` tag predates the entire `.github/workflows/` template set) — silently re-syncing a consumer to stale scaffolding.
5. The `copier-update-drift.yml` list entry MUST describe the detector as running `copier update --dry-run --vcs-ref=master`.
6. The generation sentence MUST read: "Every `livespec-impl-*` repository MUST be generated from this template via `copier copy gh:thewoolleyman/livespec <target> --vcs-ref=master` (the repo-root `copier.yml` routes to `templates/impl-plugin/` via `_subdirectory`) and MUST carry a `.copier-answers.yml` at the repo root tracking the template version it was last generated from." (was `copier copy gh:thewoolleyman/livespec/templates/impl-plugin <target> --vcs-ref=<core-release-tag>` — a form that both addresses the subdirectory in a way copier does not support and pins a release tag that predates the workflow set).
7. The re-sync paragraph MUST prescribe `copier update --vcs-ref=master` for the per-repo re-sync and `copier update --dry-run --vcs-ref=master` for each impl repo's CI drift check (both were bare).

In `SPECIFICATION/non-functional-requirements.md` §"Shared content provenance":

8. The drift-surfacing sentence MUST read "static-scaffold drift MUST surface via CI's `copier update --dry-run --vcs-ref=master` check" (was bare `copier update --dry-run`).

Descriptive (non-prescriptive) mentions — the historical "`copier update` was never run" clause and the references to `copier update`'s 3-way merge behavior and `copier copy` time in the wiring-completeness template gate — are deliberately left unpinned: they describe the mechanism, not a blessed invocation.
