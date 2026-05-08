---
proposal: conventional-commits-mandate-and-rebase-merge-only.md
decision: modify
revised_at: 2026-05-08T07:47:20Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Proposal predates the v053 NFR boundary migration. Modifying to re-target the §"Commit and merge discipline" content from `constraints.md` (the proposal's original placement) to `non-functional-requirements.md` ## Constraints (the post-v053 home for contributor-facing invariants). The contracts.md additions (Pre-commit step ordering amendment + new Plugin versioning section) land in place — they're user-facing wire contracts that already belong there. Implementation work (repo settings flip, hook tightening, release-please workflow files) remains out of scope per the proposal's §2 framing.

## Modifications

Re-targeted from the proposal's original placement to align with the v053 NFR boundary discipline (the proposal predates v053 — filed 2026-05-07T03:01:12Z, before NFR migration at 2026-05-08T03:17:18Z).

**Re-targeting:**

- The proposal's §"Commit and merge discipline" content MUST land in `non-functional-requirements.md` (under `## Constraints`), NOT `constraints.md`. Conventional Commits + rebase-merge bind only contributors; end users never see commit messages or merge strategy. Per the v053 boundary: contributor-facing invariants live in non-functional-requirements.md.
- The `contracts.md` §"Pre-commit step ordering" amendment lands in place (the section already lives in contracts.md and the proposal asks to amend, not move).
- The new `contracts.md` §"Plugin versioning" lands in place (release-please's auto-managed `plugin.json.version` is user-facing — the version is in the shipped plugin manifest visible to plugin users via the marketplace).

**Content additions:**

1. `contracts.md` §"Pre-commit step ordering" — the existing description of commit-msg stage now mentions a TWO-step gate: first the new Conventional Commits subject-prefix gate, then the v034 D3 Red→Green replay hook. Cross-references the new NFR sub-section.

2. `contracts.md` §"Plugin versioning" — NEW section describing release-please's role: `plugin.json.version` is auto-managed; `marketplace.json` carries no version; per-commit Conventional Commits → semver mapping (feat → MINOR, fix → PATCH, feat!/fix!/BREAKING CHANGE: → MAJOR); release-please-config.json + .release-please-manifest.json at repo root; CHANGELOG.md at repo root.

3. `non-functional-requirements.md` ### "Commit and merge discipline" — NEW sub-section under ## Constraints codifying: Conventional Commits 1.0 mandate (with valid type list); rebase-merge-only master strategy with GitHub repo settings; local commit-msg hook validating CC prefix BEFORE v034 D3 dispatch with the canonical type-set regex; OPTIONAL PR-title-validation workflow (advisory only).

**Out of scope (proposal §2 implementation work):**

- Repo settings flip (`gh api PATCH /repos/.../livespec`) — separate follow-up commit/PR.
- Local hook tightening in `dev-tooling/checks/red_green_replay.py` (or sibling check) — separate follow-up commit/PR.
- `.github/workflows/release-please.yml` + `release-please-config.json` + `.release-please-manifest.json` — separate follow-up commit/PR.
- `marketplace.json` `version` field omission verification — quick follow-up.

**Open questions resolved per the proposer's recommendations (§4):**

1. Local commit-msg hook rejects non-Conventional subjects on feature branches too (branch-internal-history hygiene; trivial cost).
2. OPTIONAL PR-title-validation skipped for v1; revisit if PR-list noise becomes a problem.
3. release-please configuration lives at repo root.
4. CHANGELOG.md auto-maintained at repo root.


## Resulting Changes

- contracts.md
- non-functional-requirements.md
