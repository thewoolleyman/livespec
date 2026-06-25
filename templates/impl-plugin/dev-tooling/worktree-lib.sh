#!/usr/bin/env bash
# worktree-lib.sh — portable, ecosystem-neutral worktree-lifecycle core.
#
# Generated from livespec/templates/impl-plugin/dev-tooling/worktree-lib.sh
# at copier-copy time; re-sync via `copier update --vcs-ref=master` when
# livespec publishes a new release.
#
# WHAT THIS IS
# ============
# The single source of truth for this repo's worktree discipline: every
# tracked-file mutation happens in an ISOLATED git worktree under
# ~/.worktrees/<repo>/<branch>, never on the shared primary checkout. This
# script implements the four lifecycle verbs the discipline needs —
# `create`, `hydrate`, `land`, `reap` — plus the portable primary-vs-linked
# detection they share.
#
# It is deliberately ECOSYSTEM-NEUTRAL and pure-git: it shells out to `git`
# only and makes NO assumption about Python/Rust/JS/etc., so it stays correct
# under any invocation (including before a task runner is resolvable). It is
# DRIVEN by `just`: the mandated `just worktree-{create,hydrate,land,reap}`
# recipes call this core directly — the core carries the logic, the recipes
# stay logic-free. `just` is mandated non-functionally across the fleet +
# adopters; where an ecosystem has a native tool, a strict pass-through wrapper
# (e.g. `cargo xtask worktree create` → `just worktree-create`) forwards to
# those recipes, never an alternative runner.
#
# PRIMARY-VS-LINKED DETECTION (the load-bearing primitive)
# ========================================================
# A git worktree is the PRIMARY checkout when `git rev-parse
# --git-common-dir` and `git rev-parse --git-dir` resolve to the SAME path;
# in a LINKED worktree they DIFFER (the git-dir is
# <primary>/.git/worktrees/<name>). This is config-free and portable: it
# needs no `git config` key, no environment marker, and works identically in
# every clone. The structural commit-refuse hook (git-hook-wrapper.sh) uses the
# exact same test so the hook and the lifecycle helpers always agree on what
# "primary" means.
#
# HYDRATION IS AN OVERRIDABLE HOOK
# ================================
# "Hydrate" means something different per ecosystem (populate node_modules,
# create a .venv, warm a build cache, …). The core does NOT bake any of that
# in — it delegates hydration to an OVERRIDABLE hook that DEFAULTS TO A
# NO-OP. The hook is, in resolution order:
#   1. the command in the WORKTREE_HYDRATE_HOOK environment variable, if set;
#   2. an executable dev-tooling/worktree-hydrate.sh at the repo root, if
#      present;
#   3. otherwise nothing (a friendly no-op).
# The shipped dev-tooling/worktree-hydrate.sh is itself a no-op stub; a
# consuming repo replaces it with its ecosystem-correct hydration. (A future
# livespec release adds per-ecosystem hydrate profiles selected at scaffold
# time; this core does not need to change for that.)
#
# USAGE
#   ./dev-tooling/worktree-lib.sh detect            # print 'primary' or 'linked'
#   ./dev-tooling/worktree-lib.sh create <branch> [<base-ref>]
#   ./dev-tooling/worktree-lib.sh hydrate           # run the hydrate hook (no-op by default)
#   ./dev-tooling/worktree-lib.sh land [<base-ref>] # rebase onto base then report next step
#   ./dev-tooling/worktree-lib.sh reap [--execute] [--force]
#   ./dev-tooling/worktree-lib.sh help
#
# This script is sourceable too: `source worktree-lib.sh` exposes the
# worktree_* functions without dispatching a subcommand (the dispatcher only
# runs when the script is executed directly).

set -euo pipefail

# --------------------------------------------------------------------------
# Primary-vs-linked detection.
# --------------------------------------------------------------------------

# worktree_is_primary: exit 0 iff the current worktree IS the primary
# checkout (git-common-dir == git-dir, realpath-normalized). Exit 1 in a
# linked worktree. Mirrors the structural commit-refuse hook
# (git-hook-wrapper.sh) exactly.
worktree_is_primary() {
    common_dir="$(git rev-parse --git-common-dir)"
    git_dir="$(git rev-parse --git-dir)"
    # Normalize via `cd … && pwd -P` so a relative `.git` and an absolute
    # path compare correctly.
    common_dir_abs="$(cd "$common_dir" && pwd -P)"
    git_dir_abs="$(cd "$git_dir" && pwd -P)"
    [ "$common_dir_abs" = "$git_dir_abs" ]
}

# worktree_primary_path: print the absolute path of the primary checkout.
# The first `worktree ` entry from `git worktree list --porcelain` is always
# the primary.
worktree_primary_path() {
    git worktree list --porcelain | awk '/^worktree /{print $2; exit}'
}

# worktree_repo_name: print the repo name used in the worktree root
# convention (~/.worktrees/<repo>/<branch>). Derived from the primary
# checkout's directory basename so it needs no config.
worktree_repo_name() {
    basename "$(worktree_primary_path)"
}

# worktree_root: print the per-user worktree root for this repo,
# ~/.worktrees/<repo>. Overridable via the WORKTREE_ROOT env var (a future
# scaffold question may seed a non-default root).
worktree_root() {
    if [ -n "${WORKTREE_ROOT:-}" ]; then
        printf '%s\n' "$WORKTREE_ROOT"
    else
        printf '%s/.worktrees/%s\n' "$HOME" "$(worktree_repo_name)"
    fi
}

# --------------------------------------------------------------------------
# create — branch a fresh worktree from <base-ref> (default origin's default
# branch) under ~/.worktrees/<repo>/<branch>, then hydrate it.
# --------------------------------------------------------------------------

worktree_create() {
    branch="${1:-}"
    base_ref="${2:-}"
    if [ -z "$branch" ]; then
        echo "worktree-lib create: BLOCKED — a <branch> argument is required." >&2
        echo "  usage: worktree-lib.sh create <branch> [<base-ref>]" >&2
        return 2
    fi
    primary="$(worktree_primary_path)"
    if [ -z "$base_ref" ]; then
        # Resolve the remote's default branch (e.g. origin/main or
        # origin/master) without hard-coding either name.
        base_ref="$(git -C "$primary" symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null \
            | sed 's#^refs/remotes/##' || true)"
        if [ -z "$base_ref" ]; then
            base_ref="origin/HEAD"
        fi
    fi
    dest="$(worktree_root)/$branch"

    echo "worktree-lib create: fetching origin in $primary"
    git -C "$primary" fetch origin
    echo "worktree-lib create: git worktree add -b $branch $dest $base_ref"
    git -C "$primary" worktree add -b "$branch" "$dest" "$base_ref"

    echo "worktree-lib create: hydrating $dest"
    ( cd "$dest" && worktree_hydrate )

    echo "worktree-lib create: ready — cd $dest"
}

# --------------------------------------------------------------------------
# hydrate — run the overridable, default-no-op hydrate hook.
# --------------------------------------------------------------------------

worktree_hydrate() {
    # Refuse to hydrate the primary checkout (hydration prepares an isolated
    # worktree; running it on the primary is almost always a mistake). Exit
    # 0 with a friendly skip so callers can invoke it defensively.
    if worktree_is_primary; then
        echo "worktree-lib hydrate: skip — primary checkout, nothing to hydrate"
        return 0
    fi

    if [ -n "${WORKTREE_HYDRATE_HOOK:-}" ]; then
        echo "worktree-lib hydrate: running WORKTREE_HYDRATE_HOOK"
        # shellcheck disable=SC2086
        # Intentional word-splitting so WORKTREE_HYDRATE_HOOK can carry args.
        eval ${WORKTREE_HYDRATE_HOOK}
        return $?
    fi

    repo_root="$(git rev-parse --show-toplevel)"
    hook="$repo_root/dev-tooling/worktree-hydrate.sh"
    if [ -x "$hook" ]; then
        echo "worktree-lib hydrate: running $hook"
        "$hook"
        return $?
    fi
    if [ -f "$hook" ]; then
        echo "worktree-lib hydrate: running (via sh) $hook"
        sh "$hook"
        return $?
    fi

    echo "worktree-lib hydrate: no hydrate hook configured — no-op"
    echo "  (set WORKTREE_HYDRATE_HOOK or add an executable dev-tooling/worktree-hydrate.sh"
    echo "   to teach this repo its ecosystem-correct hydration.)"
    return 0
}

# --------------------------------------------------------------------------
# land — rebase the current worktree branch onto the latest base, then print
# the land-mode-neutral next step. landing is intentionally a REPORT, not an
# automatic push/merge: the repo's own land mode (PR, merge-queue, direct
# push) is its choice, and this core must not assume one.
# --------------------------------------------------------------------------

worktree_land() {
    base_ref="${1:-}"
    if worktree_is_primary; then
        echo "worktree-lib land: BLOCKED — you are on the PRIMARY checkout." >&2
        echo "  Land from inside the worktree, never the shared primary." >&2
        return 1
    fi
    if [ -z "$base_ref" ]; then
        base_ref="$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null \
            | sed 's#^refs/remotes/##' || true)"
        if [ -z "$base_ref" ]; then
            base_ref="origin/HEAD"
        fi
    fi
    echo "worktree-lib land: fetch origin && rebase onto $base_ref"
    git fetch origin
    git rebase "$base_ref"
    branch="$(git rev-parse --abbrev-ref HEAD)"
    echo "worktree-lib land: rebased $branch onto $base_ref."
    echo "  Next, land via this repo's chosen path, e.g.:"
    echo "    git push -u origin $branch   # then open a PR / merge per the repo's land mode"
    echo "  (livespec mandates the worktree+land CONTRACT, not a specific land tool.)"
}

# --------------------------------------------------------------------------
# reap — remove stale / orphaned worktrees safely. Dry-run by default.
# Generalized from the openbrain reaper (originally TypeScript) into portable
# shell with no ecosystem assumptions.
# --------------------------------------------------------------------------

worktree_reap() {
    execute=0
    force=0
    for arg in "$@"; do
        case "$arg" in
            --execute) execute=1 ;;
            --force) force=1 ;;
            -h|--help)
                worktree_reap_help
                return 0
                ;;
            *)
                echo "worktree-lib reap: unknown argument '$arg' (see --help)." >&2
                return 2
                ;;
        esac
    done

    primary="$(worktree_primary_path)"
    current="$(git rev-parse --show-toplevel)"

    mode="dry-run"
    [ "$execute" -eq 1 ] && mode="EXECUTE"
    [ "$force" -eq 1 ] && mode="$mode, --force"
    echo "worktree-lib reap ($mode)"
    echo "  primary: $primary"

    echo "worktree-lib reap: fetching origin (to evaluate merged-into-base)"
    git -C "$primary" fetch --prune origin || true

    # Resolve the base ref once for merged-ness checks.
    base_ref="$(git -C "$primary" symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null \
        | sed 's#^refs/remotes/##' || true)"
    [ -z "$base_ref" ] && base_ref="origin/HEAD"

    removed=0
    pruned=0
    skipped=0
    need_prune=0

    # Walk `git worktree list --porcelain`. Each record is a blank-line-
    # separated block: a `worktree <path>` line, optional `HEAD <sha>`,
    # `branch <ref>` / `detached`, and `prunable <reason>`.
    wt_path=""
    wt_head=""
    wt_branch=""
    wt_detached=0
    wt_prunable=0
    wt_prunable_reason=""

    _reap_flush() {
        [ -z "$wt_path" ] && return 0
        if [ "$wt_detached" -eq 1 ]; then
            label="$wt_path [detached]"
        else
            label="$wt_path [${wt_branch:-?}]"
        fi

        if [ "$wt_path" = "$primary" ]; then
            echo "  SKIP   $label — primary checkout"
            skipped=$((skipped + 1))
            return 0
        fi
        if [ "$wt_path" = "$current" ]; then
            echo "  SKIP   $label — current worktree (running here)"
            skipped=$((skipped + 1))
            return 0
        fi
        if [ "$wt_prunable" -eq 1 ]; then
            echo "  PRUNE  $label — prunable ($wt_prunable_reason)"
            need_prune=1
            pruned=$((pruned + 1))
            return 0
        fi

        # Feature worktree. Reap only when clean AND merged into the base,
        # unless --force.
        dirty=0
        if [ -n "$(git -C "$wt_path" status --porcelain 2>/dev/null)" ]; then
            dirty=1
        fi
        merged=0
        if [ -n "$wt_head" ] && git -C "$primary" merge-base --is-ancestor "$wt_head" "$base_ref" 2>/dev/null; then
            merged=1
        fi

        if [ "$dirty" -eq 1 ] && [ "$force" -eq 0 ]; then
            echo "  SKIP   $label — uncommitted changes (pass --force to remove)"
            skipped=$((skipped + 1))
            return 0
        fi
        if [ "$merged" -eq 0 ] && [ "$force" -eq 0 ]; then
            echo "  SKIP   $label — branch not merged into $base_ref (pass --force to remove)"
            skipped=$((skipped + 1))
            return 0
        fi

        reason="$([ "$merged" -eq 1 ] && echo "merged into $base_ref" || echo "UNMERGED (forced)")"
        [ "$dirty" -eq 1 ] && reason="$reason, dirty (forced)"
        echo "  REMOVE $label — $reason"
        removed=$((removed + 1))
        if [ "$execute" -eq 1 ]; then
            if [ "$force" -eq 1 ] || [ "$dirty" -eq 1 ]; then
                git -C "$primary" worktree remove --force "$wt_path"
            else
                git -C "$primary" worktree remove "$wt_path"
            fi
            if [ -n "$wt_branch" ] && [ "$wt_detached" -eq 0 ]; then
                if [ "$force" -eq 1 ]; then
                    git -C "$primary" branch -D "$wt_branch" \
                        || echo "  (branch $wt_branch not deleted — delete manually if intended)"
                else
                    git -C "$primary" branch -d "$wt_branch" \
                        || echo "  (branch $wt_branch not deleted — delete manually if intended)"
                fi
            fi
        fi
    }

    while IFS= read -r line; do
        case "$line" in
            "worktree "*)
                _reap_flush
                wt_path="${line#worktree }"
                wt_head=""
                wt_branch=""
                wt_detached=0
                wt_prunable=0
                wt_prunable_reason=""
                ;;
            "HEAD "*) wt_head="${line#HEAD }" ;;
            "branch "*)
                ref="${line#branch }"
                case "$ref" in
                    refs/heads/*) wt_branch="${ref#refs/heads/}" ;;
                    *) wt_branch="$ref" ;;
                esac
                ;;
            "detached") wt_detached=1 ;;
            "prunable"*)
                wt_prunable=1
                wt_prunable_reason="${line#prunable}"
                wt_prunable_reason="${wt_prunable_reason# }"
                [ -z "$wt_prunable_reason" ] && wt_prunable_reason="gone"
                ;;
        esac
    done <<EOF
$(git -C "$primary" worktree list --porcelain)
EOF
    _reap_flush

    if [ "$execute" -eq 1 ] && [ "$need_prune" -eq 1 ]; then
        git -C "$primary" worktree prune -v
    fi

    echo ""
    echo "Summary: $removed to remove, $pruned to prune, $skipped skipped."
    if [ "$execute" -eq 0 ] && { [ "$removed" -gt 0 ] || [ "$pruned" -gt 0 ]; }; then
        echo "Dry-run — pass --execute to apply."
    fi
}

worktree_reap_help() {
    cat <<'EOF'
worktree-lib.sh reap — remove stale / orphaned git worktrees.

USAGE:
  worktree-lib.sh reap                  # dry-run (default): report only
  worktree-lib.sh reap --execute        # actually remove
  worktree-lib.sh reap --execute --force  # include dirty / unmerged

SAFETY:
  Never touches the primary checkout or the worktree it runs from. Never
  removes a dirty or unmerged worktree without --force. NEVER run while
  another agent is actively working in a worktree — --force discards
  uncommitted changes. Reap only at session start, after a landed branch is
  confirmed merged and its agent exited, or at loop end.
EOF
}

# --------------------------------------------------------------------------
# Dispatcher — only runs when the script is EXECUTED, not when sourced.
# --------------------------------------------------------------------------

worktree_lib_help() {
    cat <<'EOF'
worktree-lib.sh — portable, ecosystem-neutral worktree-lifecycle core.

USAGE:
  worktree-lib.sh detect             # print 'primary' or 'linked'
  worktree-lib.sh create <branch> [<base-ref>]
  worktree-lib.sh hydrate            # run the hydrate hook (no-op by default)
  worktree-lib.sh land [<base-ref>]  # rebase onto base, then report next step
  worktree-lib.sh reap [--execute] [--force]
  worktree-lib.sh help

The contract is mandated (isolated worktree, primary protected, land via
PR/merge, orphans reaped) and driven by `just` (the mandated runner): invoke
these verbs via `just worktree-create` / `worktree-hydrate` / `worktree-land`
/ `worktree-reap`, or a strict pass-through native wrapper onto them.
EOF
}

worktree_lib_main() {
    cmd="${1:-help}"
    shift || true
    case "$cmd" in
        detect)
            if worktree_is_primary; then echo "primary"; else echo "linked"; fi
            ;;
        create) worktree_create "$@" ;;
        hydrate) worktree_hydrate "$@" ;;
        land) worktree_land "$@" ;;
        reap) worktree_reap "$@" ;;
        help|-h|--help) worktree_lib_help ;;
        *)
            echo "worktree-lib.sh: unknown subcommand '$cmd' (see help)." >&2
            worktree_lib_help >&2
            return 2
            ;;
    esac
}

# `${BASH_SOURCE[0]}` differs from `$0` only when the file is sourced; when
# executed directly they are equal, so we dispatch. When sourced, the
# functions above are defined but no subcommand runs.
if [ "${BASH_SOURCE[0]:-$0}" = "$0" ]; then
    worktree_lib_main "$@"
fi
