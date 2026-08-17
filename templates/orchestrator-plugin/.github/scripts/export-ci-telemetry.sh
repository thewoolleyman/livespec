#!/usr/bin/env bash
# Export this CI run's per-job timings to Honeycomb as OTLP/HTTP-JSON spans,
# and FAIL the job if Honeycomb does not accept them.
#
# This is a CLOSED-LOOP self-verification, not an external monitor: a CI run
# deterministically knows its own telemetry should exist, so the run that
# produced the data confirms Honeycomb received it. If the ingest key is
# missing/revoked, the network is down, or the payload is rejected, this exits
# non-zero -> the job goes red -> the existing CI-failure notification fires.
# That makes a broken telemetry pipeline impossible to die silently.
#
# Wired to run on push(master)/merge_group only (never PRs), so it adds no
# latency to PR feedback. Emits one `ci.run` root span + one `ci.job.<name>`
# child per completed job. Span/trace ids are derived from the GitHub run/job
# integer ids (deterministic, unique, valid hex).
#
# Required environment:
#   REPO    - owner/name (e.g. thewoolleyman/<repo>)
#   RUN_ID  - this workflow run's id (github.run_id)
#   GH_TOKEN - gh auth token with actions:read (the workflow's GITHUB_TOKEN)
#   HONEYCOMB_GITHUB_CI_INGEST_KEY_LIVESPEC - write-only Honeycomb ingest key
set -euo pipefail

: "${REPO:?REPO required}"
: "${RUN_ID:?RUN_ID required}"
KEY="${HONEYCOMB_GITHUB_CI_INGEST_KEY_LIVESPEC:?HONEYCOMB_GITHUB_CI_INGEST_KEY_LIVESPEC required}"

DATASET="github-ci"            # OTLP service.name -> Honeycomb dataset
NAMESPACE="livespec-family"
ENDPOINT="https://api.honeycomb.io/v1/traces"
SCOPE_NAME="livespec.github-ci-export"
SCOPE_VERSION="1.0.0"

iso_to_nanos() { date -u -d "$1" +%s%N; }   # GNU date (ubuntu runners)
hex32() { printf '%032x' "$1"; }            # 16-byte trace id
hex16() { printf '%016x' "$1"; }            # 8-byte span id

run_json="$(gh run view "$RUN_ID" --repo "$REPO" \
  --json databaseId,headSha,headBranch,event,displayTitle,conclusion,createdAt,startedAt,updatedAt,jobs)"

trace_id="$(hex32 "$RUN_ID")"
run_span_id="$(hex16 "$RUN_ID")"
run_start="$(iso_to_nanos "$(jq -r '.startedAt // .createdAt' <<<"$run_json")")"
run_end="$(iso_to_nanos "$(jq -r '.updatedAt' <<<"$run_json")")"
run_concl="$(jq -r '.conclusion // ""' <<<"$run_json")"
run_code=2; [ "$run_concl" = "success" ] && run_code=1

# `$run_json` carries the whole `jobs` array and MUST reach jq on stdin, never
# as a `--argjson` value. Passing it on argv died with "jq: Argument list too
# long" (E2BIG, exit 126) on runs 30052264761 and 30052356388, reddening master
# and with it every dark-factory dispatch gated on `check-master-ci-green`.
#
# The exact runner-side threshold was NOT reproducible off-runner: the failing
# payload is ~84 KB (63 jobs) against a ~83 KB green run (62 jobs), both far
# under MAX_ARG_STRLEN, and the same call succeeds locally on the exact failing
# payload — so step env size or a runner-image change is likely also in play.
# What is certain is that this value grows without bound as the job count grows
# and it is the only such argv entry here. stdin has no argv limit, so routing
# it there removes the whole class rather than moving the threshold.
run_span="$(jq -c \
  --arg trace "$trace_id" --arg span "$run_span_id" \
  --arg start "$run_start" --arg end "$run_end" \
  --arg repo "$REPO" --argjson run_id "$RUN_ID" --argjson code "$run_code" '
  {traceId:$trace, spanId:$span, name:"ci.run", kind:1,
   startTimeUnixNano:$start, endTimeUnixNano:$end,
   attributes:[
     {key:"repo",value:{stringValue:$repo}},
     {key:"ci.run_id",value:{intValue:($run_id|tostring)}},
     {key:"ci.conclusion",value:{stringValue:(.conclusion // "")}},
     {key:"ci.title",value:{stringValue:(.displayTitle // "")}},
     {key:"git.commit.sha",value:{stringValue:(.headSha // "")}},
     {key:"git.branch",value:{stringValue:(.headBranch // "")}},
     {key:"ci.event",value:{stringValue:(.event // "")}}
   ],
   status:{code:$code}}' <<<"$run_json")"

job_spans="[]"
while IFS=$'\t' read -r jid jname jconcl jstart_iso jend_iso; do
  [ -n "$jstart_iso" ] && [ "$jstart_iso" != "null" ] || continue
  [ -n "$jend_iso" ] && [ "$jend_iso" != "null" ] || continue
  jspan_id="$(hex16 "$jid")"
  jstart="$(iso_to_nanos "$jstart_iso")"
  jend="$(iso_to_nanos "$jend_iso")"
  jcode=2; [ "$jconcl" = "success" ] && jcode=1
  span="$(jq -nc \
    --arg trace "$trace_id" --arg span "$jspan_id" --arg parent "$run_span_id" \
    --arg name "ci.job.$jname" --arg start "$jstart" --arg end "$jend" \
    --arg repo "$REPO" --argjson run_id "$RUN_ID" \
    --arg jname "$jname" --arg jconcl "$jconcl" --argjson code "$jcode" '
    {traceId:$trace, spanId:$span, parentSpanId:$parent, name:$name, kind:1,
     startTimeUnixNano:$start, endTimeUnixNano:$end,
     attributes:[
       {key:"repo",value:{stringValue:$repo}},
       {key:"ci.run_id",value:{intValue:($run_id|tostring)}},
       {key:"ci.job.name",value:{stringValue:$jname}},
       {key:"ci.job.conclusion",value:{stringValue:$jconcl}}
     ],
     status:{code:$code}}')"
  job_spans="$(jq -c ". + [$span]" <<<"$job_spans")"
done < <(jq -r '.jobs[] | [.databaseId, .name, (.conclusion // ""), (.startedAt // ""), (.completedAt // "")] | @tsv' <<<"$run_json")

# Same argv-limit class as the run span above: `$job_spans` grows with the job
# count, so it goes on stdin. `$run_span` stays a `--argjson` value because it
# is a single fixed-shape span (seven attributes) and cannot grow with the run.
payload_file="$(mktemp)"
jq -c \
  --argjson run "$run_span" \
  --arg svc "$DATASET" --arg ns "$NAMESPACE" \
  --arg scope "$SCOPE_NAME" --arg ver "$SCOPE_VERSION" '
  {resourceSpans:[{
     resource:{attributes:[
       {key:"service.name",value:{stringValue:$svc}},
       {key:"service.namespace",value:{stringValue:$ns}}
     ]},
     scopeSpans:[{
       scope:{name:$scope, version:$ver},
       spans:([$run] + .)
     }]
   }]}' <<<"$job_spans" > "$payload_file"

span_count="$(jq '.resourceSpans[0].scopeSpans[0].spans | length' "$payload_file")"
resp_file="$(mktemp)"
http="$(curl -sS -o "$resp_file" -w '%{http_code}' "$ENDPOINT" \
  -H "x-honeycomb-team: $KEY" -H "Content-Type: application/json" \
  --data-binary @"$payload_file" || echo 000)"
rejected="$(jq -r '.partialSuccess.rejectedSpans // 0' "$resp_file" 2>/dev/null || echo unknown)"

echo "Honeycomb ingest: HTTP=$http spans=$span_count rejected=$rejected dataset=$DATASET trace=$trace_id"
if [ "$http" != "200" ] || [ "$rejected" != "0" ]; then
  echo "::error::CI telemetry export to Honeycomb FAILED (HTTP=$http rejected=$rejected). The telemetry pipeline is broken; fix it rather than ignore this." >&2
  echo "--- Honeycomb response ---" >&2
  cat "$resp_file" >&2 || true
  exit 1
fi
echo "CI telemetry exported and confirmed received by Honeycomb ($span_count spans, trace $trace_id)."
