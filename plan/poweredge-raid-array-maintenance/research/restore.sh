#!/usr/bin/env bash
# restore.sh — restore poweredge-xubuntu onto a freshly-installed system.
#
#   sudo /mnt/usb-backup/restore.sh /target
#
# where /target is the mounted root of the NEW install. That is the whole
# interface: one command, one argument.
#
# WHAT THIS DOES
#   1. Refuses obviously-wrong targets (see SAFETY).
#   2. rsyncs the captured rootfs over the target, preserving hardlinks, ACLs,
#      xattrs and numeric ownership.
#   3. Regenerates /etc/fstab: rewrites the root and ESP entries to the NEW
#      disk's real UUIDs, PRESERVES every other captured entry (swap, the
#      /var/cache/ci-runner volume, the containerd/PVC bind mounts), and marks
#      any volume whose captured UUID no longer resolves `nofail` so a missing
#      device cannot wedge the boot — printing a loud remap list for the human.
#   4. Reinstalls and re-configures the bootloader inside a chroot — UNLESS the
#      bootloader step is skipped (SKIP_BOOTLOADER=1) or no ESP safe to touch is
#      available (see BOOTLOADER SAFETY).
#
# WHAT THIS DOES NOT DO
#   It does not partition anything. Create and mount your target filesystems
#   first — this script only fills them. That separation is deliberate: an
#   auto-partitioning restore script is one typo away from destroying the wrong
#   disk.
#
# SAFETY. This script REFUSES to run when the target looks wrong: not a
# directory, not a mountpoint, the live root itself, or already holding a
# running system. Those checks are not paranoia — a restore is run under
# pressure, often at 3am, and the failure mode is unrecoverable.
#
# BOOTLOADER SAFETY. Installing GRUB writes to an ESP and to EFI NVRAM — state
# SHARED with whatever system is booting this host right now. When rehearsing a
# restore onto a spare partition of the LIVE disk, that shared ESP is the live
# one, and touching it would corrupt the running boot chain. So the bootloader
# step only runs against an ESP you name explicitly (ESP_DEV=/dev/…), and never
# against an ESP that is currently mounted at the live /boot/efi. Set
# SKIP_BOOTLOADER=1 to skip it entirely (the safe default for a rehearsal); the
# script then prints the exact manual bootloader commands for the real restore.
set -euo pipefail

SRC=/mnt/usb-backup
TARGET="${1:-}"
SKIP_BOOTLOADER="${SKIP_BOOTLOADER:-0}"
ESP_DEV="${ESP_DEV:-}"

die() { echo "ERROR: $*" >&2; exit 1; }
warn() { echo "WARNING: $*" >&2; }

[ "$(id -u)" -eq 0 ] || die "must run as root"
[ -n "$TARGET" ]      || die "usage: $0 /path/to/mounted/new/root"
[ -d "$TARGET" ]      || die "target '$TARGET' is not a directory"
[ "$TARGET" != "/" ]  || die "refusing to restore over the LIVE root filesystem"
mountpoint -q "$TARGET" || die "target '$TARGET' is not a mountpoint — mount the new root filesystem there first"
[ -d "${SRC}/rootfs" ]  || die "no rootfs backup found at ${SRC}/rootfs — is the USB volume mounted?"

# Refuse to overwrite a target that is currently running something.
if [ -d "${TARGET}/proc/1" ]; then die "'$TARGET' looks like a LIVE system (has /proc/1) — refusing"; fi

echo "=== restoring ${SRC}/rootfs -> ${TARGET} ==="
echo "    source captured: $(stat -c %y "${SRC}/rootfs" 2>/dev/null || echo unknown)"
read -r -p "    Type RESTORE to proceed: " confirm
[ "$confirm" = "RESTORE" ] || die "aborted by operator"

# Same flag set as the backup — see backup.sh for why each is load-bearing.
rsync -aHAXS --numeric-ids --info=progress2 \
  "${SRC}/rootfs/" "${TARGET}/"

# ------------------------------------------------------------------ fstab --
# Rewrite the root + ESP entries to the NEW disk's real UUIDs (stale UUIDs are
# the single most common reason a restored system will not boot), while
# PRESERVING every other captured entry. The captured fstab arrived with the
# rootfs and is now at ${TARGET}/etc/fstab.
echo "=== regenerating /etc/fstab (root/ESP remapped, other volumes preserved) ==="
CAPTURED_FSTAB="${TARGET}/etc/fstab"
[ -f "$CAPTURED_FSTAB" ] || die "captured /etc/fstab missing under target — cannot regenerate safely"
cp -a "$CAPTURED_FSTAB" "${TARGET}/etc/fstab.restored-original"

ROOT_SRC=$(findmnt -no SOURCE --target "$TARGET")
ROOT_UUID=$(blkid -s UUID -o value "$ROOT_SRC")
[ -n "$ROOT_UUID" ] || die "could not read a UUID for the target root device $ROOT_SRC"

# Determine the ESP UUID to write into the / boot/efi line, if any ESP applies.
ESP_UUID=""
if [ -n "$ESP_DEV" ]; then
  ESP_UUID=$(blkid -s UUID -o value "$ESP_DEV" || true)
fi

# Rewrite fstab line-by-line from the captured original.
#   - root line (field2 == "/")           -> new root UUID
#   - ESP line  (field2 == "/boot/efi")   -> new ESP UUID, or commented out if
#                                            no ESP was supplied this run
#   - any other UUID= volume that no longer resolves -> keep, add `nofail`,
#     and collect it for a remap warning
#   - everything else (swap file, bind mounts, path-based) -> verbatim
NEW_FSTAB="$(mktemp)"
REMAP_LIST="$(mktemp)"
: > "$REMAP_LIST"
{
  echo "# regenerated by restore.sh on $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# root and ESP remapped to the restored disk; other volumes preserved from"
  echo "# the captured fstab (original kept at /etc/fstab.restored-original)."
} > "$NEW_FSTAB"

while IFS= read -r line || [ -n "$line" ]; do
  # Pass through blanks and comments untouched.
  case "$line" in
    ''|\#*) printf '%s\n' "$line" >> "$NEW_FSTAB"; continue ;;
  esac
  # Split into fields without losing the original spacing intent.
  fs=$(printf '%s' "$line" | awk '{print $1}')
  mp=$(printf '%s' "$line" | awk '{print $2}')

  if [ "$mp" = "/" ]; then
    printf 'UUID=%s / ext4 defaults 0 1\n' "$ROOT_UUID" >> "$NEW_FSTAB"
    continue
  fi
  if [ "$mp" = "/boot/efi" ]; then
    if [ -n "$ESP_UUID" ]; then
      printf 'UUID=%s /boot/efi vfat umask=0077 0 1\n' "$ESP_UUID" >> "$NEW_FSTAB"
    else
      printf '# /boot/efi NOT remapped — no ESP supplied to this restore run.\n' >> "$NEW_FSTAB"
      printf '# original: %s\n' "$line" >> "$NEW_FSTAB"
    fi
    continue
  fi

  # Non-root, non-ESP. If it names a UUID that does not resolve on this system,
  # keep it but make it non-fatal to boot, and record it for remapping.
  uuid=$(printf '%s' "$fs" | sed -n 's/^UUID=//p')
  if [ -n "$uuid" ] && ! blkid -U "$uuid" >/dev/null 2>&1; then
    opts=$(printf '%s' "$line" | awk '{print $4}')
    case ",$opts," in
      *,nofail,*) newline="$line" ;;
      *)          newline=$(printf '%s' "$line" | awk '{ $4=$4",nofail"; print }') ;;
    esac
    printf '%s\n' "$newline" >> "$NEW_FSTAB"
    printf '  %s  (was UUID=%s, mount %s)\n' "$fs" "$uuid" "$mp" >> "$REMAP_LIST"
  else
    printf '%s\n' "$line" >> "$NEW_FSTAB"
  fi
done < "${TARGET}/etc/fstab.restored-original"

cp "$NEW_FSTAB" "${TARGET}/etc/fstab"
rm -f "$NEW_FSTAB"

echo "    root: ${ROOT_SRC} (UUID=${ROOT_UUID})"
if [ -n "$ESP_UUID" ]; then echo "    ESP:  ${ESP_DEV} (UUID=${ESP_UUID})"; else echo "    ESP:  not remapped this run"; fi
if [ -s "$REMAP_LIST" ]; then
  warn "the following captured volumes did not resolve on this system and were marked nofail —"
  warn "re-point them to the new devices by UUID before relying on them:"
  cat "$REMAP_LIST" >&2
fi
rm -f "$REMAP_LIST"

# --------------------------------------------------------------- swap --
# The backup EXCLUDES swap contents (correct — swap is never backed up), but the
# restored fstab still names the swap FILE, so its swap unit fails on first boot
# (a degraded-but-harmless state — proven by the sda3 boot rehearsal, where
# swap.img.swap was the sole failed unit). Recreate any swap FILE the restored
# fstab names but that is missing, sized from meta/swap-size-bytes.txt when the
# backup recorded it, else an 8 GiB default. Swap PARTITIONS (/dev/… or UUID=)
# are left alone — only files are recreated.
echo "=== recreating swap file(s) named in the restored fstab ==="
SWAP_DEFAULT_BYTES=8589934592   # 8 GiB fallback when the backup recorded no size
swap_target_bytes() {
  if [ -f "${SRC}/meta/swap-size-bytes.txt" ]; then
    tr -cd '0-9' < "${SRC}/meta/swap-size-bytes.txt"
  else
    printf '%s' "$SWAP_DEFAULT_BYTES"
  fi
}
awk '$0 !~ /^[[:space:]]*#/ && $3=="swap" && $1 ~ /^\// && $1 !~ /^\/dev\// {print $1}' \
  "${TARGET}/etc/fstab" | while IFS= read -r swp; do
  dst="${TARGET}${swp}"
  if [ -e "$dst" ]; then echo "    ${swp}: already present, left as-is"; continue; fi
  bytes=$(swap_target_bytes)
  echo "    ${swp}: absent — recreating ${bytes} bytes"
  rm -f "$dst"
  if ! fallocate -l "$bytes" "$dst" 2>/dev/null; then
    dd if=/dev/zero of="$dst" bs=1M count=$(( bytes / 1048576 )) status=none
  fi
  chmod 600 "$dst"
  if mkswap "$dst" >/dev/null 2>&1; then echo "    ${swp}: mkswap OK"; else warn "mkswap failed on ${swp} — recreate it manually before relying on swap"; fi
done

# ------------------------------------------------------------- bootloader --
if [ "$SKIP_BOOTLOADER" = "1" ]; then
  echo "=== bootloader step SKIPPED (SKIP_BOOTLOADER=1) ==="
  DISK=$(lsblk -no PKNAME "$ROOT_SRC" | head -1)
  echo "    To install the bootloader for the real restore, from this script's host:"
  echo "      for d in dev dev/pts proc sys run; do mount --rbind /\$d ${TARGET}/\$d; done"
  echo "      mount <NEW_ESP_DEV> ${TARGET}/boot/efi"
  echo "      chroot ${TARGET} grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ubuntu --recheck"
  echo "      chroot ${TARGET} update-grub"
  echo "    (target disk detected as /dev/${DISK})"
else
  # Only touch an ESP the operator named explicitly, and never the live one.
  [ -n "$ESP_DEV" ] || die "bootloader requested but no ESP_DEV named — refusing to guess an ESP (set ESP_DEV=/dev/… or SKIP_BOOTLOADER=1)"
  live_esp=$(findmnt -no SOURCE /boot/efi 2>/dev/null || true)
  if [ -n "$live_esp" ] && [ "$live_esp" = "$ESP_DEV" ]; then
    die "ESP_DEV=$ESP_DEV is the LIVE /boot/efi — refusing to overwrite the running boot chain"
  fi
  echo "=== reinstalling bootloader in chroot (ESP=${ESP_DEV}) ==="
  for d in dev dev/pts proc sys run; do mount --rbind "/$d" "${TARGET}/$d" 2>/dev/null || true; done
  mkdir -p "${TARGET}/boot/efi"
  mountpoint -q "${TARGET}/boot/efi" || mount "$ESP_DEV" "${TARGET}/boot/efi" || true
  DISK=$(lsblk -no PKNAME "$ROOT_SRC" | head -1)
  chroot "$TARGET" /bin/bash -c "grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ubuntu --recheck || grub-install /dev/${DISK} --recheck; update-grub" \
    || warn "grub-install reported a problem — inspect before rebooting"
  for d in boot/efi run sys proc dev/pts dev; do umount -lR "${TARGET}/$d" 2>/dev/null || true; done
fi

sync
echo
echo "=== restore complete ==="
echo "Before rebooting, check:"
echo "  1. ${TARGET}/etc/fstab lists every filesystem you actually have"
echo "  2. ls ${TARGET}/boot/vmlinuz-* shows a kernel"
echo "  3. efibootmgr -v lists an 'ubuntu' entry (only after a real bootloader install)"
echo
echo "The CI cache (${SRC}/var-cache-ci-runner) is NOT restored automatically."
echo "It holds the k3s containerd image store, which is a reconstructible cache."
echo "To restore it onto a mounted target volume:"
echo "  rsync -aHAXS --numeric-ids ${SRC}/var-cache-ci-runner/ /path/to/new/cache/volume/"
