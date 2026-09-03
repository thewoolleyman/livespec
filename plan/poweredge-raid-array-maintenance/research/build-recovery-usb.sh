#!/bin/bash
# build-recovery-usb.sh — build the "Ubuntu Desktop Recovery USB" on the PNY stick.
# Everything addresses the disk via its immutable by-id path; the Toshiba backup
# (usb-TOSHIBA_External_USB_3.0_*) is never touched.
set -euo pipefail

DISK="/dev/disk/by-id/usb-PNY_USB_3.2.1_FD_071C556D2BABC126-0:0"
P1="${DISK}-part1"
P2="${DISK}-part2"
MNT=/mnt/recovery-usb
RELEASE=resolute
MIRROR=http://archive.ubuntu.com/ubuntu

echo "=== [0] sanity: resolve and verify the PNY ==="
REAL=$(readlink -f "$DISK")
lsblk -d -o NAME,SIZE,VENDOR,MODEL,SERIAL "$REAL"
MODEL=$(lsblk -dno VENDOR,MODEL "$REAL")
case "$MODEL" in *PNY*) echo "verified PNY: $REAL";; *) echo "ABORT: $REAL is not the PNY ($MODEL)"; exit 1;; esac
SIZE_G=$(lsblk -dbno SIZE "$REAL"); SIZE_G=$((SIZE_G/1024/1024/1024))
[ "$SIZE_G" -lt 130 ] || { echo "ABORT: $REAL is ${SIZE_G}G — too big to be the 128GB PNY"; exit 1; }

echo "=== [1] unmount any auto-mounts ==="
for p in $(lsblk -lno NAME "$REAL" | tail -n +2); do
  umount -f "/dev/$p" 2>/dev/null || true
done

echo "=== [2] partition: GPT, 1G ESP + rest ext4 ==="
wipefs -a "$REAL"
sgdisk --zap-all "$REAL"
sgdisk -n 1:0:+1G  -t 1:EF00 -c 1:RECOVERY-ESP "$REAL"
sgdisk -n 2:0:0    -t 2:8300 -c 2:RECOVERY-ROOT "$REAL"
partprobe "$REAL"; sleep 3; udevadm settle
[ -b "$P1" ] && [ -b "$P2" ] || { echo "ABORT: by-id partitions did not appear"; exit 1; }

echo "=== [3] filesystems ==="
mkfs.vfat -F 32 -n RECESP "$P1"
mkfs.ext4 -q -F -L RECOVERY-USB "$P2"

echo "=== [4] mount + debootstrap $RELEASE ==="
mkdir -p "$MNT"
mount "$P2" "$MNT"
debootstrap --arch=amd64 "$RELEASE" "$MNT" "$MIRROR"

echo "=== [5] base config ==="
mkdir -p "$MNT/boot/efi"
mount "$P1" "$MNT/boot/efi"
UUID_ROOT=$(blkid -s UUID -o value "$P2")
UUID_ESP=$(blkid -s UUID -o value "$P1")
cat > "$MNT/etc/fstab" <<EOF
UUID=$UUID_ROOT / ext4 defaults,noatime 0 1
UUID=$UUID_ESP /boot/efi vfat umask=0077 0 1
EOF
echo recovery-usb > "$MNT/etc/hostname"
cat > "$MNT/etc/hosts" <<EOF
127.0.0.1 localhost
127.0.1.1 recovery-usb
EOF
cat > "$MNT/etc/apt/sources.list" <<EOF
deb $MIRROR $RELEASE main restricted universe multiverse
deb $MIRROR $RELEASE-updates main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu $RELEASE-security main restricted universe multiverse
EOF
cp /etc/resolv.conf "$MNT/etc/resolv.conf" || true

for d in dev dev/pts proc sys; do mount --bind "/$d" "$MNT/$d"; done
trap 'for d in dev/pts dev proc sys boot/efi; do umount -l "$MNT/$d" 2>/dev/null || true; done; umount -l "$MNT" 2>/dev/null || true' EXIT

echo "=== [6] install packages (kernel, grub, desktop, sshd, storage tools) ==="
chroot "$MNT" /bin/bash -euxo pipefail <<'CHROOT'
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q locales
locale-gen en_US.UTF-8
apt-get install -y -q linux-generic grub-efi-amd64 grub-efi-amd64-signed shim-signed efibootmgr
apt-get install -y -q openssh-server sudo network-manager
apt-get install -y -q lvm2 mdadm gdisk parted dosfstools smartmontools nvme-cli ipmitool rsync pciutils usbutils debootstrap curl wget vim less htop
apt-get install -y -q ubuntu-desktop-minimal
echo 'root:password' | chpasswd
cat > /etc/ssh/sshd_config.d/99-recovery.conf <<EOF
PermitRootLogin yes
PasswordAuthentication yes
EOF
cat > /etc/sudoers.d/99-recovery <<EOF
root ALL=(ALL) NOPASSWD:ALL
%sudo ALL=(ALL) NOPASSWD:ALL
EOF
chmod 440 /etc/sudoers.d/99-recovery
mkdir -p /etc/netplan
cat > /etc/netplan/01-recovery.yaml <<EOF
network:
  version: 2
  renderer: NetworkManager
EOF
chmod 600 /etc/netplan/01-recovery.yaml
systemctl enable ssh NetworkManager
echo 'GRUB_DISABLE_OS_PROBER=true' >> /etc/default/grub
sed -i 's/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=3/' /etc/default/grub || true
grub-install --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot --removable --no-nvram
update-grub
CHROOT

echo "=== [7] copy perccli onto the stick ==="
if [ -d /opt/MegaRAID ]; then cp -a /opt/MegaRAID "$MNT/opt/"; echo "perccli copied"; fi

echo "=== [8] drop a README for the rebuild window ==="
cat > "$MNT/root/README-RECOVERY.md" <<'EOF'
Ubuntu Desktop Recovery USB (built 2026-09-03 for the poweredge-xubuntu rebuild)
- login: root / password  (sshd: PasswordAuthentication+PermitRootLogin yes)
- DHCP on all NICs via NetworkManager; on poweredge it comes up at 192.168.1.200
- tools: lvm2 mdadm gdisk parted smartmontools nvme-cli ipmitool rsync debootstrap
- perccli at /opt/MegaRAID/perccli/perccli64
- the Toshiba backup + restore.sh mount at /mnt/usb-backup (label POWEREDGE-BACKUP)
EOF

echo "=== [9] unmount cleanly ==="
sync
for d in dev/pts dev proc sys boot/efi; do umount "$MNT/$d"; done
umount "$MNT"
trap - EXIT
echo "=== BUILD COMPLETE ==="
