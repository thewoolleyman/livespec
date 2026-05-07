---
topic: conventional-commits-mandate-and-rebase-merge-only
author: thewoolleyman
created_at: 2026-05-07T03:01:12Z
---

## Proposal: conventional-commits-mandate-and-rebase-merge-only

### Target specification files

- SPECIFICATION/constraints.md
- SPECIFICATION/contracts.md

### Summary

Mandate Conventional Commits 1.0 for every commit on master and lock the merge strategy to rebase-merge only, eliminating the breaking-change-loss failure mode that exists under squash + PR-title workflows. Tighten the local commit-msg hook to require a Conventional Commits subject-prefix BEFORE the v034 D3 Red→Green replay dispatch. Add release-please-driven semver to plugin.json from the per-commit Conventional Commits flow.

### Motivation

Empirical gap: the recent phase-12 (commit 50acb67) and phase-13 (commit 82b409e) squash-merge commits landed on master with subjects (`phase-12: ...`, `phase-13: ...`) that are NOT valid Conventional Commits types. Root cause: GitHub squash-merge under repo setting `squash_commit_title: COMMIT_OR_PR_TITLE` uses the PR title verbatim for multi-commit branches, bypassing the local v034 D3 commit-msg hook (which only ran on per-cycle feature-branch commits, never on the squash subject that lands on master). Branch protection had zero PR-title validation gate.

Deeper failure mode (verified against release-please source `googleapis/release-please/blob/main/src/commit.ts` and semantic-release maintainer position in `semantic-release/commit-analyzer#65`): even with PR-title-validation in place under squash-merge, breaking-change markers (`!` after type, e.g., `feat!:`) authored on per-cycle commits do NOT propagate to master if the PR title omits the marker. release-please's `splitMessages()` regex explicitly does NOT match the `!` token in body lines; semantic-release explicitly ignores embedded subject-style lines in squash bodies. Only `BREAKING CHANGE:` footers in body survive — relying on author discipline to dual-author both `!` AND footer is not a mechanical guarantee.

Rebase-merge eliminates the entire failure surface: every commit lands individually on master with its own Conventional Commits type, including `!` markers exactly where authors place them. release-please reads each commit's type directly. No squash flattening, no PR-title cross-check needed, no body-scan workarounds.

The rebase-merge model also matches the project's existing per-commit-granular discipline: the v034 D3 Red→Green replay hook is designed around per-commit Red/Green pairs as units; squash collapses pairs into one commit on master, burying the Red/Green trailers in the body. Rebase-merge preserves the per-pair structure on master, giving the audit trail (already granular on the spec side via propose-change → revise → vNNN cuts) symmetric granularity on the implementation side.

Upstream tooling alignment: semantic-release maintainers explicitly recommend per-commit Conventional Commits + rebase/merge (their official troubleshooting page is titled "Squashed commits are ignored by semantic-release"). Angular, conventional-changelog, and most library/framework projects follow this pattern. Squash + PR-title is dominant in app/product repos that don't have livespec's per-commit discipline; livespec has the discipline, so the per-commit pattern fits better.

Documentation gap: the project's existing SPECIFICATION/ does not codify the merge strategy or the Conventional Commits mandate. The v034 D3 contract documents the per-cycle Red→Green discipline but does not extend that to a Conventional Commits invariant for all master commits.

### Proposed Changes

Three categories of change:

## 1. Codify the Conventional Commits + rebase-merge contract in SPECIFICATION/

### SPECIFICATION/constraints.md

Add a new top-level section §"Commit and merge discipline" (placement: after §"Self-application bootstrap exception" or wherever the layered governance/process constraints live) carrying:

- **Conventional Commits 1.0 mandate.** Every commit on every branch and every commit landing on master MUST conform to Conventional Commits 1.0 (`<type>[(scope)][!]: <subject>` with body and optional footers). Valid types: `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `revert`. Breaking changes MUST be indicated by `!` after type/scope OR a `BREAKING CHANGE:` footer (or both).
- **Master merge strategy.** Master accepts only rebase-merge. Squash-merge and merge-commit strategies are forbidden at the GitHub repo-settings level (`allow_squash_merge: false`, `allow_merge_commit: false`, `allow_rebase_merge: true`). Combined with `required_linear_history: true` (already set), every commit on master is a per-cycle commit landed individually with its own Conventional Commits type intact.
- **Local enforcement.** The commit-msg hook (`dev-tooling/checks/red_green_replay.py` or a new sibling check) MUST validate the Conventional Commits subject prefix as the FIRST step, BEFORE the v034 D3 Red→Green dispatch. Non-Conventional subjects exit non-zero regardless of staged shape.
- **Release-time enforcement.** A CI workflow `pr-conventional-commits.yml` or equivalent MAY validate PR titles for navigability (advisory only; not load-bearing under rebase-merge since per-commit subjects are what land on master).

### SPECIFICATION/contracts.md

Amend §"Pre-commit step ordering" to mention the Conventional Commits subject-prefix gate at the commit-msg stage (in addition to the existing v034 D3 replay-hook description).

Add a new section §"Plugin versioning" describing release-please's role: `plugin.json.version` is auto-managed from per-commit Conventional Commits via release-please-action; `marketplace.json` carries no version (per-Claude-Code resolution order, `plugin.json` wins anyway); release-please opens a release PR on every push to master with the next-version bump per Conventional Commits → semver mapping (`feat:` MINOR, `fix:` PATCH, `feat!:`/`fix!:`/`BREAKING CHANGE:` MAJOR, others no bump).

## 2. Implementation work (out of scope for this propose-change; lands as follow-up commits after revise accepts the contract change)

- **Repo settings flip.** Via `gh api` PATCH `/repos/thewoolleyman/livespec` setting `allow_squash_merge: false` and `allow_merge_commit: false`. Document in `branch-protection.json` if appropriate.
- **Local hook tightening.** Extend `dev-tooling/checks/red_green_replay.py` (or add a sibling check) to validate the Conventional Commits subject prefix BEFORE Red/Green dispatch. Subject regex: `^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)(\([^)]+\))?!?: .+`. Reject non-matching subjects with a structured diagnostic naming the canonical type set.
- **Release-please workflow.** New `.github/workflows/release-please.yml` running on push to master, plus `.release-please-manifest.json` and `release-please-config.json` at repo root (or under a `.release-please/` directory) configuring the manifest mode to bump `plugin.json`'s `version` field. Auto-maintained `CHANGELOG.md` at repo root.
- **`marketplace.json` `version` field.** Explicitly OMITTED so `plugin.json.version` is the single source of truth.
- **PR-title-validation workflow.** OPTIONAL — adds navigability for the open-PR list but is not load-bearing under rebase-merge. May be added as a separate propose-change later if the team finds the open-PR list noisy with non-Conventional titles.

## 3. Acceptance criteria

- `SPECIFICATION/constraints.md` carries the new §"Commit and merge discipline" section codifying all three rules (Conventional Commits mandate, master merge strategy = rebase-merge only, local enforcement gate at commit-msg).
- `SPECIFICATION/contracts.md` §"Pre-commit step ordering" mentions the new Conventional Commits subject-prefix gate.
- `SPECIFICATION/contracts.md` carries a new §"Plugin versioning" section describing release-please's role.
- The implementation follow-up is filed as a tracked work item (separate PR) referencing this revise's vNNN cut.

## 4. Tradeoffs and risks

- **More commits on master.** Rebase-merge lands every per-cycle commit individually. `git log --oneline` on master will be longer than under squash. Mitigation: PR authors run `git rebase -i` before merge to clean up noisy intermediate commits (e.g., "fix typo", "address review").
- **Stricter local hook.** Authors who currently get away with non-Conventional subjects on feature branches will be rejected. Mitigation: error message names the canonical type set; authors can amend.
- **release-please dependency.** Adds an external GitHub Action (Google-maintained, widely adopted, no Python deps). Same dependency-policy posture as existing `actions/checkout`.
- **Doing nothing.** The phase-12 / phase-13 incident demonstrates the gap is real — non-Conventional subjects already landed on master uncontested, and the breaking-change failure mode would surface the next time a per-cycle `feat!:` commit gets squashed without `!` in the PR title.

## 5. Open questions for /critique

1. Should the local commit-msg hook reject non-Conventional subjects on feature branches too, or only validate the master-bound subject? (Recommendation: reject everywhere for branch-internal-history hygiene; trivial cost.)
2. Should the OPTIONAL PR-title-validation workflow be required or skipped for v1? (Recommendation: skip for v1; not load-bearing under rebase-merge; revisit if PR-list noise becomes a problem.)
3. Should `release-please-config.json` and `.release-please-manifest.json` live at repo root, or under a `.release-please/` directory? (Recommendation: repo root per release-please's documented default.)
4. Should `CHANGELOG.md` be auto-maintained at repo root by release-please, or in a docs subdirectory? (Recommendation: repo root per the universal convention.)
