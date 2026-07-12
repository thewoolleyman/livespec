#!/usr/bin/env bash
# ci-runner-supervisor.sh — ephemeral self-hosted-runner supervisor for the
# thewoolleyman-ci-runners GitHub App. General fleet: maintains a small pool of
# ephemeral runners PER repo in CI_RUNNER_REPOS (personal accounts only support
# repo-level runners, so pools are per-repo).
#
# Runs as its OWN low-priv user (ci-sup), the only account that can read the App
# private key (from the github-ci-runners 1Password environment, injected ONLY
# into this service). Each cycle, per (repo, slot):
#   1. mint a fresh JIT config (no re-registerable token) via the App;
#   2. hand ONLY that JIT config to a freshly-launched ephemeral runner running
#      as ci-runner (via a narrow polkit-granted `systemctl start runner@<id>`);
#   3. wait for that runner unit to finish its single job (auto-deregisters);
#   4. relaunch the slot.
# The App key never crosses to ci-runner or the job container.
#
# Env (github-ci-runners 1Password environment, supervisor-only):
#   GITHUB_APP_ID_CI_RUNNER, GITHUB_APP_INSTALLATION_ID_CI_RUNNER,
#   GITHUB_PRIVATE_KEY_CI_RUNNER (real-newline PEM).
# Config: CI_RUNNER_REPOS (space-separated owner/repo), CI_RUNNER_SLOTS_PER_REPO,
#   CI_RUNNER_LABELS (default self-hosted,local-ci), CI_RUNNER_WORK.
set -euo pipefail

REPOS="${CI_RUNNER_REPOS:-thewoolleyman/livespec}"
SLOTS_PER_REPO="${CI_RUNNER_SLOTS_PER_REPO:-1}"
LABELS_CSV="${CI_RUNNER_LABELS:-self-hosted,local-ci}"
WORK_FOLDER="${CI_RUNNER_WORK:-/home/ci-runner/_work}"
MINT="${CI_RUNNER_MINT:-/usr/local/lib/ci-runner/mint-jitconfig.sh}"
JIT_DIR=/run/ci-runner                 # tmpfs, ci-runner-readable one-shot handoff

: "${GITHUB_APP_ID_CI_RUNNER:?}"; : "${GITHUB_APP_INSTALLATION_ID_CI_RUNNER:?}"
: "${GITHUB_PRIVATE_KEY_CI_RUNNER:?}"

# JSON array form of the labels for the JIT mint API.
labels_json="$(printf '%s' "$LABELS_CSV" | jq -R 'split(",")')"

run_one() {
  local repo="$1" slot="$2" name jit unit jf reposlug
  reposlug="${repo//\//-}"
  name="ci-${reposlug}-${slot}-$$-${RANDOM}"
  jit="$(APP_ID="$GITHUB_APP_ID_CI_RUNNER" \
        INSTALLATION_ID="$GITHUB_APP_INSTALLATION_ID_CI_RUNNER" \
        APP_KEY_PEM="$GITHUB_PRIVATE_KEY_CI_RUNNER" \
        REPO="$repo" RUNNER_NAME="$name" LABELS="$labels_json" WORK_FOLDER="$WORK_FOLDER" \
        "$MINT")"
  # JIT_DIR is the supervisor unit's RuntimeDirectory (0700 ci-sup). The runner
  # unit's LoadCredential= reads the file as root and stages it into the runner's
  # $CREDENTIALS_DIRECTORY (ci-runner-only) — so no cross-user chown is needed and
  # ci-runner never has raw access to the JIT file here.
  mkdir -p "$JIT_DIR"
  jf="$JIT_DIR/${name}.jit"
  ( umask 0177; printf '%s' "$jit" > "$jf" )
  unit="runner@${name}.service"
  systemctl start "$unit"                 # polkit-granted for runner@*.service only
  while systemctl is-active --quiet "$unit"; do sleep 5; done
  rm -f "$jf"
}

for repo in $REPOS; do
  for slot in $(seq 1 "$SLOTS_PER_REPO"); do
    ( while :; do run_one "$repo" "$slot" || sleep 10; done ) &
  done
done
wait
