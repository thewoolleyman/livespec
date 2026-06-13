# justfile — livespec dev-tooling task runner.
#
# `just` is the single source of truth for every dev-tooling
# invocation; lefthook.yml and .github/workflows/*.yml only
# call `just <target>`. Authoritative source for the canonical
# target list: python-skill-script-style-requirements.md
# §"Enforcement suite — Canonical target list".

# `skip` — space-separated list of `check:` aggregate targets to omit
# from a single run (epic li-cvaudit, cvredmd). Default empty: the full
# aggregate runs. The Red-mode pre-commit overrides it on the command
# line — `just skip="check-coverage check-per-file-coverage" check` —
# so the coverage gates are not run at the Red commit (coverage is
# verified at the Green amend). The Green-amend pre-commit overrides it
# with `just skip="check-red-green-replay" check` so the no-arg
# aggregate replay variant does not reject the in-progress Green amend
# (the commit-msg hook is the load-bearing per-commit verifier). This
# is a self-contained just variable; it replaces the prior ambient
# `LIVESPEC_PRECOMMIT_RED_MODE` env var with no env var and no spec
# change.
skip := ""

default:
    @just --list

# ---------------------------------------------------------------
# First-time setup.
# ---------------------------------------------------------------

bootstrap:
    #!/usr/bin/env bash
    set -euo pipefail
    # Resolve the shared git dir and primary checkout root via
    # git-common-dir so the recipe is safe from both the primary
    # checkout and secondary worktrees. From a worktree, .git is a
    # file (not a directory) and git-common-dir resolves to the
    # primary's shared .git; dirname of that gives the primary
    # checkout root. From the primary, git-common-dir returns the
    # relative `.git` path and dirname gives `.`, which realpath
    # expands to the primary root. Both cases produce the correct
    # absolute primary path and shared hooks dir.
    git_common_dir="$(realpath "$(git rev-parse --git-common-dir)")"
    primary_path="$(realpath "$(dirname "$(git rev-parse --git-common-dir)")")"
    hooks_dir="${git_common_dir}/hooks"
    # Idempotent `livespec.primaryPath` on the primary checkout's
    # git-common-dir config (per
    # `SPECIFICATION/non-functional-requirements.md`
    # §"Primary-checkout commit-refuse hook" /
    # §"Commit-refuse hook bootstrap procedure"). The commit-refuse
    # hook reads this config key to decide whether the current
    # toplevel is the primary checkout and the commit should be
    # refused. Runs FIRST so partial failure of any later step
    # cannot leave the primary-path config unset. Both the config
    # target (git-common-dir/config) and the value (primary_path,
    # derived from dirname of git-common-dir resolved via realpath)
    # are worktree-safe: from a secondary worktree, git-common-dir
    # resolves to the primary's shared .git and dirname yields the
    # primary checkout root regardless of the invocation site.
    git config --file "${git_common_dir}/config" livespec.primaryPath "${primary_path}"
    # Install the repo-tracked git-hook-wrapper.sh as pre-commit,
    # pre-push, and commit-msg hooks. Uses hooks_dir (resolved via
    # git-common-dir) so the install lands in the shared hooks dir
    # whether invoked from the primary checkout or a secondary
    # worktree (where .git is a file and mkdir -p .git/hooks would
    # fail). The wrapper carries BOTH the canonical commit-refuse
    # hook body (marker comment + `git rev-parse --show-toplevel`
    # check + `exit 1` branch, recognized by the
    # `primary-checkout-commit-refuse-hook-installed` invariant)
    # AND the mise-managed lefthook delegation, so the same file
    # satisfies the canonical fingerprint check on the primary AND
    # fires lefthook gates on secondary worktrees.
    # `mise exec lefthook -- lefthook run --no-auto-install ...` is
    # what fires the gate regardless of the user's shell config and
    # is the only mechanism that survives lefthook's auto-install
    # clobber (`--no-auto-install` is load-bearing; without it,
    # lefthook backs up the wrapper to `<name>.old` on every fire
    # and replaces it with its PATH-searching stub, which both
    # silently no-ops in Claude Code's bash AND defeats the
    # commit-refuse-hook invariant).
    mkdir -p "${hooks_dir}"
    cp dev-tooling/git-hook-wrapper.sh "${hooks_dir}/pre-commit"
    cp dev-tooling/git-hook-wrapper.sh "${hooks_dir}/pre-push"
    cp dev-tooling/git-hook-wrapper.sh "${hooks_dir}/commit-msg"
    chmod +x "${hooks_dir}/pre-commit" "${hooks_dir}/pre-push" "${hooks_dir}/commit-msg"
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
    claude plugin marketplace add thewoolleyman/livespec-driver-claude
    claude plugin marketplace add thewoolleyman/livespec-impl-beads
    claude plugin install livespec@livespec
    claude plugin install livespec@livespec-driver-claude
    claude plugin install livespec-impl-beads@livespec-impl-beads
    claude plugin update livespec@livespec
    claude plugin update livespec@livespec-driver-claude
    claude plugin update livespec-impl-beads@livespec-impl-beads

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
    #
    # `skip` is a just VARIABLE (declared at the top of this justfile,
    # default empty): a space-separated list of target names to omit
    # from this run (epic li-cvaudit, cvredmd). The Red-mode pre-commit
    # invokes `just skip="check-coverage check-per-file-coverage" check`
    # so coverage is not gated at the Red commit (verified at the Green
    # amend); the Green-amend pre-commit invokes
    # `just skip="check-red-green-replay" check` so the no-arg replay
    # aggregate variant does not reject the in-progress Green amend.
    # These replace the prior ambient `LIVESPEC_PRECOMMIT_RED_MODE` env
    # var. The recipe header stays the bare `check:` that the
    # wiring-completeness checks parse for. Pre-push and CI invoke
    # `just check` with no `skip`, so the full aggregate stays the
    # load-bearing safety net.
    read -ra skip_targets <<< "{{skip}}"
    # Sync the environment ONCE per aggregate pass, then run every
    # target with UV_NO_SYNC=1 so the ~50 per-target `uv run`
    # invocations skip their redundant per-invocation re-sync
    # (work-item livespec-7dro). The single up-front sync
    # keeps the freshness guarantee — a stale lockfile/venv still
    # fails here, loudly, before any target runs. This also caps the
    # cost of a corrupted-venv re-sync loop (e.g. an orphaned
    # dist-info missing its RECORD file, which a sync can never
    # uninstall and therefore retries on EVERY invocation) at one
    # sync attempt per pass instead of one per target, and shrinks
    # the concurrent-sync race window that produces that corruption
    # in the first place. Standalone `just check-<x>` invocations
    # keep uv's default sync-on-run behavior; CI's per-target matrix
    # jobs each sync their own fresh runner and are unaffected.
    if ! uv sync --all-groups; then
        echo "ERROR: up-front 'uv sync --all-groups' failed; aborting the check aggregate" >&2
        exit 1
    fi
    export UV_NO_SYNC=1
    targets=(
        # ---- Canonical block (39 slugs, alphabetical) ----
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
        check-no-direct-destructive-cli
        check-no-direct-tool-invocation
        check-no-except-outside-io
        check-no-inheritance
        check-no-lloc-soft-warnings
        check-no-raise-outside-io
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
        check-tool-backed-check-completeness
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
        check-canonical-slugs-projection
        check-comment-no-historical-refs
        check-copier-template-smoke
        # check-coverage is the aggregate (total) `fail_under = 100`
        # coverage gate. It is a LITERAL member here (and of the CI
        # check-python matrix) so the check-tool-backed-check-completeness
        # meta-check's both-surfaces invariant is satisfied. To avoid a
        # DUPLICATE pytest run it gates off the `.coverage` data file that
        # the canonical check-per-file-coverage slug already produced (see
        # the recipe below), so wiring it adds no second suite run locally.
        check-coverage
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
    ran=0
    for t in "${targets[@]}"; do
        skip_this=0
        for s in "${skip_targets[@]:-}"; do
            if [[ "$t" == "$s" ]]; then
                skip_this=1
                break
            fi
        done
        if [[ "$skip_this" -eq 1 ]]; then
            printf '\n::: just %s (skipped)\n' "$t"
            continue
        fi
        ran=$((ran + 1))
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
    printf '\nAll %d targets passed.\n' "$ran"
    if [[ -z "{{skip}}" ]]; then uv run python -m livespec_dev_tooling.green_token write || true; fi

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
    # Red-mode pre-commit omits this target via `check-pre-commit`'s
    # `just skip="check-coverage check-per-file-coverage" check`
    # argument (a self-contained just variable — there is NO ambient
    # env var). The commit-msg replay hook (`check-red-green-replay`)
    # is the load-bearing verifier in Red mode; coverage is checked at
    # the Green amend. Pre-push, CI, and manual `just check-coverage`
    # invocations run the full aggregate with no `skip`, so this target
    # runs normally there (epic li-cvaudit, cvredmd).
    #
    # check-coverage is the aggregate (total) `fail_under = 100`
    # coverage gate (pyproject.toml [tool.coverage.report]). It is a
    # LITERAL member of both the `just check` array and the CI
    # check-python matrix so the check-tool-backed-check-completeness
    # meta-check's both-surfaces invariant is satisfied. To avoid a
    # DUPLICATE full pytest run when
    # invoked inside the `just check` aggregate, this recipe gates off
    # the EXISTING `.coverage` data file when present: the canonical
    # check-per-file-coverage slug runs `pytest --cov` upfront and
    # alphabetically before this repo-private extra, so `.coverage` is
    # already produced by the time this runs locally. When `.coverage`
    # is ABSENT — the CI check-python matrix runs check-coverage as a
    # standalone job in its own runner with no prior pytest — the
    # recipe runs the suite itself so the aggregate gate still fires.
    # Either way the result is the `fail_under = 100` assertion with NO
    # duplicate suite run in `just check`.
    #
    # pytest-cov defaults `--cov-config` to `.coveragerc`, which
    # bypasses pyproject.toml's `[tool.coverage.run]` (including the
    # `omit = ["*/_vendor/*"]` carve-out). Pass the config path
    # explicitly so the vendored-tree exclusion takes effect under
    # `pytest --cov`. `-n auto` (pytest-xdist) parallelizes the suite;
    # pytest-cov auto-runs `coverage combine` at session-end.
    if [[ -f .coverage ]]; then
        echo ":: check-coverage: reading existing .coverage (produced by check-per-file-coverage); no duplicate suite run"
        uv run coverage report --fail-under=100
    else
        echo ":: check-coverage: no .coverage data file (CI standalone job); running the suite"
        uv run pytest -n auto --cov --cov-branch --cov-config=pyproject.toml --cov-report=term-missing
    fi
    # Per-file 100% line+branch gate. In `just check` this reads the
    # `.coverage` that check-per-file-coverage already wrote (cheap, no
    # suite re-run); in the CI standalone check-coverage job (the only
    # coverage job in livespec's CI matrix — check-per-file-coverage is
    # NOT a matrix entry) it reads the `.coverage` produced two lines
    # above. Retaining this step preserves livespec's pre-bump CI
    # per-file enforcement, which the previous single-step check-coverage
    # provided.
    uv run python -m livespec_dev_tooling.checks.per_file_coverage

# Red-mode-aware pre-commit aggregate. Classifies the staged tree
# shape via `git diff --cached --name-only --diff-filter=AM`. Red
# mode = exactly one test file added or modified under `tests/`
# AND zero implementation files added or modified under
# `.claude-plugin/scripts/livespec/**`,
# `.claude-plugin/scripts/bin/**`, or `dev-tooling/checks/**`
# (modified test files extending pre-existing mirror-pairs are
# valid Red commits too, so the diff-filter includes M as well as
# A). In Red mode, runs `just skip="check-coverage
# check-per-file-coverage" check` so the coverage gates are omitted
# (the commit-msg replay hook is the load-bearing test-verifier in
# Red mode; coverage is checked at the Green amend). This is a
# self-contained recipe argument — there is NO ambient env var
# (epic li-cvaudit, cvredmd). In all other modes (test:/chore:/etc.,
# non-Red feat:/fix:), runs `just check` unconditionally — EXCEPT
# the Green-amend shape below.
#
# Pre-push and CI keep invoking `just check` directly (no Red-mode
# classifier; full suite always).
check-pre-commit:
    #!/usr/bin/env bash
    set -uo pipefail
    staged=$(git diff --cached --name-only --diff-filter=AM)
    py_staged=$(echo "$staged" | grep -E '\.py$' || true)
    test_staged=$(echo "$staged" | grep -E '^tests/.*\.py$' || true)
    # `dev-tooling` (the whole tree, not just `dev-tooling/checks/`)
    # mirrors the red_green_replay check module's _IMPL_PREFIXES:
    # top-level dev-tooling tools (reap_stale_worktrees.py,
    # git_hook_wrapper.py) are impl too, and must trigger the same
    # Red-/Green-shape handling as dev-tooling/checks/ members.
    impl_staged=$(echo "$staged" | grep -E '^(\.claude-plugin/scripts/livespec|\.claude-plugin/scripts/bin|dev-tooling)/.*\.py$' || true)
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
        echo ":: Red-mode shape detected: $test_staged"
        echo ":: skipping coverage gates (commit-msg replay hook is the verifier; coverage runs at Green amend)"
        just skip="check-coverage check-per-file-coverage" check
        exit $?
    fi
    # Green-amend shape: impl staged while HEAD still carries Red-only
    # trailers (the Green amend has not yet written its TDD-Green-*
    # trailers — the commit-msg `check-red-green-replay {1}` hook writes
    # AND verifies them immediately after this pre-commit pass). The
    # no-arg `check-red-green-replay` aggregate variant validates HEAD,
    # which during a Green amend is the in-progress Red commit; it would
    # otherwise reject a perfectly valid Green amend. Skip the aggregate
    # variant here (the commit-msg hook is the load-bearing per-commit
    # verifier); pre-push + CI re-run the full no-arg aggregate against
    # the completed Red->Green HEAD as the safety net (epic li-cvaudit,
    # cvnoarg — mirrors livespec-dev-tooling's check-pre-commit).
    head_msg=$(git log -1 --format=%B 2>/dev/null || true)
    if [[ "$impl_count" -ge 1 ]] \
        && grep -q 'TDD-Red-Test-File-Checksum:' <<< "$head_msg" \
        && ! grep -q 'TDD-Green-Verified-At:' <<< "$head_msg"; then
        echo ":: Green-amend shape detected (impl staged; HEAD carries Red-only trailers)"
        echo ":: skipping no-arg check-red-green-replay (commit-msg replay hook verifies the Green amend)"
        just skip="check-red-green-replay" check
        exit $?
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
    if uv run python -m livespec_dev_tooling.green_token check 2>&1; then
        echo ":: pre-push: green token matched — tree byte-identical to last green check; skipping full aggregate (CI is authoritative)"
        exit 0
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

# Destructive-default CLI wrapping gate (SPECIFICATION/
# non-functional-requirements.md §"Destructive-default CLI wrapping"):
# greps the agent-facing trees (dev-tooling/, .claude-plugin/,
# .claude/plugins/) for direct invocations of known-destructive-default
# CLIs (bd init, git push --force/-f, git reset --hard, gh repo delete)
# outside the explicit `[tool.livespec_dev_tooling].
# destructive_cli_allowlist` path-prefix allowlist.
check-no-direct-destructive-cli:
    uv run python -m livespec_dev_tooling.checks.no_direct_destructive_cli

check-no-direct-tool-invocation:
    uv run python -m livespec_dev_tooling.checks.no_direct_tool_invocation

# Smoke test for templates/impl-plugin/ — runs copier copy against a
# stock answers fixture and verifies the generated tree contains the
# expected file set. Acceptance gate for the C.6 sub-task of the
# Phase C multi-repo-split epic. Repo-metadata check: not gated by
# .py changeset.
check-copier-template-smoke:
    uv run python3 dev-tooling/checks/copier_template_smoke.py

# Release-time projection of the canonical check-slug aggregate into the
# committed copier-template DATA file templates/impl-plugin/
# canonical-slugs.yml. Reads livespec_dev_tooling.canonical_checks (the
# single source of truth) and writes the alphabetically-sorted slug set.
# Re-run after the canonical set changes in livespec-dev-tooling, then
# cut a template release so consumers re-sync via copier update. Per
# SPECIFICATION/contracts.md §"Shared code sync — livespec-dev-tooling"
# → Template gate.
stamp-canonical-slugs:
    uv run python3 dev-tooling/checks/canonical_slugs_projection.py --write

# Anti-drift gate: verify the committed templates/impl-plugin/
# canonical-slugs.yml equals livespec_dev_tooling.canonical_checks.
# canonical_check_slugs(), so the release-time projection can never
# silently drift from the source of truth. Livespec-private; wired into
# the `just check` aggregate (after the canonical block) and CI.
check-canonical-slugs-projection:
    uv run python3 dev-tooling/checks/canonical_slugs_projection.py

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

# The CLI end-to-end harness consumer (former tests/e2e-cli/ +
# e2e-cli-test-claude-code-mock target) relocated to the
# livespec-driver-claude repo together with the /livespec:* skill
# bindings: structural skill discovery + the fail-closed fixture
# coverage gate run where the skills live (per SPECIFICATION/
# contracts.md §"CLI end-to-end harness contract", the harness itself
# still ships from livespec-dev-tooling).

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

# Tool-backed-check completeness meta-check. Enforces that the four
# tool-backed slugs (check-lint, check-format, check-types,
# check-coverage) are LITERAL members of BOTH the `just check` targets
# array AND a CI matrix's matrix.target list. Canonical slug (lives
# under livespec_dev_tooling/checks/), so check-aggregate-completeness
# forces it into the aggregate; it in turn forces the four tool-backed
# slugs onto both enforcement surfaces.
check-tool-backed-check-completeness:
    uv run python -m livespec_dev_tooling.checks.tool_backed_check_completeness

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

# Canonical-slug alias for the full per-file 100% line+branch
# coverage gate. The canonical slug derived from the module name
# `per_file_coverage.py` is `check-per-file-coverage`. Same logic
# as the livespec-private `check-coverage` recipe (kept for CI
# job-name + branch-protection.json compatibility); this is the
# canonical-aggregate entry. In Red-mode pre-commit this target is
# omitted by `check-pre-commit` via the `just skip=...` argument
# (coverage is verified at the Green amend; the commit-msg replay hook
# is the load-bearing verifier in Red mode), so no ambient env-var read
# is needed here (epic li-cvaudit, cvredmd).
check-per-file-coverage:
    #!/usr/bin/env bash
    set -uo pipefail
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
# mutation`. Always invoked plainly; the module self-manages its
# RUN/SKIP lever (epic li-cvaudit, cvtodo). `LIVESPEC_RUN_MUTATION`
# unset → the check logs "skipped" and exits 0; set to a non-empty
# value (the release-tag workflow sets it to `true`) → the mutmut
# suite runs. No external gate, no silent skip — replaces the prior
# `LIVESPEC_RELEASE_GATE` skip carve-out.
check-check-mutation:
    uv run python -m livespec_dev_tooling.checks.check_mutation

# Always invoked plainly; the module self-manages its severity lever
# (epic li-cvaudit, cvtodo). The heading-coverage.json TODO scan
# ALWAYS runs; `LIVESPEC_FAIL_IF_HEADING_COVERAGE_TODOS_EXIST` unset
# → TODO offenders warn + exit 0 (authoring placeholders surface
# without blocking per-commit `just check`); set (the release-tag
# workflow sets it to `true`) → they fail. Replaces the prior
# `LIVESPEC_RELEASE_GATE` skip carve-out, which silently skipped the
# scan entirely when the gate was unset.
check-no-todo-registry:
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
# incremental`. With explicit `--paths <impl_path> [<impl_path>...]`
# (repo-root-relative) it scopes the per-file 100% gate to those
# paths. With NO args (the canonical aggregate / `just check`
# invocation) the check DERIVES the changed impl-`.py` set from
# `git diff --name-only origin/master...HEAD` and gates those — no
# longer a no-op (epic li-cvaudit, cvnoarg). The interactive
# developer use case still passes `--paths` explicitly.
check-check-coverage-incremental *args:
    uv run python -m livespec_dev_tooling.checks.check_coverage_incremental {{args}}

# Always invoked plainly; the module self-manages its severity lever
# (epic li-cvaudit, cvtodo). The 201-250 LLOC soft-band scan ALWAYS
# runs; `LIVESPEC_FAIL_IF_LLOC_SOFT_WARNINGS_EXIST` unset → soft-band
# offenders warn + exit 0 (per-commit `just check` stays green); set
# (the release-tag workflow sets it to `true`) → they fail. Closes
# the soft-band drift loophole: per-commit ergonomic (warning), but
# tag-push enforcement blocks release until clean. Replaces the prior
# `LIVESPEC_RELEASE_GATE` skip carve-out.
check-no-lloc-soft-warnings:
    uv run python -m livespec_dev_tooling.checks.no_lloc_soft_warnings

# Trailer-based Red→Green replay verification (hard gate). Invoked
# by lefthook commit-msg stage with the commit-message file path as
# argv[1] (the load-bearing per-commit verifier) — the hook writes
# trailers via `git interpret-trailers --in-place`. The canonical
# aggregate / `just check` invokes this with NO msg_path; the module
# then DERIVES the message from `git log -1 --format=%B` (HEAD) and
# validates it — no longer a no-op (epic li-cvaudit, cvnoarg). The
# Green-amend pre-commit shape omits this aggregate variant via
# `check-pre-commit`'s `just skip="check-red-green-replay" check`
# (the commit-msg hook verifies the in-progress Green amend).
#
# Note on lefthook stage: the design is fundamentally `commit-msg`
# (writes to the commit-message file; distinguishes Red/Green via
# HEAD~0 inspection), not pre-commit.
check-red-green-replay *args:
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
