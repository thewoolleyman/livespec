#!/usr/bin/env bash
set -euo pipefail

# The gate Job checks out a temporary commit made from the staged tree. Rewind
# to its parent while retaining index and worktree state so the local aggregate
# sees exactly the staged tree that the committing host submitted.
gated_tree=$(git rev-parse 'HEAD^{tree}')
if [[ "$(git rev-list --parents -n 1 HEAD | wc -w)" -ne 2 ]]; then
    echo "FATAL: the gated staged-tree commit must have exactly one parent" >&2
    exit 1
fi
git reset --soft 'HEAD^'
if [[ "$(git write-tree)" != "$gated_tree" ]]; then
    echo "FATAL: rewinding changed the staged tree" >&2
    exit 1
fi

exec env LIVESPEC_GATE_CONTEXT=1 just check-pre-commit
