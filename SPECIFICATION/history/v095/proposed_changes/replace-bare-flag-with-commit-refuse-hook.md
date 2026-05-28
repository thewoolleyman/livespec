---
topic: replace-bare-flag-with-commit-refuse-hook
author: claude-opus-4-7
created_at: 2026-05-28T08:05:00Z
---

## Proposal: replace-bare-flag-with-commit-refuse-hook

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/contracts.md

### Summary

Replace the family-wide `core.bare = true` primary-checkout invariant with a `pre-commit` / `pre-push` "commit-refuse hook" invariant. Every livespec-governed primary checkout MUST host a populated working tree that tracks `origin/master` via normal `git pull --ff-only`, and MUST install a portable POSIX-shell `.git/hooks/pre-commit` and `.git/hooks/pre-push` hook that exits 1 with a "use a worktree" message when `git rev-parse --show-toplevel` equals the configured primary path. Worktrees share the `.git/` directory and inherit the hook script; because the toplevel check fails inside a worktree, the hook is a no-op there and worktree commits proceed normally. Rename the related NFR section §"Bare-flag enforcement" → §"Primary-checkout commit-refuse hook" and §"Bare-flag bootstrap procedure" → §"Commit-refuse hook bootstrap procedure", and replace the `### primary-checkout-bare-flag-set` doctor invariant entry with `### primary-checkout-commit-refuse-hook-installed`. Update every cross-reference in `non-functional-requirements.md` and `contracts.md` accordingly. The new mechanism preserves the "no commits at primary" guarantee with strictly less collateral damage than the bare-flag mechanism: `git fetch`, `git pull --ff-only`, `git show`, and ordinary on-disk reads at primaries all work normally.

### Motivation

The `core.bare = true` mechanism (landed in v091 as a livespec-private rule and promoted in v093 to a family-wide invariant per `family-wide-bare-flag-invariant`) has produced a real and recurring bug: primary checkouts at `/data/projects/<repo>/` are frozen at pre-bare-flag content and never refresh on `git fetch`, because a bare repository has no working tree to update. This forces every consumer of primary on-disk reads — doctor cross-boundary invariants, ad-hoc `cat` / `Read` invocations from agents, copier-template scaffolding readers — to use `git show HEAD:<path>` instead, a workaround already documented in user memory under `feedback_bare_flag_use_git_show_not_filesystem` ("Cross-repo doctor checks reading sibling files MUST use `git -C <clone> show HEAD:<path>`; working trees are stale by design"). The bare-flag mechanism, in other words, makes every on-disk read of a primary's spec/contracts/work-items file a foot-gun: filesystem reads return stale content silently, and only the per-invariant author's vigilance keeps the read paths correct.

The original goal of the bare-flag rule — preventing direct commits to the primary checkout, forcing every edit through `git worktree add` — does NOT require the bare-flag's collateral effect of suppressing the working tree. A `pre-commit` / `pre-push` hook that refuses to run when invoked at the primary path achieves the same "no commits at primary" guarantee while leaving the working tree populated and `git pull --ff-only`-refreshable. The hook fires exactly when an edit attempts to land on the primary (the failure mode the bare-flag was preventing); it is silent at every worktree (the success mode the bare-flag tolerates); and it imposes zero cost on reads, fetches, and pulls (the regression the bare-flag introduced).

The new mechanism is also strictly more inspectable: a contributor can `cat` or `Read` any file at a primary checkout and see its current `origin/master` content directly, instead of having to remember the `git show` workaround. Doctor cross-boundary invariants that walk sibling repos can read filesystem paths normally. The `feedback_bare_flag_use_git_show_not_filesystem` workaround becomes obsolete with this PC.

This PC keeps the three-layer enforcement architecture intact (NFR rule + bootstrap step + doctor invariant), only swapping the underlying mechanism. The shared check at `livespec_dev_tooling.checks.primary_checkout_bare_flag_set` becomes `livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed`; the canonical doctor-invariant slug becomes `primary-checkout-commit-refuse-hook-installed`; the bootstrap step continues to be a per-repo idempotent entry point, only its action changes from "set `core.bare = true`" to "install the commit-refuse hook script at `.git/hooks/pre-commit` and `.git/hooks/pre-push`".

### Heading-coverage co-edit discipline

Both renamed sections in `non-functional-requirements.md` are H3 headings (§"Bare-flag bootstrap procedure" is H3 at line 762; "Bare-flag enforcement" is a bold inline phrase inside §"Workflow discipline — spec-side changes" at line 760, not a heading at all). The renamed doctor-invariant entry `### primary-checkout-bare-flag-set` in `contracts.md` is also H3 (line 178). The `tests/heading-coverage.json` file tracks ONLY H2 headings (verified empirically — every entry's `heading` field begins with `"## "`, no `"### "` entries exist). Therefore this PC requires NO `tests/heading-coverage.json` co-edit under the v064 / spec.md §"Self-application" co-edit discipline.

### Sections to rewrite

- `non-functional-requirements.md` — bold inline phrase "**Bare-flag enforcement.**" at line 760 (inside §"Workflow discipline — spec-side changes") → renamed to "**Primary-checkout commit-refuse hook.**". Body rewritten to describe the hook mechanism (every primary checkout installs a `.git/hooks/pre-commit` + `.git/hooks/pre-push` hook that exits 1 when `git rev-parse --show-toplevel` equals the configured primary path, no-op at worktrees because their toplevel differs). The three-companion-mechanism framing (NFR rule + bootstrap step + doctor invariant) stays.

- `non-functional-requirements.md` §"Bare-flag bootstrap procedure" (H3 at line 762) → renamed to §"Commit-refuse hook bootstrap procedure". Four-clause bootstrap contract stays in shape but the action becomes "install the commit-refuse hook script idempotently at `.git/hooks/pre-commit` and `.git/hooks/pre-push`"; the verifier is the renamed doctor invariant `primary-checkout-commit-refuse-hook-installed`. Add explicit clause: re-running bootstrap MUST be idempotent (no duplicate hook bodies) AND MUST NOT overwrite a user-customized existing hook without surfacing a warning (the bootstrap entry point detects an existing non-livespec hook body and emits a warning rather than silently replacing it; the user resolves by either accepting the overwrite or merging the livespec hook body into their custom hook).

- `contracts.md` §"Doctor cross-boundary invariants" — `### primary-checkout-bare-flag-set` entry at line 178 → renamed to `### primary-checkout-commit-refuse-hook-installed`. Body rewritten to describe what the check verifies: that `<project-root>/.git/hooks/pre-commit` and `<project-root>/.git/hooks/pre-push` both exist, are executable, and contain a recognizable livespec commit-refuse hook body (a minimal POSIX-shell snippet that performs the toplevel comparison and exits 1 on match). The shared-implementation framing stays (the check ships in `livespec-dev-tooling` at `livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed`); the wiring-completeness invariant from v094 governs how every consumer wires this canonical slug into its `just check` aggregate.

- `contracts.md` §"`master-direct-uncommitted-spec-edits`" (line 192) — back-reference at line 202 mentions "sibling `primary-checkout-bare-flag-set` invariant cannot physically prevent (the bare-flag is scoped to the primary checkout only..."). Rewrite to reference the new invariant name and explain the new mechanism's complementarity: the commit-refuse hook prevents the primary-checkout-commit failure mode at its source, while `master-direct-uncommitted-spec-edits` still surfaces secondary-worktree-on-master edits as `warn` (which the commit-refuse hook does not catch, since secondary worktrees on master pass the hook's toplevel check and proceed to commit).

### Proposed prose

The complete substitute prose for each affected section is given below. The revise step composes these into the `resulting_files[].content` payload by splicing them into the current `non-functional-requirements.md` and `contracts.md` bodies at the corresponding spans.

#### `non-functional-requirements.md` — replace the inline "Bare-flag enforcement." paragraph (line 760) with:

> **Primary-checkout commit-refuse hook.** Every livespec-governed primary checkout MUST host a populated working tree tracking `origin/master` via normal `git pull --ff-only` AND MUST install a `.git/hooks/pre-commit` and `.git/hooks/pre-push` hook that refuses to run at the primary. The rule is family-wide-by-intent: it applies UNIFORMLY to `livespec` itself, every `livespec-impl-*` plugin's primary checkout, `livespec-dev-tooling`'s primary checkout, `livespec-runtime`'s primary checkout, and every future sibling repo generated from the copier template per `contracts.md` §"Shared content sync — copier template". A repo whose primary checkout lacks the commit-refuse hook (or whose hook body does not match the canonical livespec body) is out-of-contract regardless of which family role it plays. `core.bare` MUST NOT be set on the primary checkout — the v091–v094 bare-flag mechanism is superseded by this hook mechanism, and the bare-flag-induced stale-on-disk-read failure mode is the explicit motivation for the swap.
>
> The hook body is a small portable POSIX-shell snippet that runs `git rev-parse --show-toplevel`, compares the result to the consumer's configured primary path, and exits 1 with a "use a worktree" message on match (refusing the commit / push at the primary) or exits 0 on mismatch (allowing the commit / push at a worktree). Because secondary worktrees share the primary's `.git/` directory and therefore inherit the same hook script, but `git rev-parse --show-toplevel` returns the WORKTREE's path (not the primary's) when invoked inside a worktree, the toplevel comparison fails inside every worktree and the hook is a silent no-op there. The mechanism is the minimum that achieves the "no commits at primary" guarantee while leaving the working tree populated and `git pull --ff-only`-refreshable.
>
> The hook pairs with two companion mechanisms: a bootstrap step (see §"Commit-refuse hook bootstrap procedure" below) that idempotently installs the hook on fresh clones, and the `primary-checkout-commit-refuse-hook-installed` doctor static invariant (see `contracts.md` §"Doctor cross-boundary invariants") that verifies the hook is installed and contains the canonical body on every doctor run. The canonical implementation of the latter ships in `livespec-dev-tooling` at `livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed` per `contracts.md` §"Shared code sync — livespec-dev-tooling"; every consumer repo MUST wire it into its `just check` aggregate AND CI matrix on the same invocation-agnostic cadence governing every other shared check, per the wiring-completeness invariant codified in §"Shared code sync — livespec-dev-tooling" (added by v094). Per-clone non-hook state is the failure mode the bootstrap step addresses; user-tampering or pre-bootstrap clones are the failure mode the doctor invariant addresses. Together the three (NFR rule, bootstrap step, doctor invariant) make the workflow discipline structurally enforceable rather than author-vigilance-dependent — and the universality of the rule means a single shared implementation of the check satisfies the contract for every sibling at once.
>
> The mechanism explicitly preserves on-disk reads at the primary. Doctor cross-boundary invariants and ad-hoc agent reads MAY read filesystem paths at the primary directly; `git show HEAD:<path>` is no longer required as a workaround for stale-working-tree state. The `feedback_bare_flag_use_git_show_not_filesystem` workaround documented in agent memory becomes obsolete upon adoption of this contract.

#### `non-functional-requirements.md` — replace §"Bare-flag bootstrap procedure" (H3 at line 762, body through line 773) with:

> ### Commit-refuse hook bootstrap procedure
>
> Every livespec-governed repository MUST surface an idempotent bootstrap entry point that, when invoked, installs the canonical commit-refuse hook body at `.git/hooks/pre-commit` AND `.git/hooks/pre-push` in the primary checkout. The exact entry point shape is implementation choice (a `just bootstrap` target, a livespec-managed setup skill, a hook chained into clone-time tooling, etc.); the contract is that:
>
> 1. The entry point MUST be documented in the repo's `README.md`, `CLAUDE.md`, or equivalent first-touch-discovery surface.
> 2. Running the entry point on a fresh clone MUST result in `.git/hooks/pre-commit` and `.git/hooks/pre-push` both existing, executable (`chmod +x`), and containing the canonical livespec commit-refuse hook body.
> 3. Running the entry point again on a checkout that already has the canonical hook body installed at both paths MUST be a no-op (idempotent; no error, no duplicate content, no side-effect).
> 4. The entry point MAY perform other clone-time setup (lefthook installation, dependency installation, mise tool resolution) as long as the hook-install step is uncoupled from the rest (a partial failure in another setup step MUST NOT leave the hook unset).
> 5. When `.git/hooks/pre-commit` or `.git/hooks/pre-push` already exists with non-canonical content (a user-customized hook), the entry point MUST NOT silently overwrite. Acceptable resolutions: (a) emit a warning naming the customized hook path and require the user to either remove the customization or manually merge the livespec hook body into it; (b) preserve the customized hook and emit a `warn` finding that the doctor invariant will subsequently surface. The entry point MUST NOT proceed as if the install succeeded when a custom hook is present.
>
> The bootstrap step is what makes the family-wide commit-refuse hook mandate enforceable across clones rather than constituting a single-workstation hack. Doctor's `primary-checkout-commit-refuse-hook-installed` invariant (see `contracts.md` §"Doctor cross-boundary invariants") verifies the hook's presence and canonical body; the bootstrap step is the mechanism by which a user resolves a doctor `fail` finding on that invariant.
>
> The bootstrap-step requirement is itself family-wide-by-intent: every livespec-governed sibling repo — `livespec`, every `livespec-impl-*` plugin, `livespec-dev-tooling`, `livespec-runtime`, and every copier-template-generated sibling — MUST surface its own idempotent bootstrap entry point satisfying the five contract clauses above. The shared check at `livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed` is the mechanical verifier across the family; the per-repo `just bootstrap` recipe (or equivalent entry point) is the mechanical fixer that resolves a `fail` finding on a fresh or tampered clone. The bootstrap implementation is per-repo-private — a sibling MAY embed the hook-install steps directly, MAY copy a starter recipe from `livespec`'s own `justfile`, or MAY inherit it via copier-template scaffolding — but the contractual existence of an idempotent bootstrap entry point is universal.
>
> The canonical hook body is a small portable POSIX-shell snippet of the following shape (illustrative; the canonical text lives in `livespec-dev-tooling` alongside the shared check implementation and is the source of truth for the canonical body the doctor invariant compares against):
>
> ```sh
> #!/bin/sh
> # livespec commit-refuse hook — refuses commits/pushes at the primary checkout.
> # No-op at worktrees because git rev-parse --show-toplevel returns the worktree path there.
> primary_path="$(git config --get livespec.primaryPath || true)"
> toplevel="$(git rev-parse --show-toplevel)"
> if [ -n "$primary_path" ] && [ "$toplevel" = "$primary_path" ]; then
>   echo "livespec: refusing commit/push at primary checkout ($toplevel); use a worktree" >&2
>   exit 1
> fi
> exit 0
> ```
>
> The configured primary path is stored under `livespec.primaryPath` in the primary's `.git/config` and is set by the bootstrap step. Worktrees inherit the `.git/` directory but their `git rev-parse --show-toplevel` returns the worktree's own path, so the comparison fails and the hook exits 0.

#### `contracts.md` — replace the entire `### primary-checkout-bare-flag-set` entry (lines 178–190) with:

> ### `primary-checkout-commit-refuse-hook-installed`
>
> Every livespec-governed primary checkout MUST install a `.git/hooks/pre-commit` and `.git/hooks/pre-push` hook whose body refuses to run when invoked at the primary checkout. The rule is family-wide: it applies to `livespec` itself, every `livespec-impl-*` plugin's primary checkout, `livespec-dev-tooling`'s primary checkout, `livespec-runtime`'s primary checkout, and every future sibling repo generated from the copier template per §"Shared content sync — copier template". The check reads `<project-root>/.git/hooks/pre-commit` and `<project-root>/.git/hooks/pre-push`, verifies each exists and is executable, and verifies each contains the canonical livespec commit-refuse hook body (recognized via a stable marker comment string the canonical body MUST carry). The check fires `fail` when either hook is missing, non-executable, or contains a non-canonical body (including the empty file case). The narration directs the user to invoke the repo's documented bootstrap step (per `non-functional-requirements.md` §"Commit-refuse hook bootstrap procedure"), which idempotently installs the hook.
>
> The canonical implementation of this check ships in `livespec-dev-tooling` at `livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed`. The check is layout-independent (no `[tool.livespec_dev_tooling]` role keys consumed) and so belongs to the shared inventory per §"Shared code sync — livespec-dev-tooling" → §"Shared check inventory" partition criterion: its intent and CLI surface are stable across every livespec-governed project, making a single implementation correct for the whole family. Every consumer repo MUST run the shared check in their `just check` aggregate AND CI matrix per the wiring-completeness invariant codified in §"Shared code sync — livespec-dev-tooling" (added by v094) and per the same invocation-agnostic discipline that governs every other shared check (per `non-functional-requirements.md` §"Enforcement suite" — the check ships from the shared inventory, the consumer repo decides only the recipe naming and the per-repo aggregate-list entry).
>
> The shared check runs once per `just check`/CI invocation against the project root. Repo-local plugin-doctor catalog instances of the same check — e.g., `livespec`'s plugin-doctor static-phase entry that runs per spec tree under each `/livespec:doctor` invocation — remain valid and MAY coexist with the shared check: the two scopes/cadences are complementary (the shared check is a CI-time backstop against the project root; the plugin-doctor entry runs per-spec-tree under the wrapper-lifecycle of every `/livespec:*` sub-command). Defense-in-depth: both are retained.
>
> The invariant is structural per the catalogue's intro principles (binary, contract-level, mechanically checkable); the canonical hook body is either installed at both paths or it isn't. The check MUST NOT distinguish between "hook missing" and "hook present but body is non-canonical" at the contract level — both fire equally; both are corrected by the same bootstrap invocation. (The narration MAY name the specific failure mode for diagnostic clarity, but the structural `fail` finding is identical.)
>
> The check applies to the primary checkout's `.git/hooks/` directory only. Secondary worktrees share the `.git/` directory and therefore inherit the same hook scripts; the check does NOT need to inspect each worktree separately, and worktrees MUST NOT carry their own divergent `pre-commit` / `pre-push` hooks. (Per-worktree hook overrides via the `core.hooksPath` config in a worktree are forbidden by this contract.)
>
> Fresh clones that have not yet had the bootstrap step run fail this invariant immediately. This is intentional: the failure is the mechanism by which a fresh contributor discovers the discipline. The narration includes the corrective bootstrap command verbatim so the resolution path is one terminal invocation away.
>
> `core.bare` MUST NOT be set on the primary checkout. The v091–v094 bare-flag mechanism is superseded by this hook mechanism (see `non-functional-requirements.md` §"Primary-checkout commit-refuse hook" for the motivation: the bare-flag mechanism caused stale-on-disk-read failures at primaries that the hook mechanism does not). The doctor invariant MAY additionally surface a `fail` when `core.bare = true` is set on the primary, to catch the legacy-state case during the transition from the bare-flag mechanism to the hook mechanism.

#### `contracts.md` — replace the back-reference in §"`master-direct-uncommitted-spec-edits`" body (line 202) with:

> The check covers the secondary-worktree-on-master bypass that the sibling `primary-checkout-commit-refuse-hook-installed` invariant cannot physically prevent (the commit-refuse hook fires only when `git rev-parse --show-toplevel` equals the primary path; secondary worktrees on master pass that comparison and proceed to commit, so a `git worktree add /path master` + edit + commit at the secondary worktree bypasses the hook). The two checks together close the enforcement loop: the hook catches commits attempted at the primary, and this invariant surfaces uncommitted spec edits at any worktree (primary or secondary) whose HEAD is master.

### Resulting files

The revise step composes `resulting_files[]` with the full updated content of two spec files:

- `non-functional-requirements.md` — splice the new "**Primary-checkout commit-refuse hook.**" paragraph in place of the existing "**Bare-flag enforcement.**" paragraph (line 760), and splice the new §"Commit-refuse hook bootstrap procedure" body in place of the existing §"Bare-flag bootstrap procedure" body (H3 at line 762 through line 773). No other content in the file is touched.

- `contracts.md` — splice the new `### primary-checkout-commit-refuse-hook-installed` body in place of the existing `### primary-checkout-bare-flag-set` body (lines 178–190), and splice the updated back-reference in place of the existing back-reference inside `### master-direct-uncommitted-spec-edits` (line 202). No other content in the file is touched.

No `tests/heading-coverage.json` co-edit is required (verified: the renamed sections are H3 / inline-bold, and heading-coverage.json tracks only H2 entries).

### Spec commitments

This PC declares no `spec_commitments.impl_followups[]` in the front-matter, because the impl-side work for the new mechanism is the explicit scope of subsequent phases of the same epic (`li-unbare`):

- Phase 2: rename the shared check at `livespec_dev_tooling.checks.primary_checkout_bare_flag_set` → `livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed`, change its body to verify the hook installation rather than the bare-flag config, and ship a new minor release of `livespec-dev-tooling` carrying the renamed slug.

- Phase 3: update every consumer's `just bootstrap` recipe to install the commit-refuse hook (replacing `git config core.bare true`), unset `core.bare` on every primary checkout, and bump-pin to the new `livespec-dev-tooling` release that carries the renamed shared check.

The spec commits to the invariant; each phase's work-item lands separately under epic `li-unbare` and is tracked via the impl-plugin's normal work-item store, not via this PC's front-matter declaration. This pattern matches v094's `wiring-completeness-invariant` PC, which similarly declared no `spec_commitments.impl_followups[]` and tracked the impl follow-ups as sibling work-items under their own epic.
