#!/usr/bin/env bash
set -euo pipefail

# A 75 result requests the required local fallback; inspect that result without
# exiting before the case can distinguish it from a delegated refusal.
if [[ -z "${LIVESPEC_GATE_CONTEXT:-}" ]]; then
    set +e
    uv run python -m livespec_dev_tooling.pre_commit_delegate run
    delegate_status=$?
    set -e
    case "$delegate_status" in
        0)
            exit 0
            ;;
        75)
            ;;
        *)
            exit "$delegate_status"
            ;;
    esac
fi

exec just check-pre-commit-local
