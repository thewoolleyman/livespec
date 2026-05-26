---
topic: coordinating-epic-stale-revise-enforcement
author: claude-opus-4-7
created_at: 2026-05-26T07:00:00Z
---

## Coordinating-epic header

This PC is a **coordinating epic** that spans three repos in the livespec family. It owns the cross-cutting design decisions and links to two child PCs that carry the per-repo implementation surface:

- **This PC (livespec)** — Layers 1, 2, 3' (skill-level prose changes); the cross-cutting convention for declaring parent/child PCs.
- **Child PC (livespec-impl-plaintext)** — Layer 4 (work-item merge-evidence schema + static check). Topic: `work-item-merge-evidence`. See `livespec-impl-plaintext/SPECIFICATION/proposed_changes/work-item-merge-evidence.md`.
- **Child PC (livespec-dev-tooling)** — Layer 1's underlying shared git-topology check (`no_stale_revise_branches`). Topic: `no-stale-revise-branches-check`. See `livespec-dev-tooling/SPECIFICATION/proposed_changes/no-stale-revise-branches-check.md`.

The children carry a `### Cross-cutting parent` prose section citing back to this PC. They do NOT yet carry a `parent_proposed_change` front-matter field — that field is itself proposed for the first time by §"Proposal: introduce parent_proposed_change front-matter field" below; once accepted and the schema widened, the children SHOULD be retroactively edited to carry the field.

The four layers MAY land in any order across the three repos — each repo's revise cycle disposes its own PCs independently. The epic is "complete" when all four layers are merged to their respective `master` branches AND a doctor static run against every spec tree passes.


## Problem statement

The doctor + revise lifecycle as of 2026-05-26 permits a class of orphaned work: a `/livespec:revise` invocation cuts a `vNNN` snapshot, commits to a feature branch, possibly pushes, and stops. The branch can sit unmerged indefinitely. Nothing in the existing tooling refuses to start a new revise pass while a prior one is still in-flight, nothing automatically completes the round-trip to merged-on-`master`, and nothing surfaces the orphaned state on the next session-start.

This was observed on 2026-05-25/26 in livespec-dev-tooling, where a `spec/dev-tooling-revise-v003` branch sat with v003 committed but not merged across multiple agent sessions. The user identified the failure mode as a category — "make it impossible for revise to leave orphan state."

Three categories of root cause:

1. **Skill lifecycle ends at the wrong condition.** `/livespec:revise` declares itself done at "wrapper exit 0; new vNNN exists locally." The condition for "actually done" is "merged to master," but no part of the lifecycle observes that condition. The agent that ran the skill can context-switch freely and the local-completion-status is never re-evaluated.
2. **No persistent ledger semantic for "task open until externally-observable condition holds."** The impl-side work-items JSONL can record `status: closed` with `resolution: fix` and a `commits[]` audit list, but `commits[]` proves only that commits exist — not that they reached master. An agent can close a work-item against unmerged work.
3. **No on-demand surfacing.** Doctor's existing checks operate on spec-tree well-formedness (front-matter, anchor resolution, etc.) but never inspect git topology or PR state. A stale branch is invisible to doctor; the next session has no automatic prompt to attend to it.


## Proposal: introduce parent_proposed_change front-matter field

### Target specification files

- SPECIFICATION/contracts.md
- .claude-plugin/scripts/livespec/schemas/proposed_change_front_matter.schema.json

### Summary

Widen the proposed-change front-matter schema (and the contracts.md section that codifies it) to admit an optional `parent_proposed_change` field carrying the canonical topic of a parent PC. This is the mechanism that makes "coordinating epic" a structural concept rather than prose convention only.

Current schema is `additionalProperties: false` with three properties (`topic`, `author`, `created_at`). The proposed addition is one optional string property.

### Motivation

This very PC is a coordinating epic — a single design that spans three repos. The child PCs in `livespec-impl-plaintext` and `livespec-dev-tooling` need a machine-checkable way to cite this parent. Today the only mechanically-sound way is prose-only cross-reference inside the body, which:

- Cannot be enforced by a static check (no front-matter contract for the relationship to exist).
- Does not survive heading renames in the parent (the prose citation is brittle the same way every cross-spec reference is — see `reference-discipline-invariant.md`).
- Does not make the relationship visible to a static tool walking the tree (a tool inspecting "is this PC part of an epic?" has to grep prose).

The `parent_proposed_change` field gives static tooling a stable hook to:

- Verify the parent topic exists upstream (the upstream repo's PC ledger lists it).
- Refuse to revise+accept a child PC while its parent is still pending (mirrors how Layer 1 below refuses new revise passes while branches are stale).
- Render coordinating-epic dependency graphs without prose parsing.

### Proposed Changes

1. Edit `.claude-plugin/scripts/livespec/schemas/proposed_change_front_matter.schema.json` to add an optional property and update the description:

   ```json
   {
     ...,
     "properties": {
       "topic": { ... },
       "author": { ... },
       "created_at": { ... },
       "parent_proposed_change": {
         "type": "string",
         "description": "Canonical topic of a parent / coordinating-epic proposed change this PC is a child of. The parent may live in this repo OR in a sibling repo per the livespec family's cross-cutting epic convention. Format: '<repo-short-name>#<topic>' when the parent is in a sibling repo (e.g., 'livespec#coordinating-epic-stale-revise-enforcement'); just '<topic>' when in this repo.",
         "pattern": "^([a-z][a-z0-9-]*#)?[a-z][a-z0-9]*(-[a-z0-9]+)*$"
       }
     }
   }
   ```

2. Edit `SPECIFICATION/contracts.md` §"Proposed-change and revision file formats" (or the section that codifies the front-matter — exact section name to be confirmed at revise time) to document the new field:

   > **`parent_proposed_change`** (optional string). When this PC is a child of a coordinating-epic parent PC, this field carries the canonical topic of the parent. The parent MAY live in this repo or in a sibling repo per the livespec family's cross-cutting epic convention; the format `<repo-short-name>#<topic>` cites a sibling repo, the format `<topic>` cites this repo.
   >
   > Coordinating-epic parent PCs themselves do NOT carry this field (they have no parent; they ARE the parent). A PC carrying `parent_proposed_change` MUST cite an existing topic; doctor's static phase MUST verify the cited topic resolves (in the same repo for local references, or against the sibling repo's `proposed_changes/` listing for cross-repo references).

3. Document the bootstrap exemption for this very PC and its two children:

   > Until the schema widening above is accepted (this PC's revise cycle completes), the convention is bootstrapped via prose-only cross-reference in each child PC's body (a `### Cross-cutting parent` section). After acceptance, the three PCs of the inaugural coordinating epic (`coordinating-epic-stale-revise-enforcement` and its two children) SHOULD be retroactively edited via admin commits to add the `parent_proposed_change` field. Doctor static MUST tolerate the prose-only form during the bootstrap window; the `additionalProperties: false` constraint accommodates the field's absence regardless.


## Proposal: Layer 1 — refuse to start /livespec:revise while a stale spec-revise branch exists

### Target specification files

- skills/revise/SKILL.md

### Summary

Add a pre-step to the `/livespec:revise` SKILL.md that runs a doctor-static check (sibling-shipped: `no_stale_revise_branches`, owned by livespec-dev-tooling per the child PC) BEFORE invoking the revise wrapper. The check enumerates local `spec/*` branches and refuses to start a new revise pass when ANY such branch is ahead of master.

### Motivation

The orphaned-v003 incident happened because nothing refused to allow a new revise while the prior one was un-landed. The user could start a fresh /livespec:revise in a new session and the prior orphan would not surface as a blocker. Refusing to start in that condition forces the orphan to be resolved (merge, abandon, or explicit-skip) before new revise work begins.

### Proposed Changes

Edit `skills/revise/SKILL.md` to add a new step between Step 3 (enumerate pending proposed-change files) and Step 4 (capture optional steering intent):

> **Step 3.5 — Stale-branch precondition check.**
>
> Run the `no_stale_revise_branches` shared check (shipped by livespec-dev-tooling per the cross-cutting epic) against the project root. The check:
>
> - Enumerates local refs matching `refs/heads/spec/*` via `git for-each-ref`.
> - For each, computes ahead-count vs `origin/<canonical_branch>` via `git rev-list --left-right --count`.
> - Returns `fail` findings for every branch that is ahead by one or more commits.
>
> If the check returns any `fail` finding, STOP. Surface every stale branch to the user with its name, ahead-count, and most recent commit subject. Direct the user to merge, abandon (push to a backup ref + delete), or use the explicit `--skip-stale-branch-check` flag to override. The override flag MUST be acknowledged in skill narration; silent override is forbidden.
>
> If the check returns clean, proceed to Step 4.

Add the override flag to the §"Inputs" section:

> - `--skip-stale-branch-check` (optional). Skips the Step 3.5 precondition. Mutually exclusive with `--run-stale-branch-check`. When used, the SKILL.md prose MUST surface a warning narration acknowledging the skip.
> - `--run-stale-branch-check` (optional). Forces the Step 3.5 precondition to run even when `pre_step_skip_stale_branch_check` is `true` in `.livespec.jsonc`. Mutually exclusive with `--skip-stale-branch-check`.

The same pattern of explicit-skip + explicit-run + config-key + narration mirrors the existing pre-step doctor static skip semantics; the parallelism is intentional.


## Proposal: Layer 2 — extend auto-enable-merge.yml pattern to every livespec-family sibling

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The livespec repo already ships `.github/workflows/auto-enable-merge.yml` that automatically sets `--auto --rebase` on PRs from the user's allowlist when not draft and not labeled `do-not-merge`. This workflow eliminates the "agent opened a PR but forgot `gh pr merge --auto --rebase`" failure mode for livespec specifically.

The two sibling repos (`livespec-impl-plaintext`, `livespec-dev-tooling`, and any future siblings carrying the `livespec-sibling` GitHub topic) do NOT have this workflow today. The result is that PRs opened against those repos sit waiting for manual merge — the same failure mode this workflow fixes in livespec.

This proposal codifies the auto-enable-merge workflow as a required workflow for every livespec-sibling repo, and routes its delivery through the cross-repo coordination automation surface defined in livespec-dev-tooling.

### Motivation

The auto-enable-merge.yml workflow is the partial-Layer-2-implementation that already exists in livespec. It works (per the workflow's own header comment, it supersedes a previously-broken `GITHUB_TOKEN`-based approach via App-token mint). Propagating it to siblings is mechanical (the workflow's logic is identical; only the App installation needs to be present on each repo).

### Proposed Changes

Add a new §"Auto-enable-merge workflow" subsection under `SPECIFICATION/contracts.md` §"Cross-repo coordination — pin-and-bump" (or alternatively under the dev-tooling repo's automation surface section; the reviser picks the better home):

> ### Auto-enable-merge workflow
>
> Every livespec-sibling repo MUST ship `.github/workflows/auto-enable-merge.yml` that, on `pull_request` events with types `opened`, `reopened`, `ready_for_review`, automatically sets `--auto --rebase` on the PR when:
>
> - The PR is not a draft.
> - The PR does not carry a `do-not-merge` label.
> - The PR author is in the per-repo allowlist (`thewoolleyman` initially, extended via a `pull_request_author_allowlist` repo variable).
>
> The workflow MUST authenticate via a GitHub App installation token (not `GITHUB_TOKEN`) because the `enablePullRequestAutoMerge` GraphQL mutation requires admin-level access that `github-actions[bot]` lacks. The App MUST be installed on every sibling repo; the install grant supplies the access. Required repo secrets: `APP_ID`, `APP_PRIVATE_KEY`.
>
> The canonical implementation is `.github/workflows/auto-enable-merge.yml` in the livespec repo. Sibling repos MUST track byte-equivalence with the canonical version; drift surfaces as a doctor-static finding via livespec-dev-tooling's `check_branch_protection_alignment` (or a new sibling check, exact home TBD at revise time).

This proposal does NOT specify the implementation steps (file creation in each sibling repo); those are work-items in each sibling's impl-plaintext store. This PC only declares the contract.

Reference the existing canonical implementation: `livespec/.github/workflows/auto-enable-merge.yml`.


## Proposal: Layer 3' — doctor LLM-phase surfaces open spec-PR status

### Target specification files

- skills/doctor/SKILL.md
- specification-templates/livespec/prompts/doctor-llm-objective-checks.md (currently null per template.json; this proposal authors it)

### Summary

Add a new doctor LLM-driven objective check that, on every `/livespec:doctor` invocation, queries the local repo's open PRs against `spec/*` branches via `gh pr list` and surfaces findings for any PR whose state warrants user attention:

- **`open-spec-pr-red-ci`** [high]: PR is open and CI is failing.
- **`open-spec-pr-green-unmerged`** [medium]: PR is open, CI is green, but auto-merge is not enabled.
- **`open-spec-pr-merge-conflict`** [high]: PR has merge conflicts.

Each finding integrates with the existing accept/defer/dismiss per-finding dialogue. Accept on green-unmerged could invoke `gh pr merge --auto --rebase`; accept on red-ci prompts the user to investigate.

### Motivation

Layers 1 and 2 are PREVENTIVE — they refuse to create the bad state and they auto-clear it under normal CI-green conditions. Layer 3' is the RESIDUAL surfacer for the cases that fall through: a PR with red CI that auto-merge cannot complete, a PR opened by a separate session the user hasn't seen, a merge-conflict that materialized after the PR was opened.

The previously-considered alternative (a daily cron workflow posting comments on PRs) was REJECTED on user feedback dated 2026-05-26: bot-driven PR-comment / label-spam patterns are spammy and notification is not a substitute for tooling that prevents or clears the bad state. The doctor on-demand approach surfaces the same information only when the user runs doctor — opt-in awareness, no spam.

### Proposed Changes

Author `specification-templates/livespec/prompts/doctor-llm-objective-checks.md` (currently null per `template.json`'s `doctor_llm_objective_checks_prompt`) with the following content as its first dimension. The prompt MAY also carry other objective-check dimensions; this PC declares only the open-spec-PR dimension. Edit `template.json` to set `doctor_llm_objective_checks_prompt: "prompts/doctor-llm-objective-checks.md"`.

Prompt body sketch (full draft lands at revise time):

> ## Dimensions
>
> ### 1. Open spec-PR status (skill-baked — only applicable when the spec tree's `.livespec.jsonc` declares a project hosted on GitHub)
>
> Query the local repo's open PRs via `gh pr list --state open --head 'spec/*' --json number,state,statusCheckRollup,headRefName,createdAt,updatedAt,mergeable`. For each PR, emit a finding when its state warrants user attention:
>
> - When `statusCheckRollup` contains any FAILURE / ERROR / CANCELLED status: emit `doctor-llm-objective-open-spec-pr-red-ci` with severity high. Message: PR #N (`<headRefName>`) has red CI; failing checks: `<list>`. Path: empty. Line: 0.
> - When all status checks are SUCCESS and PR is `mergeable: "MERGEABLE"`: emit `doctor-llm-objective-open-spec-pr-green-unmerged` with severity medium. Message: PR #N (`<headRefName>`) is green and mergeable but unmerged. Path: empty. Line: 0.
> - When PR is `mergeable: "CONFLICTING"`: emit `doctor-llm-objective-open-spec-pr-merge-conflict` with severity high. Message: PR #N (`<headRefName>`) has merge conflicts against master. Path: empty. Line: 0.
>
> Emit no findings when `gh` is unavailable or the project is not GitHub-hosted; surface the no-op as a structured `info`-level log rather than a finding, so the absence of findings is auditable.

Edit `skills/doctor/SKILL.md` §"Steps" to acknowledge the new dimension in Step 6 (skill-baked objective checks):

> Add a fourth bullet:
>
> - **Open spec-PR status** (skill-baked, GitHub-hosted projects only). Surfaces findings for open `spec/*` PRs whose state warrants attention per `doctor-llm-objective-checks.md` §"Open spec-PR status".

The new check uses `gh` (network-aware), which is permitted in the LLM-driven phase per the existing LLM-phase contract; the static phase remains network-free per `constraints.md`.


## Cross-cutting acceptance criteria

The coordinating epic is complete when ALL of the following hold:

1. This parent PC's proposals are revised + accepted in livespec, landing the schema widening, Layer 1 skill prose, Layer 2 cross-repo contract, and Layer 3' doctor prose.
2. The child PC `work-item-merge-evidence` (in livespec-impl-plaintext) is revised + accepted, landing the schema fields, the canonical_branch config key, the static check, and the migration script.
3. The child PC `no-stale-revise-branches-check` (in livespec-dev-tooling) is revised + accepted, landing the new check module, the inventory entry, and its paired test per red-green-replay discipline.
4. The auto-enable-merge.yml workflow is propagated to both sibling repos (impl-plaintext and dev-tooling) as a follow-up impl-side work-item in each.
5. Doctor static passes against all three spec trees post-acceptance.
6. The inaugural cross-cutting epic (this PC + its two children) is retroactively annotated with the new `parent_proposed_change` front-matter field, demonstrating the convention end-to-end.

Each numbered item is independently observable; the epic does NOT need to land atomically. Partial completion (e.g., only items 1+3 land) is OK; the remaining work surfaces via doctor LLM-phase Layer 3' findings.
