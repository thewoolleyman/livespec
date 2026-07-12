#!/usr/bin/env bash
# Phase-0 provisioning pre-gate verification (design exit-tests 1,2,3,7 subset).
# Runs the ci-runner-context checks (tests 1-3) as-is, and drives a rootless
# podman container to assert test-7 properties. Re-runnable, read-only w.r.t.
# host state (only writes into a ci-runner-owned scratch dir it cleans up).
set -uo pipefail

CIRUN="ci-runner"
RUNAS=(sudo -n -u "$CIRUN" env HOME=/home/ci-runner XDG_RUNTIME_DIR=/run/user/1001)
IMG="docker.io/library/busybox:latest"
PASS=0 FAIL=0
ok(){ echo "  PASS: $1"; PASS=$((PASS+1)); }
no(){ echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

echo "===== TEST 1: ci-runner in NONE of docker/sudo/dolt, no sudoers ====="
groups_line="$(id -nG "$CIRUN")"
echo "  groups: $groups_line"
if echo " $groups_line " | grep -qE ' (docker|sudo|dolt) '; then no "ci-runner is in a forbidden group"; else ok "not in docker/sudo/dolt"; fi
if sudo -n grep -rqE "^\s*$CIRUN\b" /etc/sudoers /etc/sudoers.d/ 2>/dev/null; then no "ci-runner has a sudoers entry"; else ok "no sudoers entry"; fi

echo "===== TEST 2: ci-runner cannot read Kind-2 secret paths ====="
for p in /var/lib/doltdb /data/projects/1password-env-wrapper/.env.local; do
  if "${RUNAS[@]}" test -r "$p" 2>/dev/null; then no "ci-runner CAN read $p"; else ok "cannot read $p"; fi
done

echo "===== TEST 3: ci-runner sudo -n true fails ====="
if "${RUNAS[@]}" sudo -n true 2>/dev/null; then no "ci-runner sudo -n succeeded"; else ok "sudo -n denied"; fi

echo "===== TEST 7a: podman is rootless as ci-runner ====="
rl="$("${RUNAS[@]}" podman info --format '{{.Host.Security.Rootless}}' 2>/dev/null)"
[ "$rl" = "true" ] && ok "podman rootless=true" || no "podman rootless=$rl"

echo "===== TEST 7b: container-root maps to a host id that is NOT host uid 0 ====="
SCRATCH=/home/ci-runner/pregate-scratch
"${RUNAS[@]}" rm -rf "$SCRATCH" 2>/dev/null; "${RUNAS[@]}" mkdir -p "$SCRATCH"
"${RUNAS[@]}" podman run --rm -v "$SCRATCH:/out:Z" "$IMG" sh -c 'id -u > /out/inuid; touch /out/marker' >/dev/null 2>&1
inuid="$("${RUNAS[@]}" cat "$SCRATCH/inuid" 2>/dev/null)"
# host /home/ci-runner is 0750 ci-runner: stat as root to read inode owner
hostowner="$(sudo -n stat -c '%u' "$SCRATCH/marker" 2>/dev/null)"
echo "  in-container uid=$inuid ; host-side file owner uid=$hostowner"
if [ "$inuid" = "0" ] && [ -n "$hostowner" ] && [ "$hostowner" != "0" ]; then
  ok "container-root ($inuid) -> host uid $hostowner (NOT host root)"
else no "mapping wrong: inuid=$inuid hostowner=$hostowner"; fi
"${RUNAS[@]}" rm -rf "$SCRATCH" 2>/dev/null

echo "===== TEST 7c: even a hostile host-fs bind-mount cannot read Kind-2 (userns confines) ====="
# Mount the doltdb dir + 1password secret read-only; the container process (mapped
# to the unprivileged ci-runner host uid) must be denied by host DAC.
out="$("${RUNAS[@]}" podman run --rm \
  -v /var/lib/doltdb:/m/doltdb:ro \
  -v /data/projects/1password-env-wrapper/.env.local:/m/op.env:ro \
  "$IMG" sh -c 'cat /m/doltdb/* 2>&1 | head -1; cat /m/op.env 2>&1 | head -1' 2>&1)"
echo "  container read attempt output: $out"
if echo "$out" | grep -qiE 'permission denied|can.t open|No such'; then ok "hostile bind-mount reads denied by userns/DAC"; else no "hostile bind-mount may have read a secret: $out"; fi

echo "===== TEST 7d: --privileged does NOT yield host root (userns confinement) ====="
priv="$("${RUNAS[@]}" podman run --rm --privileged -v /var/lib/doltdb:/m:ro "$IMG" sh -c 'cat /m/* 2>&1 | head -1' 2>&1)"
echo "  --privileged read attempt: $priv"
if echo "$priv" | grep -qiE 'permission denied|can.t open|No such'; then ok "--privileged still confined (no host-root read)"; else no "--privileged read a host secret: $priv"; fi

echo "===== TEST 7e: AppArmor userns sysctls STILL =1 (host hardening intact) ====="
s1="$(sysctl -n kernel.apparmor_restrict_unprivileged_userns 2>/dev/null)"
s2="$(sysctl -n kernel.apparmor_restrict_unprivileged_unconfined 2>/dev/null)"
if [ "$s1" = "1" ] && [ "$s2" = "1" ]; then ok "both sysctls =1"; else no "sysctl downgraded: userns=$s1 unconfined=$s2"; fi

echo "===== TEST 7f: launch-path runtime binaries are NOT setuid-root ====="
setuid_hits="$(find /usr/bin/crun /usr/sbin/runc /usr/bin/bwrap /usr/bin/podman -perm -4000 2>/dev/null)"
if [ -z "$setuid_hits" ]; then ok "crun/runc/bwrap/podman not setuid-root"; else no "setuid runtime found: $setuid_hits"; fi

echo
echo "===== SUMMARY: $PASS passed, $FAIL failed ====="
[ "$FAIL" -eq 0 ]
