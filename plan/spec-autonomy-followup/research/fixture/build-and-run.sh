#!/usr/bin/env bash
# Rebuild the spec-autonomy-followup proof fixture and run its four probes.
# Usage: build-and-run.sh <empty-scratch-dir>
# Plan spec-autonomy-followup (thewoolleyman/livespec, epic livespec-7ap2fb), research note 004.
# The fixture is throwaway: it lives outside /data/projects and is never registered anywhere.
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
OUT="$(cd "$1" && pwd)"; F="$OUT/fixture"; FC="$OUT/fixture-cli"
mkdir -p "$F"; cd "$F"
git init -q -b master
git config user.name "fixture"; git config user.email "fixture@invalid"
cp "$KIT/livespec.jsonc" .livespec.jsonc
mkdir -p .claude; cp "$KIT/claude-settings.json" .claude/settings.json
echo "tmp/" > .gitignore

# Install the RELEASED core and Claude Driver at project scope (ref: release).
claude plugin marketplace update livespec
claude plugin marketplace update livespec-driver-claude
claude plugin install livespec@livespec -s project
claude plugin install livespec@livespec-driver-claude -s project
CORE="$(python3 - "$F" <<'EOF'
import json, sys
d = json.load(open("/home/ubuntu/.claude/plugins/installed_plugins.json"))
for e in d["plugins"]["livespec@livespec"]:
    if e.get("projectPath") == sys.argv[1]:
        print(e["installPath"], e.get("version"), e.get("gitCommitSha", "")[:8], file=sys.stderr)
        print(e["installPath"])
EOF
)"
echo "installed core: $CORE"

# Seed with the installed core, then add the three proposals.
python3 "$CORE/scripts/bin/seed.py" --seed-json "$KIT/seed.json" --project-root "$F"
cp "$KIT"/proposals/*.md SPECIFICATION/proposed_changes/
snap() { git -C "$F" add -A; git -C "$F" -c core.hooksPath=/dev/null commit -q -m "$1" || true; }
versions() { for d in "$1"/SPECIFICATION/history/v*; do [ -d "$d" ] && printf '%s ' "${d##*/}"; done; }
snap "fixture: seed + proposals A, B, C"
git clone -q "$F" "$FC"; cp "$F/.livespec.jsonc" "$FC/"

run() {  # $1 label, $2 topic: one bounded, explicitly started, headless revise
  ( cd "$F" && env -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_CHILD_SESSION -u CLAUDE_CODE_SESSION_ATTENDED -u CLAUDECODE \
      timeout 1800 claude -p "/livespec:revise --only-topic $2" --permission-mode bypassPermissions \
      --output-format stream-json --verbose > "$OUT/run-$1.jsonl" 2> "$OUT/run-$1.err" ) || true
  echo "== after run $1: history = $(versions "$F")"
  rm -rf "$F"/tmp/revise-*
  snap "after run $1"
}
run A greeting-trailing-period
run B unknown-name-wording
run C latency-matches-implementation

# Probe D: the released revise CLI must refuse a drift-origin decision that carries
# complete, digest-exact delegated evidence but no human confirmation.
python3 - "$CORE/scripts" "$FC" "$OUT/drift.json" <<'EOF'
import sys, json, datetime
C, FC, OUTP = sys.argv[1:4]
sys.path.insert(0, C); sys.path.insert(0, C + "/bin")
from _bootstrap import bootstrap; bootstrap()
from livespec.commands._revise_ratification import _canonical_ratification_digest
topic = "latency-matches-implementation"
nfr = open(FC + "/SPECIFICATION/non-functional-requirements.md").read().replace("within one second", "within two seconds")
prop = open(FC + f"/SPECIFICATION/proposed_changes/{topic}.md", "rb").read()
dec = {"proposal_topic": topic, "decision": "accept", "rationale": "CLI-floor probe.",
       "ratification_review": "manual-spawn", "resulting_files": [{"path": "non-functional-requirements.md", "content": nfr}]}
dig = _canonical_ratification_digest(decision=dec, proposal_bytes=prop)
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
dec["ratification_evidence"] = {"reviewer_identity": "sonnet", "reviewer_model": "sonnet", "separate_reviewer": True, "read_only": True,
    "reviewed_at": now, "verdict": "NO BLOCKERS", "proposal_stem": topic, "content_digest": dig}
dec["revise_decision_context"] = {"design_record_contradiction": False, "design_record_unavailable": False, "ratification_blocker": False, "drift_origin": True}
dec["delegated_decision_evidence"] = {"decider_identity": "probe", "decider_model": "probe", "proposal_stem": topic,
    "content_digest": dig, "selected_decision": "accept", "accepted": True}
json.dump({"author": "probe", "decisions": [dec]}, open(OUTP, "w"))
EOF
set +e
( cd "$FC" && python3 "$CORE/scripts/bin/revise.py" --revise-json "$OUT/drift.json" --only-topic latency-matches-implementation \
    --project-root "$FC" --skip-stale-branch-check ) > "$OUT/drift-cli.out" 2>&1
code=$?
echo "== probe D exit=$code ; $(grep -m1 'human decision input required' "$OUT/drift-cli.out")"
echo "== probe D history = $(versions "$FC")"
