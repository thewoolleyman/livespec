---
topic: spec-governance-pr-merge
author: openai-codex
created_at: 2026-08-03T01:29:20Z
---

## Proposal: Auto-register spec pull requests for rebase merge only after green gates

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Add `spec_governance.spec_pr_merge` with safe default `manual` and opt-in `auto-on-green`, preserving rebase-only history and the required CI gate while bringing the shipped auto-enable workflow under an explicit spec-side policy.

### Motivation

Repo thewoolleyman/livespec, plan/spec-side-autonomy/research/brainstorm.md identifies spec pull-request merge as a mechanical Class (a) gate. The shipped `auto-enable-merge.yml` workflow already registers eligible pull requests for rebase auto-merge unless they are drafts or carry `do-not-merge`; this proposal makes its behavior for pull requests touching a governed spec root explicit and safely configurable. It changes neither review doctrine nor CI/branch-protection floors.

Scope note for the reviser, not text to ratify: this proposal does not edit repository livespec-orchestrator-beads-fabro or its `drive` action boundary, and it does not disposition any sibling proposed-change file.

### Proposed Changes

In spec.md under the existing `## Sub-command lifecycle` heading, create or extend `### Spec-governance policy settings` and the core-owned top-level `.livespec.jsonc` `spec_governance` block. Add the declarative row `spec_pr_merge` (enum `manual | auto-on-green`, safe default `manual`, per-proposal override supported) and name its resolver `effective_spec_pr_merge`. A proposed-change file MAY carry `spec_pr_merge_policy: manual | auto-on-green` in front matter. The resolver MUST evaluate hard floors first, then the per-proposal override, then the global setting, then the safe default. For a pull request containing more than one ratified proposal, the pull-request effective policy MUST be the conservative fold: `auto-on-green` only when every included proposal resolves to `auto-on-green`; any `manual` result makes the pull request manual. Missing/malformed config or front matter and unknown/wrong-typed values MUST resolve to `manual` and MUST NOT raise.

Separate registration-time hard floors from completion-time host guarantees. Registration requires: the spec change has been ratified through revise; an open non-draft pull request targets the governed default branch; the pull-request author satisfies the shipped workflow's human/release-App allowlist; no `do-not-merge` label is present; no unresolved GitHub changes-requested review exists at registration time; the repository permits rebase merge; and the policy journal is writable. Only then may `auto-on-green` register the GitHub operation equivalent to `gh pr merge --rebase --auto`. After registration, branch protection and host merge-queue semantics own completion: the required all-green gate MUST succeed before merge, and a post-registration review blocks completion only when the host's configured protection supplies that behavior. The policy MUST NOT bypass, weaken, relabel, or replace a required status check, MUST NOT use squash or merge-commit mode, and MUST NOT merge a red pull request. A hosting service that cannot provide merge-when-green semantics MUST require human input instead of polling and force-merging.

In contracts.md under `## Sub-command wire contracts`, create or extend the core spec-governance control contract independently of sibling proposals. Its deterministic reference CLI is `.claude-plugin/scripts/bin/spec_governance.py`; it owns `--project-root <path> --show-effective`, allowlisted `--action <action>` policy edits, and validated `--journal-event-json <path>` appends. Create or extend the single declarative `ConfigKey` registry, the committed manifest `.claude-plugin/scripts/livespec/spec_governance/api_configurable_keys.json`, the action grammar, and the config-write allowlist; amend any wrapper/CLI catalogue whose wording would otherwise exclude this non-LLM control CLI. Add `set-spec-pr-merge:global:<manual-or-auto-on-green-or-clear>` for the config value and `set-spec-pr-merge:proposal:<proposal-stem>:<manual-or-auto-on-green-or-clear>` for front matter. `clear` removes only the selected global value or proposal override. The CLI MUST validate stems, preserve unrelated JSONC keys/comments and Markdown body bytes, and use atomic replacement. A policy edit MUST NOT open, merge, close, or otherwise transition a pull request.

The shared `awaits_manual_spec_pr_merge` predicate gates registration and human-merge advertisement. It is true exactly when the effective policy is `manual` or a registration-time hard floor prevents registration; it becomes false once an eligible pull request is validly registered for merge-when-green, even while CI is pending or red. Any awareness or advertisement surface that presents a spec pull request as awaiting a human merge MUST consume this exported predicate rather than re-derive it. Core does not normatively name or own any orchestrator awareness surface.

Create or extend the append-only journal `<project-root>/tmp/livespec-spec-governance-journal.jsonl`, written through the reference CLI. Every auto-on-green attempt MUST append an event naming `spec_pr_merge`, effective source, pull-request identity, registration result, required-gate state, and final merge evidence when it becomes available. The GitHub pull-request timeline MAY be the durable final-evidence leg, but the policy journal MUST name the governing setting; journal failure requires human input and prevents registration.

In constraints.md, state that malformed policy resolves to the safe `manual` default; every hard floor precedes overrides; and the setting is workflow automation, not authorization to bypass CI.

In non-functional-requirements.md under the exact live heading `### Workflow discipline — spec-side changes`, amend step 5 so an effective `manual` policy leaves the pull request for human merge while `auto-on-green` registers rebase auto-merge after opening and before CI completes. Co-amend step 6 so branch/worktree cleanup occurs after confirmed merge under either policy, without assuming a manual `gh pr merge --delete-branch` invocation in the automatic path.

Also amend the `auto-enable-merge.yml` requirement that currently registers every eligible pull request. For a pull request whose diff touches a configured spec root, the workflow MUST obtain `effective_spec_pr_merge` by checking out the release-pinned thewoolleyman/livespec core artifact to runner scratch and invoking its `spec_governance.py --project-root "$GITHUB_WORKSPACE" --show-effective`; it registers only an eligible `auto-on-green` result. Non-spec pull requests retain every existing eligibility gate: draft state, `do-not-merge` label, human-author allowlist, and the release-please App plus `release-please--` branch exception. Amend the template-fleet cadence sentence so explicit `auto-on-green` configuration supplies spec-PR cadence parity. The built-in template and repository thewoolleyman/livespec declare `spec_governance.spec_pr_merge: auto-on-green`; other repos inherit safe `manual` when absent.

In scenarios.md, extend `## Happy-path revise` with global auto-on-green, a per-proposal manual override defeating a global auto setting, and multiple proposals conservatively folding to manual. Add `## Error path — spec pull request cannot auto-merge` for a red required gate, draft/label/review blockers, invalid settings resolving to manual, unsupported hosting, journal failure, and all-defaults behavior arming nothing. The revise payload MUST add that heading to `tests/heading-coverage.json` with a `TODO` reason and maintain every new behavior clause's `clauses[]` link in the same `resulting_files[]` payload.
