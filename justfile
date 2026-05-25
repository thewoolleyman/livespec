# justfile — livespec dev-tooling task runner.
#
# `just` is the single source of truth for every dev-tooling
# invocation; lefthook.yml and .github/workflows/*.yml only
# call `just <target>`. Authoritative source for the canonical
# target list: python-skill-script-style-requirements.md
# §"Enforcement suite — Canonical target list".

default:
    @just --list

# ---------------------------------------------------------------
# First-time setup.
# ---------------------------------------------------------------

bootstrap:
    # Install the repo-tracked git-hook-wrapper.sh as pre-commit,
    # pre-push, and commit-msg hooks. The wrapper invokes
    # `mise exec lefthook -- lefthook run <hook-name> "$@"` so the
    # gate fires regardless of the user's shell config and the
    # commit-msg stage receives the commit-message file path as the
    # first argument (the value lefthook passes to {1}).
    mkdir -p .git/hooks
    cp dev-tooling/git-hook-wrapper.sh .git/hooks/pre-commit
    cp dev-tooling/git-hook-wrapper.sh .git/hooks/pre-push
    cp dev-tooling/git-hook-wrapper.sh .git/hooks/commit-msg
    chmod +x .git/hooks/pre-commit .git/hooks/pre-push .git/hooks/commit-msg
    # Idempotent notes-refspec install for the `refs/notes/commits`
    # advisory cache. `git config --add` tolerates duplicate values,
    # but the literal-equality grep is the cheapest skip-path on
    # repeated bootstrap invocations.
    git config --get-all remote.origin.fetch | grep -qx '+refs/notes/*:refs/notes/*' || git config --add remote.origin.fetch '+refs/notes/*:refs/notes/*'
    just ensure-plugins

# Idempotent: `claude plugin marketplace add` / `install` / `update` all exit 0
# when the target is already present / already at latest. The `update` calls
# after each `install` are required because `install` is a no-op when any
# version is already present locally — without `update`, a bumped upstream
# release never reaches a previously-bootstrapped working copy. The pin in
# `.livespec.jsonc` `compat.pinned` is advisory per
# `SPECIFICATION/contracts.md` §"Cross-repo coordination — pin-and-bump"
# (drift is doctor's `contract-version-compatibility` invariant); the install
# itself always resolves to the marketplace's current advertised version.
ensure-plugins:
    claude plugin marketplace add thewoolleyman/livespec
    claude plugin marketplace add thewoolleyman/livespec-impl-plaintext
    claude plugin install livespec@livespec
    claude plugin install livespec-impl-plaintext@livespec-impl-plaintext
    claude plugin update livespec@livespec
    claude plugin update livespec-impl-plaintext@livespec-impl-plaintext

# ---------------------------------------------------------------
# Aggregate check — runs every check below sequentially. Continues
# on failure (matches CI fail-fast: false behavior); exits non-zero
# if any target failed and prints the failure list.
# ---------------------------------------------------------------

check:
    #!/usr/bin/env bash
    set -uo pipefail
    # Canonical target list — see python-skill-script-style-requirements.md
    # §"Canonical target list". Aggregator continues on failure
    # (matches CI fail-fast: false) and exits non-zero with the
    # failure list if any target failed.
    targets=(
        check-imports-architecture
        check-coverage
        check-main-guard
        check-no-inheritance
        check-all-declared
        check-no-write-direct
        check-supervisor-discipline
        check-no-raise-outside-io
        check-no-except-outside-io
        check-keyword-only-args
        check-match-keyword-only
        check-assert-never-exhaustiveness
        check-private-calls
        check-global-writes
        check-wrapper-shape
        check-claude-md-coverage
        check-vendor-manifest
        check-no-direct-tool-invocation
        check-copier-template-smoke
        check-heading-coverage
        check-rop-pipeline-shape
        check-public-api-result-typed
        check-pbt-coverage-pure-modules
        check-newtype-domain-primitives
        check-schema-dataclass-pairing
        check-tests-mirror-pairing
        check-comment-line-anchors
        check-complexity
        check-lint
        check-format
        check-types
        check-tools
        check-branch-protection-alignment
        check-master-ci-green
        check-prompts
        e2e-test-claude-code-mock
    )
    failed=()
    for t in "${targets[@]}"; do
        printf '\n::: just %s\n' "$t"
        if ! just "$t"; then
            failed+=("$t")
        fi
    done
    if [[ ${#failed[@]} -gt 0 ]]; then
        printf '\nFailed targets (%d):\n' "${#failed[@]}"
        printf '  - %s\n' "${failed[@]}"
        exit 1
    fi
    printf '\nAll %d targets passed.\n' "${#targets[@]}"

# ---------------------------------------------------------------
# Tool-backed checks.
# ---------------------------------------------------------------

check-lint:
    uv run ruff check .

check-format:
    uv run ruff format --check .

check-types:
    uv run pyright

check-complexity:
    #!/usr/bin/env bash
    set -uo pipefail
    rc=0
    uv run ruff check --select C90,PLR . || rc=$?
    uv run python -m livespec_dev_tooling.checks.file_lloc || rc=$?
    exit $rc

check-imports-architecture:
    PYTHONPATH=.claude-plugin/scripts uv run lint-imports

check-coverage:
    #!/usr/bin/env bash
    set -uo pipefail
    # Red-mode pre-commit skip: when the Red-mode-aware aggregate
    # (`check-pre-commit`) sets LIVESPEC_PRECOMMIT_RED_MODE for the
    # staged tree, skip pytest entirely — the commit-msg replay
    # hook (`check-red-green-replay`) is the load-bearing verifier
    # in Red mode (it runs pytest on the staged test file and
    # expects non-zero exit). Pre-push, CI, and manual
    # `just check-coverage` invocations don't set the env var and
    # run normally. `check-coverage` is the sole pytest-running
    # aggregate target — a separate `check-tests` would
    # double-count pytest invocations that run as a side effect of
    # `pytest --cov`.
    if [[ -n "${LIVESPEC_PRECOMMIT_RED_MODE:-}" ]]; then
        echo ":: check-coverage skipped (Red-mode pre-commit; verified at Green amend)"
        exit 0
    fi
    # pytest-cov defaults `--cov-config` to `.coveragerc`, which
    # bypasses pyproject.toml's `[tool.coverage.run]` (including
    # the `omit = ["*/_vendor/*"]` carve-out). Pass the config
    # path explicitly so the vendored-tree exclusion takes effect
    # under `pytest --cov`. Without this, structlog (transitively
    # imported by livespec modules) is measured and inflates the
    # report with sub-100% files that aren't first-party code.
    # `-n auto` (pytest-xdist) parallelizes the suite across cores;
    # pytest-cov auto-runs `coverage combine` at session-end to
    # merge the per-worker `.coverage.<host>.<pid>.<rand>` files
    # into the single `.coverage` that `per_file_coverage.py` reads
    # on the next line. Wall-clock budget on a typical multi-core
    # machine: under ~1min (versus ~3.5min serial).
    uv run pytest -n auto --cov --cov-branch --cov-config=pyproject.toml --cov-report=term-missing
    uv run python -m livespec_dev_tooling.checks.per_file_coverage

# Red-mode-aware pre-commit aggregate. Classifies the staged tree
# shape via `git diff --cached --name-only --diff-filter=AM`. Red
# mode = exactly one test file added or modified under `tests/`
# AND zero implementation files added or modified under
# `.claude-plugin/scripts/livespec/**`,
# `.claude-plugin/scripts/bin/**`, or `dev-tooling/checks/**`
# (modified test files extending pre-existing mirror-pairs are
# valid Red commits too, so the diff-filter includes M as well as
# A). In Red mode, sets LIVESPEC_PRECOMMIT_RED_MODE=1 and runs
# `just check`; check-coverage observes the env var and skips
# (commit-msg replay hook is the load-bearing test-verifier in
# Red mode). In all other modes (Green amend, test:/chore:/etc.,
# non-Red feat:/fix:), runs `just check` unconditionally.
#
# Pre-push and CI keep invoking `just check` directly (no Red-mode
# classifier; full suite always).
check-pre-commit:
    #!/usr/bin/env bash
    set -uo pipefail
    staged=$(git diff --cached --name-only --diff-filter=AM)
    py_staged=$(echo "$staged" | grep -E '\.py$' || true)
    test_staged=$(echo "$staged" | grep -E '^tests/.*\.py$' || true)
    impl_staged=$(echo "$staged" | grep -E '^(\.claude-plugin/scripts/livespec|\.claude-plugin/scripts/bin|dev-tooling/checks)/.*\.py$' || true)
    test_count=0
    impl_count=0
    [[ -n "$test_staged" ]] && test_count=$(echo "$test_staged" | wc -l)
    [[ -n "$impl_staged" ]] && impl_count=$(echo "$impl_staged" | wc -l)
    if [[ -z "$py_staged" ]]; then
        echo ":: doc-only mode detected (zero .py files staged): running just check-pre-commit-doc-only"
        echo ":: pre-push + CI keep the full aggregate as the load-bearing safety net"
        just check-pre-commit-doc-only
        exit $?
    fi
    if [[ "$test_count" -eq 1 ]] && [[ "$impl_count" -eq 0 ]]; then
        echo ":: v037 D1 Red-mode shape detected: $test_staged"
        echo ":: skipping check-coverage (commit-msg replay hook is the verifier)"
        export LIVESPEC_PRECOMMIT_RED_MODE=1
    fi
    just check

# When zero `.py` files are staged, `check-pre-commit` delegates to this
# conservative doc-only subset. Pre-push delegates here via `check-pre-push`
# when the push contains zero `.py` changes.
check-pre-commit-doc-only:
    #!/usr/bin/env bash
    set -uo pipefail
    targets=(
        check-claude-md-coverage
        check-heading-coverage
        check-vendor-manifest
        check-no-direct-tool-invocation
        check-copier-template-smoke
        check-tools
    )
    failed=()
    for t in "${targets[@]}"; do
        printf '\n::: just %s\n' "$t"
        if ! just "$t"; then
            failed+=("$t")
        fi
    done
    if [[ ${#failed[@]} -gt 0 ]]; then
        printf '\nFailed targets (%d):\n' "${#failed[@]}"
        printf '  - %s\n' "${failed[@]}"
        exit 1
    fi
    printf '\nAll %d doc-only targets passed.\n' "${#targets[@]}"

# Skip the Python-code check subset when the pushed commits contain zero
# `.py` changes; those checks are deterministic functions of the source
# tree and would pass-or-fail identically against the merge-base. Falls
# back to `origin/master` when no upstream branch is configured locally.
check-pre-push:
    #!/usr/bin/env bash
    set -uo pipefail
    upstream=$(git rev-parse --abbrev-ref --symbolic-full-name @{upstream} 2>/dev/null || echo "origin/master")
    changeset=$(git diff --name-only "${upstream}..HEAD")
    py_changed=$(echo "$changeset" | grep -E '\.py$' || true)
    if [[ -z "$py_changed" ]]; then
        echo ":: doc-only push detected (zero .py changes vs ${upstream}): running check-pre-commit-doc-only"
        just check-pre-commit-doc-only
        exit $?
    fi
    just check

# ---------------------------------------------------------------
# AST / grep / hand-written checks.
# ---------------------------------------------------------------

check-private-calls:
    uv run python -m livespec_dev_tooling.checks.private_calls

check-global-writes:
    uv run python -m livespec_dev_tooling.checks.global_writes

check-rop-pipeline-shape:
    uv run python -m livespec_dev_tooling.checks.rop_pipeline_shape

check-supervisor-discipline:
    uv run python -m livespec_dev_tooling.checks.supervisor_discipline

check-no-raise-outside-io:
    uv run python -m livespec_dev_tooling.checks.no_raise_outside_io

check-no-except-outside-io:
    uv run python -m livespec_dev_tooling.checks.no_except_outside_io

check-public-api-result-typed:
    uv run python -m livespec_dev_tooling.checks.public_api_result_typed

check-schema-dataclass-pairing:
    uv run python3 dev-tooling/checks/schema_dataclass_pairing.py

check-main-guard:
    uv run python -m livespec_dev_tooling.checks.main_guard

check-wrapper-shape:
    uv run python -m livespec_dev_tooling.checks.wrapper_shape

check-keyword-only-args:
    uv run python -m livespec_dev_tooling.checks.keyword_only_args

check-match-keyword-only:
    uv run python -m livespec_dev_tooling.checks.match_keyword_only

check-no-inheritance:
    uv run python -m livespec_dev_tooling.checks.no_inheritance

check-assert-never-exhaustiveness:
    uv run python -m livespec_dev_tooling.checks.assert_never_exhaustiveness

check-newtype-domain-primitives:
    uv run python -m livespec_dev_tooling.checks.newtype_domain_primitives

check-all-declared:
    uv run python -m livespec_dev_tooling.checks.all_declared

check-no-write-direct:
    uv run python -m livespec_dev_tooling.checks.no_write_direct

check-pbt-coverage-pure-modules:
    uv run python -m livespec_dev_tooling.checks.pbt_coverage_pure_modules

check-claude-md-coverage:
    uv run python -m livespec_dev_tooling.checks.claude_md_coverage

check-heading-coverage:
    uv run python -m livespec_dev_tooling.checks.heading_coverage

check-vendor-manifest:
    uv run python -m livespec_dev_tooling.checks.vendor_manifest

check-no-direct-tool-invocation:
    uv run python -m livespec_dev_tooling.checks.no_direct_tool_invocation

# Smoke test for templates/impl-plugin/ — runs copier copy against a
# stock answers fixture and verifies the generated tree contains the
# expected file set. Acceptance gate for the C.6 sub-task of the
# Phase C multi-repo-split epic. Repo-metadata check: not gated by
# .py changeset.
check-copier-template-smoke:
    uv run python3 dev-tooling/checks/copier_template_smoke.py

check-tools:
    uv run python -m livespec_dev_tooling.checks.check_tools

# Guard Layer 1 mechanical checks. Both shell out to `gh api` to
# read remote GitHub state; they exit 0 with a structured warning
# when `gh` is unavailable or unauthenticated locally so per-commit
# pre-commit runs are not blocked. CI with GH_TOKEN exercises the
# full enforcement path.
check-branch-protection-alignment:
    uv run python -m livespec_dev_tooling.checks.branch_protection_alignment

check-master-ci-green:
    uv run python -m livespec_dev_tooling.checks.master_ci_green

# ---------------------------------------------------------------
# E2E + prompt verification (part of `just check`).
# ---------------------------------------------------------------

e2e-test-claude-code-mock:
    LIVESPEC_E2E_HARNESS=mock uv run pytest tests/e2e/

check-prompts:
    uv run pytest tests/prompts/

# ---------------------------------------------------------------
# Alternate-cadence target (NOT in `just check`).
#
# WARNING: the "real" harness is currently UNIMPLEMENTED. The
# LIVESPEC_E2E_HARNESS=real env var is set here but no code reads
# it — tests/e2e/fake_claude.py runs identically in both `mock`
# and `real` modes (no claude-agent-sdk integration exists yet).
# This recipe and the corresponding e2e-real.yml workflow are
# therefore dormant: they execute the mock-harness tests, not
# any live claude-agent-sdk path. Tracked as a separate beads
# issue for actual implementation; do NOT trust e2e-real CI runs
# as live-API regression coverage today.
# ---------------------------------------------------------------

e2e-test-claude-code-real:
    LIVESPEC_E2E_HARNESS=real uv run pytest tests/e2e/

# ---------------------------------------------------------------
# Release-gate targets (NOT in `just check`; run on release-tag CI
# workflow only). Per python-skill-script-style-requirements.md
# §"Mutation testing as release-gate" the threshold semantics
# live HERE in the recipe (ratchet-with-ceiling against
# .mutmut-baseline.json, capped at 80%), NOT in pyproject.toml.
# ---------------------------------------------------------------

check-mutation:
    uv run python -m livespec_dev_tooling.checks.check_mutation

check-no-todo-registry:
    uv run python -m livespec_dev_tooling.checks.no_todo_registry

check-comment-line-anchors:
    uv run python -m livespec_dev_tooling.checks.comment_line_anchors

# Path-scoped fast-feedback variant of check-coverage. Takes
# `--paths <impl_path> [<impl_path>...]` (repo-root-relative) and
# applies the per-file 100% line+branch coverage gate to the named
# impls only. Resolves each impl's mirror-paired test, runs pytest
# --cov on the combined test set with full instrumentation
# (path-scoped --cov=<dir> breaks under subprocess instrumentation,
# so the recipe runs unfiltered --cov and applies the per-file
# scoping at REPORT time), then applies
# `coverage report --include=<impl_paths> --fail-under=100`.
# NOT in `just check` aggregate — interactive developer tool, not
# per-commit gate. Wall-clock target: under 10 seconds for a
# typical single-file pair. Used during the Red→Green authoring
# loop to surface defensive-branch coverage gaps proactively,
# BEFORE the Green amend triggers a multi-minute aggregate retry.
check-coverage-incremental *args:
    uv run python -m livespec_dev_tooling.checks.check_coverage_incremental {{args}}

# Release-gate ONLY — paired with check-mutation + check-no-todo-registry
# on the release-tag CI workflow. NOT in `just check`; does NOT run
# per-commit. Closes the M3 soft-band drift loophole: forces refactor
# work to land before any v* tag push when any file is in 201-250 LLOC.
check-no-lloc-soft-warnings:
    uv run python -m livespec_dev_tooling.checks.no_lloc_soft_warnings

# Trailer-based Red→Green replay verification (hard gate). Invoked
# by lefthook commit-msg stage (NOT pre-commit) — the hook requires
# the commit-message file path as argv[1] to write trailers via
# `git interpret-trailers --in-place`. NOT in `just check`
# aggregate (per-commit, not per-tree).
#
# Note on lefthook stage: the design is fundamentally `commit-msg`
# (writes to the commit-message file; distinguishes Red/Green via
# HEAD~0 inspection), not pre-commit.
check-red-green-replay msg_path:
    uv run python -m livespec_dev_tooling.checks.red_green_replay {{msg_path}}

# Mirror-pairing: every covered .py under livespec/, bin/, and
# dev-tooling/checks/ has a paired tests/<mirror>/test_<name>.py.
# In `just check` aggregate.
check-tests-mirror-pairing:
    uv run python -m livespec_dev_tooling.checks.tests_mirror_pairing

# Commit-pair gate: every commit touching livespec/**, bin/**, or
# dev-tooling/checks/** also touches tests/**. Lefthook pre-commit
# only; NOT in `just check` aggregate (per-commit, not per-tree).
check-commit-pairs-source-and-test:
    uv run python -m livespec_dev_tooling.checks.commit_pairs_source_and_test

# Ruff fix + format on staged Python files BEFORE the rest of the
# pre-commit gate runs. Saves the ~5min retry on auto-fixable lint
# trivia. Runs as lefthook `00-lint-autofix-staged` step ahead of
# the existing checks. Non-blocking — unfixable issues fall through
# to be caught by check-lint / check-format inside the `just check`
# aggregate at the `02-check-pre-commit` step.
#
# Interaction with the commit-msg replay hook: autofix runs BEFORE
# the hook computes the Red trailer's test-file SHA-256 checksum,
# so the recorded checksum reflects post-autofix bytes. Green amend
# stages impl files only (not the test), preserving the
# test-file-byte-identical invariant.
lint-autofix-staged:
    #!/usr/bin/env bash
    set -uo pipefail
    staged=$(git diff --cached --name-only --diff-filter=AM | grep -E '\.py$' || true)
    if [[ -z "$staged" ]]; then
        exit 0
    fi
    # --exit-zero so unfixable lint issues don't fail this step;
    # they fall through to check-lint inside `just check` later.
    echo "$staged" | xargs uv run ruff check --fix --exit-zero
    echo "$staged" | xargs uv run ruff format
    # Re-stage so post-autofix bytes are what the commit captures.
    echo "$staged" | xargs git add

# ---------------------------------------------------------------
# Mutating targets (opt-in; not run in CI).
# ---------------------------------------------------------------

fmt:
    uv run ruff format .

lint-fix:
    uv run ruff check --fix .

vendor-update lib:
    uv run python3 dev-tooling/vendor_update.py {{lib}}

# ---------------------------------------------------------------
# Implementation workflow — repo-local livespec-implementation layer
# (non-functional-requirements.md §Contracts §"Implementation justfile
# namespace"). Recipes live in implementation.just and are invoked as
# `just implementation::setup-beads`, `just implementation::beads-doctor`,
# etc. The `mod` mechanism (just 1.31+) gives us a real namespace —
# the spec's `implementation:*` shorthand maps onto it via just's
# native `::` invocation form.
#
# These targets are NOT part of the shipped `livespec` plugin surface;
# the implementation layer lives under
# `.claude/plugins/livespec-implementation/` and is dogfooding-only.
# ---------------------------------------------------------------

mod implementation 'implementation.just'
