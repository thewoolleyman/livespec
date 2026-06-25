#!/usr/bin/env bash
# worktree-hydrate.sh — overridable per-repo worktree hydration hook.
#
# Generated from livespec/templates/impl-plugin/dev-tooling/worktree-hydrate.sh
# at copier-copy time; re-sync via `copier update --vcs-ref=master` when
# livespec publishes a new release.
#
# "Hydrate" means: prepare a freshly-created worktree so the repo's checks and
# tooling can run inside it. What that entails is ECOSYSTEM-SPECIFIC — there
# is no neutral default that fits Python, Rust, JS, and everything else — so
# the portable core (dev-tooling/worktree-lib.sh) delegates hydration here and
# this shipped stub DEFAULTS TO A NO-OP.
#
# This is intentional. The worktree-lifecycle CORE and the commit-refuse gate
# are pure-git and ecosystem-neutral; only hydration varies by ecosystem. A
# consuming repo teaches this repo its hydration by either:
#   - replacing this script's body with the repo's ecosystem-correct steps
#     (e.g. `uv sync` for Python, `pnpm install` for JS, warming a shared
#     cargo build cache for Rust), or
#   - exporting WORKTREE_HYDRATE_HOOK="<command>" so worktree-lib.sh runs that
#     instead of this file.
#
# (A future livespec release adds per-ecosystem hydrate profiles selected at
# scaffold time; until then this stub keeps `create` working everywhere by
# doing nothing.)
#
# Idempotent and safe to run from anywhere: worktree-lib.sh only invokes this
# from inside a linked worktree, and it must remain re-runnable.

set -euo pipefail

echo "worktree-hydrate: no-op (default stub)."
echo "  Replace dev-tooling/worktree-hydrate.sh with this repo's"
echo "  ecosystem-correct hydration, or set WORKTREE_HYDRATE_HOOK."
exit 0
