#!/usr/bin/env bash
# worktree-adapter.sh — runner-neutral thin adapter onto the worktree core.
#
# Generated from livespec/templates/impl-plugin/dev-tooling/worktree-adapter.sh
# at copier-copy time; re-sync via `copier update --vcs-ref=master` when
# livespec publishes a new release.
#
# WHAT THIS IS
# ============
# A THIN, logic-free passthrough that maps the four worktree-discipline verbs
# (create / hydrate / land / reap) onto the portable, ecosystem-neutral core
# (dev-tooling/worktree-lib.sh). It carries NO logic of its own — the core is
# the single source of truth for the lifecycle and the primary-vs-linked
# detection. This file exists so a repo whose task runner is NOT `just` still
# has one canonical, runner-agnostic entry point to wire into whatever runner
# it uses.
#
# livespec mandates the worktree CONTRACT, never a specific runner. `just` is
# ONE reference adapter (see the `worktree-*` recipes in justfile.jinja); this
# script is the runner-neutral equivalent. Wire it into your repo's runner so
# the four verbs are reachable the way your repo already invokes tasks:
#
#   - cargo / xtask:   add an xtask subcommand that execs this script, e.g.
#                        `cargo xtask worktree create <branch>` →
#                        `dev-tooling/worktree-adapter.sh create <branch>`
#   - pnpm / npm / yarn (package.json "scripts"):
#                        "wt:create": "dev-tooling/worktree-adapter.sh create",
#                        "wt:hydrate": "dev-tooling/worktree-adapter.sh hydrate",
#                        "wt:land":   "dev-tooling/worktree-adapter.sh land",
#                        "wt:reap":   "dev-tooling/worktree-adapter.sh reap"
#                      then `pnpm wt:create <branch>`.
#   - make:            wt-create: ; @dev-tooling/worktree-adapter.sh create $(b)
#   - taskfile / raw:  call this script directly.
#
# Because the adapter is logic-free and the core is shared, no ecosystem can
# drift in lifecycle behavior; `copier update` + the copier-update-drift
# workflow surface any divergence from the published core.
#
# USAGE (identical verbs to worktree-lib.sh):
#   ./dev-tooling/worktree-adapter.sh create <branch> [<base-ref>]
#   ./dev-tooling/worktree-adapter.sh hydrate
#   ./dev-tooling/worktree-adapter.sh land [<base-ref>]
#   ./dev-tooling/worktree-adapter.sh reap [--execute] [--force]
#   ./dev-tooling/worktree-adapter.sh detect

set -euo pipefail

# Resolve the core relative to THIS script so the adapter works regardless of
# the caller's cwd (a runner may invoke it from a sub-package directory).
adapter_dir="$(cd "$(dirname "$0")" && pwd -P)"
core="$adapter_dir/worktree-lib.sh"

if [ ! -x "$core" ] && [ ! -f "$core" ]; then
    echo "worktree-adapter: BLOCKED — portable core not found at $core" >&2
    echo "  The adapter is a logic-free passthrough; it requires worktree-lib.sh." >&2
    exit 1
fi

# Pure passthrough — every verb and flag is the core's. No logic here by
# design (logic lives in the core, the single source of truth).
if [ -x "$core" ]; then
    exec "$core" "$@"
else
    exec sh "$core" "$@"
fi
