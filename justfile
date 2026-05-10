# justfile — livespec dev-tooling task runner.
#
# Authoritative source: python-skill-script-style-requirements.md
# §"Enforcement suite — Canonical target list". All recipes
# delegate to their underlying tool or to a dev-tooling check
# script. Per,
# `just` is the single source of truth for every dev-tooling
# invocation; lefthook.yml and .github/workflows/*.yml only
# call `just <target>`.
#
# Phase deferrals (per PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md):
#   - `just bootstrap` recreates the `.claude/skills ->
#     ../.claude-plugin/skills` symlink (added at Phase 2 sub-step
#     8 once the target directory exists). The `lefthook install`
#     step is added at Phase 5's exit.
#   - Most check-* recipes delegate to dev-tooling/checks/<name>.py
#     scripts authored in Phase 4. They will fail until Phase 4
#     lands them; this is expected during Phases 1-3.
#   - The lefthook hook is NOT installed into .git/hooks/ until
#     `just bootstrap` is fleshed out at Phase 5 exit. Pre-commit
#     `just check` invocations therefore do not block commits
#     during Phases 2-4.

# Default to listing targets when no recipe is invoked.
default:
    @just --list

# ---------------------------------------------------------------
# First-time setup.
# ---------------------------------------------------------------

bootstrap:
    # v033 D5a Option-3 (cycle 61) + v034 step 3 (this commit):
    # install the repo-tracked git-hook-wrapper.sh as
    # .git/hooks/pre-commit, .git/hooks/pre-push, AND
    # .git/hooks/commit-msg (v034 D3 replay-hook stage). The wrapper
    # invokes `mise exec lefthook -- lefthook run <hook-name> "$@"`
    # so the gate fires regardless of the user's shell config and
    # the commit-msg stage receives the commit-message file path as
    # the first argument (the value lefthook passes to {1}).
    mkdir -p .git/hooks
    cp dev-tooling/git-hook-wrapper.sh .git/hooks/pre-commit
    cp dev-tooling/git-hook-wrapper.sh .git/hooks/pre-push
    cp dev-tooling/git-hook-wrapper.sh .git/hooks/commit-msg
    chmod +x .git/hooks/pre-commit .git/hooks/pre-push .git/hooks/commit-msg
    ln -sfn ../.claude-plugin/skills .claude/skills
    # v034 D4: notes refspec for `refs/notes/commits` advisory cache.
    # Idempotent — git config --add tolerates duplicate values across
    # repeated bootstrap invocations (the value is checked literally;
    # if already present at this exact text, --add is a no-op for the
    # config-loading semantics that consumers care about). Run only
    # if the value isn't already present.
    git config --get-all remote.origin.fetch | grep -qx '+refs/notes/*:refs/notes/*' || git config --add remote.origin.fetch '+refs/notes/*:refs/notes/*'

# ---------------------------------------------------------------
# Aggregate check — runs every check below sequentially. Continues
# on failure (matches CI fail-fast: false behavior); exits non-zero
# if any target failed and prints the failure list.
# ---------------------------------------------------------------

check:
    #!/usr/bin/env bash
    set -uo pipefail
    # v033 D5a + D5b transition: aggregate is thinned to the
    # currently-passing target set so lefthook can install at
    # the end of D5a step 5. Each second-redo cycle that
    # restores a check script (or fixes a config-tier failure)
    # ALSO re-adds its target to this list in the same commit.
    # By the end of the second redo the list returns to the
    # full canonical-target enumeration (per
    # python-skill-script-style-requirements.md §"Canonical
    # target list"). Targets removed here but still defined in
    # this file (recipes intact, just not aggregated) are: every
    # `check-*`-backed dev-tooling/checks/*.py target except the
    # four v033-D5a guardrails plus `check-coverage` (now
    # rejoined post-cycle-117 — every measured first-party file
    # is at 100% line+branch) and `check-tests-mirror-pairing`
    # (rejoined post-Phase-7 sub-step 2 mini-track item M4 — the
    # private-helper + pure-declaration exemptions are wired in)
    # + `check-lint`/`check-format`/`check-types`
    # (deferred until config-tier-fix cycles land).
    # `check-prompts` and `e2e-test-claude-code-mock` rejoined at Phase 9.
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
    uv run python3 dev-tooling/checks/file_lloc.py || rc=$?
    exit $rc

check-imports-architecture:
    PYTHONPATH=.claude-plugin/scripts uv run lint-imports

check-coverage:
    #!/usr/bin/env bash
    set -uo pipefail
    # Per v036 D1: when invoked under the pre-commit Red-mode-aware
    # aggregate (`check-pre-commit` sets LIVESPEC_PRECOMMIT_RED_MODE
    # if the staged tree matches Red mode), skip pytest entirely.
    # The commit-msg replay hook (`check-red-green-replay`) is the
    # load-bearing verifier in Red mode — it runs pytest on the
    # staged test file and expects non-zero exit. Pre-push, CI,
    # and manual `just check-coverage` invocations don't set the env
    # var and run normally. Per v039 D1, `check-coverage` is the
    # sole pytest-running aggregate target (check-tests was dropped
    # because pytest already runs as a side effect of pytest --cov,
    # so the standalone check-tests target was double-counting).
    if [[ -n "${LIVESPEC_PRECOMMIT_RED_MODE:-}" ]]; then
        echo ":: check-coverage skipped (v036 D1 Red-mode pre-commit; verified at Green amend)"
        exit 0
    fi
    # pytest-cov defaults `--cov-config` to `.coveragerc`, which
    # bypasses pyproject.toml's `[tool.coverage.run]` (including
    # the `omit = ["*/_vendor/*"]` carve-out). Pass the config
    # path explicitly so the vendored-tree exclusion takes effect
    # under `pytest --cov`. Without this, structlog (transitively
    # imported by livespec modules) is measured and inflates the
    # report with sub-100% files that aren't first-party code.
    # `-n auto` (pytest-xdist) parallelizes the suite across cores.
    # pytest-cov auto-runs `coverage combine` at session-end to merge
    # the per-worker `.coverage.<host>.<pid>.<rand>` files into the
    # single `.coverage` that `per_file_coverage.py` reads on the
    # next line. Per v039 D2 wall-clock target: drops `check-coverage`
    # from ~3.5min serial to under ~1min on a typical multi-core
    # developer machine.
    uv run pytest -n auto --cov --cov-branch --cov-config=pyproject.toml --cov-report=term-missing
    uv run python3 dev-tooling/checks/per_file_coverage.py

# Per v036 D1: Red-mode-aware pre-commit aggregate. Classifies the
# staged tree shape via `git diff --cached --name-only --diff-filter=AM`
# (broadened from `--diff-filter=A` per v037 D1 — modified test files
# extending pre-existing mirror-pairs are valid Red commits too):
# Red mode = exactly one test file added or modified under `tests/`
# AND zero implementation files added or modified under
# `.claude-plugin/scripts/livespec/**`,
# `.claude-plugin/scripts/bin/**`, or `dev-tooling/checks/**`.
# In Red mode, sets LIVESPEC_PRECOMMIT_RED_MODE=1 and runs `just
# check`; check-coverage observes the env var and skips (commit-msg
# replay hook is the load-bearing test-verifier in Red mode). In
# all other modes (Green amend, test:/chore:/etc., non-Red
# feat:/fix:), runs `just check` unconditionally.
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
    uv run python3 dev-tooling/checks/private_calls.py

check-global-writes:
    uv run python3 dev-tooling/checks/global_writes.py

check-rop-pipeline-shape:
    uv run python3 dev-tooling/checks/rop_pipeline_shape.py

check-supervisor-discipline:
    uv run python3 dev-tooling/checks/supervisor_discipline.py

check-no-raise-outside-io:
    uv run python3 dev-tooling/checks/no_raise_outside_io.py

check-no-except-outside-io:
    uv run python3 dev-tooling/checks/no_except_outside_io.py

check-public-api-result-typed:
    uv run python3 dev-tooling/checks/public_api_result_typed.py

check-schema-dataclass-pairing:
    uv run python3 dev-tooling/checks/schema_dataclass_pairing.py

check-main-guard:
    uv run python3 dev-tooling/checks/main_guard.py

check-wrapper-shape:
    uv run python3 dev-tooling/checks/wrapper_shape.py

check-keyword-only-args:
    uv run python3 dev-tooling/checks/keyword_only_args.py

check-match-keyword-only:
    uv run python3 dev-tooling/checks/match_keyword_only.py

check-no-inheritance:
    uv run python3 dev-tooling/checks/no_inheritance.py

check-assert-never-exhaustiveness:
    uv run python3 dev-tooling/checks/assert_never_exhaustiveness.py

check-newtype-domain-primitives:
    uv run python3 dev-tooling/checks/newtype_domain_primitives.py

check-all-declared:
    uv run python3 dev-tooling/checks/all_declared.py

check-no-write-direct:
    uv run python3 dev-tooling/checks/no_write_direct.py

check-pbt-coverage-pure-modules:
    uv run python3 dev-tooling/checks/pbt_coverage_pure_modules.py

check-claude-md-coverage:
    uv run python3 dev-tooling/checks/claude_md_coverage.py

check-heading-coverage:
    uv run python3 dev-tooling/checks/heading_coverage.py

check-vendor-manifest:
    uv run python3 dev-tooling/checks/vendor_manifest.py

check-no-direct-tool-invocation:
    uv run python3 dev-tooling/checks/no_direct_tool_invocation.py

check-tools:
    uv run python3 dev-tooling/checks/check_tools.py

# Guard Layer 1 mechanical checks. Both shell out to `gh api` to
# read remote GitHub state; they exit 0 with a structured warning
# when `gh` is unavailable or unauthenticated locally so per-commit
# pre-commit runs are not blocked. CI with GH_TOKEN exercises the
# full enforcement path.
check-branch-protection-alignment:
    uv run python3 dev-tooling/checks/branch_protection_alignment.py

check-master-ci-green:
    uv run python3 dev-tooling/checks/master_ci_green.py

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
    uv run python3 dev-tooling/checks/check_mutation.py

check-no-todo-registry:
    uv run python3 dev-tooling/checks/no_todo_registry.py

check-comment-line-anchors:
    uv run python3 dev-tooling/checks/comment_line_anchors.py

# Per v039 D3: path-scoped fast-feedback variant of check-coverage.
# Takes `--paths <impl_path> [<impl_path>...]` (repo-root-relative)
# and applies the per-file 100% line+branch coverage gate to the
# named impls only. Resolves each impl's mirror-paired test per
# v033 D1, runs pytest --cov on the combined test set with full
# instrumentation (path-scoped --cov=<dir> breaks under subprocess
# instrumentation, so the recipe runs unfiltered --cov and applies
# the per-file scoping at REPORT time), then applies
# `coverage report --include=<impl_paths> --fail-under=100`.
# NOT in `just check` aggregate — interactive developer tool, not
# per-commit gate. Wall-clock target: under 10 seconds for a typical
# single-file pair. Used during the v039 D4 Red→Green authoring
# loop to surface defensive-branch coverage gaps proactively,
# BEFORE the Green amend triggers a multi-minute aggregate retry.
check-coverage-incremental *args:
    uv run python3 dev-tooling/checks/check_coverage_incremental.py {{args}}

# Release-gate ONLY — paired with check-mutation + check-no-todo-registry
# on the release-tag CI workflow. NOT in `just check`; does NOT run
# per-commit. Closes the M3 soft-band drift loophole: forces refactor
# work to land before any v* tag push when any file is in 201-250 LLOC.
check-no-lloc-soft-warnings:
    uv run python3 dev-tooling/checks/no_lloc_soft_warnings.py

# v034 D3 hard gate: trailer-based Red→Green replay verification.
# Invoked by lefthook commit-msg stage (NOT pre-commit) — the hook
# requires the commit-message file path as argv[1] to write trailers
# via `git interpret-trailers --in-place`. NOT in `just check`
# aggregate (per-commit, not per-tree).
#
# Note on lefthook stage: the design is fundamentally `commit-msg`
# (writes to the commit-message file; distinguishes Red/Green via
# HEAD~0 inspection), not pre-commit.
check-red-green-replay msg_path:
    uv run python3 dev-tooling/checks/red_green_replay.py {{msg_path}}

# v033 D1 mirror-pairing: every covered .py under livespec/, bin/,
# and dev-tooling/checks/ has a paired tests/<mirror>/test_<name>.py.
# In `just check` aggregate (per v033 D1).
check-tests-mirror-pairing:
    uv run python3 dev-tooling/checks/tests_mirror_pairing.py

# v033 D3 commit-pair gate: every commit touching livespec/**, bin/**,
# or dev-tooling/checks/** also touches tests/**. Lefthook pre-commit
# only; NOT in `just check` aggregate (per-commit, not per-tree).
check-commit-pairs-source-and-test:
    uv run python3 dev-tooling/checks/commit_pairs_source_and_test.py

# Phase 7 sub-step 2 mini-track item M1: ruff fix + format on staged
# Python files BEFORE the rest of the pre-commit gate runs. Saves the
# ~5min retry on auto-fixable lint trivia. Runs as lefthook
# `00-lint-autofix-staged` step ahead of the existing checks.
# Per SPECIFICATION/spec.md §"Developer-tooling layout" + contracts.md
# §"Pre-commit step ordering" (post-v003). Non-blocking — unfixable
# issues fall through to be caught by check-lint / check-format inside
# the `just check` aggregate at the `02-check-pre-commit` step.
# v034 D2-D3 interaction: autofix runs BEFORE the commit-msg replay
# hook computes the Red trailer's test-file SHA-256 checksum, so the
# recorded checksum reflects post-autofix bytes. Green amend stages
# impl files only (not the test), preserving the
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
