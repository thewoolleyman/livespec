#!/usr/bin/env bash
# mint-jitconfig.sh — mint a just-in-time (JIT) config for ONE ephemeral runner,
# using a GitHub App installation token. No re-registerable registration token is
# ever created; the JIT config authorizes exactly one runner for one job.
#
# Runs as the SUPERVISOR user (which alone can read the App private key). Prints
# the base64 encoded_jit_config to stdout — the ONLY thing handed to the runner.
# The App key never leaves this process; nothing is echoed but the JIT config.
#
# Phase 0 supervisor (plan/fabro-ci-image-factoring/phase0-runner-containment-design.md).
# Deps: openssl, curl, jq (all host-present). Requires: APP_ID, INSTALLATION_ID,
# APP_KEY (pem path), REPO (owner/repo), RUNNER_NAME, LABELS (JSON array), WORK_FOLDER.
set -euo pipefail

: "${APP_ID:?}"; : "${INSTALLATION_ID:?}"; : "${REPO:?}"
: "${RUNNER_NAME:?}"; : "${LABELS:?}"; : "${WORK_FOLDER:?}"

# Key source: APP_KEY (a PEM file path) OR APP_KEY_PEM (the PEM content, real
# newlines — e.g. GITHUB_PRIVATE_KEY_CI_RUNNER injected from 1Password). When the
# content form is used, write it to a private temp file and clean it up on exit.
_tmpkey=""
cleanup() { [ -n "$_tmpkey" ] && rm -f "$_tmpkey"; return 0; }  # never poison exit code
trap cleanup EXIT
if [ -z "${APP_KEY:-}" ] && [ -n "${APP_KEY_PEM:-}" ]; then
  _tmpkey="$(mktemp)"; chmod 600 "$_tmpkey"
  printf '%s' "$APP_KEY_PEM" > "$_tmpkey"
  APP_KEY="$_tmpkey"
fi
: "${APP_KEY:?APP_KEY (file) or APP_KEY_PEM (content) required}"
[ -r "$APP_KEY" ] || { echo "mint: cannot read App key $APP_KEY" >&2; exit 1; }

b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }

# --- App JWT (RS256, 9-minute window, 60s clock-skew allowance) ---
now=$(date +%s); iat=$((now - 60)); exp=$((now + 540))
header='{"alg":"RS256","typ":"JWT"}'
payload="{\"iat\":${iat},\"exp\":${exp},\"iss\":\"${APP_ID}\"}"
unsigned="$(printf '%s' "$header" | b64url).$(printf '%s' "$payload" | b64url)"
sig="$(printf '%s' "$unsigned" | openssl dgst -sha256 -sign "$APP_KEY" -binary | b64url)"
jwt="${unsigned}.${sig}"

# --- installation access token (short-lived, ~1h; used once here) ---
# Separate curl from jq (no pipefail edge) and parse the field rather than
# relying on curl's exit status for HTTP handling.
inst_resp="$(curl -sS -X POST \
  -H "Authorization: Bearer ${jwt}" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/app/installations/${INSTALLATION_ID}/access_tokens")"
inst_tok="$(printf '%s' "$inst_resp" | jq -r '.token // empty')"
[ -n "$inst_tok" ] || { echo "mint: no installation token: $(printf '%s' "$inst_resp" | jq -r '.message // "unknown"')" >&2; exit 1; }

# --- JIT config for exactly one ephemeral runner ---
payload="$(jq -nc --arg n "$RUNNER_NAME" --argjson l "$LABELS" --arg w "$WORK_FOLDER" \
  '{name:$n, runner_group_id:1, labels:$l, work_folder:$w}')"
jit_resp="$(curl -sS -X POST \
  -H "Authorization: token ${inst_tok}" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/${REPO}/actions/runners/generate-jitconfig" -d "$payload")"
jit="$(printf '%s' "$jit_resp" | jq -r '.encoded_jit_config // empty')"
[ -n "$jit" ] || { echo "mint: generate-jitconfig failed: $(printf '%s' "$jit_resp" | jq -r '.message // "unknown"')" >&2; exit 1; }

printf '%s' "$jit"
