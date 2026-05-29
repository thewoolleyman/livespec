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
    # Idempotent `livespec.primaryPath` on the primary checkout's
    # git-common-dir config (per
    # `SPECIFICATION/non-functional-requirements.md`
    # §"Primary-checkout commit-refuse hook" /
    # §"Commit-refuse hook bootstrap procedure"). The commit-refuse
    # hook reads this config key to decide whether the current
    # toplevel is the primary checkout and the commit should be
    # refused. Runs FIRST so partial failure of any later step
    # cannot leave the primary-path config unset. Targets
    # `git rev-parse --git-common-dir` so the recipe writes the
    # right file when invoked from the primary checkout AND from
    # secondary worktrees; the value is `git rev-parse --show-toplevel`
    # of the primary (the common-dir's parent, when invoked at the
    # primary) — for the primary, `git rev-parse --show-toplevel`
    # gives the right answer directly; for worktrees, this recipe
    # is intended to run only at first-touch on a fresh primary
    # clone (the usual bootstrap idiom).
    git config --file "$(git rev-parse --git-common-dir)/config" livespec.primaryPath "$(git rev-parse --show-toplevel)"
    # Install the repo-tracked git-hook-wrapper.sh as pre-commit,
    # pre-push, and commit-msg hooks. The wrapper now carries
    # BOTH the canonical commit-refuse hook body (marker comment
    # + `git rev-parse --show-toplevel` check + `exit 1` branch,
    # recognized by the `primary-checkout-commit-refuse-hook-installed`
    # invariant) AND the mise-managed lefthook delegation, so the
    # same file satisfies the canonical fingerprint check on the
    # primary AND fires lefthook gates on secondary worktrees.
    # `mise exec lefthook -- lefthook run --no-auto-install ...` is
    # what fires the gate regardless of the user's shell config and
    # is the only mechanism that survives lefthook's auto-install
    # clobber (`--no-auto-install` is load-bearing; without it,
    # lefthook backs up the wrapper to `<name>.old` on every fire
    # and replaces it with its PATH-searching stub, which both
    # silently no-ops in Claude Code's bash AND defeats the
    # commit-refuse-hook invariant).
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
    # Canonical-check aggregate, per SPECIFICATION/contracts.md
    # §"Wiring-completeness invariant" (v094): every canonical slug
    # emitted by `livespec_dev_tooling.canonical_checks` MUST appear
    # here in alphabetical order; livespec-private checks MAY follow
    # after the canonical block in any order. The in-repo gate is
    # `check-aggregate-completeness`, which fails if any canonical
    # slug is missing or out-of-order.
    #
    # Aggregator continues on failure (matches CI fail-fast: false)
    # and exits non-zero with the failure list if any target failed.
    targets=(
        # ---- Canonical block (38 slugs, alphabetical) ----
        check-aggregate-completeness
        check-all-declared
        check-assert-never-exhaustiveness
        check-branch-protection-alignment
        check-check-coverage-incremental
        check-check-mutation
        check-check-tools
        check-claude-md-coverage
        check-comment-line-anchors
        check-commit-pairs-source-and-test
        check-file-lloc
        check-global-writes
        check-heading-coverage
        check-keyword-only-args
        check-main-guard
        check-master-ci-green
        check-match-keyword-only
        check-newtype-domain-primitives
        check-no-direct-tool-invocation
        check-no-except-outside-io
        check-no-inheritance
        check-no-lloc-soft-warnings
        check-no-raise-outside-io
        check-no-stale-revise-branches
        check-no-todo-registry
        check-no-write-direct
        check-pbt-coverage-pure-modules
        check-per-file-coverage
        check-primary-checkout-commit-refuse-hook-installed
        check-private-calls
        check-public-api-result-typed
        check-red-green-replay
        check-rop-pipeline-shape
        check-skill-invocation-paths
        check-supervisor-discipline
        check-tests-mirror-pairing
        check-vendor-manifest
        check-wrapper-shape
        # ---- Livespec-private block (extends after canonical) ----
        # Private checks whose intent is specific to livespec itself
        # per SPECIFICATION/contracts.md §"Shared code sync —
        # livespec-dev-tooling" partition rule. `check-coverage`,
        # `check-complexity`, and `check-tools` are intentionally
        # ABSENT here: they overlap with canonical
        # `check-per-file-coverage`, `check-file-lloc`+`check-lint`,
        # and `check-check-tools` respectively. The private recipes
        # remain defined (CI job names + branch-protection.json
        # reference them) but are not wired in the aggregate to avoid
        # running the same module twice.
        check-comment-no-historical-refs
        check-copier-template-smoke
        check-doctor-static
        check-format
        check-imports-architecture
        check-lint
        check-prompts
        check-schema-dataclass-pairing
        check-types
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

check-skill-invocation-paths:
    uv run python -m livespec_dev_tooling.checks.skill_invocation_paths

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

# Doctor deterministic static-phase coverage gate. Per SPECIFICATION/
# non-functional-requirements.md §"Enforcement-suite invocation" →
# §"Doctor static-phase coverage", this target MUST run doctor's
# static phase against the main SPECIFICATION/ tree + every sub-spec
# under SPECIFICATION/templates/<name>/, exiting non-zero (exit 3) on
# any fail-status finding. The wrapper at .claude-plugin/scripts/bin/
# doctor_static.py auto-walks the main spec + every templates/<name>/
# sub-spec in a single invocation. LLM-driven objective + subjective
# phases are OUT of scope (interactive-only via /livespec:doctor).
check-doctor-static:
    uv run --no-project .claude-plugin/scripts/bin/doctor_static.py

# Shared commit-refuse-hook invariant from livespec-dev-tooling. Per
# SPECIFICATION/contracts.md §"`primary-checkout-commit-refuse-hook-installed`"
# and §"Shared code sync — livespec-dev-tooling", the commit-refuse-hook
# rule is family-wide-by-intent and its canonical implementation ships
# in the shared inventory (available since livespec-dev-tooling v0.5.0).
# This recipe is the project-root-scoped CI/just-check adoption that the
# spec mandates for every consumer repo. Supersedes the v091-v094
# `primary-checkout-bare-flag-set` mechanism (which caused stale-on-disk
# reads at primaries that the hook mechanism does not).
check-primary-checkout-commit-refuse-hook-installed:
    uv run python -m livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed

# In-repo gate for the wiring-completeness invariant
# (SPECIFICATION/contracts.md v094 §"Shared code sync —
# livespec-dev-tooling"). Parses the local `justfile`'s `check:`
# recipe and verifies every canonical slug emitted by
# `livespec_dev_tooling.canonical_checks` is wired in alphabetical
# order, with livespec-private extras appearing only after the
# canonical block. Self-bootstrapping: the slug
# `check-aggregate-completeness` is itself canonical, so dropping
# it would fail this check on the next run.
check-aggregate-completeness:
    uv run python -m livespec_dev_tooling.checks.aggregate_completeness

# Canonical-slug alias for the shared `check-tools` discoverability
# check. The canonical slug derived from the module name
# `check_tools.py` is `check-check-tools`. Same logic as the
# livespec-private `check-tools` alias retained for CI/branch-
# protection compatibility; this is the canonical-aggregate entry.
check-check-tools:
    uv run python -m livespec_dev_tooling.checks.check_tools

# File LLOC ceiling check. Canonical-aggregate entry — the
# livespec-private `check-complexity` recipe historically composed
# ruff C90,PLR with file_lloc; the canonical partition splits the
# two so that ruff complexity is already covered by `check-lint`'s
# `select = ["C90", "PL", ...]` table and `file_lloc` runs as its
# own canonical slug. Per SPECIFICATION/contracts.md v094 wiring-
# completeness.
check-file-lloc:
    uv run python -m livespec_dev_tooling.checks.file_lloc

# Refuse new revise passes while a stale spec/* branch is ahead of
# master. Invoked by livespec's /livespec:revise SKILL.md pre-step
# refusal; included in the canonical aggregate for cross-cutting
# self-host coverage (per SPECIFICATION/contracts.md wiring-
# completeness invariant).
#
# In livespec's primary bare checkout, in-flight spec/* worktrees
# are a natural part of the dogfooded revise workflow — every
# /livespec:revise pass creates a spec/<topic> branch. The
# `--allow-stale-branches` flag surfaces the diagnostics as info
# rather than gating the aggregate; the load-bearing enforcement
# remains at the /livespec:revise pre-step refusal. See
# work-item li-stalebr for the longer-term semantic resolution
# (worktree-aware exemption or matrix gating).
check-no-stale-revise-branches:
    uv run python -m livespec_dev_tooling.checks.no_stale_revise_branches --allow-stale-branches

# Canonical-slug alias for the full per-file 100% line+branch
# coverage gate. The canonical slug derived from the module name
# `per_file_coverage.py` is `check-per-file-coverage`. Same logic
# as the livespec-private `check-coverage` recipe (kept for CI
# job-name + branch-protection.json compatibility); this is the
# canonical-aggregate entry. Red-mode pre-commit skip preserved
# (commit-msg replay hook is the verifier; aggregate-time coverage
# is not load-bearing in Red mode).
check-per-file-coverage:
    #!/usr/bin/env bash
    set -uo pipefail
    if [[ -n "${LIVESPEC_PRECOMMIT_RED_MODE:-}" ]]; then
        echo ":: check-per-file-coverage skipped (Red-mode pre-commit; verified at Green amend)"
        exit 0
    fi
    # See check-coverage above for the rationale on the cov-config
    # path + pytest-xdist parallelism.
    uv run pytest -n auto --cov --cov-branch --cov-config=pyproject.toml --cov-report=term-missing
    uv run python -m livespec_dev_tooling.checks.per_file_coverage

# ---------------------------------------------------------------
# Alternate-cadence target (NOT in `just check`).
#
# Routes tests/e2e/ through the real harness tier (tests/e2e/real_claude.py),
# which uses claude-agent-sdk + the `@anthropic-ai/claude-code` CLI against
# the live Anthropic API. Per SPECIFICATION/contracts.md §"E2E harness
# contract §"Harness mode selection".
#
# Requirements:
#   - `ANTHROPIC_API_KEY` env var set.
#   - `claude` CLI on PATH (`npm install -g @anthropic-ai/claude-code`).
#
# Selection: by default this recipe runs ONLY the `e2e_golden`-marked
# tests (the flagship multi-sub-command flows) for cost control. The
# e2e_golden tests cover seed → propose-change → critique → revise →
# doctor → prune-history in `test_happy_path_minimal`, plus the
# doctor-fail-then-fix flow. `mock_only` tests are skipped automatically
# via the conftest hook. Run with `JUST_E2E_PYTEST_ARGS='-m ""'` to
# exercise the full suite.
# ---------------------------------------------------------------

e2e-test-claude-code-real:
    #!/usr/bin/env bash
    set -uo pipefail
    # Default selection: -m e2e_golden (flagship multi-sub-command flows).
    # Override by exporting JUST_E2E_PYTEST_ARGS, e.g.:
    #   JUST_E2E_PYTEST_ARGS='-m ""' just e2e-test-claude-code-real   # full suite
    #   JUST_E2E_PYTEST_ARGS='-k happy' just e2e-test-claude-code-real # name filter
    args="${JUST_E2E_PYTEST_ARGS:--m e2e_golden}"
    LIVESPEC_E2E_HARNESS=real uv run pytest tests/e2e/ ${args}

# ---------------------------------------------------------------
# Release-gate targets (NOT in `just check`; run on release-tag CI
# workflow only). Per python-skill-script-style-requirements.md
# §"Mutation testing as release-gate" the threshold semantics
# live HERE in the recipe (ratchet-with-ceiling against
# .mutmut-baseline.json, capped at 80%), NOT in pyproject.toml.
# ---------------------------------------------------------------

check-mutation:
    uv run python -m livespec_dev_tooling.checks.check_mutation

# Canonical-slug alias for the release-gate mutation check. The
# canonical slug derived from the module name `check_mutation.py`
# (per `livespec_dev_tooling.canonical_checks`) is `check-check-
# mutation`. Gated by LIVESPEC_RELEASE_GATE so the canonical
# aggregate (`just check`) can wire the slug per the wiring-
# completeness invariant (SPECIFICATION/contracts.md §"Shared code
# sync — livespec-dev-tooling" v094) without making per-commit
# `just check` runs choke on the multi-minute mutation suite. The
# release-tag workflow MUST set LIVESPEC_RELEASE_GATE=1 before
# invoking this target.
check-check-mutation:
    #!/usr/bin/env bash
    set -uo pipefail
    if [[ -z "${LIVESPEC_RELEASE_GATE:-}" ]]; then
        echo ":: check-check-mutation skipped (LIVESPEC_RELEASE_GATE unset; release-gate-only check)"
        exit 0
    fi
    uv run python -m livespec_dev_tooling.checks.check_mutation

# Release-gate ONLY — paired with check-check-mutation and
# check-no-lloc-soft-warnings on the release-tag CI workflow. Gated
# by LIVESPEC_RELEASE_GATE so the canonical aggregate can wire the
# slug (per SPECIFICATION/contracts.md §"Shared code sync —
# livespec-dev-tooling" wiring-completeness) without making per-
# commit `just check` runs choke on TODO entries that are
# legitimate authoring placeholders. The release-tag workflow
# MUST set LIVESPEC_RELEASE_GATE=1 before invoking this target.
check-no-todo-registry:
    #!/usr/bin/env bash
    set -uo pipefail
    if [[ -z "${LIVESPEC_RELEASE_GATE:-}" ]]; then
        echo ":: check-no-todo-registry skipped (LIVESPEC_RELEASE_GATE unset; release-gate-only check)"
        exit 0
    fi
    uv run python -m livespec_dev_tooling.checks.no_todo_registry

check-comment-line-anchors:
    uv run python -m livespec_dev_tooling.checks.comment_line_anchors

check-comment-no-historical-refs:
    uv run python3 dev-tooling/checks/comment_no_historical_refs.py

# Path-scoped fast-feedback variant of check-coverage. Takes
# `--paths <impl_path> [<impl_path>...]` (repo-root-relative) and
# applies the per-file 100% line+branch coverage gate to the named
# impls only. Resolves each impl's mirror-paired test, runs pytest
# --cov on the combined test set with full instrumentation
# (path-scoped --cov=<dir> breaks under subprocess instrumentation,
# so the recipe runs unfiltered --cov and applies the per-file
# scoping at REPORT time), then applies
# `coverage report --include=<impl_paths> --fail-under=100`.
# Interactive developer tool, not per-commit gate. Wall-clock
# target: under 10 seconds for a typical single-file pair. Used
# during the Red→Green authoring loop to surface defensive-branch
# coverage gaps proactively, BEFORE the Green amend triggers a
# multi-minute aggregate retry.
check-coverage-incremental *args:
    uv run python -m livespec_dev_tooling.checks.check_coverage_incremental {{args}}

# Canonical-slug alias for the path-scoped incremental coverage
# check. The canonical slug derived from the module name
# `check_coverage_incremental.py` is `check-check-coverage-
# incremental`. Wired into the canonical aggregate (per the
# wiring-completeness invariant, SPECIFICATION/contracts.md v094)
# but short-circuits when called with no args — the full-tree
# per-file 100% gate is enforced by check-per-file-coverage.
check-check-coverage-incremental *args:
    #!/usr/bin/env bash
    set -uo pipefail
    if [[ -z "{{args}}" ]]; then
        echo ":: check-check-coverage-incremental skipped (no --paths provided; aggregate-mode no-op)"
        echo ":: full-tree per-file 100% gate is enforced by check-per-file-coverage"
        exit 0
    fi
    uv run python -m livespec_dev_tooling.checks.check_coverage_incremental {{args}}

# Release-gate ONLY — paired with check-check-mutation + check-no-
# todo-registry on the release-tag CI workflow. Wired into the
# canonical aggregate (per the wiring-completeness invariant,
# SPECIFICATION/contracts.md v094) but short-circuits unless
# LIVESPEC_RELEASE_GATE is set so per-commit `just check` runs do
# NOT choke on legitimate authoring placeholders in the 201-250
# LLOC soft band. Closes the M3 soft-band drift loophole: forces
# refactor work to land before any v* tag push when any file is
# in 201-250 LLOC.
check-no-lloc-soft-warnings:
    #!/usr/bin/env bash
    set -uo pipefail
    if [[ -z "${LIVESPEC_RELEASE_GATE:-}" ]]; then
        echo ":: check-no-lloc-soft-warnings skipped (LIVESPEC_RELEASE_GATE unset; release-gate-only check)"
        exit 0
    fi
    uv run python -m livespec_dev_tooling.checks.no_lloc_soft_warnings

# Trailer-based Red→Green replay verification (hard gate). Invoked
# by lefthook commit-msg stage (NOT pre-commit) — the hook requires
# the commit-message file path as argv[1] to write trailers via
# `git interpret-trailers --in-place`. Wired into the canonical
# aggregate (per SPECIFICATION/contracts.md v094 wiring-completeness)
# but the recipe short-circuits when called with no args — the
# load-bearing verifier is the commit-msg hook, not `just check`.
#
# Note on lefthook stage: the design is fundamentally `commit-msg`
# (writes to the commit-message file; distinguishes Red/Green via
# HEAD~0 inspection), not pre-commit.
check-red-green-replay *args:
    #!/usr/bin/env bash
    set -uo pipefail
    if [[ -z "{{args}}" ]]; then
        echo ":: check-red-green-replay skipped (no msg_path provided; aggregate-mode no-op)"
        echo ":: load-bearing verifier is the commit-msg hook (lefthook)"
        exit 0
    fi
    uv run python -m livespec_dev_tooling.checks.red_green_replay {{args}}

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

# Deterministic, idempotent worktree REAPER — the ACTION counterpart
# to doctor's detection-only `no-stale-worktree` check. The Layer 3
# orchestrator runs this to mechanically clean up orphaned worktrees
# in any family repo after their PRs rebase-merge (remote branch gone).
# Reaps a NON-primary worktree only when its branch is "done"
# (remote-gone), its working tree is clean, and it is not held by a
# LIVE process lock; never touches the primary worktree. NOT part of
# `just check` (it is an action, not a check). The first positional
# arg is the target repo (default: cwd); any trailing args pass
# through to the script (e.g. `--dry-run`):
#   just reap-stale-worktrees                          # reap cwd repo
#   just reap-stale-worktrees /path/to/repo            # reap a sibling
#   just reap-stale-worktrees . --dry-run              # preview cwd repo
#   just reap-stale-worktrees /path/to/repo --dry-run  # preview a sibling
reap-stale-worktrees repo="." *args="":
    uv run python3 dev-tooling/reap_stale_worktrees.py --repo {{repo}} {{args}}

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
