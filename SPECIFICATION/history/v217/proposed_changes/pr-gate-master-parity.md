---
topic: pr-gate-master-parity
author: pr-gate-master-parity plan session (Claude Code)
created_at: 2026-09-04T18:22:00Z
---

## Proposal: Retire the zero-`.py` gate skip — PR gate ≡ master gate

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Retire the v050 rule that lets pre-push and CI run only a subset of `just
check` when a changeset contains no `.py` files, and replace it with the
invariant that a pull request's gating-check set is IDENTICAL to the set
`master` enforces on push. §"Pre-commit step ordering" keeps the pre-commit
doc-only subset but relabels it a LOCAL speed optimization that is explicitly
NOT a merge gate, and deletes the mandate that pre-push and CI apply the same
subset (clauses (a)–(d) and the "soundness" paragraph). §"CI as a merge gate
(branch protection)" gains a `**PR gate ≡ master gate.**` paragraph naming a
new `ci_gate_parity` shared check as the companion to the existing
`ci_matrix_completeness`. The dependent `comment_no_historical_refs`
enforcement sentence is swept. No `##` heading is added, changed, or removed,
so no `tests/heading-coverage.json` co-edit arises.

### Motivation

On 2026-09-04 a pull request that changed only `.github/workflows/ci.yml`
merged with a green gate and reddened `livespec-orchestrator-beads-fabro`'s
`master` twelve seconds later. The gate a pull request runs was a SUBSET of
the gate `master` runs, chosen by asking "did any `.py` file change?" — a
question unrelated to what the skipped checks actually read. The skipped
`check-self-hosted-uv-lane` reads the workflow file the PR changed. The v050
clause justified the subsetting with a premise — "the Python-code checks are
deterministic functions of the Python source tree" — that was true for the
checks of May 2026 and false for every check added since that reads a
non-Python input (`self_hosted_uv_lane`, `self_hosted_routing` read `ci.yml`;
`plan_epic_parity`, `plan_no_tombstone` read `plan/` and the ledger; and
others). Nobody re-derived the premise when those checks landed, because
nothing asked. The maintainer's directive is absolute — "NOTHING SHOULD BE
ABLE TO BREAK MASTER" — and only a structural guarantee (no predicate to rot)
satisfies it. Full analysis and the exact edits: livespec
`plan/pr-gate-master-parity/research/001-root-cause-zero-py-skip.md` and
`002-design-decision.md`; the enforcement guard, the six-repo fan-out, and
the deferrals are cut on the plan epic `livespec-citqsd`.

### Proposed Changes

#### Change 1 — contracts.md §"Pre-commit step ordering": relabel the pre-commit subset as a non-gate

In `SPECIFICATION/contracts.md`, replace this paragraph verbatim:

> When the staged tree contains ZERO `.py` files, `just check-pre-commit` runs a CONSERVATIVE doc-only subset (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`) instead of the full aggregate, since the Python-related gates have no work to do on doc-only commits. The classification trigger is the strict "zero `.py` staged" predicate; any `.py` file in the staged tree (even a single test file in Red mode) routes through the full aggregate. Pre-push and CI MUST apply the same zero-`.py` subsetting predicate as pre-commit. (a) Pre-push delegates to a new `just check-pre-push` recipe (mirroring `check-pre-commit`) that computes the changeset via `git diff --name-only @{upstream}..HEAD` (falling back to `git diff --name-only origin/master..HEAD` when no upstream is configured); when zero `.py` paths appear in the diff, the recipe delegates to `check-pre-commit-doc-only`; otherwise it delegates to `just check`. (b) CI in `.github/workflows/ci.yml` MUST add a `setup` job that runs `git diff --name-only origin/${{ github.base_ref }}...HEAD` for `pull_request` events (and outputs `py_changed=true` for `push` and `merge_group` events unconditionally, since master/merge-queue must always run the full safety net), exposes `outputs.py_changed`, and the Python-code matrix entries gate on `if: needs.setup.outputs.py_changed == 'true'`. The repo-metadata matrix entries (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`) MUST run unconditionally in CI to preserve the metadata safety net. (c) The lefthook `pre-push` stanza in `lefthook.yml` MUST be updated from `run: just check` to `run: just check-pre-push`. (d) The categorization of every `just check` target into either `python-code-checks` or `repo-metadata-checks` MUST be kept synchronized between justfile, lefthook, and CI without drift. The repo-metadata subset is exactly the current `check-pre-commit-doc-only` body: `check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`. Every other target in `just check` is a python-code check.

with:

> When the staged tree contains ZERO `.py` files, `just check-pre-commit` runs a CONSERVATIVE doc-only subset (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`) instead of the full aggregate, since the Python-related gates have no work to do on doc-only commits. The classification trigger is the strict "zero `.py` staged" predicate; any `.py` file in the staged tree (even a single test file in Red mode) routes through the full aggregate. This pre-commit subsetting is a LOCAL developer-speed optimization ONLY and is explicitly NOT a merge gate: the pre-commit doc-only subset MAY be wrong or drift out of sync without endangering `master`, because the load-bearing gate that protects `master` — the required CI gate (`non-functional-requirements.md` §"CI as a merge gate (branch protection)") — NEVER subsets, and local pre-push is defense-in-depth that runs the same full aggregate. The categorization the pre-commit subset depends on is confined to pre-commit and gates nothing on `master`.

#### Change 2 — contracts.md §"Pre-commit step ordering": retire the pre-push+CI subsetting and state the parity invariant

In `SPECIFICATION/contracts.md`, replace this paragraph verbatim:

> The zero-`.py` subsetting is sound because the Python-code checks are deterministic functions of the Python source tree; with no `.py` delta in the changeset, every Python-code check would pass-or-fail identically against the merge-base, and any pre-existing failure is a master-branch-state concern (covered by `check-master-ci-green`), not a per-PR concern. Master-branch CI runs (`push` to `master`, `merge_group`) MUST still run the full aggregate as the merge-queue safety net.

with:

> Pre-push and CI run the full aggregate rather than the zero-`.py` subset. Pre-push delegates to `just check` (a pre-push short-circuit on a working tree byte-identical to one that already passed the full aggregate is memoization of the identical check set, not subsetting). CI in `.github/workflows/ci.yml` MUST run every gating check on a `pull_request` exactly as it runs on `push` to `master` and `merge_group`: no gating job (any job the required all-green gate job lists in its `needs:`) and no `just check` target may be conditioned on the triggering event or on a changeset predicate (such as a `.py`-changed gate) so that it runs on a `master` push but is skipped, or runs a smaller check set, on a pull request. This establishes the **PR gate ≡ master gate** invariant codified in `non-functional-requirements.md` §"CI as a merge gate (branch protection)": the set of checks a change must pass before it merges is identical to the set `master` enforces after it merges, so "nothing can break `master`" is a property of the definitions rather than of anyone's diligence. The earlier zero-`.py` subsetting of pre-push and CI is RETIRED: it rested on the false premise that every `just check` target is a deterministic function of the Python source tree, which ceased to hold the moment a check read a non-Python input (the CI workflow file, `plan/`, the ledger) — letting a change whose only skipped check read such an input merge green and redden `master`.

#### Change 3 — non-functional-requirements.md §"CI as a merge gate (branch protection)": add the parity invariant + ci_gate_parity guard

In `SPECIFICATION/non-functional-requirements.md` §"CI as a merge gate (branch protection)", insert the following new paragraph IMMEDIATELY AFTER the paragraph that ends verbatim:

> A canonical slug that runs at pre-push but never in CI, or a gating job the gate job omits from its `needs:`, therefore FAILS CI once the repo arms the guard (the `LIVESPEC_FAIL_IF_CI_MATRIX_GAPS_EXIST` lever; until then the same finding warns without reddening, so the check can propagate to a not-yet-wired repo safely).

The inserted paragraph, verbatim:

> **PR gate ≡ master gate.** The set of gating checks a `pull_request` must pass MUST be identical to the set that runs on `push` to `master` (and `merge_group`): no gating job — any job the required all-green gate job lists in its `needs:` — and no `just check` target may be conditioned on the triggering event or on a changeset predicate (such as a `.py`-changed gate) so that it runs on a `master` push but is skipped, or runs a smaller check set, on a pull request. A pull request MAY run ADDITIONAL checks a `master` push does not (for example a release-PR-only stricter gate that skips harmlessly on ordinary PRs); what is forbidden is a pull request running FEWER gating checks than `master`. Non-gating jobs — telemetry export, notifications, any job absent from the gate job's `needs:` — are exempt. Without this invariant a PR gate is a strict SUBSET of the master gate, and a change whose only skipped check reads a non-Python input (the CI workflow file, `plan/`, the ledger) can merge green and redden `master`; that exact failure occurred on 2026-09-04, when a CI-workflow-only pull request merged green and reddened `master` seconds later because the skipped check read the workflow file it changed. This invariant is enforced by the companion `ci_gate_parity` shared check from `livespec-dev-tooling` (§"Shared code sync — livespec-dev-tooling"), which reads `.github/workflows/ci.yml` statically and FAILS when a gating job — at the job level or in its real steps — is conditioned on the triggering event or on a changeset predicate in the FORBIDDEN DIRECTION: so that it runs on a `push` to `master` but is skipped, or runs a smaller check set, on a `pull_request` (a job conditioned to run pull-request-only, which ADDS strictness rather than removing it, is not flagged); like `ci_matrix_completeness` it warns without reddening until the repo arms it via the `LIVESPEC_FAIL_IF_CI_GATE_PARITY_GAPS_EXIST` lever, so the check propagates to a not-yet-fixed repo safely. The two are complementary: `ci_matrix_completeness` confirms every gating check is PRESENT in CI and covered by the gate job's `needs:`; `ci_gate_parity` confirms every such gating check actually RUNS on a pull request rather than being conditionally skipped.

#### Change 4 — non-functional-requirements.md: sweep the dependent comment_no_historical_refs sentence

In `SPECIFICATION/non-functional-requirements.md`, replace this sentence verbatim:

> The check is categorized as a python-code check per §"Pre-commit step ordering" so it is skipped when zero `.py` files change.

with:

> The check runs as part of the full `just check` aggregate at pre-push and in CI unconditionally, with no zero-`.py` subsetting, per §"Pre-commit step ordering".

#### Change 5 — contracts.md detection-surface paragraph: sweep the stale pre-push-subset reference

In `SPECIFICATION/contracts.md` (the `master-direct-uncommitted-spec-edits` **Detection surface** paragraph), replace this fragment verbatim:

> the doc-only pre-commit/pre-push subset

with:

> the doc-only pre-commit subset (at pre-push the check runs as part of the full `just check` aggregate)

This drift-sweep completes Change 1/2: after retirement, pre-push has no subset, so the detection check runs at pre-push within the full aggregate. Prose-only; the fragment sits in an existing paragraph under an H2 that is unchanged, so no `tests/heading-coverage.json` co-edit arises.
