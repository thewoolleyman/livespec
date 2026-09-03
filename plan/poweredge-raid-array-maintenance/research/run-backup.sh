#!/usr/bin/env bash
#
# run-backup.sh — back up poweredge-xubuntu to the USB volume.
#
#   sudo /mnt/usb-backup/run-backup.sh 2>&1 | tee /mnt/usb-backup/rsync.log
#   tail -f /mnt/usb-backup/rsync.log
#
# Exits 0 only if EVERY pass succeeded. Any real failure exits non-zero and is
# named in the summary. Do not judge success by eyeballing the log.
#
# ---------------------------------------------------------------------------
# EXIT-CODE POLICY — this is the bug this script was rewritten to fix.
#
# An earlier version classified rsync's exit 23 as "tolerated". That was WRONG
# and it silently accepted an incomplete backup.
#
#   0  success.
#   24 "some files vanished before they could be transferred" — the file was
#      deleted between rsync's scan and its copy. Benign on a live system, and
#      the files in question no longer exist to be backed up. WARN.
#   23 "some files/attrs were NOT transferred" — rsync tried and FAILED.
#      The backup is INCOMPLETE. This is an ERROR, never tolerated.
#
# Anything other than 0 or 24 is an error.
# ---------------------------------------------------------------------------
#
# No `set -e`. Per BashFAQ/105 it is unreliable for this shape of script — it
# would abort on the first non-zero rc and skip the remaining passes, which is
# precisely how an earlier run lost two of its three passes without saying so.
# Exit status is checked explicitly instead. `pipefail` is set so that any
# pipeline added later cannot mask a failure.
set -uo pipefail

readonly DEST=/mnt/usb-backup
declare -i failures=0
declare -a summary=()

log() { printf '%s %s\n' "$(date -u '+%H:%M:%SZ')" "$*"; }
die() { printf 'FATAL: %s\n' "$*" >&2; exit 2; }

[[ $EUID -eq 0 ]]        || die "must run as root (needs to read all files and preserve ownership)"
mountpoint -q "$DEST"    || die "$DEST is not mounted — refusing to write into the underlying directory"

# Refuse to run concurrently with another copy of itself. An ssh-launched job
# survives the client being interrupted, so a careless relaunch can put two
# `rsync --delete` runs on one destination. `pgrep -x rsync` matches the
# executable name only, so it cannot match this script's own command line.
if pgrep -x rsync >/dev/null; then
    die "an rsync is already running — refusing to start a second writer against $DEST"
fi

# Shared options. An array, so no word-splitting surprises.
#   -a archive  -H hardlinks (containerd's overlay store depends on them)
#   -A ACLs     -X xattrs (overlayfs + security contexts)  -S sparse
#   --numeric-ids  never remap uid/gid via name lookup — essential when
#                  restoring onto a fresh install
#   --one-file-system  never cross a mount boundary, so a stray mount (or this
#                  USB drive) is never swept in
#   --delete-excluded  ALSO delete excluded paths from the destination. Without
#                  it, --delete alone will not touch anything matching an
#                  --exclude, so a path that USED to be backed up and is now
#                  excluded stays stranded on the destination forever. That is
#                  how ~13G of dead PVC scratch and rollback copies accumulated
#                  here. rsync protects excluded paths from deletion by design;
#                  this opts out of that protection.
readonly -a RSYNC_OPTS=(
    -aHAXS
    --numeric-ids
    --delete
    --delete-excluded
    --info=progress2
    --one-file-system
)

# Volatile paths, excluded because backing them up is both futile and the cause
# of spurious failures:
#   k3s-storage  — local-path PVC scratch. A running CI job creates thousands of
#                  files here and deletes the whole tree when it finishes; it is
#                  4K at idle. Racing it produced the rc=23 that motivated this
#                  rewrite. Nothing here survives a job, so nothing is lost.
#   *.premove    — the rollback copies from the containerd relocation. They
#                  duplicate data already captured under var-cache-ci-runner.
#   /var/log/pods— transient per-pod logs, rotated away mid-copy.
readonly -a EXCLUDE_COMMON=( --exclude='lost+found' )
readonly -a EXCLUDE_ROOT=(
    --exclude='/swap.img'
    --exclude='/var/log/pods/***'
    --exclude='/var/lib/rancher/k3s/agent/containerd.premove/***'
    --exclude='/var/lib/rancher/k3s/storage.premove/***'
)
readonly -a EXCLUDE_CACHE=( --exclude='/k3s-storage/***' )

# run_pass <label> <rsync args...>
# Runs rsync directly — NOT through a pipe — so $? is rsync's own status and
# cannot be masked by a downstream command in a pipeline.
run_pass() {
    local -r label=$1
    shift
    log "=== ${label} ==="
    rsync "$@"
    local -i rc=$?
    case $rc in
        0)
            log "    ${label}: OK (rc=0)"
            summary+=("OK      ${label}")
            ;;
        24)
            log "    ${label}: OK with warning (rc=24 — files vanished mid-copy; they no longer exist to back up)"
            summary+=("WARN    ${label} (rc=24 vanished)")
            ;;
        *)
            log "    ${label}: FAILED (rc=${rc}) — backup is INCOMPLETE"
            summary+=("FAILED  ${label} (rc=${rc})")
            failures+=1
            ;;
    esac
    return 0
}

mkdir -p "$DEST"/{rootfs,boot-efi,var-cache-ci-runner,meta} || die "cannot create destination directories"

log "backup starting -> $DEST"

# Metadata first: a restore needs the map even if the data copy is interrupted.
{
    lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,UUID,MOUNTPOINT > "$DEST/meta/lsblk.txt"
    blkid                                                > "$DEST/meta/blkid.txt"
    cp -a /etc/fstab                                       "$DEST/meta/fstab.txt"
    sfdisk -d /dev/sda                                   > "$DEST/meta/sda-parttable.sfdisk"
    dpkg --get-selections                                > "$DEST/meta/dpkg-selections.txt"
    uname -a                                             > "$DEST/meta/uname.txt"
    systemctl list-unit-files --state=enabled --no-pager > "$DEST/meta/enabled-units.txt"
    k3s --version                                        > "$DEST/meta/k3s-version.txt"
} 2>/dev/null
log "metadata captured"

run_pass "1/3 rootfs" \
    "${RSYNC_OPTS[@]}" "${EXCLUDE_COMMON[@]}" "${EXCLUDE_ROOT[@]}" \
    / "$DEST/rootfs/"

# vfat carries no ownership/perms/xattrs, so the full flag set is meaningless
# here; the ESP is regenerated by grub-install at restore anyway.
run_pass "2/3 boot/efi" \
    -rltD --delete --delete-excluded --info=progress2 \
    /boot/efi/ "$DEST/boot-efi/"

run_pass "3/3 var/cache/ci-runner" \
    "${RSYNC_OPTS[@]}" "${EXCLUDE_COMMON[@]}" "${EXCLUDE_CACHE[@]}" \
    /var/cache/ci-runner/ "$DEST/var-cache-ci-runner/"

sync

printf '\n=== SUMMARY ===\n'
printf '  %s\n' "${summary[@]}"
if (( failures > 0 )); then
    printf '\n*** BACKUP FAILED: %d pass(es) did not complete. The backup is NOT usable. ***\n' "$failures"
    exit 1
fi
printf '\n=== BACKUP COMPLETE — all passes succeeded ===\n'
exit 0
