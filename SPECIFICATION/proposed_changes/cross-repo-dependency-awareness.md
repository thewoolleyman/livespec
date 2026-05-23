---
topic: cross-repo-dependency-awareness
author: claude-opus-4-7
created_at: 2026-05-23T08:50:00Z
---

## Proposal: cross-repo-dependency-awareness-h2-and-runtime-library-contract

### Target specification files

- contracts.md

### Summary

Add a new H2 `## Cross-repo dependency awareness` to `contracts.md` codifying the typed `DependsOnEntry` union for the work-item `depends_on` field, the cross-repo `cross_repo_targets` manifest in `.livespec.jsonc`, the exhaustive live-walk resolution semantics, the `livespec-runtime` sibling library's contract surface, the consumer-side ranker / doctor exclusion rules, the retry policy, and the GitHub-CLI authentication path. v1 is GitHub-only; GitLab and other forges are deferred. Replaces both the discarded Branch B `cross-project-interdependencies` proposal (rejected in v071) and PR #160's `cross-repo-work-item-dep-awareness` proposal (dropped from the rebased PR #163) with one consolidated contract.

### Motivation

Two independent design threads converged on the same problem: an in-flight work-item in one livespec-governed repo is often blocked by a specific in-flight work-item, an open pull request, or an undeleted branch in a sibling repo. Branch B framed this as epic-completion-aware blocking (the cross-repo state is the gating signal for closing the parent epic); PR #160 framed it as per-iteration ranker-exclusion (the ranker MUST exclude work-items with open external dependencies from candidate ranking). Both framings are correct and complementary; neither alone is sufficient.

The consolidated design unifies them as:

- One typed `depends_on` field per work-item (Model B), absorbing the prior `blocked_by` field's role — semantic dispatch happens on the entry's `kind` discriminator, not on a parallel field. This is a hard break from `blocked_by` (no compat shim).
- One source of truth for cross-repo state: an exhaustive live walk across every extant Git + GitHub query the runtime can perform, performed on every consumer invocation. No on-disk cache (the prior PR #160 design's `external_dep_cache` field is gone). The runtime tolerates partial visibility (missing local clones) by silently dropping the inaccessible view rather than failing.
- One shared runtime library, `livespec-runtime`, that any livespec-governed consumer (core skills, impl-plugin skills, doctor invariants, hooks, CI workflows) imports for cross-repo resolution. The library is sibling to `livespec`, `livespec-impl-*`, and `livespec-dev-tooling`; pinned-and-bumped per the existing pin-and-bump contract.

The exhaustive-live-walk choice over caching reflects the per-iteration unblock latency requirement: a cached value lies as soon as a sibling PR merges, and the user wants the consequence of that merge (an unblocked candidate work-item) to surface on the next `next` invocation — not after a `resolve-cross-repo-deps` skill explicitly refreshes the cache. With no cache, there is no staleness, no `external_dep_cache.checked_at` to validate, and no follow-up "did you remember to resolve?" warning surface; the resolver skill is gone entirely.

### Proposed Changes

Insert a new H2 `## Cross-repo dependency awareness` in `contracts.md` between `## Cross-repo coordination — pin-and-bump` and `## Implementation-plugin contract — the 9-skill surface`. The H2 carries the following subsections.

#### Scope and non-goals

The mechanism is parallel-and-complementary to the cross-repo version coordination of §"Cross-repo coordination — pin-and-bump": version pin-and-bump is the coarse-grained release-level coordination; this is the fine-grained per-work-item coordination for cases when an in-flight work-item depends on specific state in another repo. The two operate at different granularities and are independent.

v1 supports GitHub-hosted repos exclusively. GitLab and other forges are deferred to a future propose-change cycle; the `providers` package shape in `livespec_runtime.cross_repo` is structured so adding a `providers.gitlab` module is a non-breaking extension.

#### `cross_repo_targets` manifest in `.livespec.jsonc`

Projects participating in cross-repo work-item dependency coordination MUST declare a top-level `cross_repo_targets` block in `.livespec.jsonc`. The block is an object whose keys are short repo slugs (used as the `repo` field in every typed `depends_on` entry) and whose values are objects with the following fields:

- `github_url` — string, REQUIRED. The canonical `https://github.com/<owner>/<name>` URL (no trailing `.git`). Doctor's `cross-repo-targets-wellformedness` invariant MUST verify it parses as a GitHub URL.
- `local_clone` — string, OPTIONAL. Filesystem path to the consumer's local clone of the target repo. MAY be absolute or relative to the containing project's root. When set, the runtime walks the local clone for branch and worktree state. When absent (CI case), the runtime silently drops the local-clone view and falls back to GitHub-only queries. The path is NOT required to exist at config-load time; missing-path is a runtime-degraded-view condition, not a precondition failure.
- `default_branch` — string, OPTIONAL, default `"master"`. The repo's default branch name used by the runtime for "branch merged into default" derivations. Projects whose default branch is not `master` MUST set this explicitly.

The `cross_repo_targets` block is OPTIONAL at the top level — projects with no cross-repo work-item dependencies omit it entirely.

The `cross_repo_targets` block MUST NOT be conflated with the per-consumer `compat` block defined in §"Cross-repo coordination — pin-and-bump", which handles version pin-and-bump.

#### Typed `DependsOnEntry` union for the work-item `depends_on` field

The impl-plugin contract's work-item record schema (per §"Implementation-plugin contract — the 9-skill surface") gains a typed object shape for entries in the existing `depends_on` array, replacing the prior string-only `<work-item-id>` shape. Each entry MUST be one of the four typed variants below, discriminated on the `kind` field:

- `kind: "local"` — a same-repo work-item dependency. Carries `work_item_id` (string, e.g. `"li-abc123"`). The runtime resolves this against the active impl-plugin's local work-items store; no cross-repo walk.
- `kind: "sibling_work_item"` — a work-item in a configured sibling repo. Carries `repo` (string, MUST match a key in `.livespec.jsonc`'s `cross_repo_targets` block) and `work_item_id` (string). Resolved via the sibling repo's `local_clone/<impl-plugin>.work_items_path` if available, falling back to dropping the dependency view if neither local nor GitHub-queryable.
- `kind: "pull_request"` — a specific GitHub pull request. Carries `repo` (string, MUST match `cross_repo_targets`) and `number` (positive integer). Resolved via `gh pr view <number> --repo <github_url>`.
- `kind: "branch"` — a specific GitHub branch. Carries `repo` (string, MUST match `cross_repo_targets`) and `name` (string, the branch name without the `refs/heads/` prefix). Resolved via the exhaustive walk's branch-tip query.

A `depends_on` entry's `kind` field is REQUIRED non-null. The previous string-only shape (`"li-abc123"`) is NOT a valid v1 entry; the impl-side data-migration step (per li-f5wmjr) MUST convert every prior string entry to `{"kind": "local", "work_item_id": "li-abc123"}` form before this contract takes effect.

The `blocked_by` field is REMOVED from the work-item record schema. Its prior role — "this work-item is currently blocked by N other work-items / PRs / branches" — folds into the typed `depends_on` union; the runtime's open/closed derivation per entry is what the consumer's ranker, doctor invariants, and hooks consult. This is the "Model B" choice from the epic's design exploration; Model A (keeping `blocked_by` as a parallel field) was rejected because it would have required two stores of truth that could drift.

#### Exhaustive live-walk resolution semantics

The runtime's `resolve_ref(entry, manifest)` function MUST return a `RefStatus` (open | closed | unknown) for every `DependsOnEntry`, computed from an exhaustive query of every extant view the runtime can access:

- For `kind: "local"` — read the local work-items store via the active impl-plugin's list-work-items interface; return `closed` iff the materialized status is `closed`, else `open`.
- For `kind: "sibling_work_item"` — when `local_clone` is configured AND the path exists AND the path contains a parseable `.livespec.jsonc` with an impl-plugin config, walk the sibling's work-items store. Otherwise fall back to GitHub-queried state when the impl-plugin surface exposes a remote-queryable form (impl-plugin-dependent; the runtime calls into the impl-plugin's surface when present, returns `unknown` when not). The runtime MUST NOT cache; each call walks fresh state.
- For `kind: "pull_request"` — query `gh pr view <number> --repo <github_url> --json state`. Return `closed` iff `state == "MERGED"` OR `state == "CLOSED"` (the work-item depending on the PR is unblocked when the PR is resolved either way; the consumer ranker decides whether closed-but-unmerged warrants a different urgency). Return `open` for any other state. Return `unknown` if the GitHub query exits non-zero after retry exhaustion.
- For `kind: "branch"` — walk in this order until a derivation succeeds: (a) when `local_clone` is configured, query `git -C <local_clone> rev-parse refs/heads/<name>` to determine if the branch exists locally and has merged into `default_branch`; (b) query `gh api repos/<owner>/<name>/branches/<name>` for the remote branch tip + `gh api repos/<owner>/<name>/compare/<default_branch>...<name>` for the merged-into-default determination. Return `closed` iff the branch's tip is reachable from `default_branch` (i.e., merged) OR the branch is absent on the remote AND was previously seen merged in a local fetch. Return `open` otherwise; `unknown` on retry exhaustion.

The runtime MUST include the CURRENT repo's uncommitted state when relevant (e.g., for `kind: "local"` against the current repo, the materialized view is the latest JSONL line, including the just-appended one if the consumer is mid-revise).

Missing local clones, missing remote branches, and `gh` CLI auth failures are NOT precondition errors — they degrade the view (the runtime returns `unknown` for that entry and the consumer surfaces the degradation). The exhaustive-walk discipline tolerates partial visibility.

#### `livespec-runtime` library contract

`livespec-runtime` is a livespec-governed sibling library, peer to `livespec`, `livespec-impl-*`, and `livespec-dev-tooling`. It hosts shared runtime code consumed by livespec-governed skills, NOT enforcement-suite code (that stays in `livespec-dev-tooling`).

The library MUST:

- Govern its own `SPECIFICATION/` tree via the `livespec` template (4-file plus `non-functional-requirements.md`), structurally identical to `livespec-dev-tooling`.
- Track its own work via the active `livespec-impl-*` plugin per `.livespec.jsonc`.
- Declare a `compat` block on a `livespec-runtime` top-level key in its own `.livespec.jsonc`, structurally identical to how every `livespec-impl-*` consumer declares its block per §"Cross-repo coordination — pin-and-bump".
- Ship a Python package `livespec_runtime` invocable via `python -m livespec_runtime.<module>` from any consumer.
- Initial scope: `livespec_runtime.cross_repo` subpackage with `types`, `providers.github`, `retry`, and `resolve_ref` modules per li-aclzfe's impl scope.

The library's contract surface is the public API of `livespec_runtime.cross_repo` (the `DependsOnEntry` union types, the `CrossRepoManifest` dataclass, the `RefStatus` enum, and `resolve_ref(entry, manifest) -> RefStatus`). Breaking changes to these names or shapes require a major version bump per the semver discipline inherited from `livespec-dev-tooling`'s contract.

`livespec-runtime` is added to §"Cross-repo coordination — pin-and-bump"'s enumeration of livespec-governed sibling consumers (alongside `livespec-impl-*` plugins and `livespec-dev-tooling`).

#### Retry policy

The `livespec_runtime.cross_repo` retry policy is fixed at three attempts with 1s / 2s / 4s exponential backoff between attempts. On every-attempt failure (including subprocess timeouts on `gh` CLI calls), the runtime returns `RefStatus.unknown` rather than raising; the consumer is responsible for surfacing degraded-view findings.

The retry policy is NOT user-configurable in v1. Projects with bandwidth-constrained CI environments MAY pre-fetch sibling repos to local clones to avoid the GitHub-query path entirely.

#### Consumer surface (livespec core + impl-plugins)

The runtime is consumed by:

- The spec-side `/livespec:doctor` invariants (per the doctor catalogue extensions in this proposal).
- The impl-side `<impl-plugin>:next` ranker (per li-f5wmjr — the ranker MUST exclude any work-item with at least one open `DependsOnEntry` from the candidate list).
- Project-local hooks and CI workflows that need to gate behavior on cross-repo state (e.g., a pre-merge hook that refuses to merge a PR whose underlying work-item still has open external dependencies).

Consumer projects MUST declare `livespec-runtime` as a dependency in `pyproject.toml` via `[tool.uv.sources]` pinning the target tag, identical to how they consume `livespec-dev-tooling`.

#### GitHub CLI authentication

The runtime invokes the `gh` CLI for all GitHub queries. The CLI MUST be installed and authenticated (`gh auth status` returning success) in any environment where the runtime is consumed.

In CI environments, the standard pattern is `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` (for read-only queries) or an App installation token (for queries against private sibling repos or higher rate-limit needs). The runtime does NOT manage auth; it surfaces auth-failure findings via `RefStatus.unknown` and lets the consumer decide how to handle.

#### Hook integration

Project-local hooks (lefthook pre-push, pre-merge, etc.) MAY invoke `python -m livespec_runtime.cross_repo.resolve --work-item-id <id> --manifest <path>` to gate hook behavior on the work-item's external-dependency state. The CLI emits a JSON status object suitable for shell-level dispatch. This CLI is the same surface the impl-plugin `next` ranker invokes internally; no parallel CLI is required.

## Proposal: doctor-invariants-rename-and-extend-for-typed-depends-on

### Target specification files

- contracts.md

### Summary

Update the doctor invariant catalogue in `## Doctor cross-boundary invariants` to (a) rename `no-orphan-blocker` → `no-orphan-dependency` (since `blocked_by` is removed and the resolvability check now applies to `depends_on` entries uniformly), (b) extend `no-stalled-epic` to walk cross-repo entries via `livespec_runtime.cross_repo.resolve_ref`, and (c) add a new `depends_on-ref-wellformedness` invariant that catches manifest-drift between `depends_on` entries and the `cross_repo_targets` manifest.

### Motivation

The doctor catalogue's existing `no-orphan-blocker` invariant assumes the prior parallel `blocked_by` field exists. After this proposal removes `blocked_by` per Model B, the invariant's check (every `blocked_by` reference must resolve to an existing work-item) MUST migrate to the typed `depends_on` field. The invariant's semantic stays — orphan dependency references are still a contract violation — but the name and the field it walks both change.

`no-stalled-epic` currently checks epic-vs-sub-task aging entirely within the local work-items store. With typed `DependsOnEntry` entries referencing sibling repos and PRs, the invariant MUST walk those entries too to correctly distinguish a stalled-but-blocked epic (no fail; blocking is expected) from a stalled-and-unblocked epic (fire fail; real stalling).

The new `depends_on-ref-wellformedness` invariant catches a class of contract violation that has no current detection: a typed `depends_on` entry references a `repo` slug that's not declared in `cross_repo_targets`. Without this check, runtime calls to `resolve_ref` would silently return `unknown` and the manifest drift would never surface as a finding. The invariant is structural per the catalogue's intro principles.

### Proposed Changes

In `contracts.md` §"Doctor cross-boundary invariants":

Update the catalogue-summary paragraph to enumerate the renamed and new invariants. The current sentence "The catalogue MUST include the five work-item invariants and the contract-version-compatibility invariant below." becomes: "The catalogue MUST include the five work-item invariants (one of which renames per this proposal), the contract-version-compatibility invariant, and the `depends_on-ref-wellformedness` invariant defined below."

Rename the existing `### no-orphan-blocker` H3 to `### no-orphan-dependency`. Update its prose to walk the typed `depends_on` field instead of `blocked_by`. The invariant fires `fail` when any `DependsOnEntry` with `kind == "local"` references a `work_item_id` that does not exist in the materialized work-items store. For `kind` values `sibling_work_item`, `pull_request`, and `branch`, the invariant defers to `livespec_runtime.cross_repo.resolve_ref` and fires `fail` only when the runtime returns `unknown` AND the `cross_repo_targets` block configures the target (i.e., the dependency is declared resolvable but the resolution attempt failed); a successful `open` or `closed` resolution is NOT a doctor failure (open dependencies are expected during in-flight work).

Update the existing `### no-stalled-epic` H3 to add a sentence: "When the epic's sub-task work-items declare typed `depends_on` entries with `kind` other than `local`, the invariant MUST walk those entries via `livespec_runtime.cross_repo.resolve_ref` and treat any `open` external dependency as a legitimate stall reason (suppressing the fail)."

Add a new H3 `### depends_on-ref-wellformedness` after the `### contract-version-compatibility` section. The invariant reads every open work-item's `depends_on` field. For each entry, it enforces:

1. **Discriminator present** — every entry MUST have a `kind` field whose value is one of `local`, `sibling_work_item`, `pull_request`, `branch`. Missing or unknown `kind` fires `fail`.
2. **Per-kind required fields present** — `local` requires `work_item_id`; `sibling_work_item` requires `repo` and `work_item_id`; `pull_request` requires `repo` and `number`; `branch` requires `repo` and `name`. Missing required fields fire `fail` with the entry's index in the array.
3. **`repo` resolves to a configured target** — for every entry with a `repo` field, the value MUST be a key in `.livespec.jsonc`'s `cross_repo_targets` block. Unresolvable `repo` values fire `fail` with the value and a hint pointing to the manifest.

This invariant is structural per the catalogue's intro (binary, contract-level, mechanically checkable); it does NOT rank or judge work-item readiness, only the well-formedness of the typed dependency machinery.

## Proposal: impl-plugin-contract-rename-blocked-by-and-add-cleanup-invariants

### Target specification files

- contracts.md

### Summary

Update §"Implementation-plugin contract — the 9-skill surface" to (a) describe the typed `depends_on` field replacing the prior string-only shape and the removed `blocked_by` field, and (b) require three new impl-side cleanup invariants — `no-stale-merged-branch`, `no-stale-merged-pr-branch`, `no-stale-worktree` — that fire `warn` when local-Git or local-worktree state lags behind merged-PR state.

### Motivation

The impl-plugin contract surface for `list-work-items`, `capture-work-item`, and `next` documented the work-item record's `depends_on` field as `array of id strings`. After this proposal lands the typed union, the contract MUST describe the new shape so impl-plugin authors update their stores to match. The `blocked_by` field is removed entirely per Model B; impl-plugin authors who previously surfaced `blocked_by` MUST migrate to depending on the typed `depends_on` entries' resolution status.

The three cleanup invariants address a class of hygiene problem the existing doctor catalogue does not cover: stale local Git state (merged branches that should be deleted, worktrees on merged-and-deleted branches that should be `git worktree remove`d, GitHub branches fronted by merged PRs that should be deleted on the remote). These are impl-side concerns rather than spec-side because they depend on impl-plugin-specific worktree and JSONL conventions; the doctor catalogue extends to impl-side via the existing cross-boundary invariant pattern.

### Proposed Changes

In `contracts.md` §"Implementation-plugin contract — the 9-skill surface":

Update the `list-work-items` and `capture-work-item` bullets to reference the typed `depends_on` shape: "Work-items carry a typed `depends_on` array per §"Cross-repo dependency awareness"; the prior string-only `<work-item-id>` shape and the parallel `blocked_by` field are NOT v1 valid forms. The impl-plugin's data-migration step MUST convert prior records before this contract takes effect."

Update the `next` bullet to add: "The ranker MUST consult `livespec_runtime.cross_repo.resolve_ref` for every candidate work-item's `depends_on` entries and MUST exclude any candidate with at least one entry resolving to `open`. Excluded candidates do NOT appear in the ranked list (they are not surfaced with a lower urgency; they are absent entirely)."

Add a new H3 `### Impl-side cleanup invariants (cross-boundary)` between `### Cross-boundary handoffs` and `### Backend-variability asymmetry`. The H3 introduces and defines three invariants the active impl-plugin MUST realize. Each invariant fires `warn` (not `fail`) because the underlying state is recoverable by user action; the invariants' role is to surface the housekeeping items to the user, not to block the build.

- **`no-stale-merged-branch`** — for every local branch whose tip is reachable from the default branch (i.e., merged), the invariant fires `warn` with corrective action `git branch -d <name>`. Excludes the default branch itself. Excludes any branch the user has explicitly tagged via project-local config to skip.
- **`no-stale-merged-pr-branch`** — for every GitHub branch in `gh api repos/<owner>/<name>/branches` that is fronted by a `state == "MERGED"` PR (queried via `gh pr list --state merged --json headRefName,state`), the invariant fires `warn` with corrective action `gh api -X DELETE repos/<owner>/<name>/git/refs/heads/<name>`. The check runs against the CURRENT repo only; sibling-repo cleanup is the sibling-repo project's responsibility.
- **`no-stale-worktree`** — for every git worktree (per `git worktree list --porcelain`) whose underlying branch is either (a) merged into default and locally deleted, or (b) absent from the remote, the invariant fires `warn` with corrective action `git worktree remove <path>`. Excludes the primary worktree.

The three invariants MAY be implemented entirely within the impl-plugin's doctor-realization surface (extending `<impl-plugin>:list-work-items` consumers' invariant set), OR may dispatch to a `livespec_runtime.cleanup` helper module — the choice is the impl-plugin author's. The contract is the invariant set and its narration shape; the implementation seam is implementation-dependent.
