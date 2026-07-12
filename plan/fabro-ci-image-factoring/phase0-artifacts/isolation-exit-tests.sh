#!/usr/bin/env bash
# isolation-exit-tests.sh — Phase 0 runner containment exit criteria (the 11
# isolation tests from plan/fabro-ci-image-factoring/phase0-runner-containment-
# design.md), runnable + re-runnable against the live host. Exit 0 iff every
# non-skipped test passes. Read-only w.r.t. host state (throwaway containers only).
#
# Validated live 2026-07-12. Durable home: livespec-dev-tooling.
set -uo pipefail
RU=ci-runner
XDG=/run/user/$(id -u "$RU" 2>/dev/null || echo 1001)
POD=(sudo -n -u "$RU" env HOME=/home/$RU XDG_RUNTIME_DIR="$XDG" podman)
IMG=ghcr.io/thewoolleyman/livespec-fabro-sandbox:v0.38.1
KIND2=(/var/lib/doltdb /data/projects/1password-env-wrapper/.env.local)
WF=${1:-/data/projects/livespec/.github/workflows}   # workflows dir for static audit
P=0 F=0 S=0
pass(){ echo "  PASS $1"; P=$((P+1)); }
fail(){ echo "  FAIL $1"; F=$((F+1)); }
skip(){ echo "  SKIP $1"; S=$((S+1)); }

echo "== T1: ci-runner in NONE of docker/sudo/dolt, no sudoers =="
g=$(id -nG "$RU"); echo "  groups: $g"
echo " $g " | grep -qE ' (docker|sudo|dolt) ' && fail "forbidden group" || pass "not in docker/sudo/dolt"
sudo -n grep -rqE "^\s*$RU\b" /etc/sudoers /etc/sudoers.d/ 2>/dev/null && fail "sudoers entry" || pass "no sudoers entry"

echo "== T2: ci-runner cannot read Kind-2 secret paths =="
for p in "${KIND2[@]}"; do sudo -n -u "$RU" test -r "$p" 2>/dev/null && fail "can read $p" || pass "cannot read $p"; done

echo "== T3: ci-runner sudo -n fails =="
sudo -n -u "$RU" sudo -n true 2>/dev/null && fail "sudo succeeded" || pass "sudo denied"

echo "== T4: job container has NO docker.sock (sanitizer strips it) =="
"${POD[@]}" run --rm "$IMG" test -S /var/run/docker.sock 2>/dev/null && fail "docker.sock present" || pass "no docker.sock in container"

echo "== T5: no Kind-2 secret in a container env; SKIP full live-job env check =="
skip "T5 needs a live moved job (verify printenv shows no App key/JIT/1P/Dolt pw; GITHUB_TOKEN read-scoped)"

echo "== T6: honest fork PR routes to ubuntu-latest =="
skip "T6 external — honest fork PR must not trigger a self-hosted job (manual/CI check)"

echo "== T7: rootless; container-root != host root; sysctls =1; runtime not setuid =="
rl=$("${POD[@]}" info --format '{{.Host.Security.Rootless}}' 2>/dev/null); [ "$rl" = true ] && pass "podman rootless" || fail "rootless=$rl"
SC=/home/$RU/.exittest; "${POD[@]}" run --rm -v "$SC:/o:Z" "$IMG" sh -c 'touch /o/m' 2>/dev/null
ho=$(sudo -n stat -c '%u' "$SC/m" 2>/dev/null); sudo -n rm -rf "$SC" 2>/dev/null
[ -n "$ho" ] && [ "$ho" != 0 ] && pass "container-root -> host uid $ho (not root)" || fail "mapping ho=$ho"
s1=$(sysctl -n kernel.apparmor_restrict_unprivileged_userns); s2=$(sysctl -n kernel.apparmor_restrict_unprivileged_unconfined)
[ "$s1" = 1 ] && [ "$s2" = 1 ] && pass "sysctls =1" || fail "sysctls $s1/$s2"
[ -z "$(find /usr/bin/crun /usr/sbin/runc /usr/bin/bwrap /usr/bin/podman -perm -4000 2>/dev/null)" ] && pass "no setuid runtime" || fail "setuid runtime"

echo "== T8: no host-loopback route by any path; internet OK (dynamic enumeration) =="
# dynamic loopback listener set
mapfile -t LISTEN < <(ss -tlnH 2>/dev/null | awk '{print $4}' | grep -oE '(127\.[0-9.]+|\[::1\]):[0-9]+' | sed -E 's/\[::1\]/::1/' )
"${POD[@]}" run --rm "$IMG" bash -c '
f=0
deny(){ timeout 3 bash -c "exec 3<>/dev/tcp/$1/$2" 2>/dev/null && { echo "REACH $1:$2"; f=1; } || true; }
for hp in 127.0.0.1:3307 host.containers.internal:3307 169.254.169.254:80 '"${LISTEN[*]}"'; do deny "${hp%:*}" "${hp##*:}"; done
timeout 6 bash -c "exec 3<>/dev/tcp/1.1.1.1/443" 2>/dev/null || echo "NO-INTERNET"
exit $f' 2>/dev/null && pass "all host-loopback denied" || fail "a host-loopback route reachable"

echo "== T9: static workflow audit — no self-hosted job on a forbidden trigger =="
bad=0
for wf in "$WF"/*.yml "$WF"/*.yaml; do
  [ -f "$wf" ] || continue
  if grep -qE 'self-hosted' "$wf" && grep -qE 'pull_request_target|workflow_run|issue_comment|repository_dispatch|merge_group' "$wf"; then
    echo "  suspect: $wf"; bad=1
  fi
done
[ "$bad" = 0 ] && pass "no self-hosted job reachable from a forbidden trigger" || fail "self-hosted job on forbidden trigger"

echo "== T10: cache write-denial (supervisor-classified) =="
skip "T10 needs the supervisor event-classifier + writable/RO cache mounts (PR lane RO)"

echo "== T11: runner-agent material unreachable from a job (PID/user ns) =="
# job container is private PID ns: cannot see an arbitrary host PID
HPID=$$   # a host PID guaranteed to exist
"${POD[@]}" run --rm -e HPID="$HPID" "$IMG" bash -c '
[ -e "/proc/$HPID" ] && { echo "host PID visible"; exit 1; }
find / -xdev -maxdepth 6 \( -name .credentials -o -name .jitconfig -o -name .runner \) 2>/dev/null | grep -q . && exit 1
exit 0' 2>/dev/null && pass "agent PID ns-isolated; no runner creds in job fs" || fail "agent/job separation breach"

echo
echo "== SUMMARY: $P pass, $F fail, $S skip =="
[ "$F" -eq 0 ]
