---
topic: copier-template-required-workflow-enumeration
author: claude-opus-4-7
created_at: 2026-05-26T06:11:59Z
---

## Proposal: enumerate-required-impl-plugin-github-workflows-in-copier-template

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Tighten §"Shared content sync — copier template" (`contracts.md:452`) by replacing the loose `.github/workflows/*.yml` placeholder in the canonical-scaffold enumeration with an explicit, exhaustive list of REQUIRED workflow files every `livespec-impl-*` repo MUST inherit from `templates/impl-plugin/.github/workflows/`. The current loose wording lets workflow files that exist in livespec but aren't mirrored into the copier template fall silently out of every generated impl-plugin repo — a real gap caught when `livespec-impl-plaintext` PR #26 sat OPEN/CLEAN for 10+ minutes after CI completed because the repo lacks the `auto-enable-merge.yml` workflow that livespec itself runs. Add a doctor invariant `copier-template-workflow-coverage` that fails when the active impl-plugin's `.github/workflows/` set is a strict subset of the enumerated required-files list.

### Motivation

The §"Shared content sync — copier template" clause at `contracts.md:452` reads:

> `livespec` MUST publish a copier template at `templates/impl-plugin/` (project-root-relative) containing the canonical scaffolding every `livespec-impl-*` repo derives from: `justfile`, `lefthook.yml`, `.mise.toml`, `pyproject.toml` (with the ruff/pyright config), `.github/workflows/*.yml`, `.claude-plugin/marketplace.json` and `plugin.json` skeletons, a starter `SPECIFICATION/` skeleton, and a starter `.claude/skills/loop/SKILL.md` orchestration driver.

The wording `.github/workflows/*.yml` is silent on WHICH workflow files MUST be in the template. In practice, the template at `templates/impl-plugin/.github/workflows/` currently ships ONLY `ci.yml.jinja` and `copier-update-drift.yml.jinja`. Livespec's own `.github/workflows/` carries `auto-enable-merge.yml`, `auto-update-branches.yml`, `bump-pin-from-dispatch.yml`, `pin-freshness.yml`, `release-dispatch.yml`, `release-tag.yml`, and `e2e-real.yml` in addition to the two that DO get templated. The asymmetry is silent: there is no contract clause that says "auto-enable-merge MUST exist in every impl-plugin repo", and there is no doctor invariant that catches its absence. `copier update --dry-run` can only detect divergence in files that DO exist in the template — it is structurally unable to detect "files missing from the template that should be added."

The consequence surfaced concretely on 2026-05-26 during the cross-repo coordination workflow that landed PRs #245 (livespec), #246 (epic), and `livespec-impl-plaintext#26`: the upstream PRs auto-merged cleanly within ~30 seconds of CI green because `livespec-pr-bot` triggered the `auto-enable-merge.yml` workflow on PR open. The impl-plaintext PR sat OPEN/CLEAN for over 10 minutes with all CI checks green and required reviews unblocked, because `livespec-impl-plaintext` has no `auto-enable-merge.yml` workflow at all. The PR ultimately merged only after explicit `gh pr merge --rebase --auto --delete-branch` was issued. A user (or autonomous agent) running a cross-repo coordination flow under a time budget would have spent the budget waiting for auto-merge that was never going to happen.

The v076 propose-change `delegate-cross-repo-coordination-impl-to-dev-tooling.md` (accepted into history at `SPECIFICATION/history/v076/`) moves the auto-merge automation surface ownership to `livespec-dev-tooling`'s spec, anticipating reusable workflows (per `contracts.md:469` "Composite Actions and reusable workflows. Invoked via `uses: thewoolleyman/livespec-dev-tooling/.github/actions/<name>@vX.Y.Z` and `uses: thewoolleyman/livespec-dev-tooling/.github/workflows/<name>.yml@vX.Y.Z`"). That delegation moves the IMPLEMENTATION ownership of the auto-merge logic but does NOT close the contract crack: even with a reusable workflow at `livespec-dev-tooling/.github/workflows/auto-enable-merge.yml`, each impl-plugin still needs a thin `auto-enable-merge.yml` in its OWN `.github/workflows/` that calls `uses:` against the reusable surface. The copier template is what places that file in every impl-plugin repo, and the contract clause is what makes its presence enforceable.

The fix is in two parts:

1. **Enumerate the required-workflow-file set in the contract clause.** Replace the placeholder `.github/workflows/*.yml` at `contracts.md:452` with an exhaustive list. The list MUST include `auto-enable-merge.yml` (the immediate gap that caused the incident) and SHOULD include the other workflow files that are uniformly required across every impl-plugin repo (`auto-update-branches.yml` for the same auto-merge-adjacent reasons; `bump-pin-from-dispatch.yml`, `pin-freshness.yml`, `release-dispatch.yml` per the cross-repo coordination contract). Workflow files that are livespec-private (e.g., `release-tag.yml` if it ships livespec's own marketplace, `e2e-real.yml` if it tests livespec-private flows) MUST NOT be on the required-list.

2. **Add a doctor invariant that catches absent workflow files.** A new structural invariant `copier-template-workflow-coverage` reads the enumerated required-file list from `contracts.md`, walks the active project root's `.github/workflows/` directory, and fires `fail` for every required file that is missing. The invariant complements `copier update --dry-run` (which catches divergence in files that DO exist) by catching ABSENT files. Doctor invocations that detect missing workflows direct the user toward `copier update` to re-sync, with a corrective-action narration naming the specific missing files.

This propose-change is narrow by design: it enumerates the required-file set and adds the matching doctor invariant. It does NOT prescribe the workflow files' INTERNAL content (which lives in the template as Jinja or in `livespec-dev-tooling`'s reusable-workflow surface), and does NOT ratify the reusable-workflow consumption pattern at `livespec-dev-tooling` (that is a separate downstream propose-change against `livespec-dev-tooling`'s own `SPECIFICATION/`). The principle being established here is the load-bearing one: the contract MUST name the required-file set, and doctor MUST enforce the set's presence. The implementation details follow.

### Proposed Changes

**Edit 1.** Replace the existing single-line scaffolding enumeration at `contracts.md:452` (§"Shared content sync — copier template"):

> `livespec` MUST publish a copier template at `templates/impl-plugin/` (project-root-relative) containing the canonical scaffolding every `livespec-impl-*` repo derives from: `justfile`, `lefthook.yml`, `.mise.toml`, `pyproject.toml` (with the ruff/pyright config), `.github/workflows/*.yml`, `.claude-plugin/marketplace.json` and `plugin.json` skeletons, a starter `SPECIFICATION/` skeleton, and a starter `.claude/skills/loop/SKILL.md` orchestration driver.

with the enumerated form:

> `livespec` MUST publish a copier template at `templates/impl-plugin/` (project-root-relative) containing the canonical scaffolding every `livespec-impl-*` repo derives from: `justfile`, `lefthook.yml`, `.mise.toml`, `pyproject.toml` (with the ruff/pyright config), `.claude-plugin/marketplace.json` and `plugin.json` skeletons, a starter `SPECIFICATION/` skeleton, a starter `.claude/skills/loop/SKILL.md` orchestration driver, and the following `.github/workflows/` files:
>
> - `ci.yml` — the per-repo CI pipeline (matrix of static-phase checks; `pull_request` + `push` + `merge_group` triggers).
> - `copier-update-drift.yml` — the periodic `copier update --dry-run` drift detector that surfaces template divergence.
> - `auto-enable-merge.yml` — auto-enables REBASE auto-merge on PR open. Required so that propose-change PRs in every impl-plugin repo merge with the same cadence as upstream `livespec` PRs (incident 2026-05-26: `livespec-impl-plaintext` PR #26 sat OPEN/CLEAN for 10+ minutes because this file was absent).
> - `auto-update-branches.yml` — auto-updates open-PR branches against `master` when the base advances. Paired with `auto-enable-merge.yml`; together they make merging a hands-free operation for green PRs.
> - `bump-pin-from-dispatch.yml` — accepts the bump-pin dispatch payload from `livespec`'s release flow per `livespec-dev-tooling`'s cross-repo coordination automation surface.
> - `pin-freshness.yml` — the periodic check that the pin tag in `.livespec.jsonc` is not older than the drift threshold per the `contract-version-compatibility` doctor invariant.
> - `release-dispatch.yml` — accepts the release-dispatch payload from `livespec`'s release flow.
>
> The list is EXHAUSTIVE for the impl-plugin scaffold: any workflow file added to `templates/impl-plugin/.github/workflows/` requires a contract-clause amendment (this section) and a corresponding update to the `copier-template-workflow-coverage` doctor invariant (codified below). Livespec-private workflow files (e.g., `release-tag.yml` for livespec's own marketplace release flow, `e2e-real.yml` for livespec-private smoke tests) MUST NOT be added to the template and MUST NOT appear in the required-list.
>
> Each enumerated file MAY be a Jinja-templated thin pass-through that delegates to a reusable workflow at `thewoolleyman/livespec-dev-tooling/.github/workflows/<name>.yml@vX.Y.Z` (per §"Shared code sync — livespec-dev-tooling") — the reusable-workflow consumption pattern is the canonical sharing mechanism for any workflow whose implementation is uniform across livespec-governed repos. The contract-level requirement is that the file EXISTS in each impl-plugin's `.github/workflows/`; whether the file's body inlines logic or `uses:` a reusable workflow is the template author's choice.

**Edit 2.** Add a new doctor invariant `copier-template-workflow-coverage` to `contracts.md` §"Doctor cross-boundary invariants" (placed after the existing `copier-update-drift` invariant if one exists, or at the end of the cross-boundary invariant catalogue):

> ### `copier-template-workflow-coverage`
>
> Every consumer repository governed by livespec MUST contain a `.github/workflows/` directory whose set of workflow files is a SUPERSET of the required-file list enumerated in §"Shared content sync — copier template". The check fires `fail` for every required workflow file that is missing from the consumer's `.github/workflows/`. Each `fail` finding MUST name the specific missing file and MUST direct the user to run `copier update` to re-sync from the template.
>
> The invariant complements `copier update --dry-run` (which catches divergence in files that DO exist in both the template and the consumer): `copier-template-workflow-coverage` catches files that exist in the template but NOT in the consumer (the "file was added to the template after the consumer was generated, and `copier update` was never run" case AND the "file was present in livespec but never made it into the template, and the consumer therefore lacks it" case). The two checks together close the workflow-coverage hole.
>
> Workflow files in the consumer's `.github/workflows/` that are NOT in the required-list (consumer-local workflows) MUST NOT fire `fail` — they are out of scope for this invariant. Consumer-local workflows are catalogued by the consumer's own spec, not by livespec.
>
> The invariant runs in doctor's static phase (no LLM in the path); the required-file list is read directly from `contracts.md`'s enumerated scaffold list (Edit 1 above). Drift between the contract list and the doctor invariant's hard-coded list MUST be caught by a paired enforcement-suite check that ships in `livespec-dev-tooling` (TBD in a parallel propose-change against that sibling's spec); for v1, the doctor invariant MAY hard-code the list and rely on PR review to catch drift.

**Edit 3 (companion downstream work, not load-bearing for THIS proposal).** After this proposal lands, the immediate follow-up work is:

- Add the missing Jinja templates at `templates/impl-plugin/.github/workflows/` for `auto-enable-merge.yml`, `auto-update-branches.yml`, `bump-pin-from-dispatch.yml` (currently exists in impl-plaintext but not in template? verify), `pin-freshness.yml`, `release-dispatch.yml`. Each template MAY be a thin pass-through that `uses:` a reusable workflow at `livespec-dev-tooling` once those reusable workflows exist; in the interim the templates MAY inline the logic.
- Run `copier update` against every active `livespec-impl-*` repo (currently just `livespec-impl-plaintext`) to pull in the newly-templated files.
- Open the corresponding propose-change against `livespec-dev-tooling`'s own `SPECIFICATION/` to add the reusable-workflow surface for the workflows whose implementation is identical across consumers (auto-enable-merge, auto-update-branches).

These downstream work items are NOT part of THIS proposal's scope; they will be filed as work-items (or as a tracking epic) after THIS contract clause lands.
