#!/usr/bin/env bash
# run-jit-runner.sh — ExecStart for runner@.service. Reads the one-shot JIT config
# that systemd staged via LoadCredential (ci-runner-only $CREDENTIALS_DIRECTORY)
# and execs the runner for a single ephemeral job. The JIT config never lands in a
# path the job container can reach (the sanitize-hook mounts only _work).
set -euo pipefail
jit="$(cat "${CREDENTIALS_DIRECTORY}/jit")"
exec /home/ci-runner/actions-runner/run.sh --jitconfig "$jit"
