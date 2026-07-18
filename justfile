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

# Install the canonical livespec commit-refuse hook by REUSING the
# shared livespec-dev-tooling installer module
# (`python -m livespec_dev_tooling.install_commit_refuse_hooks`) — the
# SINGLE source of the structural hook body, pinned in pyproject.toml.
# This is the Installer slot of the Worktree-discipline concern (per
# `SPECIFICATION/non-functional-requirements.md` §"Conformance
# Pattern") — a shared, idempotent `just` recipe `bootstrap` delegates
# to. The installed body refuses commits/pushes STRUCTURALLY: it exits
# 1 when `git rev-parse --git-dir` equals `git rev-parse
# --git-common-dir` (a real primary checkout; a secondary worktree's
# git-dir is `.git/worktrees/<name>` and so differs) UNLESS `git config
# livespec.sandboxExempt` is `true`. There is therefore NO
# `livespec.primaryPath` arming step and so no fail-open window — the
# hook is armed the moment it is installed (this supersedes the v095
# `livespec.primaryPath` mechanism, which failed OPEN whenever its
# arming step was missed). At worktrees (and in declared-exempt Fabro
# sandboxes) the body delegates to mise-managed lefthook so the per-hook
# gates fire (the body's `--no-auto-install` keeps lefthook from
# clobbering it). The installer resolves the shared hooks dir via
# git-common-dir so the install lands correctly whether invoked from the
# primary checkout or a secondary worktree, and is idempotent. There is
# NO repo-tracked git-hook-wrapper.sh copy any more — the body ships
# ONCE in the wheel (convergence zs22.7.9.1; no vendored duplicate to
# drift).
install-commit-refuse-hooks:
    uv run python -m livespec_dev_tooling.install_commit_refuse_hooks

# First-touch setup — a THIN delegator to the shipped LOCAL first-touch
# reconcile verb (`livespec_dev_tooling.fleet.local_reconcile`), the
# generalized successor to this recipe's former inline steps. Reuse-first:
# NO copied logic — the verb walks the LOCAL obligation partition
# (`contract.LOCAL_OBLIGATION_ROWS`): mise trust/install, uv sync, the
# structural commit-refuse hooks, the advisory `refs/notes/*` refspec, the
# worktree-root mise-trust entry, the beads tenant-dir hardening, and
# project-scoped Claude/Codex plugin registration — each an idempotent
# assert-then-reconcile row. The two plugin rows delegate back to THIS
# repo's own `ensure-plugins` / `ensure-codex-plugins` recipes below (the
# plugin set is repo-specific, so each governed repo's recipe stays the
# single source). The verb resolves the target checkout worktree-safely via
# `git rev-parse --git-common-dir`, so invoking from a linked worktree still
# provisions the primary checkout's shared state — preserving this recipe's
# former primary-root resolution. `--checkout` defaults to the working
# directory. Mirrors the `install-commit-refuse-hooks` recipe's
# `uv run python -m ...` from-package invocation.
bootstrap:
    uv run python -m livespec_dev_tooling.fleet.local_reconcile

# The standard shared derive-from-settings wrapper: it reads the committed
# `.claude/settings.json` (`extraKnownMarketplaces`, including each source's
# `ref`, and `enabledPlugins`) at runtime and issues the `claude plugin
# marketplace add` / `install` / `update` commands for exactly the
# marketplaces and plugins it finds there — one source of truth, so
# recipe-content drift is structurally impossible. Idempotent: the underlying
# `add` / `install` / `update` all exit 0 when the target is already present /
# already at latest, and the post-install `update` is what carries a bumped
# upstream release to a previously-bootstrapped working copy.
ensure-plugins:
    mise exec -- uv run --no-sync python -m livespec_dev_tooling.fleet.ensure_plugins

# Idempotent host-wide Codex plugin provisioning. Codex does not support
# project-scoped plugin enablement, so these registrations intentionally land in
# the user's default CODEX_HOME and are visible to every repo on the host. Codex
# is an optional dogfooding runtime; bootstrap skips this target when the CLI is
# absent but fails on real install errors when Codex is present.
ensure-codex-plugins:
    #!/usr/bin/env bash
    set -euo pipefail
    if ! command -v codex >/dev/null 2>&1; then
        echo "codex CLI not found; skipping host-wide Codex plugin install." >&2
        exit 0
    fi
    codex plugin marketplace add thewoolleyman/livespec --ref release
    codex plugin marketplace add thewoolleyman/livespec-driver-codex --ref release
    codex plugin marketplace add thewoolleyman/livespec-orchestrator-beads-fabro --ref release
    codex plugin marketplace upgrade livespec
    codex plugin marketplace upgrade livespec-driver-codex
    codex plugin marketplace upgrade livespec-orchestrator-beads-fabro
    codex plugin add livespec@livespec
    codex plugin add livespec@livespec-driver-codex
    codex plugin add livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro

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
        # ---- Canonical block (42 slugs, alphabetical) ----
        check-agents-ai-references-resolve
        check-aggregate-completeness
        check-all-declared
        check-assert-never-exhaustiveness
        check-branch-protection-alignment
        check-canonical-recipe-fidelity
        check-check-coverage-incremental
        check-check-mutation
        check-check-tools
        check-ci-matrix-completeness
        check-claude-md-coverage
        check-comment-line-anchors
        check-commit-pairs-source-and-test
        check-file-lloc
        check-fleet-marketplace-relative-sources
        check-global-writes
        check-handoff-dispatch-routing
        check-heading-coverage
        check-keyword-only-args
        check-local-memory-drift-audit
        check-main-guard
        check-master-ci-green
        check-match-keyword-only
        check-newtype-domain-primitives
        check-no-direct-destructive-cli
        check-no-direct-tool-invocation
        check-no-except-outside-io
        check-no-fmt-directives
        check-no-inheritance
        check-no-lloc-soft-warnings
        check-no-raise-outside-io
        check-no-shadow-ledger-body-identical
        check-no-todo-registry
        check-no-write-direct
        check-partition-completeness
        check-pbt-coverage-pure-modules
        check-per-file-coverage
        check-plan-thread-anchor-declared
        check-plan-thread-epic-parity
        check-plugin-resolution
        check-primary-checkout-commit-refuse-hook-installed
        check-private-calls
        check-public-api-result-typed
        check-red-green-replay
        check-rop-pipeline-shape
        check-self-hosted-routing
        check-skill-invocation-paths
        check-source-trees-scoped-to-consumer
        check-supervisor-discipline
        check-tests-mirror-pairing
        check-tests-no-subprocess-spawn
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
        check-behavior-scenario-link
        check-canonical-slugs-projection
        check-cli-explicit-project-root
        check-codex-no-repo-local-adapters
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
        check-no-renderer-vendoring
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

# `check-static` — fastest-first fail-fast helper for fast agent/dev
# feedback (work-item livespec-dev-tooling-7us.8). Runs ONLY the cheap
# static checks — `ruff format --check .`, `ruff check .`, `pyright`
# (i.e. check-format, check-lint, check-types) — as a fail-fast
# sequence: it STOPS at the first failing check and exits non-zero, so
# a sub-2s ruff/pyright failure surfaces immediately instead of after
# `just check`'s slow pytest+coverage tail. This is a developer/agent
# convenience like the helper recipes above; it is deliberately NOT a
# member of the `check:` aggregate `targets=(...)` array, NOT a
# canonical slug (no livespec_dev_tooling/checks/ module), and NOT in
# the CI matrix. The authoritative full gate remains `just check`
# (still run at pre-push and in CI) — `check-static` is a fast
# pre-flight, never a replacement for it.
check-static:
    #!/usr/bin/env bash
    set -euo pipefail
    uv run ruff format --check .
    uv run ruff check .
    uv run pyright

# `changed-files` — print the changed `.py` set this branch touches,
# repo-root-relative, one path per line, sorted + de-duplicated
# (work-item livespec-dev-tooling-7us.9). The set is the UNION of two
# git views, so an agent gets the live working set whether or not it has
# committed yet:
#   - `git diff --name-only origin/master...HEAD` — every `.py` this
#     branch's commits changed vs the merge-base with origin/master;
#   - `git diff --cached --name-only --diff-filter=AM` — added/modified
#     `.py` currently staged but not yet committed.
# This is the exact set `check-changed` consumes for its scoped gate.
# Helper recipe (like `check-static`): NOT a member of the `check:`
# aggregate `targets=(...)` array, NOT a canonical slug, NOT in the CI
# matrix.
changed-files:
    #!/usr/bin/env bash
    set -uo pipefail
    # `grep` exits 1 on zero matches; an empty changed set is normal (a
    # clean branch), so swallow that into exit 0 via `|| true` — the
    # consuming `check-changed` treats empty as "nothing to gate".
    { git diff --name-only origin/master...HEAD;
      git diff --cached --name-only --diff-filter=AM; } \
        | { grep -E '\.py$' || true; } | sort -u

# `check-changed` — modified-files INNER-LOOP gate for fast scoped
# feedback during iteration (work-item livespec-dev-tooling-7us.9). Feeds
# the `changed-files` set into `check-check-coverage-incremental --paths
# <set>`, which already (a) resolves each changed impl `.py` to its
# mirror-paired test and runs that pytest SUBSET, and (b) applies the
# path-scoped per-file coverage gate — i.e. it composes the existing
# scoping plumbing rather than re-deriving it. An empty changed set is a
# no-op (exit 0): nothing changed, nothing to gate.
#
# SCOPE — INNER-LOOP SPEEDUP ONLY, NOT a replacement for the final gate.
# It runs only the test subset + path-scopable checks for the files this
# branch touched, so an agent gets sub-suite feedback while iterating. The
# AUTHORITATIVE gate remains `just check`, which runs the FULL suite + the
# full AST scans + the aggregate 100% coverage gate at pre-push and in CI.
# Like `check-static`, this is a developer/agent convenience: NOT a member
# of the `check:` aggregate `targets=(...)` array, NOT a canonical slug,
# and NOT in the CI matrix.
check-changed:
    #!/usr/bin/env bash
    set -uo pipefail
    mapfile -t changed < <(just changed-files)
    if [[ "${#changed[@]}" -eq 0 ]]; then
        echo ":: check-changed: no changed .py vs origin/master (and none staged); nothing to gate"
        echo ":: the authoritative full gate remains 'just check' (run at pre-push + CI)"
        exit 0
    fi
    echo ":: check-changed: scoping the test subset + per-file coverage gate to ${#changed[@]} changed .py:"
    printf '   %s\n' "${changed[@]}"
    echo ":: INNER-LOOP ONLY — 'just check' runs the FULL suite/AST scans at pre-push + CI"
    just check-check-coverage-incremental --paths "${changed[@]}"

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
    # `-e` (errexit) is load-bearing: without it a non-zero pytest/coverage
    # exit is swallowed by the trailing per_file_coverage command (whose exit
    # code would become the recipe's), silently reporting GREEN on a RED suite.
    set -euo pipefail
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
    # `pytest --cov`. `-n 4` (pytest-xdist) parallelizes the suite;
    # pytest-cov auto-runs `coverage combine` at session-end.
    if [[ -f .coverage ]]; then
        echo ":: check-coverage: reading existing .coverage (produced by check-per-file-coverage); no duplicate suite run"
        uv run coverage report --fail-under=100
    else
        echo ":: check-coverage: no .coverage data file (CI standalone job); running the suite"
        uv run pytest -n 4 --cov --cov-branch --cov-config=pyproject.toml --cov-report=term-missing
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
        check-codex-no-repo-local-adapters
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

# Smoke test for templates/orchestrator-plugin/ — runs copier copy against a
# stock answers fixture and verifies the generated tree contains the
# expected file set. Acceptance gate for the C.6 sub-task of the
# Phase C multi-repo-split epic. Repo-metadata check: not gated by
# .py changeset.
check-copier-template-smoke:
    uv run python3 dev-tooling/checks/copier_template_smoke.py

# Release-time projection of the canonical check-slug aggregate into the
# committed copier-template DATA file templates/orchestrator-plugin/
# canonical-slugs.yml. Reads livespec_dev_tooling.canonical_checks (the
# single source of truth) and writes the alphabetically-sorted slug set.
# Re-run after the canonical set changes in livespec-dev-tooling, then
# cut a template release so consumers re-sync via copier update. Per
# SPECIFICATION/contracts.md §"Shared code sync — livespec-dev-tooling"
# → Template gate.
stamp-canonical-slugs:
    uv run python3 dev-tooling/checks/canonical_slugs_projection.py --write

# Anti-drift gate: verify the committed templates/orchestrator-plugin/
# canonical-slugs.yml equals livespec_dev_tooling.canonical_checks.
# canonical_check_slugs(), so the release-time projection can never
# silently drift from the source of truth. Livespec-private; wired into
# the `just check` aggregate (after the canonical block) and CI.
# Guardrail #1a — the mechanical clause→scenario link. Extracts
# every MUST/SHOULD behavior clause from the live core spec, derives
# its gap-id via the shared dev-tooling/spec_clauses.py primitive, and
# surfaces any clause lacking a `clauses[]` link to an existing
# scenarios.md H2 section in tests/heading-coverage.json. ALWAYS-WIRED
# and ALWAYS-RUNNING with a self-documenting severity lever:
# LIVESPEC_BEHAVIOR_SCENARIO_LINK=warn|fail (default warn — advisory
# while the link backlog is backfilled; flips to fail later). Never
# silently skipped.
check-behavior-scenario-link:
    uv run python3 dev-tooling/checks/behavior_scenario_link.py

check-canonical-slugs-projection:
    uv run python3 dev-tooling/checks/canonical_slugs_projection.py

# Spec-side CLI explicit-project-root conformance (SPECIFICATION/
# contracts.md §"CLI shape conventions" → the explicit-project-root
# addressing rule): every livespec module that defines a build_parser()
# factory (a spec-side CLI) must register --project-root, so a consumer
# can address any repository's state through the named CLI.
check-cli-explicit-project-root:
    uv run python3 dev-tooling/checks/cli_explicit_project_root.py

check-codex-no-repo-local-adapters:
    uv run python3 dev-tooling/checks/codex_no_repo_local_adapters.py

# Renderer non-vendoring gate (SPECIFICATION/constraints.md
# §"Renderer non-vendoring"): scans pyproject.toml dependency
# declarations AND .claude-plugin/scripts/_vendor/ for any diagram
# renderer (plantuml, graphviz, mermaid, or equivalents) and fails if
# any is present. Livespec ships Mermaid-native diagrams and depends on
# no renderer; an author needing another diagram type renders it
# outside livespec and commits an opaque image asset.
check-no-renderer-vendoring:
    uv run python3 dev-tooling/checks/no_renderer_vendoring.py

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

# Cross-harness plugin-resolution Verifier from livespec-dev-tooling
# (the Conformance Pattern's concern #2). Reads the `.livespec.jsonc`
# `harnesses` declaration and verifies each declared agent-runtime
# harness either resolves the `/livespec:*` surface or is marked
# exempt. Per SPECIFICATION/non-functional-requirements.md §"Conformance
# Pattern". Core declares both harnesses exempt (artifact carrier), so
# this passes trivially.
check-plugin-resolution:
    uv run python -m livespec_dev_tooling.checks.plugin_resolution

# Shared commit-refuse-hook invariant from livespec-dev-tooling. Per
# SPECIFICATION/contracts.md §"`primary-checkout-commit-refuse-hook-installed`"
# and §"Shared code sync — livespec-dev-tooling", the commit-refuse-hook
# rule is fleet-wide-by-intent and its canonical implementation ships
# in the shared inventory (available since livespec-dev-tooling v0.5.0).
# This recipe is the project-root-scoped CI/just-check adoption that the
# spec mandates for every consumer repo. Supersedes the v091-v094
# `primary-checkout-bare-flag-set` mechanism (which caused stale-on-disk
# reads at primaries that the hook mechanism does not).
check-primary-checkout-commit-refuse-hook-installed:
    uv run python -m livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed

# Shared agent-instruction `.ai/` reference-resolution Verifier from
# livespec-dev-tooling. Parses each AGENTS.md `.ai/<topic>.md` reference
# and verifies it resolves to an existing file, per
# SPECIFICATION/contracts.md §"Fleet agent-instruction core". Core's
# AGENTS.md references already resolve, so this passes trivially.
check-agents-ai-references-resolve:
    uv run python -m livespec_dev_tooling.checks.agents_ai_references_resolve

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

# Fleet marketplace ref-pin guard: catalog plugin sources MUST stay
# checkout-relative (`./...`). Github-type or other non-relative
# sources silently ignore the registered marketplace ref pin and clone
# default HEAD instead.
check-fleet-marketplace-relative-sources:
    uv run python -m livespec_dev_tooling.checks.fleet_marketplace_relative_sources

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
    # `-e` (errexit) is load-bearing: without it a non-zero pytest exit is
    # swallowed by the trailing per_file_coverage command, silently reporting
    # GREEN on a RED suite. See check-coverage above for the same rationale.
    set -euo pipefail
    # See check-coverage above for the rationale on the cov-config
    # path + pytest-xdist parallelism.
    uv run pytest -n 4 --cov --cov-branch --cov-config=pyproject.toml --cov-report=term-missing
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

# Forbid test-spawned Python subprocesses (`subprocess.run([sys.executable, ...])`)
# in tests/ — they self-instrument under `pytest --cov` and race concurrent
# coverage runs; prefer the in-process `main()` pattern. Canonical check added
# in livespec-dev-tooling v0.14.1 (4i5). In `just check` aggregate.
check-tests-no-subprocess-spawn:
    uv run python -m livespec_dev_tooling.checks.tests_no_subprocess_spawn

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
    uv run python -m livespec_dev_tooling.vendor_update {{lib}}

# Deterministic, idempotent worktree REAPER — the ACTION counterpart
# to doctor's detection-only `no-stale-worktree` check. The Layer 3
# orchestrator runs this to mechanically clean up orphaned worktrees
# in any fleet member repo after their PRs rebase-merge (remote branch gone).
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

check-partition-completeness:
    uv run python -m livespec_dev_tooling.checks.partition_completeness

check-canonical-recipe-fidelity:
    uv run python -m livespec_dev_tooling.checks.canonical_recipe_fidelity

check-ci-matrix-completeness:
    uv run python -m livespec_dev_tooling.checks.ci_matrix_completeness

check-no-fmt-directives:
    uv run python -m livespec_dev_tooling.checks.no_fmt_directives

check-no-shadow-ledger-body-identical:
    uv run python -m livespec_dev_tooling.checks.no_shadow_ledger_body_identical

check-local-memory-drift-audit:
    uv run python -m livespec_dev_tooling.checks.local_memory_drift_audit

check-handoff-dispatch-routing:
    uv run python -m livespec_dev_tooling.checks.handoff_dispatch_routing

check-self-hosted-routing:
    uv run python -m livespec_dev_tooling.checks.self_hosted_routing

check-source-trees-scoped-to-consumer:
    uv run python -m livespec_dev_tooling.checks.source_trees_scoped_to_consumer

check-plan-thread-anchor-declared:
    uv run python -m livespec_dev_tooling.checks.plan_thread_anchor_declared

check-plan-thread-epic-parity:
    uv run python -m livespec_dev_tooling.checks.plan_thread_epic_parity
