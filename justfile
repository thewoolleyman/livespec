# justfile — livespec dev-tooling task runner.
#
# Authoritative source: python-skill-script-style-requirements.md
# §"Enforcement suite — Canonical target list". All recipes
# delegate to their underlying tool or to a dev-tooling check
# script. Per PROPOSAL.md §"Dev tooling and task runner",
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
    # v033 D5a Option-3 (cycle 61): install the repo-tracked
    # git-hook-wrapper.sh as both .git/hooks/pre-commit and
    # .git/hooks/pre-push. The wrapper invokes
    # `mise exec lefthook -- lefthook run <hook-name>` so the
    # gate fires regardless of the user's shell config (the
    # vanilla `lefthook install` hook fails in zsh sessions
    # without `~/.zshrc` mise activation).
    mkdir -p .git/hooks
    cp dev-tooling/git-hook-wrapper.sh .git/hooks/pre-commit
    cp dev-tooling/git-hook-wrapper.sh .git/hooks/pre-push
    chmod +x .git/hooks/pre-commit .git/hooks/pre-push
    ln -sfn ../.claude-plugin/skills .claude/skills

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
    # (still deferred until the docstring-+-`__all__`
    # __init__.py exemption is wired into the cycle-1 mirror-
    # pairing script) + `check-lint`/`check-format`/`check-types`
    # (deferred until config-tier-fix cycles land) +
    # `check-prompts` / `e2e-test-claude-code-mock` (Phase 5/9
    # deferrals unchanged).
    targets=(
        check-imports-architecture
        check-tests
        check-coverage
        check-main-guard
        check-no-inheritance
        check-all-declared
        check-no-write-direct
        check-supervisor-discipline
        check-no-raise-outside-io
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

check-tests:
    uv run pytest

check-coverage:
    #!/usr/bin/env bash
    set -uo pipefail
    # pytest-cov defaults `--cov-config` to `.coveragerc`, which
    # bypasses pyproject.toml's `[tool.coverage.run]` (including
    # the `omit = ["*/_vendor/*"]` carve-out). Pass the config
    # path explicitly so the vendored-tree exclusion takes effect
    # under `pytest --cov`. Without this, structlog (transitively
    # imported by livespec modules) is measured and inflates the
    # report with sub-100% files that aren't first-party code.
    uv run pytest --cov --cov-branch --cov-config=pyproject.toml --cov-report=term-missing
    uv run python3 dev-tooling/checks/per_file_coverage.py

# ---------------------------------------------------------------
# AST / grep / hand-written checks. Each delegates to a script
# under dev-tooling/checks/ authored in Phase 4.
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

# ---------------------------------------------------------------
# E2E + prompt verification (part of `just check`).
# ---------------------------------------------------------------

e2e-test-claude-code-mock:
    LIVESPEC_E2E_HARNESS=mock uv run pytest tests/e2e/

check-prompts:
    uv run pytest tests/prompts/

# ---------------------------------------------------------------
# Alternate-cadence target (NOT in `just check`).
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

# v033 D4 hard gate: returns 1 if any redo commit lacks `## Red output`.
# Lefthook pre-commit only; NOT in `just check` aggregate (the aggregate
# runs once per `just check` invocation, this gate is intrinsically
# per-commit and lives in lefthook directly).
check-red-output-in-commit:
    uv run python3 dev-tooling/checks/red_output_in_commit.py

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

# ---------------------------------------------------------------
# Mutating targets (opt-in; not run in CI).
# ---------------------------------------------------------------

fmt:
    uv run ruff format .

lint-fix:
    uv run ruff check --fix .

vendor-update lib:
    uv run python3 dev-tooling/vendor_update.py {{lib}}
